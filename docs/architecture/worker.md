# worker

**Source:** `backend/src/voices/worker/app.py`, `backend/src/voices/worker/catch_up_task.py`   ·   **Tests:** `backend/tests/test_worker.py`, `backend/tests/test_catch_up_task.py`

## Purpose
Runs background jobs through Celery, with Celery Beat scheduling them. Its main job is the
catch-up that fills the database from the archive ([atlas plate 40](../atlas/40-backend.md),
[ingestion](ingestion.md)).

## Public interface
- `celery_app` — the Celery application.
- Task `voices.catch_up` — processes every complete day not yet done; returns whether it
  ran (it does nothing while another catch-up is running).
- Task `voices.ping` — answers `"pong"`, to prove the worker is consuming jobs.
- `catch_up_once(lock, run)`, `forget_stale_catch_up(queue)`, `catch_up_now()` in
  `catch_up_task.py`.

## How it works
- **When the catch-up runs:** when a worker starts (so first start and every restart catch
  up), and daily at 06:00 UTC from Beat. Nothing in the web app queues it yet; it can be
  queued by hand as the `voices.catch_up` task.
- **One at a time:** a Redis lock (`lock:catch-up`) makes a second request do nothing while a
  catch-up is running. A worker that is starting clears any leftover lock first: none can be
  running yet, so a held lock belongs to a run that died with its worker.
- **One job, days in order:** the catch-up is one job that walks the missing days oldest
  first, each day in its own transaction and under its own trace id (`day-YYYY-MM-DD`). The
  embedding model, database and archive connections are built once per worker process.

Redis is both the queue and the result store. Celery's own logging is replaced with the
JSON logging, named after the container (`SERVICE_NAME`): the worker's lines go to
`worker.jsonl`, Beat's to `beat.jsonl`. Celery keeps retrying the Redis connection at
startup (`broker_connection_retry_on_startup`), which also silences its startup warning.

## Uses
[ingestion](ingestion.md), [database](database.md) (`voices.db.store`), [events](events.md),
[logging](logging.md), [environment](environment.md) (settings), Redis.

## Used by
[environment](environment.md) runs it twice, as the `worker` and `beat` services. Beat and
the worker's own start-up queue `voices.catch_up`.

## Configuration and data
`REDIS_URL`, `DATABASE_URL`, `MODEL_DIR`, `LOG_DIR`, `SERVICE_NAME`. Beat keeps its schedule
file in `/tmp` inside its container. The worker uses about 2 GB while embedding.
