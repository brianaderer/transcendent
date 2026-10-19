# api

**Source:** `backend/src/voices/api/main.py`, `backend/src/voices/health.py`   ·   **Tests:** `backend/tests/test_health_route.py`, `backend/tests/test_health.py`, `backend/tests/test_ingestion_route.py`, `backend/tests/test_explore_routes.py`, `backend/tests/test_topic_and_retrieval_routes.py`, `backend/tests/test_run_routes.py`, `backend/tests/test_sync_route.py` (the route tests share their stand-ins — a fixed `FakeExplore`, `FakeTopics` and `FakeRetrievals`, a `FakeRuns` that starts nothing, a `FakeSync` that queues nothing, an empty event stream, and `stand_in_services(**chosen)`, which builds `ApiServices` from them with the chosen ones replaced — from `backend/tests/stand_ins.py`)

## Purpose
The web API the frontend calls. Every route lives under `/api`.

## Public interface
- `GET /api/health` — `200 {"status": "ok", "checks": {...}}` when every dependency
  answers; `503 {"status": "degraded", "checks": {...}}` naming each one that doesn't.
- `GET /api/ingestion` — how far the catch-up has got: `days_done`, `days_wanted` (56, added
  by the route), `posts`,
  `latest_day`, `running_day`, `failed_day`, `failed_reason` (the error recorded for the
  latest failed day, as the error's message; `null` when no day has failed), and `backfill`:
  while the first boot rebuilds the seed's vectors, what it is preparing and how far it has
  got (`{"what": "posts", "done": 4120, "total": 12682}`; `what` is `posts`, `threads` or
  `topics`), read from the [seed](seed.md) backfill's record in Redis; `null` otherwise.
- `POST /api/catch-up` (route function `sync_now`, so the generated call is `syncNow`) — the
  top bar's Sync now button ([ingestion](ingestion.md)'s `SyncNow`). Works out the missing
  days exactly as the catch-up does (complete days only, six hours after they end, UTC) and
  answers `{queued, reason, missing_days, next_complete_day, next_complete_at}`: `reason` is
  `days_missing` (it queued `voices.catch_up` on the [worker](worker.md), and
  `missing_days` are what it will fetch, oldest first), `nothing_new` (nothing queued; every
  complete day is loaded) or `already_running` (nothing queued; a day is loading or the seed
  is being prepared, so the worker's lock would make a second catch-up do nothing, and
  `missing_days` are what the running one will reach). `next_complete_day` is the first day
  not yet complete and `next_complete_at` when it becomes complete, in UTC.
- `GET /api/streams/{stream}/events` — live events as server-sent events ([events](events.md));
  the streams are `ingestion` and one per comparison run, `run-<id>` (twelve hex digits, checked by
  `is_run_stream` in [report](report.md)'s `runs`); 404 for any other name.
- `GET /api/days`, `GET /api/topics?start=YYYY-MM-DD&end=YYYY-MM-DD`,
  `GET /api/map?start=…&end=…` — the Explore page's reads ([explore](explore.md)): posts per
  day, the range's topics with their badges, and the range's map. Both ends of a range are
  required (422 otherwise); a range that ends before it starts is a 422 saying so.
- `POST /api/runs` (`{start, end}`) — starts a comparison run ([report](report.md)) and answers
  `{run_id, stream}`; a backwards range is a 422. `GET /api/runs/{run_id}` — the run's state:
  `running`, `finished` with both versions and their scores, or `failed` with the reason; 404
  for a run never started or older than a day. A run's live events come on
  `GET /api/streams/run-<id>/events`.
- `GET /api/topics/{topic_id}` — one topic for the Topic detail page ([topics](topics.md)):
  its summary, its daily engagement, three typical posts and the tagging decisions that
  built it; 404 `{"detail": "no topic with id N"}` for a topic that doesn't exist.
- `GET /api/retrievals?start=…&end=…&agent=report|tagging&run=…` — the Retrieval stats
  page's read ([retrievals](retrievals.md)): the most retrieved posts written in the range,
  retrievals per topic, the runs to choose from and the total. `agent` defaults to
  `report`; with no `run`, every run counts. An unknown agent, or a range that ends before
  it starts, is a 422.
- `GET /api/openapi.json` — the API description the frontend's typed client is generated
  from (atlas OPEN-1). Each operation is named after its route function
  (`name_operation_after_its_function`), so the generated calls read `reportTopics`,
  `useReportMap`, `useReportTopic`, `useReportRetrievals` and so on.
- `create_app(services)` — builds the app around `ApiServices` (the health checks, the
  ingestion status, the backfill's progress, the event stream, the Explore reads, `ExploreReads`, which take a `DayRange`, the
  comparison runs, `Runs`, the Sync now request, `Syncs`, the topic
  read, `TopicReads`, and the retrieval read, `RetrievalReads`, which takes a
  `RetrievalFilter`), so tests pass stand-ins. Responses over 1,000 bytes are gzip-compressed when the browser accepts it
  (a range's map runs to megabytes), except the live event streams under `/api/streams/`
  (`CompressAllButLiveEvents`): compression holds events back until a buffer fills, so the
  browser would see none of them as they happen.
  `create_production_app()` wires in the real ones.
- `database_is_reachable(url)`, `queue_is_reachable(url)` — the real checks.

## How it works
Uvicorn runs `create_production_app` (a factory), which reads settings, configures
logging under the container's `SERVICE_NAME` (`api`), and checks Postgres and Redis on each health request.
It also builds the Explore reads ([explore](explore.md)) on the store's database connection,
with a map cache on Redis at `REDIS_URL`, and the topic and retrieval reads on the same
connection. The comparison runs are [report](report.md)'s `RunLauncher` on the same Redis: a
run's state is kept there, and its job is sent to the worker by name (`queue_on`, a Celery
client, typed `voices.tasks.Queue`), so the API never imports the worker's code. The Sync
now request is [ingestion](ingestion.md)'s `SyncNow` on the same queue, reading the done
days from the store's ledger and counting a catch-up as busy while the store reports a
running day or the backfill's record in Redis says the seed is being prepared
(`catch_up_progress`). A range that ends before it starts is answered with 422 and the reason; a
topic that doesn't exist (`TopicNotFound`) with 404. A
health check that fails logs why (`health.database_unreachable`, `health.queue_unreachable`).
Every request is logged as `api.request` with its method, path, status and time taken,
under a trace id of its own; a request that raises is logged as `api.request_failed` with
the full error, then re-raised.

## Uses
[logging](logging.md), [environment](environment.md) (settings and `HISTORY_DAYS`), [database](database.md)
(`voices.db.store` for the ingestion status, `voices.db.explore_store` for the Explore reads,
`voices.db.topic_store` and `voices.db.retrieval_store` for the topic and retrieval reads),
[events](events.md), [explore](explore.md), [ingestion](ingestion.md) (`SyncNow`, `SyncAnswer`, `CatchUpProgress`, `a_catch_up_is_busy`), [seed](seed.md) (`RedisBackfillProgress` for the backfill's progress), [topics](topics.md), [retrievals](retrievals.md),
[report](report.md) (`RunLauncher`, `RunStarted`, `RunStore`, `RunState`, `RunNotFound`), Postgres,
Redis, Celery (only to send `voices.compare` and `voices.catch_up` to the [worker](worker.md)).
`HISTORY_DAYS` (the days wanted) comes from `voices.config`.

## Used by
[frontend](frontend.md) (`GET /api/health`, `GET /api/ingestion`, `POST /api/catch-up`, `GET /api/days`, `GET /api/topics`,
`GET /api/map`, `GET /api/topics/{topic_id}`, `GET /api/retrievals`, `POST /api/runs`,
`GET /api/runs/{run_id}`, `GET /api/streams/ingestion/events` and
`GET /api/streams/run-<id>/events`, through a client generated from `GET /api/openapi.json`); [environment](environment.md) runs it as the `api`
service.

## Configuration and data
`DATABASE_URL`, `REDIS_URL`, `LOG_DIR`, `SERVICE_NAME`.
