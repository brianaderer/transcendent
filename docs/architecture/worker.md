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
own logging is replaced with the JSON logging, named after the container (`SERVICE_NAME`):
the worker's lines say `worker` and go to `worker.jsonl`, Beat's say `beat` and go to
`beat.jsonl`.

## Uses
[logging](logging.md), [environment](environment.md) (settings), Redis.

## Used by
No module sends it jobs yet. [environment](environment.md) runs it twice, as the `worker`
and `beat` services.

## Configuration and data
`REDIS_URL`, `LOG_DIR`, `SERVICE_NAME`. Beat keeps its schedule file in `/tmp` inside its container.
