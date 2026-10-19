# environment

**Source:** `compose.yaml`, `.env.example`, `backend/Dockerfile`, `frontend/Dockerfile`, `backend/pyproject.toml` (test settings), `backend/src/voices/config.py`   ·   **Tests:** `backend/tests/test_config.py`

## Purpose
Runs every part of the app with one command, `docker compose up --build`, so a reviewer
needs only Docker. Plan: [atlas plate 04](../atlas/04-environment.md).

## Public interface
- `docker compose up --build` — starts every service; the app is at `http://localhost:5173`
  (or the port set as `PORT` in `.env`).
- `docker compose down --volumes` — stops it and erases all stored data.
- `voices.config.load_settings()` — the backend's settings, read from the environment.
- `voices.config.HISTORY_DAYS` (56) — how many days back the app keeps r/sailing (eight
  weeks, atlas OPEN-7); fixed in code, not read from the environment.

## How it works
The Compose project is named `community-voices`, so containers and volumes get that prefix
whichever folder the repo is cloned into. The backend runs as an ordinary user
(`voices`), not root; the folders its volumes mount onto belong to that user. The
frontend's container exits 0 when stopped.

Seven services. `postgres` (with the pgvector extension) and `redis` start first and
report healthy. `setup` then runs any database migrations not yet applied (see [database](database.md)) and exits; `api` and `worker` wait for it
to finish successfully. `beat` schedules jobs onto Redis. `frontend` serves the built web
app on port 5173 inside its container, published on your computer as `PORT` (5173 unless
`.env` says otherwise), and passes every `/api` request through to `api`, so only one port is
exposed. It runs with `init: true`, and its start command catches Docker's stop signal and
exits 0, because `vite preview` doesn't stop on that signal by itself; so `Ctrl+C` stops it
at once and cleanly. The four backend services are all built from the same `backend/` folder and differ only
in the command they run. Backend tests run with pytest's cache turned off
(`backend/pyproject.toml`), because the ordinary user can't write one inside the container
and the containers are thrown away after each run anyway. The same settings leave out tests
marked `database` (they need a running Postgres; run them with `pytest -m database`) and
the one test marked `bakeoff` (it calls the real tagging model and spends money; run it with
`pytest -m bakeoff`, see [bakeoff](bakeoff.md)). For the same reason the backend
image points Ruff's cache at `/tmp/ruff-cache` (`RUFF_CACHE_DIR` in `backend/Dockerfile`), so
linting works inside the container. The image also carries `alembic.ini` and `migrations/`,
which the `setup` service needs.

## Uses
[database](database.md), [api](api.md), [worker](worker.md), [frontend](frontend.md), [logging](logging.md).

## Used by
- [api](api.md), [worker](worker.md) and [database](database.md) (setup) read their
  settings through `voices.config.load_settings()`; the worker passes
  `OPENROUTER_API_KEY` and `TAGGING_MODEL_NAME` on to [tagging](tagging.md).
- [bakeoff](bakeoff.md) reads `OPENROUTER_API_KEY` and `MODEL_DIR` through
  `load_settings()`; its `bakeoff`-marked test also reads `TAGGING_MODEL_NAME`.
- [ingestion](ingestion.md) (the catch-up) and [api](api.md) (`GET /api/ingestion`) read
  `voices.config.HISTORY_DAYS`.
- The README's install and run steps.

## Configuration and data
- `.env` (copied from `.env.example`): `PORT` (default 5173), the port the app is opened
  on; `OPENROUTER_API_KEY`, needed from the first start (tagging each loaded day calls the
  model; without it loading stops at the first day with the reason on the page).
  `TAGGING_MODEL_NAME` (default `anthropic/claude-haiku-5.5`, set in `voices/config.py`)
  is not in `.env.example`; adding a `TAGGING_MODEL_NAME=` line to `.env` switches tagging
  to another OpenRouter model. Both reach the backend containers through `env_file: .env` in `compose.yaml`,
  which is read when a container is created: after editing `.env`, run `docker compose up`
  again (it re-creates the containers whose settings changed); `docker compose restart`
  keeps the old values.
- Set by `compose.yaml` for the backend services: `DATABASE_URL`, `REDIS_URL`, `LOG_DIR`,
  and `SERVICE_NAME` (each container's own name, used in its log lines).
- `MODEL_DIR` is set nowhere; its default in `voices/config.py`,
  `/home/voices/.cache/models`, is where the worker downloads the embedding model, on the
  `model-cache` volume.
- The backend's dependencies are pinned in `backend/pyproject.toml` and `backend/uv.lock`;
  among them `fastembed` runs the embedding model, `httpx` reads the archive,
  `scikit-learn` clusters posts (HDBSCAN), and `langgraph`, `langchain-core` and
  `langchain-openai` run the tagging agent against OpenRouter.
- The first start needs an internet connection (the worker fetches from the Arctic Shift
  archive, downloads the embedding model, and calls the tagging model on OpenRouter) and
  about 1 GB of memory for the worker (give Docker at least 4 GB).
- Named volumes (created as `community-voices_<name>`): `postgres-data`, `redis-data`
  (Redis writes an append-only file), `model-cache` (the embedding model's files, from
  build step 2, mounted at `/home/voices/.cache`), `logs` (mounted at `/var/log/voices`).
