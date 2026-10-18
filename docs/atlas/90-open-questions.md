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
| OPEN-3 | The community is r/trawlers on Reddit, fetched through Reddit's official API with a registered app. Trawler Forum itself was ruled out: it blocks automated access and bans AI crawlers in its robots.txt. Still to check: whether r/trawlers is busy enough (roughly four or five new posts a day); if not, r/boating keeps the theme. | 2026-10-18 |
