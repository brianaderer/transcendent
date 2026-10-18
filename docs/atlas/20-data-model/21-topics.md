# 21 — Topics and engagement over time (DRAFT)

[← Index](../00-index.md) · [01 System Map](../01-system-map.md) · [40 Backend](../40-backend.md) · [Open questions](../90-open-questions.md)

How the community's conversation is stored as **topics** that can be followed week to
week. This is what the prediction stands on: next week is forecast from how each
topic's engagement has been moving, not guessed from one week of text.

**Specified by Brian:** Postgres holds a table of topic tags. Each topic carries
semantic information, and its engagement over time is easy to graph. Prediction is
made from measured signals rather than by asking the model to guess.
**Everything else on this plate is *proposed*** — the table layout below is the
answer to "how should that be structured".

## Tables

```mermaid
erDiagram
    THREADS ||--o{ POSTS : contains
    POSTS ||--o{ PASSAGES : "split into"
    PASSAGES }o--|| TOPICS : "tagged with"
    TOPICS ||--o{ TOPIC_DAILY_ENGAGEMENT : "measured by"

    THREADS {
        text source_id "the site's own id, unique"
        text title
        timestamptz created_at
    }
    POSTS {
        text source_id "unique, so re-fetching never duplicates"
        text author
        timestamptz created_at
        text body
        int score "upvotes"
        text parent_source_id "the post it replies to"
    }
    PASSAGES {
        text text "a chunk of one post"
        vector embedding "its meaning, as numbers"
        float topic_similarity "how close it sits to its topic's center"
    }
    TOPICS {
        text label "short name, written by the model"
        text description "one or two sentences, written by the model"
        text_array keywords "the words that most set it apart"
        vector centroid "the average meaning of its passages"
        date first_seen
        date last_seen
    }
    TOPIC_DAILY_ENGAGEMENT {
        date day
        int posts
        int comments
        int unique_authors
        int total_score
        int new_threads
        int unanswered_questions
    }
```

### What each table is for

- **threads, posts** — the raw community data, exactly as fetched. The site's own id is
  unique, so fetching the same week twice changes nothing (`CLAUDE.md` §7).
- **passages** — each post cut into pieces small enough to embed and to hand the
  model. Each passage has its embedding and **one topic**. One topic per passage keeps
  the counts honest: a passage is never counted twice.
- **topics** — the topic tags. The *semantic information* is four things together:
  - a **label** and **description** a person can read, written by the model from the
    topic's most typical passages;
  - **keywords**, the words that most distinguish it from other topics, computed by
    code;
  - the **centroid**: the average of its passages' embeddings, which is the topic's
    position in meaning-space. New passages are tagged by finding the nearest
    centroid, and it's what lets a topic be recognized again next week.
- **topic_daily_engagement** — one row per topic per day: how many posts, comments,
  distinct people, upvotes, new threads and unanswered questions. **This is the
  graph.** Engagement over time for any topic is one query, and weekly totals are sums
  of seven rows. It's a summary rebuilt from the posts after each ingestion, never
  edited by hand, so it can always be recreated from the raw data. Five weeks of about
  thirty topics is roughly a thousand rows.

## How topics stay the same topic from week to week

This is the hard part, and why the centroid exists. Grouping posts by meaning from
scratch every week would invent fresh groups each time, with no link to last week's.
Instead, after each week is fetched:

```mermaid
flowchart TB
    NEW["New week's passages, embedded"]
    NEAR{"Close enough to an existing topic's centroid?"}
    TAG["Tag it with that topic; nudge the centroid toward it"]
    POOL["Hold it as unassigned"]
    CLUSTER["Group the unassigned passages by meaning"]
    BORN["Each group big enough becomes a new topic; the model names it"]
    ROLL["Rebuild topic_daily_engagement"]

    NEW --> NEAR
    NEAR -->|yes| TAG
    NEAR -->|no| POOL
    POOL --> CLUSTER
    CLUSTER --> BORN
    TAG --> ROLL
    BORN --> ROLL
```

So a topic that keeps getting talked about keeps its identity and its history, and a
genuinely new conversation shows up as a new topic with a `first_seen` date, which is
itself a prediction signal ("this started three days ago and is growing fast").

## Where similarity search is used

The nearest-centroid step and the passage retrieval for the document are both "find
the closest vectors" questions, which is what the pgvector extension does inside
Postgres. That's a second use beyond retrieval, so the recommendation in OPEN-4 now
covers both.

## Open in this draft

- `?` The closeness threshold for "same topic", and the smallest group that counts as a
  new topic — to be tuned against the real snapshot.
- `?` How a passage is cut from a post (length, overlap) — a later plate on ingestion.
- `?` Whether topics that go quiet are ever merged or retired.
