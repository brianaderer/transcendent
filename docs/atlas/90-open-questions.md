# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| OPEN-3 | Which community does the app cover? Brian asked for Trawler Forum (trawlerforum.com), a forum for owners of trawler-style motor yachts. Checked on 2026-10-18: the site sits behind Cloudflare's bot challenge, so every automated request gets a 403 'Just a moment…' page instead of the forum, and its robots.txt (the file where a site says what automated visitors may do) explicitly bans AI crawlers by name: GPTBot, ClaudeBot, Google-Extended. Getting the posts anyway would mean disguising our fetcher as a person's browser to get past the challenge, against the owners' stated wishes; that isn't something to build, and it's not something to show reviewers. The honest route to Trawler Forum is to email its administrators, explain the project, and ask for permission or an export of eight weeks of posts. It may work, but it can't be counted on in time. The recommendation is to keep the boating theme and use Reddit through its official API: r/boating, or r/sailing, which is larger and busier. Reddit now blocks unregistered requests too (checked today: 403), so Brian would register a free Reddit app (five minutes, at reddit.com/prefs/apps) and we'd fetch with its credentials, within Reddit's published limits. The committed eight-week snapshot means reviewers never need those credentials. Cruisers Forum, the other big boating forum, has the same Cloudflare block as Trawler Forum. | [40](40-backend.md) |
| OPEN-5 | Which models write the document, make the decisions, and make the embeddings? Deferred by Brian until the agentic loop (the sequence of LLM steps and the decisions each makes) is designed. The earlier recommendation stands as a starting point: Claude for writing and decisions, and a small open embedding model inside the container so reviewers need only one key. | [40](40-backend.md) |

## Resolved

| ID | Decision | Date |
|---|---|---|
| OPEN-1 | The frontend's API client is generated from an OpenAPI description the backend publishes (typed TanStack Query hooks, for example with orval). The backend choice must support publishing one. | 2026-10-18 |
| OPEN-2 | The embedding map is drawn with Apache ECharts. | 2026-10-18 |
| OPEN-4 | Similarity search is done in Postgres with the pgvector extension, for both jobs: comparing clusters with topic tags, and retrieving passages for the document. | 2026-10-18 |
| OPEN-6 | Posts are fetched daily. Clustering is not on a fixed schedule: it runs on demand, over whatever time period is requested. | 2026-10-18 |
| OPEN-7 | The committed snapshot holds eight weeks of history: seven to fit trends, one held back for the backtest. | 2026-10-18 |
