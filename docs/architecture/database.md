# database

**Source:** `backend/src/voices/db/schema.sql`, `backend/src/voices/db/setup.py`   ·   **Tests:** `backend/tests/test_setup.py`

## Purpose
Creates the tables on first start. The tables follow [atlas plate 21](../atlas/20-data-model/21-topics.md)
and the `ingested_days` record from [plate 40](../atlas/40-backend.md).

## Public interface
- `python -m voices.db.setup` — waits for Postgres, then runs `schema.sql`. Run by the
  `setup` service on every start.
- `wait_for(connect, tries, pause_seconds)` — retries a connection, raising
  `DatabaseNotReady` after the last try.
- `create_tables(database_url)`.

## How it works
Every statement in `schema.sql` is `IF NOT EXISTS`, so running it again changes nothing.
Embeddings are `vector(768)`, the size nomic-embed-text produces (atlas OPEN-5).

Tables: `threads`, `posts` (one embedding each; `pending` or `tagged`; `upvotes` from
agreeing replies, apart from `reddit_score`), `post_upvotes_daily`, `topics` (label,
description, keywords, centroid), `topic_daily_engagement`, `cluster_decisions`,
`retrieval_events`, `ingested_days`.

## Uses
[logging](logging.md), Postgres with pgvector.

## Used by
[environment](environment.md) (the `setup` service), [api](api.md) (health check).

## Configuration and data
`DATABASE_URL`. Data lives on the `postgres-data` volume.
