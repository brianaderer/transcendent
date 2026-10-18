# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| OPEN-5 | Which models write the document, make the decisions, and make the embeddings? The agentic loop is now on plate 60: two LangGraph agents, one that ratifies tags and one that writes the report. The earlier recommendation stands as a starting point: Claude for writing and decisions, and a small open embedding model inside the container so reviewers need only one key. Since posts are no longer cut into pieces (OPEN-14), the embedding model must accept a whole long post: a model with a long input limit (several thousand words) rather than one capped at a few hundred. | [40](40-backend.md) |
| OPEN-13 | What exactly is in the committed snapshot? Raw posts alone would mean the reviewer's first boot has to embed eight weeks of posts and run the tagging agent over all of them, which takes time and costs model calls before anything is on screen, and gives different tags each time. The recommendation: commit the raw posts plus the embeddings, the tags, the cluster decisions, and one finished comparison run, so the app opens fully populated with no key at all; a fresh tagging or report run is then the live part of the demo and needs the reviewer's key. | [40](40-backend.md) |
| OPEN-18 | How the whole thing boots is not on any plate: six services (frontend, API, Postgres, Redis, Celery worker, Celery Beat), the snapshot load, the database setup, and which key the reviewer supplies. The README promises one command. The recommendation: an environment plate covering the compose file, a one-time setup step that runs automatically on first start (create tables, load the snapshot), and .env.example with the single key, depending on OPEN-5. | [01](01-system-map.md) |

## Resolved

| ID | Decision | Date |
|---|---|---|
| OPEN-1 | The frontend's API client is generated from an OpenAPI description the backend publishes (typed TanStack Query hooks, for example with orval). The backend choice must support publishing one. | 2026-10-18 |
| OPEN-2 | The embedding map is drawn with Apache ECharts. | 2026-10-18 |
| OPEN-4 | Similarity search is done in Postgres with the pgvector extension, for both jobs: comparing clusters with topic tags, and retrieving passages for the document. | 2026-10-18 |
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
