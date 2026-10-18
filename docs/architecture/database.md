# database

**Source:** `backend/src/voices/db/models.py`, `backend/src/voices/db/setup.py`, `backend/src/voices/db/address.py`, `backend/alembic.ini`, `backend/migrations/`   ·   **Tests:** `backend/tests/test_models.py`, `backend/tests/test_setup.py`, `backend/tests/test_migrations_match_models.py` (needs a database)

## Purpose
Describes the tables and keeps the database in step with them. The tables follow
[atlas plate 21](../atlas/20-data-model/21-topics.md) and the `ingested_days` record from
[plate 40](../atlas/40-backend.md). Changes are made with Alembic migrations (atlas OPEN-28).

## Public interface
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
extension and every table. Embeddings are `vector(768)`, the size nomic-embed-text
produces (atlas OPEN-5).

Tables: `threads`, `posts` (one embedding each; `pending` or `tagged`; `upvotes` from
agreeing replies, apart from `reddit_score`; the cluster decision that tagged it),
`post_upvotes_daily`, `topics` (label, description, keywords, centroid),
`topic_daily_engagement`, `cluster_decisions`, `retrieval_events`, `ingested_days`.

**Changing the database:** edit `models.py`, then, with the stack running, generate the
migration and read it before committing:

```bash
docker compose run --rm --no-deps -v "$PWD/backend/migrations:/srv/migrations" \
  api alembic revision --autogenerate -m "what changed"
```

`docker compose run --rm api pytest -m database` checks that the models and the applied
migrations agree (it's left out of the default test run because it needs a running
database). Running the `alembic` command directly reads the address from `DATABASE_URL`.

`topic_similarity` is double precision (`Float`); the earlier SQL file used `real`.

## Uses
[logging](logging.md), [environment](environment.md) (settings, through
`voices.config.load_settings`), Postgres with pgvector, SQLAlchemy, Alembic.

## Used by
[environment](environment.md): the `setup` service in `compose.yaml` runs it. No other
module imports it yet; the [api](api.md) health check connects to Postgres directly.

## Configuration and data
`DATABASE_URL`. Data lives on the `postgres-data` volume.
