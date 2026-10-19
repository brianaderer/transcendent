# 07 — Boot data migration (DRAFT)

[← Index](00-index.md) · [01 System Map](01-system-map.md) · [04 Environment](04-environment.md) · [21 Topics](20-data-model/21-topics.md) · [40 Backend](40-backend.md) · [Open questions](90-open-questions.md)

How a reviewer's database is seeded on first boot, quickly and without a large download.
Today a first start fetches eight weeks from the archive and tags them with the model:
about 1 hour 40 minutes and $1.30 to $1.70 (OPEN-13). This plate replaces that with data
that comes with the repo.

**Specified by Brian (2026-10-19):**
- The seeded data comes over **with the repo, encoded in a migration**: the posts and
  their metadata, including the topics, and everything else the app has worked out.
- **The vectors are not encoded.** The boot's last step runs all migrations and then
  **backfills every vector that didn't come over**.
- The purpose: a quick and easy seed that doesn't hit the reviewer with 80 MB, or even
  10 MB, of data, zipped databases and the like.
- **The migration is written as the last build step**, on whatever schema the app has then
  (OPEN-35): a **point-in-time snapshot**. If the schema changes later, a migration changes
  it, seeded rows included.
- **Loading progress is first class in the app** (Brian, 2026-10-19): the top bar shows the backfill counting up live ("Preparing the history: 4,120 of 12,682 posts"), then the catch-up's days, as one progress line for the whole first boot. The backfill reports on the same live `ingestion` stream as the catch-up (`backfill.progress` events, plate 41), and the API's loading status includes it, so a page opened mid-way shows where it is.
- **The app stays live after the seed** (OPEN-36): the catch-up fetches and tags the days
  since the seed's last day. A few days of that on the reviewer's machine is fine, even good;
  the seed only spares a cold boot from processing the whole history.

Everything else on this plate is *proposed*, from a red-team of the plan against the code.

```mermaid
flowchart LR
    SEEDFILE[("seed data in the repo<br/>posts, threads, topics, decisions,<br/>engagement, day ledger · about 2 MB gzipped<br/>no vectors")]
    MIG["setup: run all migrations"]
    LOAD["the seed migration, the last one<br/>a point-in-time snapshot"]
    PG[("postgres + pgvector<br/>see 21")]
    FILL["worker: backfill the vectors<br/>posts, then threads, then topic centres<br/>under the catch-up lock"]
    CU["catch-up<br/>days after the seed's last day, see 40"]
    PAGE["the page<br/>topics at once; map and search<br/>once the vectors are back"]

    MIG --> LOAD
    SEEDFILE --> LOAD
    LOAD --> PG
    PG --> FILL
    FILL --> CU
    PG --> PAGE
    classDef open stroke-dasharray: 5 5
    class FILL open
```

The seed migration holds the rows and runs with the others; the worker then rebuilds the
vectors before it does anything else, and catches up the days since the seed. The database is plate
[21](20-data-model/21-topics.md); the catch-up is plate [40](40-backend.md).

## What comes over, and how big it is

Measured on the local database (12,682 posts and comments, 640 threads, 152 topics),
as CSV and gzipped:

| Rows | Raw | Gzipped | Comes over |
|---|---|---|---|
| Posts and comments (text, author, time, scores, upvotes, parent) | 3.7 MB | 1.5 MB | yes |
| Threads (title, start, first seen, topic, stage) | 67 KB | 27 KB | yes |
| Topics (label, description, keywords, first and last seen) | 62 KB | 24 KB | yes |
| Tagging decisions, without their prompts | 3.4 MB | 344 KB | yes |
| The exact prompt behind each decision | 5.3 MB | 571 KB | no *(proposed)*: the bulk, and only for tracing |
| Daily engagement, daily upvotes, the day ledger | 53 KB | 9 KB | yes |
| Retrieval records (all from tagging) | 528 KB | 47 KB | yes, so the most-retrieved list isn't empty |
| **Total** | | **about 2 MB** | |

The vectors, left behind, were most of the database at full precision: 37 MB of the
75 MB. Stored at half precision since OPEN-34, they take about half that (about 18 MB,
worked out from the halving, not measured); the whole database measured 44 MB once
compacted, the posts table 26 MB.

## The backfill *(proposed)*

- **Posts and comments** are embedded again by the same model, each whole, as at intake.
- **Threads** are encoded again as their *final* text: the post (or its title, if the post
  isn't stored) and its top five replies as they stood at the end of the thread's third
  day, or its first day for a thread still waiting for its third. This reuses the tagging
  code's own reads and `thread_text`, not a copy of them.
- **Topic centres** are then the average of their threads' new embeddings, which is what
  they are now (checked: every topic's centre matches that average to within 0.001). The
  2 topics left with no threads are not seeded.
- Re-embedding won't give the stored numbers bit for bit (batching and the processor change
  the last digits), but the nearest neighbours, the grouping and the map hold. A test
  checks a sample against today's vectors (similarity 0.999 or more).
- **It resumes.** It works in batches, each committed, picking up whatever still has no
  vector, so a restart mid-way carries on. It runs inside the catch-up lock, before the
  catch-up, so tagging never sees a store without vectors.
- **How long.** Measured on an M4 Max (Docker with 14 cores): 30 to 60 posts a second, so
  about 4 to 7 minutes for the posts and 1 to 3 more for the thread texts. A base M1 to M3
  is slower: about **10 to 15 minutes** in all *(estimate from a 4-thread run)*. Limiting the
  model to 4 threads ran faster than its default (60 against 30 posts a second), so the
  backfill sets its thread count.
- **While it runs**, the topics, the slider and the badges work at once (they need no
  vectors). The map and search wait, and no map drawn before the backfill finishes is kept;
  the progress line (specified, above) says how far it has got.

## The seed migration *(details proposed)*

- **One migration, written last** (specified, OPEN-35). It reads a gzipped data file kept
  beside it, with the table and column names written out in the migration itself rather
  than taken from the table models, so it stays exactly the snapshot it was when the
  models change later. Alembic runs it once, in order, like every migration.
- Rows keep their ids, and every id counter is moved past them, so the next new topic or
  decision doesn't collide with a seeded one.
- **After it, the app is live** (specified, OPEN-36): the catch-up takes the days from the
  seed's last day to yesterday, fetching and tagging each, once the backfill is done.

## As built (build step 7, 2026-10-19)

Code: [seed](../architecture/seed.md), [database](../architecture/database.md),
[worker](../architecture/worker.md). Choices made while building are defaults, held as named
constants, not Brian's decisions.

- **The export** is `python -m voices.db.seed_export <path>`: one gzipped JSON file
  (`voices-seed/1`), one row set per table, each table's columns written out in the export
  code rather than taken from the models. Rows come in key order and the gzip header carries
  no timestamp, so the same database writes the same bytes. **Measured: 1.93 MB** (8.2 MB of
  JSON) on the local database: posts 1.48 MB, decisions 0.34 MB, retrieval records 0.06 MB,
  the rest under 0.1 MB together.
- **Left out:** every embedding and centre; each decision's prompt, which reads
  `(left out of the seed)` because the column can't be empty; and the 2 topics with no
  threads, with their engagement rows; the 3 decisions that named them keep their record
  with no topic.
- **Usernames are replaced** (specified by Brian, 2026-10-19, OPEN-37): every author in the
  file is a stand-in, `sailor-0001` onward, numbered in the order authors first appear, and
  a post that names a user (`u/name`) names the same stand-in. The README says usernames
  were changed to comply with Reddit's public data policy. Posts fetched later, on the
  reviewer's machine, keep their real names there.
- **The loader**, `load_seed(connection, data_file)`, puts each table's rows in with plain
  SQL under the file's own column names (Postgres's `json_populate_recordset`), keeps the
  ids, and moves every id counter on the loaded tables past them. It loads nothing into a
  database that already has a day in `ingested_days`, so a restart, or a database that
  filled itself, is left alone. Into an empty scratch database, the real file loaded in
  under a second.
- **A schema change the plan didn't name:** migration `0007` lets `topics.centroid` be
  missing, since seeded topics arrive without one until the backfill.
- **The seed migration itself is not in the repo yet.** It is written as the last build step
  (specified): the export into `backend/migrations/versions/0008_seed_snapshot.json.gz`, and a
  migration of a few lines calling `load_seed` with that file. The exact command and file are
  in [database](../architecture/database.md) → *Writing the seed migration*; that exact file,
  with a real export, was run through setup on an empty scratch database and loaded every row.
- **The backfill** runs first in every catch-up, under its lock, and does nothing when no
  vector is missing. Batches of 256 (`ROWS_PER_BATCH`), each saved before the next; posts,
  then threads (as of their third day once settled, their first while they wait, read
  through the tagging store's `threads_as_of` and `thread_text`), then centres. The model
  runs on 4 threads (`EMBEDDING_THREADS`). A failed backfill stops that catch-up, which
  tries again ten minutes later and carries on from the last saved batch.
- **Progress** (specified, built): after each batch, `{what, done, total}` is kept in Redis
  (`backfill:progress`), returned by `GET /api/ingestion` as `backfill`, and sent as a
  `backfill.progress` event; the top bar reads "Preparing the history: 4,120 of 12,682
  posts", then threads, then topics, then the catch-up's days. When it finishes, every kept
  map (`map:*`) is forgotten, the record cleared, and `backfill.finished` sent.
- **How long, measured** on this Mac under Docker with the real seed in a scratch database:
  **6 minutes 21 seconds** in all: posts 4 min 55 s (about 43 a second), threads 1 min 27 s,
  centres under a second.
- **How close the rebuilt vectors come, measured:** not to 0.999 as proposed above. Against
  the stored vectors the median similarity was 0.979 for posts (lowest 0.952), 0.984 for
  threads, 0.990 for centres. The model gives that much spread on its own: the same post
  embedded alone and in a batch agreed only to 0.977, whatever the thread count, so the
  stored vectors carry the same noise. A post's ten nearest posts are 70% the same as
  before, a thread's ten nearest threads 77%, a topic's five nearest topics 90%. No test
  in the suite checks this: it needs the real model.
- **The README** describes both first starts: with a seed, "Preparing the history…" then the
  days since; without one, the eight weeks and the measured 1 hour 40 minutes. It is true
  before and after the snapshot is committed.

## Open in this draft

Nothing open.
