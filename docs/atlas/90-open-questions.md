# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| OPEN-5 | Which models write the document, make the decisions, and make the embeddings? Deferred by Brian until the agentic loop (the sequence of LLM steps and the decisions each makes) is designed. The earlier recommendation stands as a starting point: Claude for writing and decisions, and a small open embedding model inside the container so reviewers need only one key. | [40](40-backend.md) |
| OPEN-8 | Where do r/sailing's posts come from, now that Reddit won't issue an API key without approval? Reddit's Responsible Builder Policy (late 2025) blocks creating an app until a separate access request is approved, which can take days or weeks and may be refused. Checked on 2026-10-18, two sources work right now with no key. (1) Arctic Shift (arctic-shift.photon-reddit.com), a free archive of Reddit run for researchers. It returned r/sailing's posts and comments for this week and for eight weeks ago, so it can fill the whole history at once. It is run by volunteers, not by Reddit, so it can be slow or go offline, and its data is Reddit's content collected outside Reddit's own API. (2) Reddit's public RSS feeds, which are official and keyless but return only the latest few dozen posts, so they can't fill eight weeks of history and would need comment threads fetched one by one. The recommendation: use Arctic Shift for both the eight-week history and the daily fetch, behind our own small 'post source' interface, so the source can be swapped for the official API later by replacing one module; and file Reddit's access request in parallel as the clean long-term route. Reviewers need no Reddit credentials at all, and the committed snapshot covers the demo if Arctic Shift is down. Because the repo goes public with that snapshot inside, authors' usernames in it should be replaced with stable pseudonyms (the same person always gets the same stand-in name), so we're not republishing who said what. | [40](40-backend.md) |

## Resolved

| ID | Decision | Date |
|---|---|---|
| OPEN-1 | The frontend's API client is generated from an OpenAPI description the backend publishes (typed TanStack Query hooks, for example with orval). The backend choice must support publishing one. | 2026-10-18 |
| OPEN-2 | The embedding map is drawn with Apache ECharts. | 2026-10-18 |
| OPEN-4 | Similarity search is done in Postgres with the pgvector extension, for both jobs: comparing clusters with topic tags, and retrieving passages for the document. | 2026-10-18 |
| OPEN-6 | Posts are fetched daily. Clustering is not on a fixed schedule: it runs on demand, over whatever time period is requested. | 2026-10-18 |
| OPEN-7 | The committed snapshot holds eight weeks of history: seven to fit trends, one held back for the backtest. | 2026-10-18 |
| OPEN-3 | The community is r/sailing on Reddit, fetched from Reddit (the source is OPEN-8). Trawler Forum was ruled out because it blocks automated access and bans AI crawlers in its robots.txt; r/trawlers was ruled out because it isn't busy enough for eight weeks of clusters and trends. | 2026-10-18 |
