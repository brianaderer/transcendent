# frontend

**Source:** `frontend/`   ·   **Tests:** `frontend/src/*.test.ts` and `*.test.tsx`

## Purpose
The web app. For now it shows whether the backend is running and how far the r/sailing
history has loaded; the Explore page arrives in
build step 4 ([atlas plates 30](../atlas/30-frontend.md) and [31](../atlas/30-frontend/31-screens.md)).

## Public interface
- `BackendStatus` — shows "Checking the backend…" until the first answer, then "Backend
  running", or "Not answering:" with each service that isn't, or "Backend unreachable"
  when the API itself doesn't answer (for example while it is still starting). It
  rechecks every five seconds.
- `fetchHealth()` and `describeHealth(health)` (the sentence shown) in `src/health.ts`.
- `IngestionStatus` — how far the history has loaded ("Loading r/sailing history: 23 of
  56 days · 9,412 posts", then "History up to date through 17 Oct"; "Waiting to start
  loading r/sailing history" before the first day begins; when a day failed, "Loading
  stopped at 26 Aug" followed by the reason the API gives as `failed_reason`, with the
  error's name taken off — for example "Loading stopped at 26 Aug: OPENROUTER_API_KEY is
  not set in .env (README step 3); tagging needs it. It will try again at the next
  catch-up"), fetched again whenever a live `ingestion` event arrives. `describeIngestion(status)` in `src/ingestion.ts` writes
  the sentence.
- `useLiveEvents(stream, onEvent)` — listens to a server-sent event stream ([events](events.md)).

## How it works
React with TanStack Query, built by Vite and served by `vite preview` on port 5173 inside its container (published on
your computer as `PORT`, see [environment](environment.md)), which
passes `/api` through to the API container. The backend answers 503 with the same body
when something is down, so the status reads the body either way.

## Uses
[api](api.md) (`GET /api/health`, `GET /api/ingestion`), [events](events.md)
(`GET /api/streams/ingestion/events`).

## Used by
The reviewer's browser.

## Configuration and data
`API_URL` (default `http://api:8000`) — where `/api` is passed to. Tests: `npm test`
(Vitest, offline, `fetch` and `EventSource` replaced with stand-ins). Lint: `npm run lint` (ESLint +
Prettier).
