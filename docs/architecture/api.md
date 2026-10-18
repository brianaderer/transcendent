# api

**Source:** `backend/src/voices/api/main.py`, `backend/src/voices/health.py`   ·   **Tests:** `backend/tests/test_health_route.py`, `backend/tests/test_health.py`

## Purpose
The web API the frontend calls. Every route lives under `/api`.

## Public interface
- `GET /api/health` — `200 {"status": "ok", "checks": {...}}` when every dependency
  answers; `503 {"status": "degraded", "checks": {...}}` naming each one that doesn't.
- `GET /api/openapi.json` — the API description the frontend's typed client will be
  generated from (atlas OPEN-1).
- `create_app(checks)` — builds the app around a dictionary of named health checks, so
  tests pass stand-ins. `create_production_app()` wires in the real ones.
- `database_is_reachable(url)`, `queue_is_reachable(url)` — the real checks.

## How it works
Uvicorn runs `create_production_app` (a factory), which reads settings, configures
logging under the container's `SERVICE_NAME` (`api`), and checks Postgres and Redis on each health request. A
health check that fails logs why (`health.database_unreachable`, `health.queue_unreachable`).
Every request is logged as `api.request` with its method, path, status and time taken,
under a trace id of its own; a request that raises is logged as `api.request_failed` with
the full error, then re-raised.

## Uses
[logging](logging.md), [environment](environment.md) (settings), Postgres, Redis.

## Used by
[frontend](frontend.md) (`GET /api/health`); [environment](environment.md) runs it as the
`api` service.

## Configuration and data
`DATABASE_URL`, `REDIS_URL`, `LOG_DIR`.
