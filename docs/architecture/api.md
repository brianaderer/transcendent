# api

**Source:** `backend/src/voices/api/main.py`, `backend/src/voices/health.py`   ·   **Tests:** `backend/tests/test_health_route.py`, `backend/tests/test_health.py`, `backend/tests/test_ingestion_route.py`

## Purpose
The web API the frontend calls. Every route lives under `/api`.

## Public interface
- `GET /api/health` — `200 {"status": "ok", "checks": {...}}` when every dependency
  answers; `503 {"status": "degraded", "checks": {...}}` naming each one that doesn't.
- `GET /api/ingestion` — how far the catch-up has got: `days_done`, `days_wanted` (56, added
  by the route), `posts`,
  `latest_day`, `running_day`, `failed_day`, `failed_reason` (why the latest failed day
  failed).
- `GET /api/streams/{stream}/events` — live events as server-sent events ([events](events.md));
  404 for a stream that doesn't exist.
- `GET /api/openapi.json` — the API description the frontend's typed client will be
  generated from (atlas OPEN-1).
- `create_app(services)` — builds the app around `ApiServices` (the health checks, the
  ingestion status and the event stream), so tests pass stand-ins.
  `create_production_app()` wires in the real ones.
- `database_is_reachable(url)`, `queue_is_reachable(url)` — the real checks.

## How it works
Uvicorn runs `create_production_app` (a factory), which reads settings, configures
logging under the container's `SERVICE_NAME` (`api`), and checks Postgres and Redis on each health request. A
health check that fails logs why (`health.database_unreachable`, `health.queue_unreachable`).
Every request is logged as `api.request` with its method, path, status and time taken,
under a trace id of its own; a request that raises is logged as `api.request_failed` with
the full error, then re-raised.

## Uses
[logging](logging.md), [environment](environment.md) (settings and `HISTORY_DAYS`), [database](database.md)
(`voices.db.store` for the ingestion status), [events](events.md), Postgres, Redis.
`HISTORY_DAYS` (the days wanted) comes from `voices.config`.

## Used by
[frontend](frontend.md) (`GET /api/health`, `GET /api/ingestion` and
`GET /api/streams/ingestion/events`); [environment](environment.md) runs it as the `api`
service.

## Configuration and data
`DATABASE_URL`, `REDIS_URL`, `LOG_DIR`, `SERVICE_NAME`.
