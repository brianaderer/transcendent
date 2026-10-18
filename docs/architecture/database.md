# database

**Source:** `backend/src/voices/db/schema.sql`, `backend/src/voices/db/setup.py`   ·   **Tests:** `backend/tests/test_setup.py`

## Purpose
Creates the tables on first start. The tables follow [atlas plate 21](../atlas/20-data-model/21-topics.md)
and the `ingested_days` record from [plate 40](../atlas/40-backend.md).

## Public interface
- `python -m voices.db.setup` — waits for Postgres, then runs `schema.sql`. Run by the
  `setup` service on every start.
- `retry_connecting(connect, tries, pause_seconds)` — retries a connection, raising
  `DatabaseNotReady` after the last try (at once if `tries` is 0).
- `wait_for_database_then_create_tables(database_url)`.

## How it works
Every statement in `schema.sql` is `IF NOT EXISTS`, so running it again changes nothing.
Embeddings are `vector(768)`, the size nomic-embed-text produces (atlas OPEN-5).

Tables: `threads`, `posts` (one embedding each; `pending` or `tagged`; `upvotes` from
agreeing replies, apart from `reddit_score`), `post_upvotes_daily`, `topics` (label,
description, keywords, centroid), `topic_daily_engagement`, `cluster_decisions`,
`retrieval_events`, `ingested_days`. Each post records the cluster decision that tagged
it (`cluster_decision_id`).

## Uses
[logging](logging.md), [environment](environment.md) (settings, through
`voices.config.load_settings`), Postgres with pgvector.

## Used by
[environment](environment.md): the `setup` service in `compose.yaml` runs it. No other
module imports it; the [api](api.md) health check connects to Postgres directly.

## Configuration and data
`DATABASE_URL`. Data lives on the `postgres-data` volume.
