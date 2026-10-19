# bakeoff

**Source:** `backend/src/voices/bakeoff/`   ·   **Tests:** `backend/tests/bakeoff/`

## Purpose
Compares language models at the tagging decision on fixed sample data with known right
answers, so a choice of model rests on measured quality, time and cost rather than on
guesses (atlas plate 60). The model the app is set to use must also keep getting at least
eight cases in ten right; a separately marked test checks that against the real model.
The latest results are committed in [`docs/benchmarks/tagging-models.md`](../benchmarks/tagging-models.md).

## Public interface
- `python -m voices.bakeoff [model ...]` — runs every case once per model (default: Claude
  Haiku 5.5 and Claude Sonnet 5.5) and prints the results page in markdown. Calls the real
  models, so it needs `OPENROUTER_API_KEY` and spends money (about 20 cents for both models).
- `sample.load_sample_data(path=CASES_FILE) -> SampleData` — the committed sample: topics,
  threads with their top comments, and cases. `Case` holds a group of thread ids, the right
  action (`attach`, `mint` or `noise`) and, for attach, the right topic.
- `sample_store.SampleStore(sample, embedder)` — the sample behind the tagging tools' store
  interface (`search_posts`, `lookup_post`, `search_topics`, `record_retrievals`), searched
  by meaning with the real embedding model; `brief(case)` builds the case's brief the way
  production builds a cluster's; `case_day(case)`, `topic_label(topic_id)`.
  `thread_text(thread)` is a thread as one text: its post and its five best-scored comments.
- `scoring.judge(case, decision) -> Verdict` — right, or which mistake: wrong topic, a
  duplicate of an existing topic, a real conversation called noise, a new subject attached
  to an old topic, noise kept, or no decision.
- `runner.run_bakeoff(model_names, store, embedder, connect) -> list[ModelResult]` — checks
  every model has a price before calling any, then runs each case through the production
  `ToolLoopDecider` and `TaggingTools`. `ModelResult` gives `right`, `share_right`,
  `count(verdict)`, `tokens_in`, `tokens_out`, `cost`, `mean(measure)` and every `CaseResult`.
- `metering.MeteredModel`, `metering.CountingTools`, `metering.Meter` — wrap a chat model and
  the tools to count model calls, tokens read and written, and look-ups. A reply without token
  counts raises `MissingUsage`.
- `pricing.price_of(model_name) -> Price` — OpenRouter's listed price; raises `UnknownPrice`
  for a model not in `PRICES`.
- `report.render_report(results, sample, run_on) -> str` — the results page: a summary table
  per model, then every case with the right answer and each model's answer.

## How it works
`SampleStore` embeds every post and comment, every thread as one text and every topic's
label and description once, at the start. For each case it builds a brief exactly as the
tagging step does for a cluster: the six threads closest to the case's centre as typical
posts, and the five topics closest to it as candidates (the same `TYPICAL_POSTS_SHOWN` and
`CANDIDATE_TOPICS_SHOWN` production uses). The production decision then runs on that
brief with the production tools, which read the sample instead of the database. The
decision is judged against the case's right answer and the meter's counts are kept with it.
Cases run one after another, so the time per decision is not affected by other decisions.

## Uses
[tagging](tagging.md) (`ToolLoopDecider`, `NoDecision`, `TaggingTools`, `Decision`,
`ClusterBrief`, `TypicalPost`, `CandidateTopic`, `connect_model`, and the brief sizes
`TYPICAL_POSTS_SHOWN` and `CANDIDATE_TOPICS_SHOWN`),
[database](database.md) (`PostNotFound` and the excerpt lengths from `tagging_store`),
[ingestion](ingestion.md) (`load_embedder`, the real embedding model),
[environment](environment.md) (`load_settings()`: `OPENROUTER_API_KEY` and `MODEL_DIR`, plus
`TAGGING_MODEL_NAME` in the marked test), OpenRouter (through tagging's `connect_model`),
LangChain (`langchain_core` message types, in `metering.py`), numpy.

## Used by
Nothing in the app. Run by hand (`python -m voices.bakeoff`) and by the `bakeoff`-marked
test `tests/bakeoff/test_live_floor.py`.

## Configuration and data
- `backend/src/voices/bakeoff/tagging_cases.json` — 25 cases over 52 real r/sailing threads
  from 23–26 August 2026 (up to 15 top comments each), and nine topics written for the
  bake-off. The right answers were labelled by Claude from reading the threads and have not
  yet been reviewed by Brian. Removed posts are left out.
- `PRICES` in `pricing.py`, read from OpenRouter on 2026-10-18.
- `FLOOR = 0.8` in `test_live_floor.py` (proposed in atlas plate 60).
- The `bakeoff` pytest marker is excluded from the default run in `pyproject.toml`.
