# events

**Source:** `backend/src/voices/events.py`, `frontend/src/useLiveEvents.ts`   ·   **Tests:** `backend/tests/test_events.py`, `frontend/src/IngestionStatus.test.tsx`

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
`catch_up.finished`, `day.started` (with `progress`, e.g. "4 of 56"), `day.finished`
(with the day's counts) and `day.failed` (with the error), and `decision.made` (one per cluster the tagging agent
decides: action, topic, label, reason, posts).

## Uses
Redis, [logging](logging.md).

## Used by
[worker](worker.md) (`catch_up_task.py` builds `RedisEvents` and hands its `emit` to the
[ingestion](ingestion.md) catch-up); [api](api.md) (the stream route uses
`server_sent_events`); [frontend](frontend.md) (`IngestionStatus` uses `useLiveEvents`).

## Configuration and data
`REDIS_URL`.
