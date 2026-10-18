# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| OPEN-5 | Which models write the document, make the decisions, and make the embeddings? Deferred by Brian until the agentic loop (the sequence of LLM steps and the decisions each makes) is designed. The earlier recommendation stands as a starting point: Claude for writing and decisions, and a small open embedding model inside the container so reviewers need only one key. | [40](40-backend.md) |

## Resolved

| ID | Decision | Date |
|---|---|---|
| OPEN-1 | The frontend's API client is generated from an OpenAPI description the backend publishes (typed TanStack Query hooks, for example with orval). The backend choice must support publishing one. | 2026-10-18 |
| OPEN-2 | The embedding map is drawn with Apache ECharts. | 2026-10-18 |
| OPEN-4 | Similarity search is done in Postgres with the pgvector extension, for both jobs: comparing clusters with topic tags, and retrieving passages for the document. | 2026-10-18 |
| OPEN-6 | Posts are fetched daily. Clustering is not on a fixed schedule: it runs on demand, over whatever time period is requested. | 2026-10-18 |
| OPEN-7 | The committed snapshot holds eight weeks of history: seven to fit trends, one held back for the backtest. | 2026-10-18 |
| OPEN-3 | The community is r/sailing on Reddit, fetched from Reddit through the Arctic Shift archive (OPEN-8). Trawler Forum was ruled out because it blocks automated access and bans AI crawlers in its robots.txt; r/trawlers was ruled out because it isn't busy enough for eight weeks of clusters and trends. | 2026-10-18 |
| OPEN-8 | r/sailing's posts and comments are fetched from Arctic Shift (arctic-shift.photon-reddit.com), a free research archive of Reddit that needs no key, for both the eight-week history and the daily fetch. Reddit's own API was ruled out for now because creating an app requires approval under its Responsible Builder Policy. | 2026-10-18 |
| OPEN-9 | The committed snapshot keeps authors' real Reddit usernames; no pseudonyms. | 2026-10-18 |
