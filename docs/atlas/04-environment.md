# 04 — Environment (DRAFT)

[← Index](00-index.md) · [01 System Map](01-system-map.md) · [40 Backend](40-backend.md) · [Open questions](90-open-questions.md)

How the app runs on a reviewer's machine. **Specified by Brian:** everything runs under
**Docker Compose**, and **every service that stores information keeps it on a mounted
volume**. The model key is an **OpenRouter** key, sent to the reviewers in the
submission email (README → *Install and run*). Everything else is *proposed*.

```mermaid
flowchart LR
    subgraph COMPOSE["docker compose up"]
        FE["frontend<br/>Vite build, served"]
        API["api<br/>FastAPI"]
        WORK["worker<br/>Celery"]
        BEAT["beat<br/>Celery Beat, one copy"]
        SETUP["setup<br/>runs once: create tables, load snapshot"]
        PG[("postgres + pgvector")]
        RD[("redis")]
    end
    VPG[/"volume: postgres-data"/]
    VRD[/"volume: redis-data"/]
    VMOD[/"volume: model-cache<br/>the embedding model's files"/]
    ENV[/".env<br/>OPENROUTER_API_KEY"/]

    FE --> API
    API --> PG
    API --> RD
    WORK --> PG
    WORK --> RD
    BEAT --> RD
    SETUP --> PG
    PG --- VPG
    RD --- VRD
    WORK --- VMOD
    API --- VMOD
    ENV -.-> API
    ENV -.-> WORK
```

- **Mounted volumes** (specified): the database, Redis, and the embedding model's
  downloaded files each live on a volume, so stopping and restarting keeps everything
  and the model isn't downloaded twice. Redis is set to write to disk (append-only
  file) so queued jobs survive a restart *(proposed)*.
- **First start runs setup automatically** *(proposed)*: `setup` waits for Postgres,
  creates the tables, and loads the snapshot if the database is empty, then exits. The
  API and worker wait for it to finish. A second start finds the data and skips the
  load.
- **One key, one file:** `.env.example` lists every setting with an explanation;
  only `OPENROUTER_API_KEY` must be filled in. Without it the app still opens and shows
  the snapshot and the example comparison; only generating a new report needs it
  *(proposed)*.
- **Ports:** the frontend on `http://localhost:5173` *(proposed)*; nothing else is
  exposed to the host except what the README needs.

## Open in this draft

- `?` What the snapshot contains — OPEN-13.
