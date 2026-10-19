# ingestion

**Source:** `backend/src/voices/ingestion/` (`arctic_shift.py`, `items.py`, `filters.py`, `agreement.py`, `embedder.py`, `day.py`, `catch_up.py`)   ·   **Tests:** `backend/tests/ingestion/`

## Purpose
Fills the database with r/sailing, one day at a time, from the Arctic Shift archive of
Reddit. Plans: [atlas plate 40](../atlas/40-backend.md) (the catch-up) and
[plate 21](../atlas/20-data-model/21-topics.md) (what is kept). Posts are stored with
their threads; [tagging](tagging.md) sorts the threads into topics right after each day is loaded.

## Public interface
- `catch_up.CatchUp(ledger, process, emit).run(now, history_days=56)` — processes every
  complete day not yet done, oldest first, at most `history_days` back. Marks each day in
  the ledger and emits its events; stops at the first day that fails, re-raising its error.
  The failure is recorded as the error's message (for example `OPENROUTER_API_KEY is not set…`), which the API returns as `failed_reason` and the page
  shows.
  `ledger` is anything with `done_days`, `mark_running`, `mark_done` and `mark_failed`
  (the `Ledger` interface); `process` takes a day and returns its counts; `emit(event_type,
  **body)` sends one event on the ingestion stream (the worker binds `RedisEvents.emit` to
  the `ingestion` stream).
- `catch_up.missing_days(...)`, `catch_up.last_complete_day(now)` — a day is complete six
  hours after it ends, so the archive has caught up.
- `catch_up.Emit` — the shape of that `emit` function; [tagging](tagging.md) uses it too.
- `day.DayIngestion(archive, embedder, agreement, store).process(day)` — one day, returning counts
  (`fetched`, `dropped_unwanted`, `dropped_as_noise` (items on a thread already deleted as
  noise, atlas OPEN-31), `dropped_without_thread`, `dropped_orphan_upvotes`,
  `stored`, `threads_added`, `upvotes`), read off what was left after each step. Each
  collaborator is a small interface (`Archive`,
  `DocumentEmbedder`, `Agreement`, `DayStore`), so tests pass stand-ins.
- `day.DayBatch`, `day.EmbeddedItem`, `day.NewThread` — what one day hands to the store to
  save together.
- `arctic_shift.ArcticShift` — `posts_created_between`, `comments_created_between`,
  `posts_by_id`; `connect_to_archive()` builds the real one. Raises `ArchiveUnavailable`
  when a request still fails after seven tries, naming the last reason (a status, the
  archive's "slow down" message, a network error, the start of an answer that isn't the
  archive's usual JSON, "an empty answer" when nothing came back, or "no reason given" when
  the archive's error carries no message). A success status whose answer isn't readable
  JSON counts as a failure too. Each answer is read once. The archive's "slow down" message
  is always retried, whatever status it comes with (it often arrives as 422); any other 4xx error
  except 429 is a bad request and is not retried.
- `embedder.NomicEmbedder` — `embed_documents`, `embed_query`, `embed_for_comparison`;
  `load_embedder(cache_dir)` loads nomic-embed-text-v1.5-Q (768 numbers per text).
- `embedder.ComparisonEmbedder` — the one interface for anything with
  `embed_for_comparison(texts)`; `NomicEmbedder` satisfies it. Used by `AgreementDetector`
  here and by [comparison](comparison.md)'s name matching and [report](report.md)'s run.
- `agreement.AgreementDetector.agreeing(texts)` — which replies only agree with their parent.
- `filters.is_unwanted(item)`, `items.Item`, `items.post_from_archive`, `items.comment_from_archive`.
  An `Item` keeps what its author wrote as `text`, with a post's `title` apart from it (the
  filter reads `text`). `body` is worked out from them, a post's title then its text, or a
  comment's text, and is what gets embedded and saved.

## How it works
A day: fetch every post and every comment *created* that day (new comments on old threads
arrive with the day they were written), drop removed and deleted posts and bots, drop whatever belongs to a thread already deleted
as noise (the store's `noise_thread_ids`; the thread isn't brought back to be stored and
decided again), look up
the title of any older thread a comment belongs to, turn agreeing replies into upvotes on
their parent, embed the rest, and save it all in one transaction. A day whose loading fails
leaves nothing behind. In the worker, `process` loads the day and then tags it; if tagging
fails, the loaded posts stay (their threads undecided) and the day is marked failed. Either way the
day is redone from the start at the next catch-up (the worker retries a failed one after ten
minutes), and saving it again adds nothing; a thread deleted as noise since the day was
first loaded stays deleted, its post and comments dropped like any later comment on it.

- **The archive** returns at most 100 items a request, so reads are paged by creation time;
  an item repeated across a page boundary is kept once, and a page that never advances is
  stepped past. Each try waits first: a one-second pause, then twice as long after each
  failure (about two minutes over seven tries), or as long as the archive's
  `x-ratelimit-reset` header says (never more than five minutes), whichever is longer. The archive answers "slow down" when
  pushed, especially when two copies of the app fetch at once.
- **Removed, deleted, and bot posts** (atlas OPEN-14, `filters.py`): an item is dropped when
  its author is `[deleted]`, when its own text is exactly `[deleted]`, `[removed]`, or
  `[ Removed by Reddit ]`, or when its author's name ends in "bot" or is AutoModerator. The
  check reads each item's `text` (what its author wrote: a post's text without its title,
  which survives removal, or a comment's body), not the stored body. A post with a title and
  no text at all is kept.
- **Agreeing replies** (atlas OPEN-19): eight words or fewer, no question mark or link, and
  close in meaning (≥ 0.80) to examples such as "+1", "same here", "good point". They are
  not stored; each adds one to the parent's `upvotes` and to that day's
  `post_upvotes_daily`. One whose parent we don't have is dropped. Re-saving a day replaces
  that day's upvote rows as a whole and recounts every post they touched, so a redone day
  never double-counts and can also take upvotes away.
- **Embedding**: posts are embedded whole as `search_document:`; the tagging agent's search
  terms are embedded as `search_query:`; agreement checks use `classification:`, as nomic-embed-text
  expects. Texts go shortest first, in batches of at most 4,000 characters and 32 texts
  (a longer text goes alone): the model's memory grows with batch size times the square of
  the longest text, and the library keeps its high point. Fixed batches of 8 climbed past
  8 GB over a first start in a boot test; length-sized batches stay under 1 GB and are about
  20% faster (measured on 3,600 real r/sailing posts).

**Measured on a laptop, first start, loading only (before tagging was added):** about 35–50 seconds a day, so roughly 40–45 minutes
for the full eight weeks; around 550–600 posts and comments kept a day; the worker then used
about 2 GB, climbing higher; with length-sized batches it stays under 1 GB.

## Uses
[logging](logging.md); [environment](environment.md) (`HISTORY_DAYS` from `voices.config`); the Arctic Shift archive (through `httpx`); the embedding model
(through `fastembed`), on the `model-cache` volume. It never imports the
[database](database.md) or [events](events.md) modules: the [worker](worker.md) hands it
the store and the `emit` function, which match the small interfaces above.

## Used by
[worker](worker.md) (the catch-up job builds and runs it, and hands the same
`NomicEmbedder` to tagging); [database](database.md)
(`voices.db.store` saves a `DayBatch`, with its `EmbeddedItem`s and `NewThread`s);
[tagging](tagging.md) (`day_tagging` uses the `Emit` interface and encodes each thread with
`NomicEmbedder.embed_documents`; its search tools embed terms with
`NomicEmbedder.embed_query`); [bakeoff](bakeoff.md) (`load_embedder`);
[comparison](comparison.md) and [report](report.md) (the `ComparisonEmbedder` interface;
`worker/report_task.py` also loads a `NomicEmbedder` with `load_embedder`, once per worker
process, for version B's searches and for matching topic names).

## Configuration and data
`MODEL_DIR` (default `/home/voices/.cache/models`, on the `model-cache` volume). `HISTORY_DAYS = 56`
comes from `voices.config`, shared with the API. Fixed in code: `ARCHIVE_CATCH_UP_HOURS = 6`, `PAGE_SIZE = 100`, `ERROR_TEXT_CHARACTERS = 200`,
`ATTEMPTS = 7`, `MAX_AGREEMENT_WORDS = 8`, `AGREEMENT_SIMILARITY = 0.80`, `BATCH_TEXT_BUDGET = 4000`, `MAX_BATCH = 32`.
