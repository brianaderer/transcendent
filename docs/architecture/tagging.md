# tagging

**Source:** `backend/src/voices/tagging/` (`agent.py`, `threads.py`, `grouping.py`, `window.py`, `decisions.py`, `decider.py`, `tools.py`, `graph.py`, `day_tagging.py`, `keywords.py`, `model.py`), `backend/src/voices/db/tagging_store.py`   ·   **Tests:** `backend/tests/tagging/`, `backend/tests/test_tagging_store.py` (needs a database)

## Purpose
Sorts r/sailing's threads into topics, so the conversation can be followed day by day
([atlas plate 21](../atlas/20-data-model/21-topics.md), the tagging agent on
[plate 60](../atlas/60-agents.md)). Runs right after a day is loaded; a day is done only once
both have happened.

## Public interface
- `day_tagging.DayTagging(store, embedder, decide_all, emit).tag(day)` — tags one day's
  threads and returns counts: `threads` (encoded today), `groups` (decided), `attached`
  (threads given a topic, by attach or by mint), `minted` (new topics), `noise_waiting`
  (threads called noise on their first day, kept for their third), `noise_deleted` (threads
  called noise on their third day, deleted with their posts), and `left_waiting` (threads
  left as they were because the agent named a topic that doesn't exist: on their first day
  they wait for their third, on their third they keep their first day's topic, if any, and
  are settled). `decide_all` is any
  function from a day and its briefs to their decisions; the worker passes
  `agent.TaggingAgent(...).decide`, which connects the model and decides the day's groups.
- `threads.thread_text(post, replies)` — a thread as one text: its post, then its five
  best-scored replies, cut at 3,000 characters. `threads.DueThread` is a thread due a
  decision with its replies so far; `threads.Reply` one reply's text and score.
- `grouping.group_by_meaning(threads)` — groups `EncodedThread`s whose embeddings are on
  average closer than `GROUPING_DISTANCE` (agglomerative clustering, cosine distance,
  average linkage) into `Group`s with a centre. Every thread lands in a group, alone if
  nothing is like it.
- `window.window_start(day)` — the first of the three days ending on `day`: the day the
  threads decided a second time today were started, and the start of the agents' search
  window.
- `decider.ToolLoopDecider(model, model_name, tools, max_look_ups=3).decide(brief)` — the agent's
  decision for one group, as a `DecidedCluster` with the exact prompt it saw and the model's name.
  `max_look_ups` is how many tool calls it may make, counted across turns, before it is made to
  decide (default `MAX_LOOK_UPS_BEFORE_DECIDING`). Raises `NoDecision` if the agent never gives a
  valid decision, which stops the day.
- `graph.decide_all(decider, briefs)` — every group decided in parallel (a LangGraph
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
  group's threads and rare in the rest of the day's, best first.
- `model.connect_model(api_key, model_name)` — the chat model through OpenRouter; raises
  `MissingModelKey` (naming `OPENROUTER_API_KEY` and README step 3) when there's no key.
- `voices.db.tagging_store.TaggingStore(engine)` — the reads and writes below:
  `threads_due`, `save_thread_embeddings`, `typical_threads`, `nearest_topics`, the tools'
  searches and lookups (`search_posts`, `lookup_post`, `search_topics`), `record_retrievals`,
  `apply_decisions`, `rebuild_engagement`. `DayTagging` and `TaggingTools` each
  depend only on a small interface (`DayTaggingStore`, `ToolStore`) so tests pass stand-ins.

## How it works
For day D (atlas OPEN-29):
1. **Threads due.** Threads started on D that haven't been decided (`stage` `new`), and
   threads started on D−2 that haven't been settled (`new` or `decided_once`), each with its
   post and the replies it has by the end of D. A thread whose post was never loaded (an
   older thread that only its comments brought in) is never due, so its comments count for
   no topic.
2. **Encoding.** Each due thread is written out as one text (`thread_text`) and embedded;
   the embedding is saved on the thread, replacing a first-day one on the third day.
3. **Groups.** The due threads are grouped by meaning; every thread is in a group, so every
   thread gets a decision.
4. **Briefs.** For each group, the six threads closest to its centre (their posts) and the
   five existing topics closest to it (with how many posts their threads had in the topic's
   last week).
5. **Decisions.** The tagging agent (Claude Haiku 5.5 through OpenRouter, chosen for cost) gets each brief,
   may call `search` (posts in the window by meaning, 20 at most), `lookup` (one post in
   full) or `search_tags` (existing topics by meaning, 10 at most), and answers by calling
   `Decision`. It gets three look-ups (tool calls, counted across turns; a turn with no look-up still
   spends one, and calls beyond the limit are answered "No look-ups left"); then it is
   told to decide and offered only `Decision` (not forced: Claude Sonnet 5.5 refuses a
   forced tool choice), and if that answer still isn't a valid decision the day fails.
   If one reply calls `Decision` more than once, the first valid call is used and a malformed
   one is skipped; when a reply has no valid decision, each `Decision` call in it is answered
   with what was wrong with it.
   All groups of a day are decided in parallel, at most eight at a time
   (`MAX_PARALLEL_DECISIONS`). A lookup of an id that isn't stored, a missing tool
   argument or an unknown tool is answered with an explanation, not an error. Search and lookup hits are recorded in
   `retrieval_events` as the tagging agent's (run `tagging-YYYY-MM-DD`). Every model turn
   and everything sent back to the model is logged in full (`tagging.turn`, `tagging.answer`,
   `tagging.decided`). Each decision is announced live as
   `decision.made`.
6. **Settling.** If two groups mint topics whose centres are 0.90 alike or closer, the
   second joins the first's new topic. Applying relies on this order; a merged mint whose
   twin wasn't minted first is an error, not a silent skip.
7. **Applying** (one transaction): every decision is recorded in `cluster_decisions`.
   Attach and mint give the group's threads the topic (a thread on its third day becomes
   `settled`, one on its first `decided_once`) and move the topic's centre to the average of
   its threads; a thread moved to another topic on its third day also moves that old topic's
   centre (a topic left with no threads keeps the centre it had). Mint first creates the
   topic (label, description, keywords picked by code, centre). Noise on a thread's first
   day keeps it, untagged, for its third; noise on its third day deletes the thread with its
   posts, which also removes their upvote and retrieval rows, and moves the centre of any
   topic its first day gave it. An attach to a topic id that doesn't exist is recorded with
   no topic and the threads are left as they were (`left_waiting`): a first-day thread is
   decided again on its third day; a third-day thread keeps the topic its first day gave it,
   if any, and is settled.
8. **Engagement.** `topic_daily_engagement` is rebuilt for D−2 to D, every post counting
   for its thread's topic, so a comment that arrives days later counts for the topic on the
   day it was written: posts, comments, agreeing-reply upvotes that day (also for older
   posts, so a day can have upvotes and no new posts), distinct people, threads started,
   revived threads (threads more than seven days old with comments that day), and
   questions started (a post with a question mark) with no reply.

Without `OPENROUTER_API_KEY`, `connect_model` raises `MissingModelKey` as soon as the day
reaches step 5; the day's threads stay undecided (their embeddings already saved), the day is marked failed with that
message, and the page shows it ([frontend](frontend.md)).

**Cost estimate:** about forty decisions a day (twenty groups, each thread decided twice), so roughly 2,000 for a first start, well under
$5 at Haiku 5.5's OpenRouter price ($0.10 per million tokens in, $0.50 out). The
[bakeoff](bakeoff.md) measured about $0.0005 a decision on Haiku over its 25 sample cases,
which puts a first start well under $1; real days may look things up more, and a whole first
start has not been timed or costed yet.

## Uses
[database](database.md) (`tagging_store` reads and writes the tables in `voices.db.models`),
[ingestion](ingestion.md) (the `Emit` interface from `catch_up`; the worker hands tagging
its `NomicEmbedder`: `embed_documents` encodes the threads, `embed_query` turns search terms
into embeddings),
[events](events.md) (through the `emit` the worker hands it, on the `ingestion` stream),
[logging](logging.md), [environment](environment.md) (`OPENROUTER_API_KEY`, `TAGGING_MODEL_NAME`,
read by the worker and passed in), OpenRouter (through `langchain-openai`), LangGraph,
LangChain, scikit-learn (agglomerative clustering), numpy, Postgres with pgvector.

## Used by
[worker](worker.md) (`catch_up_task.py` builds `TaggingStore`, `TaggingAgent` and `DayTagging`, and tags each day of the catch-up right after
loading it); [bakeoff](bakeoff.md) (writes its sample threads out with `thread_text`, runs `ToolLoopDecider` with `TaggingTools` on sample cases, connects
models through `connect_model`, takes its list of right actions from `Action`, and builds briefs with `ClusterBrief`, `TypicalPost`,
`CandidateTopic` and the sizes `TYPICAL_POSTS_SHOWN` and `CANDIDATE_TOPICS_SHOWN`).

## Configuration and data
`OPENROUTER_API_KEY` (required for tagging), `TAGGING_MODEL_NAME` (default
`anthropic/claude-haiku-5.5`). Fixed in code: `THREAD_DAYS = 3` (`window.py`),
`GROUPING_DISTANCE = 0.3` (`grouping.py`), `TOP_REPLIES_IN_THREAD_TEXT = 5` and
`THREAD_TEXT_CHARACTERS = 3000` (`threads.py`), `REVIVAL_DAYS = 7`, `TYPICAL_POSTS_SHOWN = 6`, `CANDIDATE_TOPICS_SHOWN = 5`,
`MAX_LOOK_UPS_BEFORE_DECIDING = 3`, `MAX_PARALLEL_DECISIONS = 8`, `SEARCH_RESULTS = 20`,
`TAG_RESULTS = 10`, `SAME_NEW_TOPIC_SIMILARITY = 0.90`, `KEYWORDS_PER_TOPIC = 8`,
`MIN_WORD_LENGTH = 4`, `RECENT_DAYS = 7`, `EXCERPT_CHARACTERS = 300`,
`TYPICAL_POST_CHARACTERS = 600`; the model call uses temperature 0, a 120-second timeout
and 3 retries (`model.py`).
Writes `topics`, `cluster_decisions`, `threads` (embedding, topic, decision, stage; deletes
noise with its `posts`), `topic_daily_engagement`, `retrieval_events`.
