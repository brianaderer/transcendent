# 30 — Frontend (DRAFT)

[← Index](00-index.md) · [01 System Map](01-system-map.md) · [Open questions](90-open-questions.md)

The web app the reviewer clicks through. Brian specified React, TanStack Query,
TanStack Router and Zustand, and on 2026-10-18 agreed to the rest of the stack as
proposed. The screens below are still a proposal.

## Stack

| Concern | Choice |
|---|---|
| UI library | **React** — specified |
| Routing | **TanStack Router** — specified |
| Server state | **TanStack Query** — specified. Everything fetched from the backend lives here, including live events folded in from the SSE streams ([41](40-backend/41-live-events.md)) |
| Client state | **Zustand** — specified, used only for state that lives purely in the browser (for example which comparison panel is expanded). Anything a reviewer should be able to link to — the selected week, the selected run — lives in the address, through TanStack Router's search parameters |
| Language and build | TypeScript, built with Vite |
| Tables | TanStack Table, for the retrieval-statistics list and the comparison measurements |
| Embedding chart | Apache ECharts — draws a few thousand points in a 2D scatter on a canvas, with hover and coloring built in |
| Showing the document | The Community Voices Document rendered from markdown |
| Styling | Tailwind CSS |
| API client | Typed client generated from the backend's API description — the backend must publish an OpenAPI description (OPEN-1 resolved) |
| Tests | Vitest + React Testing Library, with a stand-in backend (MSW) so tests run offline (`CLAUDE.md` §7) |
| Lint and format | ESLint + Prettier, one of each (`CLAUDE.md` §8) |
| Running it | Its own service in Docker Compose |

## Screens the brief implies *(proposed)*

The full set of six screens, with a design brief for mockups, is on
[31 Screens](30-frontend/31-screens.md).

```mermaid
flowchart LR
    DOC["Community Voices Document<br/>past week + next week's prediction"]
    AB["Comparison<br/>without vs with retrieval, side by side, with measurements"]
    MAP["Embedding map<br/>2D scatter, colored by topic"]
    STATS["Retrieval statistics<br/>most-retrieved posts"]
    DOC --> AB
    classDef open stroke-dasharray: 5 5
    class DOC,AB,MAP,STATS open
```

These four come from the brief's requirements (`README.md` → *Primary objective*),
not from Brian; the layout and navigation between them haven't been discussed.

## Open in this draft

- `?` The screens' layout — mockups from the brief on [31](30-frontend/31-screens.md).
