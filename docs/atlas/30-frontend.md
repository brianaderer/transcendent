# 30 — Frontend (DRAFT)

[← Index](00-index.md) · [01 System Map](01-system-map.md) · [Open questions](90-open-questions.md)

The web app the reviewer clicks through. Brian specified React, TanStack Query,
TanStack Router and Zustand. Everything else on this plate is *proposed* and waits
for Brian to confirm or change it; see [Open in this draft](#open-in-this-draft).

## Stack

| Concern | Choice |
|---|---|
| UI library | **React** — specified |
| Routing | **TanStack Router** — specified |
| Server state | **TanStack Query** — specified. Everything fetched from the backend lives here |
| Client state | **Zustand** — specified. Proposed rule: only for state that lives purely in the browser (for example which comparison panel is expanded). Anything a reviewer should be able to link to — the selected week, the selected run — lives in the address, through TanStack Router's search parameters |
| Language and build | TypeScript, built with Vite *(proposed)* |
| Tables | TanStack Table, for the retrieval-statistics list and the comparison measurements *(proposed)* |
| Embedding chart | A charting library that can draw a few thousand points in a 2D scatter — Apache ECharts *(proposed, OPEN-2)* |
| Showing the document | The Community Voices Document rendered from markdown *(proposed)* |
| Styling | Tailwind CSS *(proposed)* |
| API client | Typed client generated from the backend's API description *(proposed, OPEN-1)* |
| Tests | Vitest + React Testing Library, with a stand-in backend (MSW) so tests run offline (`CLAUDE.md` §7) *(proposed)* |
| Lint and format | ESLint + Prettier, one of each (`CLAUDE.md` §8) *(proposed)* |
| Running it | Its own service in Docker Compose *(proposed)* |

## Screens the brief implies *(proposed)*

```mermaid
flowchart LR
    DOC["Community Voices Document<br/>past week + next week's prediction"]
    AB["Comparison<br/>without vs with retrieval, side by side, with measurements"]
    MAP["Embedding map<br/>2D scatter, colored by topic"]
    STATS["Retrieval statistics<br/>most-retrieved passages"]
    DOC --> AB
    classDef open stroke-dasharray: 5 5
    class DOC,AB,MAP,STATS open
```

These four come from the brief's requirements (`README.md` → *Primary objective*),
not from Brian; the layout and navigation between them haven't been discussed.

## Open in this draft

- `?` How the frontend gets typed access to the backend — OPEN-1.
- `?` Which charting library draws the embedding map — OPEN-2.
- `?` Everything marked *proposed* above.
