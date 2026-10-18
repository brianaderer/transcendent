# frontend

**Source:** `frontend/`   ·   **Tests:** `frontend/src/*.test.tsx`

## Purpose
The web app. For now it shows whether the backend is running; the Explore page arrives in
build step 4 ([atlas plates 30](../atlas/30-frontend.md) and [31](../atlas/30-frontend/31-screens.md)).

## Public interface
- `BackendStatus` — shows "Checking the backend…" until the first answer, then "Backend
  running", or "Not answering:" with each service that isn't, or "Backend unreachable"
  when the API itself doesn't answer (for example while it is still starting). It
  rechecks every five seconds.
- `fetchHealth()` and `describeHealth(health)` (the sentence shown) in `src/health.ts`.

## How it works
React with TanStack Query, built by Vite and served by `vite preview` on port 5173 inside its container (published on
your computer as `PORT`, see [environment](environment.md)), which
passes `/api` through to the API container. The backend answers 503 with the same body
when something is down, so the status reads the body either way.

## Uses
[api](api.md) (`GET /api/health`).

## Used by
The reviewer's browser.

## Configuration and data
`API_URL` (default `http://api:8000`) — where `/api` is passed to. Tests: `npm test`
(Vitest, offline, `fetch` replaced with a stand-in). Lint: `npm run lint` (ESLint +
Prettier).
