# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| OPEN-3 | Which community does the app cover? It needs enough posts every week to fill a document, and posts we can fetch reliably. The recommendation is a subreddit from the brief's own examples, the fantasy map makers: r/mapmaking or r/worldbuilding. Reddit gives each post and comment a date, author and thread, which the document and the measurements need, and its free API allows a week's fetch easily. The risk is that Reddit throttles or blocks the fetcher, but the demo never depends on live fetching, because a one-week snapshot is committed to the repo. The brief's other examples are harder: Discord needs a bot invited into the server by its admins, and tango is spread across Facebook groups that can't be fetched. Hacker News is the easiest to fetch of all (open API, no key), but it reads more like a news feed than a community with its own culture. | [40](40-backend.md) |
| OPEN-4 | The database is Postgres (decided 2026-10-18). Still open: how similarity search is done inside it. The recommendation is the pgvector extension, which adds search by meaning to Postgres. The topic design on plate 21 makes it do two jobs, not one: tagging each new passage with the nearest existing topic, and finding the passages most relevant to the document being written. Doing that without pgvector would mean loading every embedding into Python for every search, which works at this size but puts search logic in our code that the database could do for us. | [21](20-data-model/21-topics.md), [40](40-backend.md) |
| OPEN-5 | Which models write the document and make the embeddings? The recommendation is Claude (Sonnet 5.5) for writing, through Anthropic's API, and a small open embedding model (for example BGE-small) that runs inside the backend container. Anthropic doesn't offer embeddings itself, so the choice is between a second paid service (Voyage AI or OpenAI) and a local model. The local model means the reviewer needs only one key, the Anthropic one, and embedding the snapshot costs nothing and works offline. Its search quality is a little below the paid services, which doesn't matter at this size. The cost is a larger container image (a few hundred megabytes more) and a slower first build. | [40](40-backend.md) |

## Resolved

| ID | Decision | Date |
|---|---|---|
| OPEN-1 | The frontend's API client is generated from an OpenAPI description the backend publishes (typed TanStack Query hooks, for example with orval). The backend choice must support publishing one. | 2026-10-18 |
| OPEN-2 | The embedding map is drawn with Apache ECharts. | 2026-10-18 |
