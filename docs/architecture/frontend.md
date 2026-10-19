# frontend

**Source:** `frontend/`   ·   **Tests:** `frontend/src/**/*.test.ts` and `*.test.tsx`

## Purpose
The web app the reviewer clicks through ([atlas plates 30](../atlas/30-frontend.md) and
[31](../atlas/30-frontend/31-screens.md)). Today it is the Explore page (build step 4): one
date range governs a dot plot of the range's posts and a list of its topics. A top bar
shows whether the backend is running and how far the r/sailing history has loaded.

## Public interface
Screens and parts:
- **The router** (`src/router.tsx`, TanStack Router): `buildRouter(history?)` builds the one
  route, `/`, the Explore page, inside a layout with the top bar. The range lives in the
  address as `?start=YYYY-MM-DD&end=YYYY-MM-DD`; anything else in those fields is dropped.
- `explore/ExplorePage` — reads the history (`GET /api/days`, days up to the latest loaded
  one), takes the range from the address (`rangeFrom`: kept if it fits inside the history,
  otherwise the last seven days, atlas OPEN-26), and shows the range in words, the slider,
  the dot plot, the topics panel and a **Generate report for …** button that is drawn
  disabled until build step 5. While a new range loads, the previous range's map and topics
  stay on screen.
- `explore/RangeSlider` — two handles over the history with each day's posts as a bar behind
  them, and the presets **Last 7 days**, **Last 14 days**, **All 8 weeks**. A handle changes
  the range only when it is let go (pointer up or key up), so the map isn't recomputed
  mid-drag.
- `explore/DotPlot` — every post and comment in the range as a dot (`GET /api/map`), coloured
  by its thread's topic, "Recomputing map…" while a new map is fetched. Each new map is lined
  up with the one shown before (`alignTo`) so staying dots glide. Hovering shows a card
  (author, day, thread title, excerpt, topic), every part HTML-escaped because people wrote
  it; clicking opens the post or comment on Reddit (`redditLink`). Hovering a topic in the
  panel fades every other topic's dots.
- `explore/TopicsPanel` — the range's topics busiest first (`GET /api/topics`): colour, label
  (the description on hover), a sparkline of the daily engagement, posts and comments, and
  the badge **New**, **Rising**, **Steady** or **Fading**.
- `TopBar` — the app's name, the Explore link, `IngestionStatus`, `BackendStatus` and
  `ThemeToggle` (light or dark, starting from the system's choice).
- `BackendStatus` — "Checking the backend…" until the first answer, then "Backend running",
  or "Not answering:" with each service that isn't, or "Backend unreachable" when the API
  itself doesn't answer; rechecked every five seconds. `fetchHealth()` and
  `describeHealth(health)` in `src/health.ts`.
- `IngestionStatus` — how far the history has loaded ("Loading r/sailing history: 23 of 56
  days · 9,412 posts", then "History up to date through 17 Oct"; "Waiting to start loading
  r/sailing history" before the first day; "Loading stopped at 26 Aug: " and the reason when
  a day failed), fetched again whenever a live `ingestion` event arrives.
  `describeIngestion(status)` in `src/ingestion.ts` writes the sentence.
- `useLiveEvents(stream, onEvent)` — listens to a server-sent event stream ([events](events.md)).

Logic, each in its own small module with its own tests:
- `explore/range.ts` — `DayRange`, `rangeFrom`, `lastDays`, `addDays`, `daysIn`,
  `describeRange` ("12 Oct – 18 Oct 2026 · 1,097 posts") and `shortRange` ("12–18 Oct",
  "28 Sept – 4 Oct"); `DEFAULT_DAYS = 7`, `PRESETS`.
- `explore/align.ts` — `alignTo(previous, next)`: the turn (or turn after a flip), scale and
  shift that best carries the new map onto the old on the posts both share; with fewer than
  three shared posts the new map is left as it is.
- `explore/colours.ts` — `topicColours(ids)`: the twelve busiest topics get their own colour
  (`PALETTE`), the rest share `OTHER_TOPIC`; `NO_TOPIC` for posts whose thread waits for a
  decision.
- `explore/links.ts` — `redditLink(post)`, `escapeHtml(text)`.
- `explore/uiState.ts` — the browser-only state (Zustand): which topic is highlighted.
- `explore/chart.ts` — `createScatter(element, open)`: ECharts behind a small interface of
  our own (`show(dots)`, `resize()`, `dispose()`), so tests swap it for a stand-in.

## How it works
React with TanStack Query and TanStack Router, styled with Tailwind (dark mode by a class
on `<html>`), built by Vite and served by `vite preview` on port 5173 inside its container
(published on your computer as `PORT`, see [environment](environment.md)), which passes
`/api` through to the API container.

The API calls and their types are **generated** from the backend's OpenAPI description
(atlas OPEN-1) by orval into `src/api/generated.ts` (React Query hooks such as
`useReportTopics`, named after the backend's route functions). The description is kept in
`frontend/openapi.json`. After changing a route or a response shape, refresh both with the
app running:

```bash
curl -s http://localhost:5173/api/openapi.json | python3 -m json.tool > frontend/openapi.json
cd frontend && npm run api
```

The backend answers 503 with the same body when something is down, so the status reads the
body either way.

## Uses
[api](api.md) (`GET /api/health`, `GET /api/ingestion`, `GET /api/days`, `GET /api/topics`,
`GET /api/map`), [events](events.md) (`GET /api/streams/ingestion/events`), [explore](explore.md)
(the shapes those routes return).

## Used by
The reviewer's browser.

## Configuration and data
`API_URL` (default `http://api:8000`) — where `/api` is passed to. Pinned libraries:
React 18.3.1, TanStack Query 5.62.8 and Router 1.170.38, Zustand 5.0.15, ECharts 6.1.0,
Tailwind 4.3.3; orval 8.34.0 and MSW 2.15.0 for development. Tests: `npm test` (Vitest,
offline: the Explore page runs against MSW, a stand-in backend, in `src/test/standInBackend.ts`,
with the chart swapped for a recorder; the status parts replace `fetch` and `EventSource`).
Lint: `npm run lint` (ESLint + Prettier).
