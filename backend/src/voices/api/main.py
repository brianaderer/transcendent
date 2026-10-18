"""The web API. Every route lives under /api, which the frontend's server passes through."""

import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from voices.config import HISTORY_DAYS, load_settings
from voices.db.store import connect_store
from voices.events import server_sent_events
from voices.health import database_is_reachable, queue_is_reachable
from voices.log import configure_logging, log_event, tracing

HealthChecks = dict[str, Callable[[], bool]]
STREAMS = {"ingestion"}  # report runs get their own streams in build step 5


@dataclass(frozen=True)
class ApiServices:
    """What the routes depend on, passed in so tests can use stand-ins."""

    health_checks: HealthChecks
    ingestion_status: Callable[[], dict]
    event_stream: Callable[[str], AsyncIterator[str]]


logger = logging.getLogger(__name__)
TRACE_ID_HEX_DIGITS = 12  # long enough to be unique across a day of requests


def create_app(services: ApiServices) -> FastAPI:
    app = FastAPI(title="Community Voices", openapi_url="/api/openapi.json")
    app.middleware("http")(log_each_request)

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
        if stream not in STREAMS:
            raise HTTPException(status_code=404, detail=f"no stream named {stream}")
        return StreamingResponse(services.event_stream(stream), media_type="text/event-stream")

    return app


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
    return create_app(
        ApiServices(
            health_checks={
                "database": lambda: database_is_reachable(settings.database_url),
                "queue": lambda: queue_is_reachable(settings.redis_url),
            },
            ingestion_status=store.ingestion_status,
            event_stream=lambda stream: server_sent_events(settings.redis_url, stream),
        )
    )
