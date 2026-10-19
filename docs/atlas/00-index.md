# Transcendent Atlas — Index

**Presentation page:** [https://claude.ai/artifact/VUfVs6dZ9gjBJFKwE1enLJ](https://claude.ai/artifact/VUfVs6dZ9gjBJFKwE1enLJ) (private). Or open
[`atlas.html`](atlas.html) from a checkout to click through the plates as diagrams.

| Plate | What it shows |
|---|---|
| [01 System Map (DRAFT)](01-system-map.md) | The whole app: frontend, API, store, worker, agents, archive source and model provider |
| [04 Environment (DRAFT)](04-environment.md) | Docker Compose services, mounted volumes, first-start setup, and the one OpenRouter key |
| [05 Logging (DRAFT)](05-logging.md) | Everything logged, turn by turn: every model call, job step, outside call and error, as JSON lines on a mounted volume |
| [06 Build order](06-build-order.md) | The seven build steps, each ending with something that runs from a fresh clone |
| [07 Boot data migration (DRAFT)](07-boot-data.md) | Seeding a reviewer's database from about 2 MB in the repo (posts and everything worked out about them, no vectors), then rebuilding the vectors on boot |
| [21 Topics and engagement (DRAFT)](20-data-model/21-topics.md) | The posts (with their agreeing-reply upvotes) and topic tags tables, the daily engagement table that graphs each tag over time, and the daily intake that clusters with a three-day lookahead and lets an LLM attach, mint or drop |
| [30 Frontend (DRAFT)](30-frontend.md) | The web app's stack (agreed) and the screens the brief implies (proposed) |
| [31 Screens (DRAFT)](30-frontend/31-screens.md) | The screens, led by the date-slider Explore page with its dot plot and Generate report button, written as a design brief ready to paste into Claude Design |
| [40 Backend (DRAFT)](40-backend.md) | FastAPI, the stack, the modules, and the one catch-up operation that does all ingestion |
| [41 Live events (DRAFT)](40-backend/41-live-events.md) | Detailed server-sent events from every agent and job to the frontend: streams and event types |
| [50 Prediction (DRAFT)](50-prediction.md) | Per-tag trend vectors across periods, extrapolated to predict the next period, and the backtest that scores it |
| [60 Agents (DRAFT)](60-agents.md) | The two LangGraph agents (one ratifies topic tags, one writes the report with retrieval on or off) and their search and lookup tools |
| [70 Comparison (DRAFT)](70-comparison.md) | Version A without retrieval against version B with it: what makes it fair, and each measurement against one answer key |
| [90 Open Questions](90-open-questions.md) | Decisions still waiting on the owner, and the log of decisions made |
