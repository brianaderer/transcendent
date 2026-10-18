# 21 — Topics and engagement over time (DRAFT)

[← Index](../00-index.md) · [01 System Map](../01-system-map.md) · [40 Backend](../40-backend.md) · [50 Prediction](../50-prediction.md) · [60 Agents](../60-agents.md) · [Open questions](../90-open-questions.md)

How the community's conversation is stored as **topics** that can be followed day by
day. This is what the prediction stands on: next week is forecast from how each
topic's engagement has been moving, not guessed from one week of text.

**Specified by Brian:**
- Postgres holds a table of topic tags. Each tag carries semantic information, and its
  engagement over time is easy to graph.
- Posts are fetched daily and **tagged by day on intake**. Any time range (a week, the
  eight weeks of history) is then just a range of days (OPEN-10).
- Each day, embeddings are clustered with a **three-day lookahead**: a post has three
  days to fall into a cluster. Each cluster is compared with the tags' embeddings to
  place it in the domain space, and an LLM makes the final call per cluster: **add it
  to an existing tag, mint a new tag, or ignore it as noise**. A post that hasn't
  fallen into a cluster within three days **is noise and is deleted**.
- **Posts are not cut into pieces**: one post or comment is one embedding.
- Deleted posts and bot posts are dropped. **Short replies are kept**: they're
  significant, and they are tabulated, because they inform the trend.

**Everything else on this plate is *proposed*.**

## Tables

```mermaid
erDiagram
    THREADS ||--o{ POSTS : contains
    POSTS }o--o| TOPICS : "tagged with"
    POSTS ||--o{ REACTIONS : "replied to with"
    TOPICS ||--o{ TOPIC_DAILY_ENGAGEMENT : "measured by"
    CLUSTER_DECISIONS }o--o| TOPICS : "attached to or minted"
    CLUSTER_DECISIONS ||--o{ POSTS : "covers"

    THREADS {
        text source_id "Reddit's id, unique"
        text title
        timestamptz created_at
    }
    POSTS {
        text source_id "Reddit's id, unique, so a repeat is dropped"
        text kind "post or comment"
        text author
        timestamptz created_at
        text body
        int score "upvotes at fetch time, not used for trends"
        text parent_source_id "what it replies to"
        vector embedding "its meaning, as numbers"
        text status "pending, tagged"
        float topic_similarity "how close it sits to its tag's center"
    }
    REACTIONS {
        text source_id "Reddit's id, unique"
        text author
        timestamptz created_at
        text body "the short reply itself"
        text parent_source_id "what it reacts to"
    }
    TOPICS {
        text label "short name, written by the LLM"
        text description "one or two sentences, written by the LLM"
        text_array keywords "the words that most set it apart"
        vector centroid "the average meaning of its posts"
        date first_seen
        date last_seen
    }
    TOPIC_DAILY_ENGAGEMENT {
        date day
        int posts
        int comments
        int reactions "short replies"
        int unique_authors
        int new_threads
        int unanswered_questions
    }
    CLUSTER_DECISIONS {
        date day
        text decision "attach, mint or noise"
        text reason "the LLM's explanation"
        jsonb candidate_tags "the nearest tags and how close each was"
        text prompt "exactly what the LLM was shown"
        text model
    }
```

### What each table is for

- **threads, posts** — the community's posts and comments as fetched, one embedding
  each. Reddit's id is unique, so the small overlap between daily pulls is dropped on
  insert (`CLAUDE.md` §7). A post is `pending` until a cluster takes it, then `tagged`;
  noise is deleted rather than marked.
- **reactions** — short replies ("this", "+1", "same here") *(proposed, OPEN-19)*. They
  carry no meaning of their own to cluster, so they are not embedded; they count toward
  the tag of the post they reply to, on the day they were written. Kept in their own
  table so the three-day noise rule can't delete them for failing to cluster.
- **topics** — the topic tags. The *semantic information* is four things together:
  - a **label** and **description** a person can read, written by the LLM from the
    tag's most typical posts;
  - **keywords**, the words that most set it apart from other tags, computed by code;
  - the **centroid**: the average of its posts' embeddings, the tag's position in
    meaning-space. Clusters are compared against the centroids to find the tags they
    might belong to, and the centroid moves whenever posts are added.
- **topic_daily_engagement** — one row per tag per day: posts, comments, reactions,
  distinct people, new threads and unanswered questions. **This is the graph.** Any
  range — a week, eight weeks — is a sum over its days. Rebuilt from the posts after
  each day's intake, never edited by hand. Eight weeks of about thirty tags is under two
  thousand rows.
- **cluster_decisions** — one row per cluster per day: what the LLM decided, why, which
  tags it was choosing between and how close each was, and the exact prompt it saw.
  Every tag is traceable to the decisions that built it, and because tagging always
  moves forward one day at a time, it also records what was known on each day — which
  is what keeps the backtest honest (OPEN-11).

## The daily intake

Runs once a day as a Celery job ([40](../40-backend.md)). The flow is specified by
Brian; details in brackets are *proposed*.

```mermaid
flowchart TB
    PULL["Fetch new posts and comments<br/>(Arctic Shift, since the newest stored)"]
    DROP["Drop deleted and removed posts, and bots<br/>(AutoModerator and other known bot accounts)"]
    SHORT{"Short reply?<br/>(no meaning of its own)"}
    REACT[("reactions<br/>counted toward the parent's tag")]
    EMB["Embed each post or comment whole<br/>status: pending"]
    CL["Cluster the last three days of posts<br/>(HDBSCAN · tagged posts in the window act as anchors)"]
    CMP["Compare each cluster with the tags' centroids<br/>places it in the domain space"]
    LLM["Tagging agent decides, per cluster<br/>see 60"]
    ADD["Attach to an existing tag"]
    MINT["Mint a new tag"]
    NOISE["Noise: delete"]
    EXPIRE["Pending for three days and still in no cluster:<br/>noise, delete"]
    ROLL["Rebuild topic_daily_engagement<br/>for the days touched"]

    PULL --> DROP --> SHORT
    SHORT -->|yes| REACT
    SHORT -->|no| EMB --> CL --> CMP --> LLM
    LLM --> ADD
    LLM --> MINT
    LLM --> NOISE
    CL --> EXPIRE
    ADD --> ROLL
    MINT --> ROLL
    REACT --> ROLL
```

- **Why three days:** one day of r/sailing is often too few posts for a conversation to
  form a cluster. Giving every post three days lets a thread that starts slowly gather
  enough company, while anything still alone after three days really is noise.
- **Why the LLM decides rather than a threshold:** closeness in meaning-space alone
  can't tell "the same conversation continuing" from "a new conversation next door to
  an old one". The LLM reads the posts and the candidate tags' descriptions.
- **Tagging always moves forward in time**, one day after another. Nothing tagged is
  re-decided, so a tag's history never changes under it.
- **Cost:** one LLM call per cluster per day, roughly ten a day for r/sailing. Tagging the
  eight-week history once is a few hundred calls *(estimate)*.
- **Tests** replace the LLM and the embedder with stand-ins (`CLAUDE.md` §7).

## Where similarity search is used

Comparing a cluster with the tags, and the agents' search tool ([60](../60-agents.md)),
are both "find the closest vectors" questions, which pgvector answers inside Postgres
(OPEN-4, resolved).

## Open in this draft

- `?` How a short reply is recognized — OPEN-19.
- `?` What happens to a reply whose parent was deleted as noise *(proposed: the parent
  keeps a stub row — id, author, time, no text or embedding — so threads stay connected
  and lookup can say "removed as noise")*.
- `?` The smallest group the clustering counts as a cluster, and how many nearest tags
  the LLM is shown — tuned against the real data.
- `?` Whether tags that go quiet are ever merged or retired.
