# tagging

**Source:** `backend/src/voices/tagging/` (`agent.py`, `clustering.py`, `window.py`, `decisions.py`, `decider.py`, `tools.py`, `graph.py`, `day_tagging.py`, `keywords.py`, `model.py`), `backend/src/voices/db/tagging_store.py`   ·   **Tests:** `backend/tests/tagging/`, `backend/tests/test_tagging_store.py` (needs a database)

## Purpose
Sorts each day's posts into topics, so the conversation can be followed day by day
([atlas plate 21](../atlas/20-data-model/21-topics.md), the tagging agent on
[plate 60](../atlas/60-agents.md)). Runs right after a day is loaded; a day is done only once
both have happened.

## Public interface
- `day_tagging.DayTagging(store, decide_all, emit).tag(day)` — tags one day and returns
  counts: `clusters` (how many were decided), `attached` (posts given a topic, by attach or
  by mint), `minted` (new topics), `noise_deleted` and `expired` (posts deleted), and
  `left_waiting` (posts kept waiting because the agent named a topic that doesn't exist).
  `decide_all` is any function from a day and its briefs to their decisions; the worker
  passes `agent.TaggingAgent(...).decide`, which connects the model and decides the day's
  clusters.
- `clustering.find_clusters(posts, min_cluster_size)` — groups `WindowPost`s by meaning
  (HDBSCAN on unit-length embeddings); stragglers join no group. A window about a single
  subject still forms one group (`allow_single_cluster`).
- `window.window_start(day)` — the first day of the three-day window ending on `day`; the
  one place the window is defined.
- `decider.ToolLoopDecider(model, model_name, tools, max_look_ups=3).decide(brief)` — the agent's
  decision for one cluster, as a `DecidedCluster` with the exact prompt it saw and the model's name.
  `max_look_ups` is how many tool calls it may make, counted across turns, before it is made to
  decide (default `MAX_LOOK_UPS_BEFORE_DECIDING`). Raises `NoDecision` if the agent never gives a
  valid decision, which stops the day.
- `graph.decide_all(decider, briefs)` — every cluster decided in parallel (a LangGraph
  fan-out), returned in the briefs' order.
- `decisions.Decision` (attach / mint / noise, with topic id, label, description, reason;
  the three action names are the `decisions.Action` type), `ClusterBrief`, `CandidateTopic`,
  `TypicalPost`, `DecidedCluster`, `settle_mints(...)`.
- `tools.TaggingTools(store, embedder, day).run(name, arguments)` — `search`, `lookup`,
  `search_tags`; returns what the agent reads back, as JSON text (or a sentence naming the
  real tools when asked for one that doesn't exist). `TOOL_ARGUMENT` lists each tool with
  its one required argument; the tool named `x` runs the method `_x`, and the schemas the
  model sees (`decider.TOOLS`) must match that list.
- `keywords.distinctive_keywords(cluster_texts, all_texts, limit)` — the words common in a
  cluster's posts and rare in the rest of the window, best first.
- `model.connect_model(api_key, model_name)` — the chat model through OpenRouter; raises
  `MissingModelKey` (naming `OPENROUTER_API_KEY` and README step 3) when there's no key.
- `voices.db.tagging_store.TaggingStore(engine)` — the reads and writes below: the window,
  typical posts, nearest topics, the tools' searches and lookups (`search_posts`,
  `lookup_post`, `search_topics`), `record_retrievals`, `apply_decisions`,
  `delete_expired_pending`, `rebuild_engagement`. `DayTagging` and `TaggingTools` each
  depend only on a small interface (`DayTaggingStore`, `ToolStore`) so tests pass stand-ins.

## How it works
For day D:
1. **Window.** Every post from D−2 to D with an embedding; posts already tagged act as
   anchors.
2. **Clusters.** HDBSCAN groups them; only clusters with at least one post still waiting
   for a tag go further.
3. **Briefs.** For each, the six posts closest to its centre and the five existing topics
   closest to it (with how many posts each had in its last week).
4. **Decisions.** The tagging agent (Claude Haiku 5.5 through OpenRouter, chosen for cost) gets each brief,
   may call `search` (posts in the window by meaning, 20 at most), `lookup` (one post in
   full) or `search_tags` (existing topics by meaning, 10 at most), and answers by calling
   `Decision`. It gets three look-ups (tool calls, counted across turns; a turn with no look-up still
   spends one, and calls beyond the limit are answered "No look-ups left"); then it is
   told to decide and offered only `Decision` (not forced: Claude Sonnet 5.5 refuses a
   forced tool choice), and if that answer still isn't a valid decision the day fails.
   If one reply calls `Decision` more than once, the first valid call is used and a malformed
   one is skipped; when a reply has no valid decision, each `Decision` call in it is answered
   with what was wrong with it.
   All clusters of a day are decided in parallel, at most eight at a time
   (`MAX_PARALLEL_DECISIONS`). A lookup of an id that isn't stored, a missing tool
   argument or an unknown tool is answered with an explanation, not an error. Search and lookup hits are recorded in
   `retrieval_events` as the tagging agent's (run `tagging-YYYY-MM-DD`). Every model turn
   and everything sent back to the model is logged in full (`tagging.turn`, `tagging.answer`,
   `tagging.decided`). Each decision is announced live as
   `decision.made`.
5. **Settling.** If two clusters mint topics whose centres are 0.90 alike or closer, the
   second joins the first's new topic. Applying relies on this order; a merged mint whose
   twin wasn't minted first is an error, not a silent skip.
6. **Applying** (one transaction): every decision is recorded in `cluster_decisions`;
   attach tags the cluster's waiting posts and moves the topic's centre to the average of
   its posts; mint creates the topic (label, description, keywords picked by code, centre)
   and tags the posts; noise deletes the waiting posts. Posts already tagged are never
   changed. An attach to a topic id that doesn't exist is recorded with no topic, and the
   cluster's waiting posts are left waiting for another day's decision (counted in
   `left_waiting`, which counts only posts that were still waiting); they are deleted only if they never join a topic within three days. Deleting a
   post also removes its upvote and retrieval rows.
7. **Expiry.** Posts from before D−2 still waiting are deleted as noise (atlas OPEN-14).
8. **Engagement.** `topic_daily_engagement` is rebuilt for D−2 to D from tagged posts:
   posts, comments, agreeing-reply upvotes that day (also for older posts, so a day can have
   upvotes and no new posts), distinct people, threads started, and questions started (a
   post with a question mark) with no reply.

Without `OPENROUTER_API_KEY`, `connect_model` raises `MissingModelKey` as soon as the day
reaches step 4; the day's loaded posts stay `pending`, the day is marked failed with that
message, and the page shows it ([frontend](frontend.md)).

**Cost estimate:** about ten decisions a day, so roughly 560 for a first start, well under
$5 at Haiku 5.5's OpenRouter price ($0.10 per million tokens in, $0.50 out). The
[bakeoff](bakeoff.md) measured about $0.0005 a decision on Haiku over its 25 sample cases,
which puts a first start well under $1; real days may look things up more, and a whole first
start has not been timed or costed yet.

## Uses
[database](database.md) (`tagging_store` reads and writes the tables in `voices.db.models`),
[ingestion](ingestion.md) (the `Emit` interface from `catch_up`; the worker hands the tools
its `NomicEmbedder`, whose `embed_query` turns search terms into embeddings),
[events](events.md) (through the `emit` the worker hands it, on the `ingestion` stream),
[logging](logging.md), [environment](environment.md) (`OPENROUTER_API_KEY`, `TAGGING_MODEL_NAME`,
read by the worker and passed in), OpenRouter (through `langchain-openai`), LangGraph,
LangChain, scikit-learn (HDBSCAN), numpy, Postgres with pgvector.

## Used by
[worker](worker.md) (`catch_up_task.py` builds `TaggingStore`, `TaggingAgent` and `DayTagging`, and tags each day of the catch-up right after
loading it); [bakeoff](bakeoff.md) (runs `ToolLoopDecider` with `TaggingTools` on sample cases, connects
models through `connect_model`, takes its list of right actions from `Action`, and builds briefs with `ClusterBrief`, `TypicalPost`,
`CandidateTopic` and the sizes `TYPICAL_POSTS_SHOWN` and `CANDIDATE_TOPICS_SHOWN`).

## Configuration and data
`OPENROUTER_API_KEY` (required for tagging), `TAGGING_MODEL_NAME` (default
`anthropic/claude-haiku-5.5`). Fixed in code: `LOOKAHEAD_DAYS = 3` (`window.py`),
`MIN_CLUSTER_SIZE = 5`, `TYPICAL_POSTS_SHOWN = 6`, `CANDIDATE_TOPICS_SHOWN = 5`,
`MAX_LOOK_UPS_BEFORE_DECIDING = 3`, `MAX_PARALLEL_DECISIONS = 8`, `SEARCH_RESULTS = 20`,
`TAG_RESULTS = 10`, `SAME_NEW_TOPIC_SIMILARITY = 0.90`, `KEYWORDS_PER_TOPIC = 8`,
`MIN_WORD_LENGTH = 4`, `RECENT_DAYS = 7`, `EXCERPT_CHARACTERS = 300`,
`TYPICAL_POST_CHARACTERS = 600`; the model call uses temperature 0, a 120-second timeout
and 3 retries (`model.py`).
Writes `topics`, `cluster_decisions`, `posts` (tags; deletes noise),
`topic_daily_engagement`, `retrieval_events`.
