# environment

**Source:** `compose.yaml`, `.env.example`, `backend/Dockerfile`, `frontend/Dockerfile`, `backend/src/voices/config.py`   ·   **Tests:** `backend/tests/test_config.py`

## Purpose
Runs every part of the app with one command, `docker compose up --build`, so a reviewer
needs only Docker. Plan: [atlas plate 04](../atlas/04-environment.md).

## Public interface
- `docker compose up --build` — starts every service; the app is at `http://localhost:5173`.
- `docker compose down --volumes` — stops it and erases all stored data.
- `voices.config.load_settings()` — the backend's settings, read from the environment.

## How it works
Seven services. `postgres` (with the pgvector extension) and `redis` start first and
report healthy. `setup` then creates the tables and exits; `api` and `worker` wait for it
to finish successfully. `beat` schedules jobs onto Redis. `frontend` serves the built web
app on port 5173 and passes every `/api` request through to `api`, so only one port is
exposed. The four backend services are all built from the same `backend/` folder and differ only
in the command they run.

## Uses
[database](database.md), [api](api.md), [worker](worker.md), [frontend](frontend.md), [logging](logging.md).

## Used by
- [api](api.md), [worker](worker.md) and [database](database.md) (setup) read their
  settings through `voices.config.load_settings()`.
- The README's install and run steps.

## Configuration and data
- `.env` (copied from `.env.example`): `PORT` (default 5173), the port the app is opened
  on; `OPENROUTER_API_KEY`, needed once tagging and
  reports exist; the app starts without it.
- Set by `compose.yaml` for the backend services: `DATABASE_URL`, `REDIS_URL`, `LOG_DIR`,
  and `SERVICE_NAME` (each container's own name, used in its log lines).
- Named volumes: `postgres-data`, `redis-data` (Redis writes an append-only file),
  `model-cache` (the embedding model's files, from build step 2), `logs`.
