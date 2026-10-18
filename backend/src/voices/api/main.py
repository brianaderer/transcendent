"""The web API. Every route lives under /api, which the frontend's server passes through."""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from voices.config import load_settings
from voices.health import database_is_reachable, queue_is_reachable
from voices.log import configure_logging, log_event, tracing

HealthChecks = dict[str, Callable[[], bool]]

logger = logging.getLogger(__name__)


def create_app(checks: HealthChecks) -> FastAPI:
    app = FastAPI(title="Community Voices", openapi_url="/api/openapi.json")
    app.middleware("http")(log_each_request)

    @app.get("/api/health")
    def report_health() -> JSONResponse:
        """Say whether every dependency answers, and name any that doesn't."""
        results = {name: check() for name, check in checks.items()}
        healthy = all(results.values())
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={"status": "ok" if healthy else "degraded", "checks": results},
        )

    return app


def create_production_app() -> FastAPI:
    settings = load_settings()
    configure_logging("api", settings.log_dir)
    log_event(logger, "api.started")
    return create_app(
        {
            "database": lambda: database_is_reachable(settings.database_url),
            "queue": lambda: queue_is_reachable(settings.redis_url),
        }
    )


async def log_each_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Log every request with its outcome, under a trace id of its own (atlas plate 05)."""
    started = time.perf_counter()
    with tracing(f"request-{uuid.uuid4().hex[:12]}"):
        response = await call_next(request)
        log_event(
            logger,
            "api.request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            milliseconds=round((time.perf_counter() - started) * 1000),
        )
    return response
