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
| [database](database.md) | `backend/src/voices/db/` | Tables and first-start setup |
| [frontend](frontend.md) | `frontend/` | The web app; backend status for now |
