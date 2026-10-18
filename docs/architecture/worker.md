# worker

**Source:** `backend/src/voices/worker/app.py`   ·   **Tests:** none yet (build step 2 adds the jobs)

## Purpose
Runs background jobs through Celery, with Celery Beat scheduling them. Ingestion's
day-by-day catch-up arrives in build step 2 ([atlas plate 40](../atlas/40-backend.md)).

## Public interface
- `celery_app` — the Celery application.
- Task `voices.ping` — answers `"pong"`, to prove the worker is consuming jobs.

## How it works
Redis is both the queue and the result store. The Beat schedule is empty for now. Celery's
own logging is replaced with the JSON logging as the `worker` service (Beat's lines also
appear under `worker`).

## Uses
[logging](logging.md), [environment](environment.md) (settings), Redis.

## Used by
Nothing yet.

## Configuration and data
`REDIS_URL`, `LOG_DIR`. Beat keeps its schedule file in `/tmp` inside its container.
