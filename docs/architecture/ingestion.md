# ingestion

**Source:** `backend/src/voices/ingestion/` (`arctic_shift.py`, `items.py`, `filters.py`, `agreement.py`, `embedder.py`, `day.py`, `catch_up.py`)   ·   **Tests:** `backend/tests/ingestion/`

## Purpose
Fills the database with r/sailing, one day at a time, from the Arctic Shift archive of
Reddit. Plans: [atlas plate 40](../atlas/40-backend.md) (the catch-up) and
[plate 21](../atlas/20-data-model/21-topics.md) (what is kept). Clustering and tagging come
in build step 3; posts are stored as `pending` until then.

## Public interface
- `catch_up.run_catch_up(now, ledger, process, emit)` — processes every complete day not
  yet done, oldest first, at most 56 days back. Stops at the first day that fails.
- `catch_up.missing_days(...)`, `catch_up.last_complete_day(now)` — a day is complete six
  hours after it ends, so the archive has caught up.
- `day.process_day(day, archive, embedder, agreement, store)` — one day, returning counts.
- `arctic_shift.ArcticShift` — `posts_created_between`, `comments_created_between`,
  `posts_by_id`; `connect_to_archive()` builds the real one.
- `embedder.NomicEmbedder` — `embed_documents`, `embed_query`, `embed_for_comparison`;
  `load_embedder(cache_dir)` loads nomic-embed-text-v1.5-Q (768 numbers per text).
- `agreement.AgreementDetector.agreeing(texts)` — which replies only agree with their parent.
- `filters.is_unwanted(item)`, `items.Item`, `items.post_from_archive`, `items.comment_from_archive`.

## How it works
A day: fetch every post and every comment *created* that day (new comments on old threads
arrive with the day they were written), drop removed and deleted posts and bots, look up
the title of any older thread a comment belongs to, turn agreeing replies into upvotes on
their parent, embed the rest, and save it all in one transaction. A day that fails leaves
nothing behind and is retried at the next catch-up.

- **The archive** returns at most 100 items a request, so reads are paged by creation time;
  an item repeated across a page boundary is kept once, and a page that never advances is
  stepped past. Requests are paced and retried, since the archive answers "slow down" when
  pushed.
- **Agreeing replies** (atlas OPEN-19): eight words or fewer, no question mark or link, and
  close in meaning (≥ 0.80) to examples such as "+1", "same here", "good point". They are
  not stored; each adds one to the parent's `upvotes` and to that day's
  `post_upvotes_daily`. One whose parent we don't have is dropped.
- **Embedding**: posts are embedded whole as `search_document:`; search terms will be
  embedded as `search_query:`; agreement checks use `classification:`, as nomic-embed-text
  expects. Texts go in batches of 8, shortest first: memory grows with batch size times the
  longest text, and the library's default of 256 ran Docker out of memory.

**Measured on a laptop, first start:** about 35–50 seconds a day, so roughly 40–45 minutes
for the full eight weeks; around 550–600 posts and comments kept a day; the worker uses
about 2 GB.

## Uses
[database](database.md) (through `voices.db.store`), [events](events.md),
[logging](logging.md), the Arctic Shift archive, the embedding model on the `model-cache`
volume.

## Used by
[worker](worker.md) (the catch-up job).

## Configuration and data
`MODEL_DIR` (default `/home/voices/.cache/models`, on the `model-cache` volume). Fixed in
code: `HISTORY_DAYS = 56`, `ARCHIVE_CATCH_UP_HOURS = 6`, `PAGE_SIZE = 100`,
`MAX_AGREEMENT_WORDS = 8`, `AGREEMENT_SIMILARITY = 0.80`, `EMBED_BATCH_SIZE = 8`.
