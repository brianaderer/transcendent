# retrievals

**Source:** `backend/src/voices/retrievals/` (`retrieval_stats.py`, `shapes.py`), `backend/src/voices/db/retrieval_store.py`   ·   **Tests:** `backend/tests/retrievals/`, `backend/tests/test_topic_and_retrieval_routes.py`, `backend/tests/test_retrieval_store.py` (needs a database)

## Purpose
The read behind the Retrieval stats page ([atlas plate 31](../atlas/30-frontend/31-screens.md),
screen 5; CLAUDE.md §7, *Record retrieval statistics*): which stored posts an agent's tools
retrieved most, and how its retrievals spread over the topics. The counts are the
`retrieval_events` rows the agents' `search` and `lookup` tools write, one per post handed
back: the [tagging](tagging.md) agent's, and the [report](report.md) agent's (version B's
`search` and `lookup`, and `upcoming_events`, which is counted as `search`, under the run
`report-<id>`).

## Public interface
- `shapes.RetrievalFilter(agent, days, run=None)` — which retrievals count: one agent's
  (`report` or `tagging`), of posts **written** in the `DayRange` (not retrieved in it, so
  the range means the same as on Explore), from one run or from every run.
- `retrieval_stats.RetrievalStatistics(data)` — the service the API calls:
  - `stats(which)` — a `RetrievalStats`: `agent`; `runs`, the agent's runs that retrieved
    any of the range's posts, newest first (for the run filter, so not narrowed by `run`);
    `total`, every counted retrieval; `posts`, up to `MOST_RETRIEVED_SHOWN` (100)
    `RankedPost`s (`rank` from 1, `post_id`, `thread_id`, `kind`, `author`, `day` written,
    `excerpt`, `topic_id`, `topic_label`, `times_retrieved`, `last_retrieved`); and
    `topics`, a `TopicRetrievals` (`topic_id`, `label`, `times_retrieved`) per topic, most
    retrieved first, with the posts of threads that have no topic yet together under a
    `null` topic. No retrievals is an empty answer, not an error.
- `RetrievalData` — the small interface the service depends on (`most_retrieved`,
  `per_topic`, `runs`), so tests pass a stand-in.
- `voices.db.retrieval_store.RetrievalStore(engine)` — the real `RetrievalData`. Posts are
  ordered by times retrieved, then the latest retrieval, then id; topics by times
  retrieved, then label. The excerpt is the post's first `SHORT_EXCERPT_CHARACTERS` (160, from `voices.db.post_columns`)
  characters, or its thread's title for a post with no text.

## How it works
Every read joins each retrieval to its post, the post's thread and the thread's topic
(outer, so untagged threads still count), keeps the filter's agent, run and range, and
groups. The service numbers the posts in the order the store gives them and adds up the
topics' counts for the total. On the real data, a week of the tagging agent's retrievals
(468) is read in about 0.04 seconds.

## Uses
[database](database.md) (`retrieval_events`, `posts`, `threads`, `topics`;
`voices.db.post_columns` for the written-in-range test, the UTC day and the excerpt),
[explore](explore.md) (`DayRange`), Pydantic.

## Used by
[api](api.md) (`GET /api/retrievals`), which the [frontend](frontend.md)'s Retrieval stats
page calls.

## Configuration and data
Fixed in code: `MOST_RETRIEVED_SHOWN = 100`, `SHORT_EXCERPT_CHARACTERS = 160` (shared). Reads only.
