# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| OPEN-13 | For now, nothing is pre-seeded: the first `docker compose up` prewarms from live data (fetch eight weeks from Arctic Shift, embed, place, tag day by day) and the reviewer waits it out (Brian, 2026-10-18). Still open, to revisit once prewarm is built and timed: (1) how long it takes, likely minutes, dominated by a few hundred tagging calls and embedding on the laptop's processor; (2) the demo then depends on Arctic Shift being up and on the OpenRouter key working at the moment the reviewer starts it, and the tagging calls during prewarm are paid from that key; (3) CLAUDE.md §7 currently requires a committed snapshot so the demo never depends on live fetching, which this decision sets aside. If prewarm proves slow or fragile, the fallback is committing the computed database. | [04](04-environment.md) |

## Resolved

| ID | Decision | Date |
|---|---|---|
| OPEN-1 | The frontend's API client is generated from an OpenAPI description the backend publishes (typed TanStack Query hooks, for example with orval). The backend choice must support publishing one. | 2026-10-18 |
| OPEN-2 | The embedding map is drawn with Apache ECharts. | 2026-10-18 |
| OPEN-4 | Similarity search is done in Postgres with the pgvector extension, for both jobs: comparing clusters with topic tags, and retrieving posts for the document. | 2026-10-18 |
| OPEN-6 | Posts are fetched daily. (Superseded by OPEN-10: clustering is no longer on demand; posts are tagged day by day on intake.) | 2026-10-18 |
| OPEN-7 | The committed snapshot holds eight weeks of history: seven to fit trends, one held back for the backtest. | 2026-10-18 |
| OPEN-3 | The community is r/sailing on Reddit, fetched from Reddit through the Arctic Shift archive (OPEN-8). Trawler Forum was ruled out because it blocks automated access and bans AI crawlers in its robots.txt; r/trawlers was ruled out because it isn't busy enough for eight weeks of clusters and trends. | 2026-10-18 |
| OPEN-8 | r/sailing's posts and comments are fetched from Arctic Shift (arctic-shift.photon-reddit.com), a free research archive of Reddit that needs no key, for both the eight-week history and the daily fetch. Reddit's own API was ruled out for now because creating an app requires approval under its Responsible Builder Policy. | 2026-10-18 |
| OPEN-9 | The committed snapshot keeps authors' real Reddit usernames; no pseudonyms. | 2026-10-18 |
| OPEN-10 | Posts are tagged day by day on intake; any period, including the eight-week history and the trend periods, is a range of days. | 2026-10-18 |
| OPEN-11 | Tagging moves forward in time one day at a time, and the backtest uses only tags and centroids as they stood before the held-back week. | 2026-10-18 |
| OPEN-12 | A retrieval_events table records one row per post returned by a search or lookup, with the run, agent, tool and time; statistics separate the report agent from the tagging agent. | 2026-10-18 |
| OPEN-14 | Large data: deleted and bot posts are dropped. Short replies are kept and tabulated as engagement. No cap on comments per thread. Posts are not cut into pieces. Clustering runs daily with a three-day lookahead; a post that falls into no cluster within three days is noise and is deleted. | 2026-10-18 |
| OPEN-15 | The comparison gets a plate of its own (70). | 2026-10-18 |
| OPEN-16 | The document follows the brief: a web page covering the past week's topics with notable threads and quotes linked to real posts, and next week's predictions with their trend evidence. Screen specs for design mockups are on plate 31. | 2026-10-18 |
| OPEN-17 | The main page is governed by a date-range slider that populates and depopulates the dot plot, with a Generate report button for the selected range; each topic's engagement over time is graphed on Topic detail; runs show live progress. See plate 31. | 2026-10-18 |
| OPEN-19 | Short agreeing replies ("+1", "this", "same here") are found by a basic semantic check (short, and close in meaning to a handful of agreement examples) and are not saved; each adds one to its parent post's upvotes, which count as engagement for the parent's tag. Proposed alongside: a per-day count so the trend knows when the agreement happened. | 2026-10-18 |
| OPEN-5 | Writing and tag decisions: Claude Sonnet 5.5 through OpenRouter. Embeddings: a small open long-input model inside the container. Reviewers need one key, an OpenRouter key Brian sends in the submission email; the README says so. | 2026-10-18 |
| OPEN-18 | Everything runs under Docker Compose; every service that stores information (Postgres, Redis, the model cache) keeps it on a mounted volume. See plate 04. | 2026-10-18 |
| OPEN-20 | Each post is embedded once and its dot-plot position computed once, per day at intake, and stored; the dot plot only reads stored positions. | 2026-10-18 |
