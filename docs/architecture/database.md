# database

**Source:** `backend/src/voices/db/models.py`, `backend/src/voices/db/setup.py`, `backend/src/voices/db/address.py`, `backend/src/voices/db/store.py`, `backend/src/voices/db/tagging_store.py`, `backend/alembic.ini`, `backend/migrations/`   ·   **Tests:** `backend/tests/test_models.py`, `backend/tests/test_setup.py`, `backend/tests/test_migrations_match_models.py`, `backend/tests/test_store.py` and `backend/tests/test_tagging_store.py` (these three need a database)

## Purpose
Describes the tables and keeps the database in step with them. The tables follow
[atlas plate 21](../atlas/20-data-model/21-topics.md) and the `ingested_days` record from
[plate 40](../atlas/40-backend.md). Changes are made with Alembic migrations (atlas OPEN-28).

## Public interface
- `voices.db.tagging_store.TaggingStore` — the reads and writes for tagging; described in
  [tagging](tagging.md).
- `voices.db.store.Store` (built by `connect_store(database_url)`) — the reads and writes
  for ingestion: `known_post_ids`, `known_thread_ids`, `save_day(batch)` (threads, posts
  and upvotes in one transaction; saving a day again adds nothing — the day's upvote rows
  are replaced as a whole, and every post they touched before or touch now is recounted
  from its days, so a redone day never double-counts and can also take upvotes away), the day ledger (`done_days`,
  `mark_running`, `mark_done`, `mark_failed`) and `ingestion_status()` (days done, posts stored including comments,
  the latest done, running and failed day, and `failed_reason`, the error recorded for the
  latest failed day; the API adds how many days are wanted).
- `voices.db.models` — the tables as SQLAlchemy classes (`Thread`, `Topic`,
  `ClusterDecision`, `Post`, `PostUpvotesDaily`, `TopicDailyEngagement`,
  `RetrievalEvent`, `IngestedDay`) on `Base.metadata`. This is the one description of
  the database; migrations are generated from it.
- `python -m voices.db.setup` — waits for Postgres, then runs every migration not yet
  applied (`alembic upgrade head`). Run by the `setup` service on every start; a second
  start changes nothing.
- `retry_connecting(connect, tries, pause_seconds)` — retries a connection, raising
  `DatabaseNotReady` after the last try (at once if `tries` is 0).
- `wait_for_database_then_migrate(database_url)`.
- `voices.db.address.sqlalchemy_url(database_url)` — the same address with the `psycopg`
  driver named, which SQLAlchemy and Alembic need. Used by setup and by `migrations/env.py`.

## How it works
Alembic records which migrations have run in its own `alembic_version` table and applies
the rest in order. `migrations/versions/0001_initial_tables.py` creates the pgvector
extension and every table; `0002` adds `ingested_days.error`, why a day failed; `0003` makes the thread the unit of
tagging (atlas OPEN-29): threads gain `embedding`, `topic_id`, `cluster_decision_id` and
`stage`, posts lose `status`, `topic_id`, `topic_similarity` and `cluster_decision_id`, and
`topic_daily_engagement` gains `revived_threads`. Embeddings are `vector(768)`, the size nomic-embed-text
produces (atlas OPEN-5).

Tables: `threads` (the unit of tagging: the thread's own embedding of its post and top
replies, its topic, the decision that gave it, and its `stage`: `new`, `decided_once` on its
first day or `settled` on its third), `posts` (one embedding each; `upvotes` from agreeing
replies, apart from `reddit_score`; a post's topic is its thread's),
`post_upvotes_daily`, `topics` (label, description, keywords, centroid),
`topic_daily_engagement`, `cluster_decisions`, `retrieval_events`, `ingested_days`.

**Changing the database:** edit `models.py`, then, with the stack running, generate the
migration and read it before committing:

```bash
docker compose run --rm --no-deps -v "$PWD/backend/migrations:/srv/migrations" \
  api alembic revision --autogenerate -m "what changed"
```

`docker compose run --rm api pytest -m database` runs the thirty tests that need a running
database: one checks that the models and the applied migrations agree; five check that
the store saves a day (twice without duplicates), never double-counts a re-saved day's
upvotes, takes a day's upvotes away when the redone day no longer has them, adds up upvotes
from different days, and keeps the day ledger; and twenty-four check the tagging store: which
threads are due on their first and third days (with their replies, best first) and that a
settled thread is never due again, minting, attaching, noise on a first day waiting and on a
third day deleting the thread with its comments and moving the centre of the topic it
leaves, attaching to a topic that doesn't exist (on a third day the thread keeps its
first day's topic),
merged mints, last-seen days, a topic's centre following its threads, a thread moved on its
third day, candidate topics' recent posts, typical threads, daily engagement (including a
late comment counting on its own day, revived threads only after seven days, and upvotes on a day with no new
posts), search with recorded retrievals, and looking up an unknown post. They are left out of the default test run. Running the `alembic` command directly reads the address from `DATABASE_URL`.

## Uses
[logging](logging.md), [environment](environment.md) (settings, through
`voices.config.load_settings`), [ingestion](ingestion.md) (the store saves its `DayBatch`,
with its `EmbeddedItem`s and `NewThread`s), [tagging](tagging.md) (`tagging_store` returns
its `DueThread`s with their `Reply`s, its `TypicalPost`s and `CandidateTopic`s, applies its
`DecidedCluster`s, and uses its `window_start` for the three days ending on a day),
Postgres with pgvector,
SQLAlchemy, Alembic.

## Used by
[environment](environment.md): the `setup` service in `compose.yaml` runs setup.
[worker](worker.md) builds the store and hands it to the [ingestion](ingestion.md)
catch-up, which saves each day and keeps the day ledger through it; the worker also builds
`TaggingStore` on the same connection and hands it to [tagging](tagging.md); [api](api.md) uses it for `GET /api/ingestion` (its health check connects to Postgres
directly); [bakeoff](bakeoff.md) uses `PostNotFound` and `tagging_store`'s excerpt lengths.

## Configuration and data
`DATABASE_URL`. Data lives on the `postgres-data` volume.
