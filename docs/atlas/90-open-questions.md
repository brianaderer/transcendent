# 90 — Open Questions

[← Index](00-index.md)

| ID | Question | Raised on |
|---|---|---|
| OPEN-1 | How should the frontend know the exact shape of the data the backend sends? The recommendation is to have the backend publish a machine-readable description of every endpoint (an OpenAPI document, which Python frameworks like FastAPI produce for free) and generate a typed TypeScript client and TanStack Query hooks from it with a tool such as orval. Then a backend change that breaks the frontend shows up as a type error before anything runs. The alternative is writing the fetch calls and their types by hand, which is less setup but drifts out of step silently. This depends on the backend choice, which hasn't been discussed. | [30](30-frontend.md) |
| OPEN-2 | Which library should draw the embedding map? It has to plot a few thousand points on a flat chart, colored by topic, with a hover that shows the passage. The recommendation is Apache ECharts, because it draws on a canvas and stays fast at that size, and its scatter chart does hover and coloring out of the box. Recharts is simpler to use from React but slows down past a thousand or so points; Plotly handles the size but is a much larger download. | [30](30-frontend.md) |

## Resolved

| ID | Decision | Date |
|---|---|---|
