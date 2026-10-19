---
name: refetch-day
description: Tests the automated daily retrieval end to end on the running local app. Health-checks Celery (worker ping, a task round trip, Beat alive), deletes one loaded day (its posts, the threads and topics it created, its decisions) and moves the day ledger (the high-water mark) back past it, then fires the daily catch-up as Beat would, and watches the day come back — live events, the page's loading line, embeddings, model calls — until everything settles. Reports the timings and any step that misbehaved. Changes only the local database, which is test data. Takes an optional day (default: the latest loaded day).
argument-hint: "[YYYY-MM-DD]"
---

# /refetch-day

Arguments: `$ARGUMENTS`

The app must be running (`docker compose up`) with at least a few days loaded. Every
command below runs from the repo root. This skill **changes the local database only**
(Brian allows it: it is test data); never point it at anything remote. Never print the
OpenRouter key. Tagging one day costs about two cents of OpenRouter credit.

Write every captured file under the scratchpad (or `.boot-test/refetch-<time>/`, which is
gitignored), never in the repo.

## 1. Health-check Celery

All three must pass; if one fails, stop and report it.

```bash
docker compose exec -T worker celery -A voices.worker.app:celery_app inspect ping
docker compose exec -T worker python -c "from voices.worker.app import ping; print(ping.delay().get(timeout=30))"
docker compose ps beat --format '{{.State}}'
docker compose logs beat --since 24h | grep -i 'beat: starting' | tail -1
```

Expect `pong` from the worker (`inspect ping` answers `OK`), the round trip to print
`pong`, and Beat `running`. Note that the catch-up and a report run share the worker; if
`/api/ingestion` shows a `running_day`, wait for it to finish first.

## 2. Choose the day and record "before"

- **Day:** the argument, or else `latest_day` from `curl -s localhost:5173/api/ingestion`
  (the PORT in `.env` if it isn't 5173). It must be a day marked done in the ledger.
- Record, for that day: the ledger row's counts (`select counts from ingested_days where
  day = …`), posts and comments written that day, threads first seen that day, decisions
  made that day, topics first seen that day, and the topics with engagement that day (with
  their engagement). Use `docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d
  "$POSTGRES_DB" …'` (the role `postgres` does not exist).

## 3. Delete the day and move the high-water mark back

In **one transaction**, for day `D` (dates are UTC):

1. Delete the posts and comments written on `D` (`created_at` in UTC on `D`); their upvote
   rows and retrieval rows go with them (`ON DELETE CASCADE`).
2. Delete the threads first seen on `D` that have no posts left.
3. Delete the decisions made on `D` that no remaining thread points to
   (`threads.cluster_decision_id`). Decisions that settled older threads on `D` stay: those
   threads are settled and are not decided again.
4. Delete the topics first seen on `D` that no thread carries any more, with their
   `topic_daily_engagement` rows.
5. Delete the engagement rows for `D` (the catch-up rebuilds `D−2` to `D`).
6. Delete the ledger row for `D` from `ingested_days`. This is the high-water mark: the
   catch-up fetches every complete day in the window that the ledger doesn't list as done.

Then check: the ledger no longer lists `D`, no posts are left for `D`, and
`/api/ingestion` shows one day fewer done.

## 4. Watch, then fire the catch-up as Beat does

Start the watchers first, in the background, each writing to its own file:

- the live stream the page listens to:
  `curl -sN localhost:5173/api/streams/ingestion/events` (ask for gzip too, as a browser
  does, with `-H 'Accept-Encoding: gzip, deflate, br' --compressed`: events must still
  arrive as they happen);
- the page's loading status, once a second: `curl -s localhost:5173/api/ingestion`, each
  line stamped with the time;
- the worker's log: `docker compose logs -f worker --since 1s`.

Then fire the daily task exactly as Beat's schedule does (by name, `voices.catch_up`), and
note the time:

```bash
docker compose exec -T worker python -c "from voices.worker.app import celery_app; print(celery_app.send_task('voices.catch_up').id)"
```

## 5. Confirm each stage, and time it

Wait until the status shows no `running_day` and the ledger lists `D` as done again (or
`failed_day` is set: then report the reason and stop). Then check, from the captured files:

- **The page's loading states.** The status went from all days done, to `running_day: D`
  (the top bar reads "Loading r/sailing history: N of 56 days…"), back to up to date
  ("History up to date through …"). Report what `describeIngestion` would have shown at
  each change. If a browser can reach the app, take a screenshot of the top bar while
  `D` is running; say so if none could.
- **Live events, streaming.** The stream carried `catch_up.started`, `day.started` for `D`,
  a `decision.made` per group, `day.finished` with the day's counts and
  `catch_up.finished`, each arriving as it happened (their times in order, spread over
  the run, not all at the end).
- **Vectors.** Every post and comment re-fetched for `D` has an embedding, and the
  threads due that day have theirs (`select count(*) … where embedding is null`).
- **Model calls.** The worker's log has `tagging.turn` lines (one per model reply) and
  `tagging.decided` lines for `D`; count them and the groups decided.
- **Settled.** The ledger row is done with counts; `topic_daily_engagement` has rows for
  `D` again; `GET /api/topics?start=D&end=D` and `GET /api/map?start=D&end=D` answer; no
  error or failed day in the log.
- **Compare with "before".** Posts and threads back within a few percent (the archive may
  hold a few more or fewer by now; say which), and the topics with engagement on `D`.

**Time** each part: fire → `day.started`, fetching and embedding (`day.started` → the first
`decision.made`), tagging (first to last `decision.made`), and fire → `day.finished`.

## 6. Report

In plain prose (`CLAUDE.md` §1): the day, the health check, every stage above with what
was verified and what was only inferred, the timings, the before/after comparison, and
anything that misbehaved, with the evidence (file and line). Leave the app running.
