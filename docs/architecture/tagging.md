# tagging

**Source:** `backend/src/voices/tagging/` (`clustering.py`, `decisions.py`, `decider.py`, `tools.py`, `graph.py`, `day_tagging.py`, `keywords.py`, `model.py`), `backend/src/voices/db/tagging_store.py`   ·   **Tests:** `backend/tests/tagging/`, `backend/tests/test_tagging_store.py` (needs a database)

## Purpose
Sorts each day's posts into topics, so the conversation can be followed day by day
([atlas plate 21](../atlas/20-data-model/21-topics.md), the tagging agent on
[plate 60](../atlas/60-agents.md)). Runs right after a day is loaded; a day is done only once
both have happened.

## Public interface
- `day_tagging.DayTagging(store, decide_all, emit).tag(day)` — tags one day and returns
  counts (`clusters`, `attached`, `minted`, `noise_deleted`, `expired`).
- `clustering.find_clusters(posts, min_cluster_size)` — groups `WindowPost`s by meaning
  (HDBSCAN on unit-length embeddings); stragglers join no group.
- `decider.ToolLoopDecider(model, tools).decide(brief)` — the agent's decision for one
  cluster, as a `DecidedCluster` with the exact prompt it saw.
- `graph.decide_all(decider, briefs)` — every cluster decided in parallel (a LangGraph
  fan-out), returned in the briefs' order.
- `decisions.Decision` (attach / mint / noise, with topic id, label, description, reason),
  `ClusterBrief`, `CandidateTopic`, `TypicalPost`, `DecidedCluster`, `settle_mints(...)`.
- `tools.TaggingTools(store, embedder, day).run(name, arguments)` — `search`, `lookup`,
  `search_tags`.
- `keywords.distinctive_keywords(cluster_texts, all_texts, limit)`.
- `model.connect_model(api_key, model_name)` — the chat model through OpenRouter; raises
  `MissingModelKey` (naming `OPENROUTER_API_KEY` and README step 3) when there's no key.
- `voices.db.tagging_store.TaggingStore` — the reads and writes below.

## How it works
For day D:
1. **Window.** Every post from D−2 to D with an embedding; posts already tagged act as
   anchors.
2. **Clusters.** HDBSCAN groups them; only clusters with at least one post still waiting
   for a tag go further.
3. **Briefs.** For each, the six posts closest to its centre and the five existing topics
   closest to it (with how many posts each had in its last week).
4. **Decisions.** The tagging agent (Claude Sonnet 5.5 through OpenRouter) gets each brief,
   may call `search` (posts in the window by meaning, 20 at most), `lookup` (one post in
   full) or `search_tags`, and answers by calling `Decision`. After six tool calls it must
   decide. Search and lookup hits are recorded in `retrieval_events` as the tagging agent's.
   Every turn is logged in full. Each decision is announced live as `decision.made`.
5. **Settling.** If two clusters mint topics whose centres are 0.90 alike or closer, the
   second joins the first's new topic.
6. **Applying** (one transaction): every decision is recorded in `cluster_decisions`;
   attach tags the cluster's waiting posts and moves the topic's centre to the average of
   its posts; mint creates the topic (label, description, keywords picked by code, centre)
   and tags the posts; noise deletes the waiting posts. An attach to a topic id that doesn't
   exist changes nothing; those posts keep waiting.
7. **Expiry.** Posts from before D−2 still waiting are deleted as noise (atlas OPEN-14).
8. **Engagement.** `topic_daily_engagement` is rebuilt for D−2 to D: posts, comments,
   agreeing-reply upvotes that day (also for older posts), distinct people, threads
   started, and questions started with no reply.

**Cost estimate:** about ten decisions a day, so roughly 560 for a first start, around $5
at Sonnet 5.5's OpenRouter price ($2 per million tokens in, $10 out). Not yet measured.

## Uses
[database](database.md) (`tagging_store`), [ingestion](ingestion.md) (`NomicEmbedder` for
search terms; `Emit`), [events](events.md), [logging](logging.md),
[environment](environment.md) (`OPENROUTER_API_KEY`, `MODEL_NAME`), OpenRouter, LangGraph,
LangChain, scikit-learn.

## Used by
[worker](worker.md) (each day of the catch-up is loaded, then tagged).

## Configuration and data
`OPENROUTER_API_KEY` (required for tagging), `MODEL_NAME` (default
`anthropic/claude-sonnet-5.5`). Fixed in code: `LOOKAHEAD_DAYS = 3`,
`MIN_CLUSTER_SIZE = 5`, `TYPICAL_POSTS_SHOWN = 6`, `CANDIDATE_TOPICS_SHOWN = 5`,
`MAX_TOOL_CALLS = 6`, `SAME_NEW_TOPIC_SIMILARITY = 0.90`, `KEYWORDS_PER_TOPIC = 8`.
Writes `topics`, `cluster_decisions`, `posts` (tags; deletes noise),
`topic_daily_engagement`, `retrieval_events`.
