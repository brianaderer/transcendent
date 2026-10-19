# worker

**Source:** `backend/src/voices/worker/app.py`, `backend/src/voices/worker/catch_up_task.py`, `backend/src/voices/worker/report_task.py`   ·   **Tests:** `backend/tests/test_worker.py`, `backend/tests/test_catch_up_task.py`, `backend/tests/test_report_task.py` (the comparison run itself is tested in `backend/tests/report/`)

## Purpose
Runs background jobs through Celery, with Celery Beat scheduling them. Its main job is the
catch-up that fills the database from the archive and sorts each day into topics
([atlas plate 40](../atlas/40-backend.md), [ingestion](ingestion.md), [tagging](tagging.md)).
It also runs each comparison run the page starts ([report](report.md)).

## Public interface
- `celery_app` — the Celery application.
- Task `voices.compare(run_id, start, end)` — one comparison run for a date range
  ([report](report.md)), queued by `POST /api/runs`.
- Task `voices.catch_up` — loads and tags every complete day not yet done, queued by Beat,
  a starting worker, and the page's Sync now button (`POST /api/catch-up`); returns whether
  it ran (it does nothing while another catch-up is running); on failure, retries itself
  ten minutes later.
- Task `voices.ping` — answers `"pong"`, to prove the worker is consuming jobs.
- `catch_up_once(lock, run)`, `forget_stale_catch_up(redis_client)`, `catch_up_now()` and
  `backfill_then_catch_up(backfill, catch_up, now)` in `catch_up_task.py`; `backfill` is
  anything with `run()` (`Backfills`) and `catch_up` anything with `run(now)` (`CatchesUp`).
- `compare_now(run_id, start, end)` and `run_and_keep_result(comparison, record, job)` in
  `report_task.py`. `RunJob` is the run's id and range;
  `RunRecord` is where its outcome goes (the `RunStore` and the run's stream); `Comparison`
  is anything with `run(run_id, days)`, so the outcome handling is tested with stand-ins.

## How it works
- **When the catch-up runs:** when a worker starts (so first start and every restart catch
  up), daily at 06:00 UTC from Beat, and whenever someone presses Sync now in the page's
  top bar: `POST /api/catch-up` ([api](api.md)) queues it when a complete day is missing
  and no catch-up is busy. It can still be queued by hand as the `voices.catch_up` task.
- **One at a time:** a Redis lock (`lock:catch-up`) makes a second request do nothing while a
  catch-up is running. A worker that is starting clears any leftover lock first: none can be
  running yet, so a held lock belongs to a run that died with its worker. That holds while there is exactly one worker
  container; with several, a starting worker could clear another's lock.
- **The backfill comes first:** every catch-up starts by running the [seed](seed.md)
  backfill under the same lock, under the trace id `backfill`: on a first boot from the
  seed it rebuilds every vector the seed left behind (posts, then threads, then topic
  centres) before any day is fetched or tagged, so tagging never meets a store without
  them; on every other run nothing is missing and it does nothing. If it fails, the
  catch-up doesn't run, and the task tries again ten minutes later like any failed
  catch-up, carrying on from the last saved batch.
- **One job, days in order:** the catch-up is one job that walks the missing days oldest
  first, under one trace id per day (`day-YYYY-MM-DD`). Each day is loaded
  ([ingestion](ingestion.md)) and then tagged ([tagging](tagging.md)); it is marked done only
  when both have happened; the day's counts are the two sets of counts together. The
  embedding model, database and archive connections, and the settings (including the
  OpenRouter key), are read once per worker process: `_catch_up_runner` connects what the
  steps share (settings, store, embedding model, Redis, the `ingestion` event stream), then
  builds the day's loading, its tagging and the backfill from it. The chat model is connected per day,
  so a missing key fails the day (with a message saying where the key goes) rather than the
  worker's start. A key added to `.env` reaches the worker only when its container is
  created again, which `docker compose up` does when `.env` has changed;
  `docker compose restart` keeps the old settings.
- **A failed catch-up tries again by itself** ten minutes later (`RETRY_FAILED_CATCH_UP_SECONDS`),
  and keeps doing so, so a brief archive outage doesn't hold a first start until the next
  06:00 run. A catch-up that did nothing because another holds the lock is not a failure
  and is not retried. A missing OpenRouter key is not retried either: retrying can't help
  until the key is added and the worker re-created; the reason shows on the page.

- **A comparison run** (`voices.compare`, queued by `POST /api/runs`) runs under the trace id
  `run-<id>`. Both versions of the report run at once, as a LangGraph fan-out with one branch per
  version ([report](report.md)'s `graph`); each branch runs in a copy of the run's logging
  context, so their log lines carry the same trace id. Progress
  is announced on the run's own stream, `run-<id>`. `compare_now` only builds the parts;
  `run_and_keep_result` does the rest. When it finishes, the result is kept in
  Redis for a day and only then is `run.finished` announced, so the page, rereading the run
  when it hears it, finds the result. If anything fails, `run.failed` is logged, the run is
  marked failed with the reason (which the page shows), and only then is `run.failed`
  announced, so the page's reread finds "failed" rather than "running"; the error is then
  raised for the worker's log. The database connection and the embedding model are loaded once per worker process
  (both stores the run reads, `ExploreStore` and `TaggingStore`, share the one connection);
  the report model is connected afresh for each run. Details in [report](report.md).

Redis is both the queue and the result store. Celery's own logging is replaced with the
JSON logging, named after the container (`SERVICE_NAME`): the worker's lines go to
`worker.jsonl`, Beat's to `beat.jsonl`. Celery keeps retrying the Redis connection at
startup (`broker_connection_retry_on_startup`), which also silences its startup warning.

## Uses
[seed](seed.md) (`Backfill`, `BackfillStore`, `RedisBackfillProgress`), [ingestion](ingestion.md), [tagging](tagging.md), [report](report.md) (`ComparisonRun`, `RunParts`, `RunStore`), [database](database.md) (`voices.db.store`, `voices.db.tagging_store`, `voices.db.explore_store`), [explore](explore.md) (`DayRange`; `RedisMapCache.forget_all` for the backfill), [events](events.md),
[logging](logging.md), [environment](environment.md) (settings), Redis.

## Used by
[environment](environment.md) runs it twice, as the `worker` and `beat` services. Beat and
the worker's own start-up queue `voices.catch_up`; [api](api.md) queues `voices.compare`
(`POST /api/runs`) and `voices.catch_up` (`POST /api/catch-up`, the Sync now button).

## Configuration and data
`REDIS_URL`, `DATABASE_URL`, `MODEL_DIR`, `LOG_DIR`, `SERVICE_NAME`, `OPENROUTER_API_KEY`,
`TAGGING_MODEL_NAME`, `REPORT_MODEL_NAME`. Fixed in code: `RETRY_FAILED_CATCH_UP_SECONDS = 600`,
`LOCK_SECONDS = 12 hours`. Beat keeps its schedule
file in `/tmp` inside its container. The worker uses under 1 GB while embedding.
