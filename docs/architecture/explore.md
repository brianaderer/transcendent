# explore

**Source:** `backend/src/voices/explore/` (`explore.py`, `day_range.py`, `direction.py`, `projection.py`, `cache.py`, `shapes.py`), `backend/src/voices/db/explore_store.py`   ·   **Tests:** `backend/tests/explore/`, `backend/tests/test_explore_routes.py`, `backend/tests/test_explore_store.py` (needs a database)

## Purpose
The reads behind the Explore page ([atlas plate 31](../atlas/30-frontend/31-screens.md),
*How Explore is built*): how many posts each day had, which topics were active in a date
range and which way each is moving, and a two-dimensional map of the range's posts for the
dot plot, recomputed for each range (atlas OPEN-20).

## Public interface
- `day_range.DayRange(start, end)` — a range of whole days, both ends included: `length`,
  `days()` (each date in order), `period_before()` (the range of the same length just before),
  and `day in range`. Building one that ends before it starts raises `InvalidRange`, which the
  API turns into a 422 saying why.
- `explore.Explore(data, cache, flatten)` — the service the API calls:
  - `days()` — a `Days`: posts and comments per day (UTC) across the history, and the latest
    fully loaded day.
  - `topics(days)` — a list of `TopicInRange` (a `TopicInfo` with the range's numbers): every topic with engagement in the range,
    busiest first (ties by id), with its range's `engagement` (posts, comments and upvotes),
    `posts` (posts and comments), `daily` (engagement on each day of the range, zeros on
    quiet days) and `direction`.
  - `map(days)` — a `Map`: every embedded post and comment written in the range, oldest
    first, each with its place (`x`, `y`, in the square from −1 to 1), thread, author, day,
    `thread_title`, a short excerpt and `thread_topic_id` (`null` while the thread waits for a
    decision).
- `direction.is_new(first_seen, days)` — first seen on or after the range's first day.
  `direction.trend(now, before)` — `rising` or `fading` when the range's engagement is more
  than a quarter (`CHANGE_THAT_COUNTS`) above or below the period of the same length just
  before it, and `steady` in between; a topic silent before the range and active in it is
  `rising`. A topic's badge (`direction`) is `new` when `is_new`, otherwise its trend.
- `projection.flatten(vectors)` — one point per vector, near in meaning near on the map.
- `cache.RedisMapCache(redis)` — `get(key)`, `put(key, value)`; each map is kept two days
  (`KEPT_SECONDS`).
- `shapes` — the response shapes (`Days`, `DayCount`, `TopicInRange`, `Map`, `MapPoint`) and the rows
  the store hands the service (`TopicDay`, `TopicInfo`, `MapPost`); `MapPost` and `MapPoint`
  share `PostSummary`, the fields the hover card shows, as Pydantic models, so the
  API's OpenAPI description names every field.
- `voices.db.explore_store.ExploreStore(engine)` — `posts_per_day`, `latest_day`,
  `topic_days(first, last)`, `topics(ids)`, `posts_in(first, last)`. `Explore` depends only on
  the small `ExploreData` and `MapCache` interfaces, so tests pass stand-ins. Its latest day
  is the latest day with status done, read by the query the ingestion store uses too
  (`voices.db.day_ledger`).

## How it works
- **Topics.** For a range of N days the store is asked for the topics' daily engagement over
  the N days before the range and the range itself, in one read. Each topic's range total is
  compared with its total before to give the badge; topics with no engagement in the range
  are left out.
- **The map.** The range's posts are read with their embeddings and flattened by t-SNE on
  cosine distance, started from the principal components with a fixed seed (`SEED`), so the
  same posts always give the same map; perplexity is 30, or a third of the posts for small
  ranges, and fewer than five posts are laid out in a row. The result is centred and scaled
  into the square from −1 to 1. Measured on the real data: about 9 seconds for a week
  (1,097 posts, including the read), 26 for all eight weeks.
- **Caching.** Each map is kept in Redis under `map:<start>:<end>:<latest loaded day>`
  (`nothing-loaded` before the first day), so a
  range is flattened once and flattened again only after a new day is loaded. A repeat read
  of a week took 0.02 seconds.
- The map is computed in the API process, not the worker, so it doesn't wait behind a
  first start's catch-up (atlas plate 40).

## Uses
[database](database.md) (`posts`, `threads`, `topics`, `topic_daily_engagement`,
`ingested_days`), Redis, scikit-learn (t-SNE), numpy, Pydantic.

## Used by
[api](api.md) (`GET /api/days`, `GET /api/topics`, `GET /api/map`), which the
[frontend](frontend.md)'s Explore page calls.

## Configuration and data
`REDIS_URL` (read by the API, which builds the cache). Fixed in code: `CHANGE_THAT_COUNTS =
0.25`, `SEED = 0`, `LARGEST_PERPLEXITY = 30`, `FEWEST_FOR_TSNE = 5`, `KEPT_SECONDS` (two
days), `EXCERPT_CHARACTERS = 160`. Reads only; writes nothing to Postgres.
