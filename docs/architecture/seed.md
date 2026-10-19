# seed

**Source:** `backend/src/voices/db/seed_snapshot.py`, `backend/src/voices/db/seed_export.py`, `backend/src/voices/db/seed_load.py`   ·   **Tests:** `backend/tests/seed/` (`test_snapshot_file.py` and `test_published_author.py` run offline; `test_seed_export.py` and `test_seed_load.py` need a database and work in a scratch schema, `backend/tests/scratch_schema.py`), fixture `backend/tests/fixtures/seed_snapshot.json`

## Purpose
The boot seed ([atlas plate 07](../atlas/07-boot-data.md)): the history the app has already
fetched and sorted into topics, carried in the repo so a reviewer's first start doesn't
spend an hour and a half and a dollar or two rebuilding it. The seed holds the rows but no
vectors; the worker's backfill rebuilds those on first boot.

## Public interface
- `python -m voices.db.seed_export <path>` — writes the database's seed data file to `<path>`
  (gzipped JSON when the name ends in `.gz`). `export_seed(engine, path)` and
  `snapshot_of(connection)` are the same thing for code.
- `voices.db.seed_export.published_author(author)` — every author name passes through it on
  its way into the seed. It keeps names as they are: whether usernames go into a public
  repo is atlas OPEN-37, still open, and a decision is a change to this one function.
- `voices.db.seed_export.SEED_TABLES` — what is seeded: each table with its columns written
  out, the SQL that gives each value, which rows and in what order. `PROMPT_LEFT_OUT` is the
  text a decision's `prompt` carries in the seed.
- `voices.db.seed_load.load_seed(connection, data_file)` — loads a data file into an empty
  database, for the seed migration to call. Raises `UnsafeName` for a table or column name
  that isn't plain lower-case letters and underscores.
- `voices.db.seed_snapshot` — the file itself: `Snapshot` (tables in load order) of
  `SeedTable`s (name, column names, rows as lists of values), `write_snapshot(snapshot, path)`,
  `read_snapshot(path)` (gzipped or plain JSON; raises `UnknownSnapshotFormat` for a file not
  in `SNAPSHOT_FORMAT`, `voices-seed/1`).

## How it works
**Export.** Each table in `SEED_TABLES` is read with plain SQL naming its columns, not
through the table models, so the file is a snapshot of the schema it was taken on. Rows come
in primary-key order and the gzip header carries no timestamp, so the same database writes
the same bytes. Left out: every embedding and topic centre (the backfill rebuilds them), each
tagging decision's prompt (the bulk of the data and only there for tracing; the column can't
be empty, so it reads `(left out of the seed)`), and any topic with no threads left, because
its centre can't be rebuilt from them; its engagement rows go with it, and a decision that
named it keeps its record with no topic. Tables come in the order they load in, each after
the tables it points to: topics, cluster decisions, threads, posts, daily upvotes, daily
engagement, retrieval records, noise markers, and the day ledger last.

**Load.** `load_seed` does nothing when `ingested_days` has any row: a database the catch-up
filled, or one already seeded, is left as it is, so a restart never loads twice and the
seed never lands on someone's own history. Otherwise each table's rows go in a thousand at a
time as one JSON array, which Postgres turns into the table's own row type
(`json_populate_recordset`), so days, times, keyword arrays and JSON columns arrive with
their proper types and columns the file doesn't name take their defaults. Ids are kept; then
every id counter on the loaded tables (any column whose default draws from a sequence:
`topics.id`, `cluster_decisions.id`, `retrieval_events.id`) is moved past the highest loaded
id, so the next new topic, decision or retrieval doesn't collide with a seeded one.

**Measured** on the local database (19 October 2026: 12,682 posts and comments, 640 threads,
150 seeded topics of 152, 1,496 decisions, 7,997 retrieval records, 57 days): the file is
1.93 MB gzipped (8.2 MB of JSON), the posts 1.48 MB of it, the decisions 0.34 MB, the
retrieval records 0.06 MB. Loaded through the migrations into an empty database, the seed
took under a second.

**The seed migration is written last** (atlas plate 07, OPEN-35): it is a point-in-time
snapshot on whatever schema exists then. Neither it nor a real data file is in the repo
yet. The procedure, from the repository root with the stack running, is in
[database](database.md) → *Writing the seed migration*.

## Uses
[database](database.md) (the tables it reads and fills; `voices.db.address.sqlalchemy_url`),
[environment](environment.md) (`DATABASE_URL` through `voices.config.load_settings`),
[logging](logging.md) (`seed.loaded`, `seed.skipped`), SQLAlchemy, Postgres.

## Used by
The seed migration, once written ([database](database.md)), calls `load_seed`; the export is
run by hand.

## Configuration and data
`DATABASE_URL`. Fixed in code: `ROWS_PER_INSERT = 1000`, `PROMPT_LEFT_OUT`,
`SNAPSHOT_FORMAT = "voices-seed/1"`.
