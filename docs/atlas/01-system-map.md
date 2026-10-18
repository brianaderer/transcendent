# 01 — System Map (DRAFT)

[← Index](00-index.md) · [Open questions](90-open-questions.md)

The whole Community Voices app at the highest level. The frontend and the backend
framework are specified; the other boxes are placeholders for parts the brief
requires and are drawn dashed until they're decided.

```mermaid
flowchart LR
    USER(["Reviewer<br/>(browser)"])
    FE["Frontend<br/>React · TanStack Query + Router · Zustand<br/>see 30"]
    API["Backend<br/>FastAPI<br/>see 40"]
    STORE[("Postgres + pgvector")]
    INGEST["Ingestion<br/>daily fetch · r/sailing · source ? (OPEN-8)"]

    USER --> FE
    FE --> API
    API --> STORE
    INGEST --> STORE

    classDef open stroke-dasharray: 5 5
    class INGEST open
```

- **Frontend** — specified. Details on [30 Frontend](30-frontend.md).
- **Backend** — FastAPI, specified. Its modules are on [40 Backend](40-backend.md).
- **Passage store** — Postgres with pgvector, specified.
- **Ingestion** — fetches posts daily, specified; from r/sailing (OPEN-3, resolved); where the posts are fetched from is OPEN-8.
- Everything runs under Docker Compose (the README's install steps already assume
  Docker).

## Open in this draft

- `?` Where r/sailing's posts are fetched from: OPEN-8.
- `?` The models (OPEN-5), deferred until the agentic loop is designed.
