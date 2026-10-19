# report

**Source:** `backend/src/voices/report/` (`tasks.py`, `writer.py`, `tools.py`, `reading_tools.py`, `versions.py`, `graph.py`, `comparison_run.py`, `runs.py`, `launcher.py`), `backend/src/voices/worker/report_task.py`, `frontend/src/runs/`   ·   **Tests:** `backend/tests/report/`, `backend/tests/test_run_routes.py`, `frontend/src/runs/*.test.ts*`

## Purpose
Writes the Community Voices Document for a date range, with and without retrieval, and
compares the two (atlas plates [50](../atlas/50-prediction.md), [60](../atlas/60-agents.md),
[70](../atlas/70-comparison.md); `CLAUDE.md` §7). One code path writes both versions; the
only difference is the tools the model gets: version A may only read posts, a few at a time in
a fixed shuffle with no retrieval by meaning, at most 10 per step; version B searches our
store by meaning (atlas OPEN-39).

## Public interface
- `tasks.write_task(days)` and `tasks.predict_task(days)` — what the model is asked, as a
  `Task` (phase, instructions, answer tool). The words are the same for both versions. The report
  asks for each topic's direction and, for each topic, where it looks to be heading next and
  why. Both tasks say to work from what the model can see in the community's posts with its
  tools (A's reading, B's searches) and from what it knows of the community and the season,
  and to say plainly where its evidence is thin (`FROM_WHAT_YOU_CAN_SEE`); the prediction
  adds that the tools show the community only up to the day before the range.
  `Report` (the document in Markdown, and its `topics`: name, rank, direction) and
  `Prediction` (`predicted` topics with directions, and a short `reasoning`) are the answer
  tools; their lists are the comparison's committed lists (atlas OPEN-25).
- `writer.ReportWriter(model, tools, emit).write(task)` — one call of the agent. The model
  is offered exactly the schemas its tools object carries (`Tools.schemas`) and the answer
  tool, so version A is offered only `read_posts` and version B its four tools; a tools
  object offering no schemas leaves only the answer tool. It may take up to `MAX_TOOL_CALLS` turns (each tool call spends one, and so does a reply that
  looks nothing up, plain text or a malformed answer, so a model that keeps talking or
  answering badly still ends), then is offered only the answer; a reply
  without a valid answer is told why (or reminded) `CORRECTIONS` times before `NoAnswer` is
  raised. Returns a `Written`: the answer, tool calls made, posts seen, tokens in and out,
  seconds. Each tool call is announced as `tool.called` and `tool.returned`.
- `tools.ReportTools(store, embedder, window, run_name, trends)` — version B's tools:
  `search(term)` (posts in the window closest in meaning, 20 at most), `lookup(post_id)`
  (one post in full; a post written after the window is refused), `topic_trends()` (what the
  run hands in), `upcoming_events()` (posts in the window that read like dated plans). Every
  post returned is counted in `retrieval_events` as the report agent's, under the run's name.
  `run(name, arguments)` returns a `ToolResult` (the text the model reads, and the post ids);
  `schemas` is `TOOL_SCHEMAS`, what the model is offered. `said(text)` is a result with no
  posts, shared with the reading tools.
- `reading_tools.ReadingTools(reader, window, seed)` — version A's one tool,
  `read_posts(day?)`: up to `READ_BATCH` (5) whole posts written in the window, or on the one
  day given (a day outside the window, or not a date, is explained instead), each with its
  author, date and thread title, in the fixed shuffle the seed (the run's name) gives, never
  ranked by meaning, and never a post already given. One `ReadingTools` serves one phase, and
  it hands out `READ_BUDGET` (35) posts in all, and they are shared evenly over the window's days (`_even_shares`: 35 split by the number of days, the first few taking one more), and the tool holds each day to its share: a read with no day takes the day with the most share left, a day that gives back fewer posts than were asked for has none left, so its share is closed at once (`_spend_share`) and the next read moves on to another day; and a day whose share is spent is refused, naming the days still unread; after that every call answers
  `NOTHING_LEFT_TO_READ` ("No posts left to read; answer now with what you have.") without
  asking the store. Reads are not retrieval, so they are not counted in `retrieval_events`.
  `schemas` is `READING_SCHEMAS`; `ids_given` lists the posts handed out so far. `reader` is
  anything with `sample_posts(days, limit, seed, exclude_ids)` (`PostReader`).
- `versions` — `Version` (`"A"` or `"B"`) and `VERSIONS`, the order they are shown in.
- `graph.every_version_at_once(work)` — runs `work(version)` for every version at once, as a
  LangGraph fan-out (atlas plate 60): `START` sends one branch per version to a `version`
  node, whose results are gathered by an `operator.add` reducer, with `max_concurrency =
  MAX_PARALLEL_VERSIONS` (2, one per version). Answers in the order of `VERSIONS`. Each
  branch runs in a copy of the caller's context variables (LangGraph does this itself; a
  test proves it), so its log lines carry the run's trace id. A version's error is carried
  out of the graph and raised unchanged, because LangGraph appends the task's name and id to
  an error raised inside a node, and the message is the failure reason the page shows.
- `comparison_run.ComparisonRun(parts, emit).run(run_id, days)` — one
  comparison, both versions at once through `every_version_at_once`: for each version, the report for the range (B's tools see the range, and
  `topic_trends` gives the range's measured topics) and the prediction for the range made as
  of the day before (B's tools see only the 28 days before, and `topic_trends` gives the
  projected trends, plate 50). Each phase's tools are built by their own method
  (`_tools_for_the_report`, `_tools_for_the_prediction`); version A gets a fresh
  `ReadingTools` for each phase (`_reading`), over the same windows as B's (the range, then
  the 28 days before it), with the run's name as the shuffle's seed so the same run reads the
  same posts. Both are scored against the same answer key
  ([comparison](comparison.md)'s `mark` then `score`). `RunParts.data` is anything with
  explore's `TopicData` reads, the `ReportStore` reads and `sample_posts` (`PostReader`); `RunParts.embedder` anything with
  `embed_query` and `embed_for_comparison` (`QueryEmbedder` and ingestion's
  `ComparisonEmbedder`). Returns a `RunResult`: the range, the model, the range's main
  topics, the instructions, and per version a `VersionResult` (document, topics, predicted,
  reasoning, scores, the matches behind them, tool calls, posts seen, tokens, seconds).
- `runs.RunStore(redis)` — a run's `RunState` (`running`, `finished` with its result, or
  `failed` with the reason), kept for a day (`KEPT_SECONDS`) and then gone: there is no run
  history (atlas OPEN-24). `stream_of(run_id)` is its live-event stream, `run-<id>`, and
  `is_run_stream(name)` says whether a name is one (the API's stream route uses it; the
  frontend's `runStream(runId)` must match it).
- `launcher.RunLauncher(store, queue)` — `start(days)` marks a new run running and queues the
  worker's `voices.compare` task, returning a `RunStarted` (run id and stream); `state(run_id)`.
- API: `POST /api/runs` (`{start, end}`) and `GET /api/runs/{run_id}` ([api](api.md)); a run's
  events come on `GET /api/streams/run-<id>/events`.
- Frontend: **Generate report** on Explore starts a run and puts its id in the address
  (`?run=`); `RunProgress` shows both versions' steps and tool calls live, then links to the
  **Document** (`/runs/<id>/report`, version B unless `?version=A`) and the **Comparison**
  (`/runs/<id>/comparison`: the scoreboard, the real topics against what each version said,
  invented topics marked, and both documents side by side).

## How it works
The worker's `voices.compare` task (`compare_now`) builds the model (`REPORT_MODEL_NAME`, Claude Sonnet 5.5
through OpenRouter), the stores and the embedder, and hands the comparison to
`run_and_keep_result(comparison, record, job)`, which keeps the result or, on any failure,
the reason ([worker](worker.md)). The run is a LangGraph graph with one branch per
version; inside each branch the writer's tool loop (`ReportWriter`) stays a plain loop over
LangChain, the same design as the tagging agent's decision loop inside its own fan-out.
Events go out on the run's stream: `run.started`, per version `step.started` /
`step.finished` / `usage` / `tool.called` / `tool.returned`, then a `measurement.done` per
score, then `run.finished` (or `run.failed` with the reason). `run.finished` is sent by the
worker task (`run_and_keep_result`) only after the result is saved, so a page that rereads the
run on hearing it finds the result; likewise `run.failed` is sent only after the run is marked
failed with its reason. The result is kept in Redis for a
day so the Document and Comparison pages can read it; nothing else is kept.

## Uses
[comparison](comparison.md) (answer key, `mark`, scores, commitments),
[prediction](prediction.md) (projected trends), [explore](explore.md) (`DayRange`, the range's
topics, `ExploreStore`), [tagging](tagging.md) (`TaggingStore`'s search, lookup, `sample_posts` and
retrieval counting; `connect_model`), [database](database.md) (`connect_store`, and `PostNotFound` for a
lookup of an unknown post), [ingestion](ingestion.md) (the embedder and its
`ComparisonEmbedder` interface), [events](events.md),
[logging](logging.md), Redis, Celery, LangGraph, LangChain, OpenRouter.

## Used by
[api](api.md) (the run routes), [worker](worker.md) (`voices.compare`),
[frontend](frontend.md) (Explore's Generate report, the Document and Comparison screens).

## Configuration and data
`OPENROUTER_API_KEY`, `REPORT_MODEL_NAME` (default `anthropic/claude-sonnet-5.5`). Fixed in
code: `MAX_TOOL_CALLS = 20`, `CORRECTIONS = 1`, `SEARCH_RESULTS = 20`, `EVENT_RESULTS = 15`,
`READ_BATCH = 5`, `READ_BUDGET = 35`,
`DAYS_SEEN_BEFORE_A_PREDICTION = 28`, `KEPT_SECONDS` (a day). Writes `retrieval_events`
(agent `report`, version B's tools only) and the run's state in Redis.
