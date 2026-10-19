"""The web API. Every route lives under /api, which the frontend's server passes through."""

import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import redis
from celery import Celery
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel
from starlette.types import ASGIApp, Receive, Scope, Send

from voices.config import HISTORY_DAYS, load_settings
from voices.db.explore_store import ExploreStore
from voices.db.retrieval_store import RetrievalStore
from voices.db.store import connect_store
from voices.db.topic_store import TopicStore
from voices.events import server_sent_events
from voices.explore.cache import RedisMapCache
from voices.explore.day_range import DayRange, InvalidRange
from voices.explore.explore import Explore
from voices.explore.projection import flatten
from voices.explore.shapes import Days, Map, TopicInRange
from voices.health import database_is_reachable, queue_is_reachable
from voices.log import configure_logging, log_event, tracing
from voices.report.launcher import RunLauncher, RunStarted
from voices.report.runs import RunNotFound, RunState, RunStore, is_run_stream
from voices.retrievals.retrieval_stats import RetrievalStatistics
from voices.retrievals.shapes import Agent, RetrievalFilter, RetrievalStats
from voices.topics.shapes import TopicDetail
from voices.topics.topic_detail import TopicDetails, TopicNotFound

HealthChecks = dict[str, Callable[[], bool]]
STREAMS = {"ingestion"}
LIVE_EVENTS_PATH = "/api/streams/"
SMALLEST_RESPONSE_TO_COMPRESS = 1000  # bytes; a range's map runs to megabytes


class RunRequest(BaseModel):
    start: date
    end: date


class Runs(Protocol):
    def start(self, days: DayRange) -> RunStarted: ...
    def state(self, run_id: str) -> RunState: ...


class ExploreReads(Protocol):
    def days(self) -> Days: ...
    def topics(self, days: DayRange) -> list[TopicInRange]: ...
    def map(self, days: DayRange) -> Map: ...


class TopicReads(Protocol):
    def detail(self, topic_id: int) -> TopicDetail: ...


class RetrievalReads(Protocol):
    def stats(self, which: RetrievalFilter) -> RetrievalStats: ...


@dataclass(frozen=True)
class ApiServices:
    """What the routes depend on, passed in so tests can use stand-ins."""

    health_checks: HealthChecks
    ingestion_status: Callable[[], dict]
    event_stream: Callable[[str], AsyncIterator[str]]
    explore: ExploreReads
    runs: Runs
    topics: TopicReads
    retrievals: RetrievalReads


logger = logging.getLogger(__name__)
TRACE_ID_HEX_DIGITS = 12  # long enough to be unique across a day of requests


def create_app(services: ApiServices) -> FastAPI:
    app = FastAPI(
        title="Community Voices",
        openapi_url="/api/openapi.json",
        generate_unique_id_function=name_operation_after_its_function,
    )
    app.middleware("http")(log_each_request)
    app.add_middleware(CompressAllButLiveEvents, minimum_size=SMALLEST_RESPONSE_TO_COMPRESS)
    app.exception_handler(InvalidRange)(refuse_the_range)
    app.exception_handler(TopicNotFound)(say_the_topic_is_not_found)

    @app.get("/api/health")
    def report_health() -> JSONResponse:
        """Say whether every dependency answers, and name any that doesn't."""
        results = {name: check() for name, check in services.health_checks.items()}
        healthy = all(results.values())
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={"status": "ok" if healthy else "degraded", "checks": results},
        )

    @app.get("/api/ingestion")
    def report_ingestion() -> dict:
        """How far the catch-up has got through the history."""
        return {**services.ingestion_status(), "days_wanted": HISTORY_DAYS}

    @app.get("/api/streams/{stream}/events")
    def stream_events(stream: str) -> StreamingResponse:
        """Live events as server-sent events (atlas plate 41)."""
        if stream not in STREAMS and not is_run_stream(stream):
            raise HTTPException(status_code=404, detail=f"no stream named {stream}")
        return StreamingResponse(services.event_stream(stream), media_type="text/event-stream")

    @app.get("/api/days")
    def report_days() -> Days:
        """Posts and comments per day across the history, and the latest day loaded."""
        return services.explore.days()

    @app.get("/api/topics")
    def report_topics(start: date, end: date) -> list[TopicInRange]:
        """The topics with engagement in the range, busiest first, each with its badge."""
        return services.explore.topics(DayRange(start, end))

    @app.get("/api/map")
    def report_map(start: date, end: date) -> Map:
        """Every post and comment written in the range, placed on the range's own map."""
        return services.explore.map(DayRange(start, end))

    @app.post("/api/runs")
    def start_run(request: RunRequest) -> RunStarted:
        """Starts a comparison for the range: both versions, then their scores (plate 70)."""
        return services.runs.start(DayRange(request.start, request.end))

    @app.get("/api/runs/{run_id}")
    def report_run(run_id: str) -> RunState:
        """A run's state: running, finished with both versions and their scores, or failed."""
        try:
            return services.runs.state(run_id)
        except RunNotFound as error:
            raise HTTPException(status_code=404, detail=f"no run {run_id}") from error

    @app.get("/api/topics/{topic_id}")
    def report_topic(topic_id: int) -> TopicDetail:
        """One topic: its engagement each day across the history, its typical posts, and the
        tagging decisions that built it. 404 for a topic that doesn't exist."""
        return services.topics.detail(topic_id)

    @app.get("/api/retrievals")
    def report_retrievals(
        start: date, end: date, agent: Agent = "report", run: str | None = None
    ) -> RetrievalStats:
        """Which posts written in the range an agent retrieved most, and its retrievals per
        topic; from one run, or from every run when none is named."""
        return services.retrievals.stats(RetrievalFilter(agent, DayRange(start, end), run))

    return app


class CompressAllButLiveEvents:
    """Gzip for every answer except the live event streams: compression holds events back
    until a buffer fills, so the browser would see none of them as they happen."""

    def __init__(self, app: ASGIApp, minimum_size: int):
        self.app = app
        self.compressed = GZipMiddleware(app, minimum_size=minimum_size)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"].startswith(LIVE_EVENTS_PATH):
            await self.app(scope, receive, send)
        else:
            await self.compressed(scope, receive, send)


def name_operation_after_its_function(route: APIRoute) -> str:
    """The frontend's generated client names its calls after these (atlas OPEN-1)."""
    return route.name


async def refuse_the_range(_request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(error)})


async def say_the_topic_is_not_found(_request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"no topic with id {error}"})


async def log_each_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Log every request with its outcome, under a trace id of its own (atlas plate 05)."""
    started = time.perf_counter()
    where = {"method": request.method, "path": request.url.path}
    with tracing(new_request_trace_id()):
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("api.request_failed", extra=where)
            raise
        log_event(
            logger,
            "api.request",
            **where,
            status=response.status_code,
            milliseconds=milliseconds_since(started),
        )
    return response


def new_request_trace_id() -> str:
    return f"request-{uuid.uuid4().hex[:TRACE_ID_HEX_DIGITS]}"


def milliseconds_since(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def create_production_app() -> FastAPI:
    settings = load_settings()
    configure_logging(settings.service_name, settings.log_dir)
    log_event(logger, "api.started")
    store = connect_store(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    map_cache = RedisMapCache(redis_client)
    return create_app(
        ApiServices(
            health_checks={
                "database": lambda: database_is_reachable(settings.database_url),
                "queue": lambda: queue_is_reachable(settings.redis_url),
            },
            ingestion_status=store.ingestion_status,
            event_stream=lambda stream: server_sent_events(settings.redis_url, stream),
            explore=Explore(ExploreStore(store.engine), map_cache, flatten),
            runs=RunLauncher(RunStore(redis_client), queue_on(settings.redis_url)),
            topics=TopicDetails(TopicStore(store.engine)),
            retrievals=RetrievalStatistics(RetrievalStore(store.engine)),
        )
    )


def queue_on(redis_url: str) -> Callable[[str, list[str]], object]:
    """Sends a task to the worker by name, so the API doesn't import the worker's code."""
    celery = Celery(broker=redis_url)
    return lambda name, arguments: celery.send_task(name, args=arguments)
