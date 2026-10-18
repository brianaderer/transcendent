"""The web API. Every route lives under /api, which the frontend's server passes through."""

import logging
from collections.abc import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from voices.config import load_settings
from voices.health import database_is_reachable, queue_is_reachable
from voices.log import configure_logging

HealthChecks = dict[str, Callable[[], bool]]


def create_app(checks: HealthChecks) -> FastAPI:
    app = FastAPI(title="Community Voices", openapi_url="/api/openapi.json")

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
    logging.getLogger(__name__).info("api.started")
    return create_app(
        {
            "database": lambda: database_is_reachable(settings.database_url),
            "queue": lambda: queue_is_reachable(settings.redis_url),
        }
    )
