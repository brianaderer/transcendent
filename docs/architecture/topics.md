# topics

**Source:** `backend/src/voices/topics/` (`topic_detail.py`, `shapes.py`), `backend/src/voices/db/topic_store.py`   ·   **Tests:** `backend/tests/topics/`, `backend/tests/test_topic_and_retrieval_routes.py`, `backend/tests/test_topic_store.py` (needs a database)

## Purpose
The read behind the Topic detail page ([atlas plate 31](../atlas/30-frontend/31-screens.md),
screen 4, and *How Topic detail and Retrieval stats are built*): one topic with its
engagement on every day across the history, the posts most typical of it, and the tagging
decisions that built it.

## Public interface
- `topic_detail.TopicDetails(data)` — the service the API calls:
  - `detail(topic_id)` — a `TopicDetail`: the topic's `id`, `label`, `description`,
    `keywords`, `first_seen`, `last_seen`; `daily`, one `EngagementDay` (`day`, `posts`,
    `comments`, `upvotes`, `people` — distinct authors) for each day it had any engagement,
    oldest first; `typical_posts`, `TYPICAL_POSTS_SHOWN` (3) `PostCard`s (`post_id`,
    `thread_id`, `kind`, `author`, `day`, `title`, `excerpt`), closest to the topic's centre
    first; and `decisions`, every `TopicDecision` (`day`, `decision` — `mint` or `attach`,
    `threads`, `reason`) that minted it or attached threads to it, oldest first.
    Raises `TopicNotFound` for an id with no topic, which the API turns into a 404.
- `TopicData` — the small interface the service depends on (`summary`, `engagement`,
  `typical_posts`, `decisions`), so tests pass a stand-in.
- `voices.db.topic_store.TopicStore(engine)` — the real `TopicData`:
  - `summary(topic_id)` — raises `TopicNotFound` when there is no such topic.
  - `engagement(topic_id)` — rows of `topic_daily_engagement`, oldest first.
  - `typical_posts(topic_id, limit)` — the topic's encoded threads ordered by cosine
    distance to the topic's centroid (ties by id), each shown by its opening post: the
    author (`unknown` when the post isn't stored), the thread's day in UTC, its title, and
    the post's opening `CARD_EXCERPT_CHARACTERS` (280) characters, or the title for a post
    with no text or none stored.
  - `decisions(topic_id)` — the `cluster_decisions` rows naming the topic, each with how
    many threads carry it now.

## How it works
The service makes four reads and puts them together; it adds nothing of its own. A
thread's `cluster_decision_id` names the latest decision about it, so a thread decided on
its first day and again on its third counts under the third-day decision only, and an
early decision can show no threads. Noise decisions name no topic and never appear. Days
with no engagement are left out of `daily`; the frontend lays the rows over the loaded
history and fills the quiet days with zeros.

## Uses
[database](database.md) (`topics`, `topic_daily_engagement`, `threads`, `posts`,
`cluster_decisions`; `voices.db.post_columns` for the excerpt; `UNKNOWN_AUTHOR` from
`voices.db.tagging_store`), Pydantic.

## Used by
[api](api.md) (`GET /api/topics/{topic_id}`), which the [frontend](frontend.md)'s Topic
detail page calls.

## Configuration and data
Fixed in code: `TYPICAL_POSTS_SHOWN = 3`, `CARD_EXCERPT_CHARACTERS = 280`. Reads only.
