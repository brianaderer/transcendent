# events

**Source:** `backend/src/voices/events.py`, `frontend/src/useLiveEvents.ts`   ·   **Tests:** `backend/tests/test_events.py`, `frontend/src/IngestionStatus.test.tsx`, `frontend/src/explore/ExplorePage.test.tsx`

## Purpose
Live events from the backend's jobs to the browser, as server-sent events (atlas
[plate 41](../atlas/40-backend/41-live-events.md)). Live only: nothing is stored; the logs
are the permanent record.

## Public interface
- `RedisEvents(redis).emit(stream, event_type, **body)` — publishes `{type, time, ...body}`
  on the Redis channel `events:<stream>`, and logs it.
- `server_sent_events(redis_url, stream)` — yields each published event as one SSE message,
  with a heartbeat comment every 15 seconds of quiet.
- `GET /api/streams/{stream}/events` ([api](api.md)) — the stream; only `ingestion` exists
  so far.
- Frontend: `useLiveEvents(stream, onEvent)`.

## How it works
Streams and event types so far: `ingestion` carries `catch_up.started`,
`catch_up.finished`, `day.started` (with `progress`, e.g. "4 of 56"), `day.step` (as each
step of the day begins: `day`, `step`, and how much the step has to get through:
`fetching`; `checking` with `replies`, the comments checked for agreement; `embedding` with `posts`, the posts and comments to embed; `grouping` with
`threads`, the threads due to be encoded and grouped; `tagging` with `groups`, the groups
the agent is to decide, each answered by a `decision.made`; `applying`, saving the
decisions and rebuilding engagement; sent by `announce_step` in
[ingestion](ingestion.md)'s `catch_up.py`, from `DayIngestion` and [tagging](tagging.md)'s
`DayTagging`), `day.finished`
(with the day's counts, from loading and tagging together), `day.failed` (with the error,
as the error's message), `decision.made` (one per group of threads, sent the moment the tagging
agent decides it, from inside the decision's own branch: `group`, `threads`, `action`,
`topic_id`, `label`, `reason`), `mint.merged` (after all of a day's groups are decided, one per
second mint of the same new topic: `group`, `into`), and, on a first
boot from the seed, `backfill.progress` (`what`: `posts`, `threads` or `topics`, `done`,
`total`; one as each step starts and one after each saved batch) and `backfill.finished`
([seed](seed.md)).

## Uses
Redis, [logging](logging.md).

## Used by
[worker](worker.md) (`catch_up_task.py` builds `RedisEvents` and hands its `emit` to the
[ingestion](ingestion.md) catch-up and its `DayIngestion`, which send the day's events and
its first `day.step`s, to [tagging](tagging.md), which sends the tagging's `day.step`s and
`decision.made` through it, and to the [seed](seed.md) backfill, which sends
`backfill.progress` and `backfill.finished`); [api](api.md) (the stream route uses
`server_sent_events`); [frontend](frontend.md) (two parts listen to the `ingestion` stream through
`useLiveEvents`: `IngestionStatus`, which refetches the loading line on every event and folds `day.step`
and `decision.made` into the step it ends with, and
`ExplorePage`, which refetches everything it shows on each `day.finished`); each comparison
run announces itself on its own stream, `run-<id>` ([report](report.md): `worker/report_task.py`
emits, `RunProgress` listens).

## Configuration and data
`REDIS_URL`.
