# seed

**Source:** `backend/src/voices/db/seed_snapshot.py`, `backend/src/voices/db/seed_export.py`, `backend/src/voices/db/seed_load.py`, `backend/src/voices/backfill/` (`backfill.py`, `progress.py`), `backend/src/voices/db/backfill_store.py`   ·   **Tests:** `backend/tests/seed/` (`test_snapshot_file.py` and `test_published_author.py` run offline; `test_seed_export.py` and `test_seed_load.py` need a database and work in a scratch schema, `backend/tests/scratch_schema.py`), fixture `backend/tests/fixtures/seed_snapshot.json`; `backend/tests/backfill/` (`test_backfill.py` and `test_progress.py` offline with stand-ins; `test_backfill_store.py` needs a database, in a scratch schema)

## Purpose
The boot seed ([atlas plate 07](../atlas/07-boot-data.md)): the history the app has already
fetched and sorted into topics, carried in the repo so a reviewer's first start doesn't
spend an hour and a half and a dollar or two rebuilding it. The seed holds the rows but no
vectors; the worker's backfill rebuilds those on first boot, reporting its progress to the
page as it goes.

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

- `voices.backfill.backfill.Backfill(store, embedder, progress, emit, forget_maps, batch_size=ROWS_PER_BATCH).run()`
  — fills every missing vector, then forgets the kept maps; does nothing at all when no
  vector is missing and no earlier backfill was left unfinished. It depends on small
  interfaces (`BackfillStore`, `DocumentEmbedder`, `Progress`, the ingestion `Emit`, and a
  plain function to forget the maps), so tests pass stand-ins. Its shapes: `Tally(done,
  total)` with `missing`, `PostText(source_id, body)`, `UnencodedThread(source_id,
  first_seen_on, stage)`.
- `voices.db.backfill_store.BackfillStore(engine)` — `posts_tally`, `threads_tally`,
  `topics_tally` (rows with their vector, of all), `posts_without_embeddings(limit)` and
  `threads_without_embeddings(limit)` (in id order), `save_post_embeddings`,
  `threads_as_of(day, ids)` and `save_thread_embeddings` (both through
  [tagging](tagging.md)'s `TaggingStore`), `rebuild_missing_centres()`.
- `voices.backfill.progress.RedisBackfillProgress(redis)` — `record(what, done, total)`,
  `read()` (the last record, or `None` when no backfill is under way), `recorded()`,
  `clear()`; kept under the Redis key `backfill:progress`.

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

**Backfill.** The [worker](worker.md) runs it first in every catch-up, under the catch-up's
lock, so tagging never meets a store without vectors; when nothing is missing it does
nothing. Three steps, in order, each picking up whatever still has no vector, so a restart
carries on where it stopped:

1. **Posts and comments**, 256 at a time (`ROWS_PER_BATCH`), each embedded whole with
   `embed_documents`, exactly as at intake, and saved before the next batch.
2. **Threads**, 256 at a time, each encoded from the text tagging last gave it: as it stood
   at the end of its third day (`third_day(first_seen_on)`) once `settled`, or at the end
   of its first day while it waits for its third. The text is read with `TaggingStore`'s
   `threads_as_of` (its post, or its title when the post isn't stored, and its replies by
   then) and joined with tagging's own `thread_text`, so it is the same text tagging
   embedded.
3. **Topic centres**: every topic with no centre gets the average of its threads'
   embeddings, which is what tagging keeps a centre at.

Each step reports as it starts and after every saved batch: `progress.record(what, done,
total)` for `GET /api/ingestion` ([api](api.md), its `backfill` field), and a
`backfill.progress` event on the `ingestion` stream ([events](events.md)), which the
top bar's loading line ([frontend](frontend.md)) refetches on, reading "Preparing the
history: 4,120 of 12,682 posts". When the three steps are done, every kept map is
forgotten ([explore](explore.md)'s `RedisMapCache.forget_all`), since a map drawn meanwhile
had only the posts already embedded; then the progress record is cleared and
`backfill.finished` is emitted. A backfill stopped between its last batch and that finish
(its record still there, nothing missing) finishes on the next run. The embedding model runs
on four threads (`EMBEDDING_THREADS`, [ingestion](ingestion.md)).

**The seed migration is written last** (atlas plate 07, OPEN-35): it is a point-in-time
snapshot on whatever schema exists then. Neither it nor a real data file is in the repo
yet. The procedure, from the repository root with the stack running, is in
[database](database.md) → *Writing the seed migration*.

## Uses
[database](database.md) (the tables it reads and fills; `voices.db.address.sqlalchemy_url`),
[tagging](tagging.md) (`TaggingStore.threads_as_of` and `save_thread_embeddings`,
`thread_text`, `third_day`), [ingestion](ingestion.md) (the `Emit` interface; the worker's
`NomicEmbedder`), [explore](explore.md) (`RedisMapCache.forget_all`, passed in by the worker),
Redis (the progress record),
[environment](environment.md) (`DATABASE_URL` through `voices.config.load_settings`),
[logging](logging.md) (`seed.loaded`, `seed.skipped`), SQLAlchemy, Postgres.

## Used by
The seed migration, once written ([database](database.md)), calls `load_seed`; the export is
run by hand. [worker](worker.md) builds the `Backfill` and runs it before every catch-up;
[api](api.md) reads `RedisBackfillProgress` for `GET /api/ingestion`.

## Configuration and data
`DATABASE_URL`, `REDIS_URL` (the progress record `backfill:progress`). Fixed in code:
`ROWS_PER_INSERT = 1000`, `ROWS_PER_BATCH = 256`, `PROMPT_LEFT_OUT`,
`SNAPSHOT_FORMAT = "voices-seed/1"`.
