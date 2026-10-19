# database

**Source:** `backend/src/voices/db/models.py`, `backend/src/voices/db/setup.py`, `backend/src/voices/db/address.py`, `backend/src/voices/db/store.py`, `backend/src/voices/db/tagging_store.py`, `backend/src/voices/db/explore_store.py`, `backend/src/voices/db/topic_store.py`, `backend/src/voices/db/retrieval_store.py`, `backend/src/voices/db/post_columns.py`, `backend/src/voices/db/day_ledger.py`, `backend/alembic.ini`, `backend/migrations/`   ·   **Tests:** `backend/tests/test_models.py`, `backend/tests/test_setup.py`, `backend/tests/test_migrations_match_models.py`, `backend/tests/test_store.py`, `backend/tests/test_tagging_store.py`, `backend/tests/test_explore_store.py`, `backend/tests/test_topic_store.py` and `backend/tests/test_retrieval_store.py` (these six need a database)

## Purpose
Describes the tables and keeps the database in step with them. The tables follow
[atlas plate 21](../atlas/20-data-model/21-topics.md) and the `ingested_days` record from
[plate 40](../atlas/40-backend.md). Changes are made with Alembic migrations (atlas OPEN-28).

## Public interface
- `voices.db.tagging_store.TaggingStore` — the reads and writes for tagging; described in
  [tagging](tagging.md).
- `voices.db.explore_store.ExploreStore` — the Explore page's reads; described in
  [explore](explore.md).
- `voices.db.topic_store.TopicStore` — the Topic detail page's reads; described in
  [topics](topics.md).
- `voices.db.retrieval_store.RetrievalStore` — the Retrieval stats page's reads; described
  in [retrievals](retrievals.md).
- `voices.db.backfill_store.BackfillStore` — the backfill's reads and writes (which rows
  still lack their vector, and saving rebuilt ones); described in [seed](seed.md).
- `voices.db.post_columns` — column expressions the reading stores share: `written_on(column)`
  (the UTC day of a timestamp column: `Post.created_at` or `Thread.created_at`), `written_between(first, last)` (both days included) and
  `excerpt(characters)` (a post's opening words, or its thread's title for a post with no
  text); `SHORT_EXCERPT_CHARACTERS = 160`, the one-line excerpt the Explore hover card and
  the Retrieval stats table both show.
- `voices.db.store.Store` (built by `connect_store(database_url)`) — the reads and writes
  for ingestion: `known_post_ids`, `known_thread_ids`, `noise_thread_ids` (those of the given threads deleted as noise), `save_day(batch)` (threads, posts
  and upvotes in one transaction; a new thread is recorded as first seen on the batch's day; saving a day again adds nothing — the day's upvote rows
  are replaced as a whole, and every post they touched before or touch now is recounted
  from its days, so a redone day never double-counts and can also take upvotes away), the day ledger (`done_days`,
  `mark_running`, `mark_done`, `mark_failed`) and `ingestion_status()` (days done, posts stored including comments,
  the latest done, running and failed day, and `failed_reason`, the error recorded for the
  latest failed day; the API adds how many days are wanted).
- `voices.db.models` — the tables as SQLAlchemy classes (`Thread`, `Topic`,
  `ClusterDecision`, `Post`, `PostUpvotesDaily`, `TopicDailyEngagement`,
  `RetrievalEvent`, `IngestedDay`, `NoiseThread`) on `Base.metadata`, and an ingested day's
  statuses as `DAY_RUNNING`, `DAY_DONE`, `DAY_FAILED`, gathered in `DAY_STATUSES`, from which
  the `ingested_days` table's check that a status is one of these three is built. `voices.db.day_ledger.latest_day_with_status`
  is the one query for the latest day in a status, used by both `Store` and `ExploreStore`. This is the one description of
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
`topic_daily_engagement` gains `revived_threads`; `0004` adds `threads.first_seen_on`, the day a thread was
first stored, filled for stored threads from their earliest post or comment (atlas OPEN-30); `0005` adds `noise_threads` (atlas OPEN-31); `0006` stores every embedding at half
precision (atlas OPEN-34), converting the stored ones in place (its downgrade converts them
back); `0007` lets a topic's centre (`topics.centroid`) be missing, as it is between loading the boot seed and the worker's backfill that rebuilds it from the topic's threads ([atlas plate 07](../atlas/07-boot-data.md)); `0008` loads the boot seed, the gzipped data file beside it, into an empty database ([seed](seed.md)). Embeddings (`posts.embedding`, `threads.embedding`, `topics.centroid`) are
pgvector's `halfvec(768)`: 768 numbers, the size nomic-embed-text produces (atlas OPEN-5),
at two bytes each instead of four, which shrank the database from 74 MB to 44 MB once
compacted, on eight weeks of r/sailing (the posts table from 55 MB to 26 MB). Read back, an embedding is a pgvector
`HalfVector`, not a list; `explore_store` turns it into a list of floats with `to_list()`.

Tables: `threads` (the unit of tagging: the thread's own embedding of its post and top
replies, its topic, the decision that gave it, its `stage`: `new`, `decided_once` on its
first day or `settled` on its third, and `first_seen_on`, the day those days count from;
`created_at` stays the day it was started, which the revived-thread count uses), `posts` (one embedding each; `upvotes` from agreeing
replies, apart from `reddit_score`; a post's topic is its thread's),
`post_upvotes_daily`, `topics` (label, description, keywords, centroid),
`topic_daily_engagement`, `cluster_decisions`, `retrieval_events`, `ingested_days`,
`noise_threads` (the id of each thread deleted as noise and the day it went, no text, so a
comment arriving on it later is dropped at intake; atlas OPEN-31).

**Changing the database:** edit `models.py`, then, with the stack running, generate the
migration and read it before committing:

```bash
docker compose run --rm --no-deps -v "$PWD/backend/migrations:/srv/migrations" \
  api alembic revision --autogenerate -m "what changed"
```

**Writing the seed migration** (the last build step, atlas plate 07; the seed's code is
described in [seed](seed.md)). The migration and its data file are in the repo; to take the
seed again, with the stack running and the history the seed should carry
loaded, from the repository root, write the data file beside the migrations (the export
replaces every username with a stand-in as it writes, so the file holds no real one):

```bash
docker compose run --rm --no-deps -v "$PWD/backend/migrations:/srv/migrations" \
  api python -m voices.db.seed_export /srv/migrations/versions/0008_seed_snapshot.json.gz
```

`backend/migrations/versions/0008_seed_snapshot.py` beside it holds only:

```python
"""seed snapshot

Revision ID: 0008
Revises: 0007
"""

from pathlib import Path

from alembic import op

from voices.db.seed_load import load_seed

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    load_seed(op.get_bind(), Path(__file__).with_name("0008_seed_snapshot.json.gz"))


def downgrade() -> None:
    """The seeded rows stay: they are data the app has since built on."""
```

The image copies `backend/migrations/` whole, so the data file goes with it. A database
that already has days (yours) records the migration as run and loads nothing; an empty one
(a reviewer's) loads the seed. This exact file and a real data file were run through
`python -m voices.db.setup` on an empty scratch database on 19 October 2026 and loaded every
row.

`docker compose run --rm api pytest -m database` runs the ninety-three tests that need a running
database: one checks that the models and the applied migrations agree; eleven check that
the store saves a day (twice without duplicates), records a thread as first seen on the day it is saved rather than the day it was started and keeps that day when saved again, never double-counts a re-saved day's
upvotes, takes a day's upvotes away when the redone day no longer has them, adds up upvotes
from different days, keeps the day ledger, finds threads deleted as noise by their marker, and stores each of the three embedding columns as `halfvec(768)`; and thirty-seven check the tagging store: which
threads are due on their first and third days (with their replies, best first), threads read as of a day having only the replies they had by its end (and one without its post written from its title), a thread
without its post is due on the day first seen (whether it was started that day or years before), written from its title, is due again two days later, and can be a typical thread (shown by its title, with its author given as unknown), and that a
settled thread is never due again, minting, attaching, noise on a first day waiting and on a
third day deleting the thread with its comments and moving the centre of the topic it
leaves, attaching to a topic that doesn't exist (on a third day the thread keeps its
first day's topic, and one that had none is expired, its thread gone), threads with no topic expired, the thread and its posts gone, once their third day has come (that day included) but not before, and never a thread with a topic, a marker left by every thread deleted as noise (on its third day or expired) but not by one waiting for its third day,
merged mints, last-seen days, a topic's centre following its threads, a thread moved on its
third day, candidate topics' recent posts, typical threads, daily engagement (including a
late comment counting on its own day, revived threads only after seven days, and upvotes on a day with no new
posts), search with recorded retrievals, and looking up an unknown post; and seven check the Explore store: the latest day counting only finished days, posts counted by the day they were written in UTC, a topic's engagement as its posts, comments and upvotes, a range's posts with their thread and topic ending with its last day, a post's embedding coming back as the list of floats it was saved as, a post with no text shown by its title and long text cut, and topics read by id; and nineteen check the [seed](seed.md) in scratch schemas of their own (so they never touch the real rows): the export leaves out embeddings, centres, prompts and topics with no threads (with their engagement), replaces usernames with stand-ins in authors and in mentions, keeps rows in a fixed order and tables in load order, and loads back as it was; the loader keeps ids and types, moves every id counter past the loaded rows, leaves a database with days alone (so a second load adds nothing), and refuses a name that isn't plain; the backfill store tallies each kind as filled of all, hands out posts and threads still without a vector in id order a batch at a time, saves rebuilt ones, and gives a topic with no centre the average of its threads while leaving the others alone. They are left out of the default test run. Running the `alembic` command directly reads the address from `DATABASE_URL`.

## Uses
[logging](logging.md), [environment](environment.md) (settings, through
`voices.config.load_settings`), [ingestion](ingestion.md) (the store saves its `DayBatch`,
with its `EmbeddedItem`s and `NewThread`s), [tagging](tagging.md) (`tagging_store` returns
its `DueThread`s with their `Reply`s, its `TypicalPost`s and `CandidateTopic`s, applies its
`DecidedCluster`s, and uses its `window_start` for the three days ending on a day),
[explore](explore.md) (`explore_store` returns its `DayCount`s, `TopicDay`s, `TopicInfo`s and
`MapPost`s), [topics](topics.md) (`topic_store` returns its shapes and raises its
`TopicNotFound`), [retrievals](retrievals.md) (`retrieval_store` takes its
`RetrievalFilter` and returns its shapes),
Postgres with pgvector,
SQLAlchemy, Alembic.

## Used by
[seed](seed.md) reads every table for the export and fills them in the seed migration; its backfill builds `BackfillStore` on the worker's connection.
[environment](environment.md): the `setup` service in `compose.yaml` runs setup.
[worker](worker.md) builds the store and hands it to the [ingestion](ingestion.md)
catch-up, which saves each day and keeps the day ledger through it; the worker also builds
`TaggingStore` on the same connection and hands it to [tagging](tagging.md); [api](api.md) uses it for `GET /api/ingestion` and builds `ExploreStore`, `TopicStore` and `RetrievalStore` on its connection for the [explore](explore.md), [topics](topics.md) and [retrievals](retrievals.md) reads (its health check connects to Postgres
directly); [bakeoff](bakeoff.md) uses `PostNotFound` and `tagging_store`'s excerpt lengths;
[report](report.md)'s worker task (`worker/report_task.py`) connects with `connect_store` and
builds one object on both `ExploreStore` and `TaggingStore` over that connection, for a run's
topic reads, searches, lookups and retrieval counts, and its tools refuse an unknown post on
`PostNotFound`.

## Configuration and data
`DATABASE_URL`. Data lives on the `postgres-data` volume.
