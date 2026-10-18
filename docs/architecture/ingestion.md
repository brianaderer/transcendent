# ingestion

**Source:** `backend/src/voices/ingestion/` (`arctic_shift.py`, `items.py`, `filters.py`, `agreement.py`, `embedder.py`, `day.py`, `catch_up.py`)   ·   **Tests:** `backend/tests/ingestion/`

## Purpose
Fills the database with r/sailing, one day at a time, from the Arctic Shift archive of
Reddit. Plans: [atlas plate 40](../atlas/40-backend.md) (the catch-up) and
[plate 21](../atlas/20-data-model/21-topics.md) (what is kept). Clustering and tagging come
in build step 3; posts are stored as `pending` until then.

## Public interface
- `catch_up.CatchUp(ledger, process, emit).run(now, history_days=56)` — processes every
  complete day not yet done, oldest first, at most `history_days` back. Marks each day in
  the ledger and emits its events; stops at the first day that fails, re-raising its error.
  `ledger` is anything with `done_days`, `mark_running`, `mark_done` and `mark_failed`
  (the `Ledger` interface); `process` takes a day and returns its counts; `emit(event_type,
  **body)` sends one event on the ingestion stream (the worker binds `RedisEvents.emit` to
  the `ingestion` stream).
- `catch_up.missing_days(...)`, `catch_up.last_complete_day(now)` — a day is complete six
  hours after it ends, so the archive has caught up.
- `day.DayIngestion(archive, embedder, agreement, store).process(day)` — one day, returning counts
  (`fetched`, `dropped_unwanted`, `dropped_without_thread`, `dropped_orphan_upvotes`,
  `stored`, `threads_added`, `upvotes`), read off what was left after each step. Each
  collaborator is a small interface (`Archive`,
  `DocumentEmbedder`, `Agreement`, `DayStore`), so tests pass stand-ins.
- `day.DayBatch`, `day.EmbeddedItem`, `day.NewThread` — what one day hands to the store to
  save together.
- `arctic_shift.ArcticShift` — `posts_created_between`, `comments_created_between`,
  `posts_by_id`; `connect_to_archive()` builds the real one. Raises `ArchiveUnavailable`
  when a request still fails after five tries, naming the last reason (a status, the
  archive's "slow down" message, a network error, or the start of an error page that isn't
  the archive's own). The archive's "slow down" message is always
  retried, whatever status it comes with (it often arrives as 422); any other 4xx error
  except 429 is a bad request and is not retried.
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
  `post_upvotes_daily`. One whose parent we don't have is dropped. Re-saving a day sets
  its upvote count again rather than adding to it, so a redone day never double-counts.
- **Embedding**: posts are embedded whole as `search_document:`; search terms will be
  embedded as `search_query:`; agreement checks use `classification:`, as nomic-embed-text
  expects. Texts go in batches of 8, shortest first: memory grows with batch size times the
  longest text, and the library's default of 256 ran Docker out of memory.

**Measured on a laptop, first start:** about 35–50 seconds a day, so roughly 40–45 minutes
for the full eight weeks; around 550–600 posts and comments kept a day; the worker uses
about 2 GB.

## Uses
[logging](logging.md); the Arctic Shift archive (through `httpx`); the embedding model
(through `fastembed`), on the `model-cache` volume. It never imports the
[database](database.md) or [events](events.md) modules: the [worker](worker.md) hands it
the store and the `emit` function, which match the small interfaces above.

## Used by
[worker](worker.md) (the catch-up job builds and runs it); [database](database.md)
(`voices.db.store` saves a `DayBatch`, with its `EmbeddedItem`s and `NewThread`s).

## Configuration and data
`MODEL_DIR` (default `/home/voices/.cache/models`, on the `model-cache` volume). `HISTORY_DAYS = 56`
comes from `voices.config`, shared with the API. Fixed in code: `ARCHIVE_CATCH_UP_HOURS = 6`, `PAGE_SIZE = 100`, `ERROR_TEXT_CHARACTERS = 200`,
`MAX_AGREEMENT_WORDS = 8`, `AGREEMENT_SIMILARITY = 0.80`, `EMBED_BATCH_SIZE = 8`.
