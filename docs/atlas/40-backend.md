# 40 — Backend (DRAFT)

[← Index](00-index.md) · [01 System Map](01-system-map.md) · [30 Frontend](30-frontend.md) · [Open questions](90-open-questions.md)

The server side: the API the frontend calls, and the modules behind it that ingest,
store, retrieve, write and compare. Brian specified **FastAPI** and **Postgres**.
Everything else on this plate is *proposed*.

## Stack

| Concern | Choice |
|---|---|
| Web framework | **FastAPI** — specified. It publishes the OpenAPI description the frontend's client is generated from (OPEN-1, resolved) |
| Language | Python 3.12 *(proposed)* |
| Data shapes | Pydantic models, shared by the API and the modules *(proposed)* |
| Dependencies | uv, with a lockfile *(proposed)* |
| Tests | pytest, with stand-ins for the model, the embedder and the website (`CLAUDE.md` §7) *(proposed)* |
| Lint and format | Ruff for both *(proposed)* |
| Data store | **Postgres with pgvector** — specified (OPEN-4, resolved) |
| Writing model | Claude, through Anthropic's API *(proposed, OPEN-5)* |
| Embedding model | A small open model run inside the container *(proposed, OPEN-5)* |
| Background jobs | **Celery** workers, with **Celery Beat** scheduling the archive pulls — specified. Broker: Redis, its own container *(proposed)* |
| Agents | **LangGraph / LangChain** — specified. Two agents, see [60](60-agents.md) |
| Running it | Its own service in Docker Compose *(proposed)* |

## Modules *(proposed)*

`CLAUDE.md` §7 asks for these to be separate modules behind small interfaces. The
arrows are who calls whom.

```mermaid
flowchart LR
    WEB["web<br/>FastAPI routes"]
    ING["ingestion<br/>fetch a week · split · embed · store"]
    STORE[("storage<br/>passages, embeddings, runs, retrieval counts")]
    RET["retrieval<br/>nearest passages + count each hit"]
    GEN["generation<br/>writes the document · retrieval on or off"]
    CMP["comparison<br/>runs both versions · measures · saves the run"]
    MAP["projection<br/>embeddings squashed to 2D"]

    WEB --> CMP
    WEB --> MAP
    WEB --> STORE
    CMP --> GEN
    GEN -.->|"only when retrieval is on"| RET
    RET --> STORE
    ING --> STORE
    MAP --> STORE
    classDef open stroke-dasharray: 5 5
    class WEB,ING,STORE,RET,GEN,CMP,MAP open
```

- **generation** is one code path with a switch (`CLAUDE.md` §7): with retrieval off it
  never receives a retriever, so it cannot reach the store.
- **ingestion** fetches posts **daily** from the **Arctic Shift** archive of Reddit (specified, OPEN-8), as a Celery task scheduled by Celery Beat (specified), behind a small *post source* interface so the source can be swapped for Reddit's official API by replacing one module *(interface proposed)*. It runs as a command (`docker compose run …`), not inside the web server,
  and is never needed for the demo: a committed one-week snapshot is loaded instead.
- **projection** squashes embeddings to two dimensions for the embedding map, for
  example with UMAP, and caches the result per week.

## Background jobs *(proposed details)*

```mermaid
flowchart LR
    BEAT["Celery Beat<br/>exactly one copy"]
    REDIS[("Redis<br/>job queue")]
    WORK["Celery worker"]
    PULL["Archive pull<br/>daily, 06:00 UTC"]
    TAGJ["Tagging run<br/>on demand, see 60"]
    REPJ["Report run<br/>on demand, see 60"]
    WEB["web (FastAPI)"]
    AS["Arctic Shift"]
    PG[("Postgres + pgvector")]

    BEAT -->|"schedules"| REDIS
    WEB -->|"queues on request"| REDIS
    REDIS --> WORK
    WORK --> PULL
    WORK --> TAGJ
    WORK --> REPJ
    PULL --> AS
    PULL --> PG
    TAGJ --> PG
    REPJ --> PG
```

- **Daily, with a look-back.** Each pull fetches the last **seven days**, not just
  yesterday, and updates what's already stored. Comments keep arriving on a post for
  days, and upvote counts keep changing, so a strictly one-day pull would freeze every
  thread at its first day. Posts and comments are keyed by Reddit's own id, so
  re-fetching updates rows and never duplicates them (`CLAUDE.md` §7).
- **Why daily is enough.** The document is weekly and trends are computed by the day;
  pulling more often adds load on a volunteer-run archive without changing any result.
- **Tagging and report runs are Celery jobs too.** A report run makes many LLM calls and
  can take a minute; the web request queues the job and returns at once, and the
  frontend checks its status through TanStack Query until it's done.
- **Beat runs as exactly one copy**, or every pull would happen twice.
- **The demo never waits on Beat.** The committed eight-week snapshot is loaded by a
  command; Beat only keeps the data fresh afterwards.

## Open in this draft

- `?` The models — OPEN-5, deferred until the agentic loop is designed.
- `?` Everything marked *proposed* above.
