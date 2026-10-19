# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| — | Nothing is waiting on Brian. | |

## Resolved

| ID | Decision | Date |
|---|---|---|
| OPEN-34 | Embeddings are stored at half precision (pgvector's halfvec: two bytes a number instead of four), for posts, threads and topic centres, so the database stays small. Measured before the change: 75 MB for the eight weeks once compacted, of which 37 MB is embeddings and 2.7 MB the posts' text; expected about 40 MB after. Fewer numbers per embedding (256) was ruled out because search gets blurrier. | 2026-10-19 |
| OPEN-13 | The first start loads the history live: it fetches eight weeks from Arctic Shift, embeds, groups and tags day by day, and the reviewer waits it out; nothing is pre-seeded. Measured on two full runs (2026-10-19): about 1 hour 40 minutes on a laptop and $1.30 to $1.70 of OpenRouter credit, recorded in the README's step 4. | 2026-10-19 |
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
| OPEN-31 | A thread deleted as noise is remembered by its id and the day it was deleted, with no text, so we are parsimonious with data: a comment that arrives on it later is dropped at intake rather than bringing the thread back to be stored, embedded and decided again. Fetching stays one day at a time, each day once, with the day ledger as the high-water mark. This also settles plate 21's open item on replies to a parent deleted as noise. | 2026-10-19 |
