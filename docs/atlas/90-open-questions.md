# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| OPEN-13 | For now, nothing is pre-seeded: the first `docker compose up` prewarms from live data (fetch eight weeks from Arctic Shift, embed, place, tag day by day) and the reviewer waits it out (Brian, 2026-10-18). Still open, to revisit once prewarm is built and timed: (1) how long it takes. **Measured 2026-10-18, build step 2 (fetch and embedding, before tagging exists):** about 35–50 seconds a day on a laptop, so roughly 40–45 minutes for the eight weeks, plus a one-time 130 MB model download; tagging in step 3 will add model calls on top. **Measured 2026-10-19, with tagging:** about 1 hour 38 minutes for the 56 days on a laptop, and at most $1.67 of model calls (OpenRouter's total for the day, which includes two bake-off runs); (2) the demo then depends on Arctic Shift being up and on the OpenRouter key working at the moment the reviewer starts it, and the tagging calls during prewarm are paid from that key; (3) If prewarm proves slow or fragile, the fallback is committing the computed database. | [04](04-environment.md) |

## Resolved

| ID | Decision | Date |
|---|---|---|
| OPEN-1 | The frontend's API client is generated from an OpenAPI description the backend publishes (typed TanStack Query hooks, for example with orval). The backend choice must support publishing one. | 2026-10-18 |
| OPEN-2 | The embedding map is drawn with Apache ECharts. | 2026-10-18 |
| OPEN-3 | The community is r/sailing on Reddit, fetched from Reddit through the Arctic Shift archive (OPEN-8). Trawler Forum was ruled out because it blocks automated access and bans AI crawlers in its robots.txt; r/trawlers was ruled out because it isn't busy enough for eight weeks of clusters and trends. | 2026-10-18 |
| OPEN-4 | Similarity search is done in Postgres with the pgvector extension, for both jobs: comparing clusters with topic tags, and retrieving posts for the document. | 2026-10-18 |
| OPEN-5 | Writing and tag decisions: Claude Sonnet 5.5 through OpenRouter; tag decisions later moved to Claude Haiku 5.5, with at most three look-ups, for cost (Brian, 2026-10-18). Embeddings: a small open long-input model inside the container. Reviewers need one key, an OpenRouter key Brian sends in the submission email; the README says so. | 2026-10-18 |
| OPEN-6 | Posts are fetched daily. (Superseded by OPEN-10: clustering is no longer on demand; posts are tagged day by day on intake.) | 2026-10-18 |
| OPEN-7 | The stored history covers eight weeks: seven to fit trends, one held back for the backtest. | 2026-10-18 |
| OPEN-8 | r/sailing's posts and comments are fetched from Arctic Shift (arctic-shift.photon-reddit.com), a free research archive of Reddit that needs no key, for both the eight-week history and the daily fetch. Reddit's own API was ruled out for now because creating an app requires approval under its Responsible Builder Policy. | 2026-10-18 |
| OPEN-9 | Stored data keeps authors' real Reddit usernames; no pseudonyms. | 2026-10-18 |
| OPEN-10 | Posts are tagged day by day on intake; any period, including the eight-week history and the trend periods, is a range of days. | 2026-10-18 |
| OPEN-11 | Tagging moves forward in time one day at a time, and the backtest uses only tags and centroids as they stood before the held-back week. | 2026-10-18 |
| OPEN-12 | A retrieval_events table records one row per post returned by a search or lookup, with the run, agent, tool and time; statistics separate the report agent from the tagging agent. | 2026-10-18 |
| OPEN-14 | Large data: deleted and bot posts are dropped. Short replies are kept and tabulated as engagement. No cap on comments per thread. Posts are not cut into pieces. Clustering runs daily with a three-day lookahead; a post that falls into no cluster within three days is noise and is deleted. | 2026-10-18 |
| OPEN-15 | The comparison gets a plate of its own (70). | 2026-10-18 |
| OPEN-16 | The document follows the brief: a web page covering the past week's topics with notable threads and quotes linked to real posts, and next week's predictions with their trend evidence. Screen specs for design mockups are on plate 31. | 2026-10-18 |
| OPEN-17 | The main page is governed by a date-range slider that populates and depopulates the dot plot, with a Generate report button for the selected range; each topic's engagement over time is graphed on Topic detail; runs show live progress. See plate 31. | 2026-10-18 |
| OPEN-18 | Everything runs under Docker Compose; every service that stores information (Postgres, Redis, the model cache) keeps it on a mounted volume. See plate 04. | 2026-10-18 |
| OPEN-19 | Short agreeing replies ("+1", "this", "same here") are found by a basic semantic check (short, and close in meaning to a handful of agreement examples) and are not saved; each adds one to its parent post's upvotes, which count as engagement for the parent's tag. Proposed alongside: a per-day count so the trend knows when the agreement happened. | 2026-10-18 |
| OPEN-20 | Each post is embedded once, at intake. The squashing to two dimensions for the dot plot is recomputed from the posts in the selected date range whenever the range changes (Brian, replacing the earlier stored-position decision). | 2026-10-18 |
| OPEN-21 | The document's conclusions are aggregate (which topics, how big, which way they're moving), drawn from the topic and engagement data, not per-post. The comparison scores both versions against one answer key computed from that data; per-sentence checking against posts is dropped. | 2026-10-18 |
| OPEN-22 | To try first: predictions are scored on a committed list of expected topics and directions, not on prose or numbers. Each report also predicts its own range from what was known the day before the range began, so it is scored at once. The code's numerical projections are checked separately, outside the A/B scores. | 2026-10-18 |
| OPEN-23 | No longer applies: positions aren't stored, so first start doesn't need a layout. | 2026-10-18 |
| OPEN-24 | Runs are not referred back to: no run history, no LangGraph checkpoints, no stored event log, no Runs screen. Results are shown when a run finishes. | 2026-10-18 |
| OPEN-25 | The report agent returns one answer in two parts: the prose report, and a fixed list of its topics with rank and direction plus its predicted topics. The page shows the prose with the list as a small table beside it; the app scores the list. | 2026-10-18 |
| OPEN-26 | Reports can cover any date range; the Explore slider starts on the last seven days, so the default report is the brief's weekly one. The prediction covers a period the same length as the range. | 2026-10-18 |
| OPEN-27 | Logging is under the hood, for developers only: JSON log files, no viewer, nothing shown to reviewers. | 2026-10-18 |
| OPEN-28 | Database changes are made with Alembic. Tables are described once as SQLAlchemy models; migrations are generated from them and applied by setup on every start. The earlier schema file and local data were wiped. | 2026-10-18 |
| OPEN-29 | The thread is the unit: each thread is written out as its post plus its top comments and encoded as one text. It is encoded on day one, so a topic shows without a three-day lag, and encoded again on day three with the comments that have arrived since; each time, that day's threads are grouped by meaning and the tagging agent attaches, mints or calls noise. Comments arriving later, and old threads that become active again, are heat signals. Measured on three real days: single posts left 86% in no group; post plus top five comments gave the most coherent groups. | 2026-10-18 |
| OPEN-30 | A thread whose opening post we don't have, because it was removed or started before our history, is tagged from what we have: its title plus its top comments. Its first and third days count from the day we first see it, which is the day of its first stored comment. Found on the first start: 277 such threads held 865 of 13,613 stored posts and comments and counted for no topic. | 2026-10-19 |
