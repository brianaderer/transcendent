# api

**Source:** `backend/src/voices/api/main.py`, `backend/src/voices/health.py`   ·   **Tests:** `backend/tests/test_health_route.py`

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
logging as the `api` service, and checks Postgres and Redis on each health request.

## Uses
[logging](logging.md), [environment](environment.md) (settings), Postgres, Redis.

## Used by
[frontend](frontend.md).

## Configuration and data
`DATABASE_URL`, `REDIS_URL`, `LOG_DIR`.
