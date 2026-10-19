# 05 — Logging and observability (DRAFT)

[← Index](00-index.md) · [01 System Map](01-system-map.md) · [04 Environment](04-environment.md) · [Open questions](90-open-questions.md)

**Specified by Brian:** turn-by-turn logging and observability. **Everything is
logged.** It's **under the hood, for developers only**: JSON log files, no viewer,
nothing in the app (OPEN-27). Everything else is *proposed*.

## What is logged *(proposed)*

- **Every model turn**, in full: which agent, which run or day, the complete prompt, the
  complete answer, every tool call with its arguments and result, tokens in and out,
  cost, and how long it took. *(As built, the tagging agent's turns are logged in full. The report
  agent's are not: each comparison run logs every event it announces, with `stream` set to
  `run-<id>` (the steps, each tool call with its arguments and how many posts it returned,
  tokens in and out per step, the measurements), and `run.failed` with the reason; every
  line of the run, in both versions' threads, carries the trace id `run-<id>`. The
  instructions are kept with the run's result for a day, and the model's answers are its
  documents and lists.)*
- **Every job step:** each day's catch-up (fetch, filter, upvotes, embed, cluster, tag,
  noise deleted, roll-up) with counts and timings; each report run's steps; each map
  recompute.
- **Every outside call:** Arctic Shift requests and responses (status, item counts,
  time), OpenRouter calls, the embedding model.
- **Every API request** and every error, with the full error.

## How *(proposed)*

- **One line of JSON per event**, from every service (API, worker, Beat, setup),
  written through one small logging module so every line has the same fields: time,
  service, level, event name, and a **trace id** shared by everything one run or one
  day job does — so a single run can be followed end to end across services.
- **Written to standard output and to a mounted volume** (`logs`), so `docker compose
  logs` shows it live and the files survive a restart (`CLAUDE.md`'s storage rule on
  [04](04-environment.md)).
- **Kept apart from the live events** ([41](40-backend/41-live-events.md)): live events
  feed the screen and are not stored; logs are for the people running the app.

## Open in this draft

- Nothing open on this plate.
