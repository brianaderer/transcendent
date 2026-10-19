# Architecture — as built

How the code is **actually built**, one document per module. Plans for what *should*
be built live in the [atlas](../atlas/00-index.md). These documents describe what
*is*, and `/commit-chain` keeps them in step with every commit.

Each module document follows the template in [`CLAUDE.md`](../../CLAUDE.md) §6:
purpose, public interface, how it works, what it uses, what uses it, and its
configuration and data.

| Module | Source | What it does |
|---|---|---|
| [tooling](tooling.md) | `.claude/`, `.githooks/` | Commit hooks, loop guard, and the `/commit-chain` skill that runs after every commit in its own worktree; the `/document-commit` skill and agent that keep documentation in step with every commit; the `/uncle-bob` skill and agent that review each code commit and its documentation commit against *Clean Code*; the `/test-boot` skill and agent that follow the README from a fresh clone the way a reviewer will; offline tests for the hook scripts |
| [environment](environment.md) | `compose.yaml`, `.env.example`, Dockerfiles, `voices/config.py` | Runs every service with one command; settings |
| [logging](logging.md) | `backend/src/voices/log.py` | One JSON line per event, with a trace id, to standard output and the logs volume |
| [api](api.md) | `backend/src/voices/api/`, `voices/health.py` | The web API under `/api`; health check |
| [worker](worker.md) | `backend/src/voices/worker/` | Celery worker and Beat |
| [database](database.md) | `backend/src/voices/db/`, `backend/migrations/` | The tables as SQLAlchemy models, Alembic migrations, and the setup step that applies them on every start |
| [frontend](frontend.md) | `frontend/` | The web app; backend status and history loading for now |
| [ingestion](ingestion.md) | `backend/src/voices/ingestion/` | The daily catch-up: fetch a day of r/sailing from Arctic Shift, filter, fold agreeing replies into upvotes, embed, store |
| [events](events.md) | `backend/src/voices/events.py`, `frontend/src/useLiveEvents.ts` | Live events from jobs to the browser over SSE |
| [tagging](tagging.md) | `backend/src/voices/tagging/`, `voices/db/tagging_store.py` | Sorts threads into topics: each thread encoded as its post and top replies on its first and third days, grouped by meaning, the tagging agent decides attach, mint or noise, threads still without a topic after their third day deleted as noise, daily engagement rebuilt |
| [bakeoff](bakeoff.md) | `backend/src/voices/bakeoff/` | Compares tagging models on fixed sample cases with known right answers: quality, time and cost; results in `docs/benchmarks/` |
