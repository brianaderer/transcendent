# frontend

**Source:** `frontend/`   ·   **Tests:** `frontend/src/**/*.test.ts` and `*.test.tsx`

## Purpose
The web app the reviewer clicks through ([atlas plates 30](../atlas/30-frontend.md) and
[31](../atlas/30-frontend/31-screens.md)). The Explore page: one date range governs a dot
plot of the range's posts and a list of its topics, and starts a report for the range; the
Document and Comparison screens show a finished run ([report](report.md)); Topic detail shows
one topic's engagement across the history, its typical posts and how it was built; Retrieval
stats shows which posts the agents retrieved most. A top bar links the screens and shows
whether the backend is running and how far the r/sailing history has loaded. The range chosen
on Explore travels with every link between screens.

## Public interface
Screens and parts:
- **The router** (`src/router.tsx`, TanStack Router): `buildRouter(history?)` builds the
  routes inside a layout with the top bar: `/` (Explore), whose address holds the range
  (`?start=YYYY-MM-DD&end=YYYY-MM-DD`, `rangeInAddress`) and a started run (`&run=<id>`);
  `/topics/$topicId` (Topic detail) and `/retrievals` (Retrieval stats), which keep the range,
  `/retrievals` also `agent` (`report` or `tagging`) and `run` (`retrievals/search.ts`,
  `retrievalSearch`); `/runs/<id>/report` (`?version=A` for version A) and
  `/runs/<id>/comparison` ([report](report.md)). Anything that isn't text is dropped.
- `HistoryGate` — reads the loaded history (`GET /api/days`) and renders its page with it
  only once a day has loaded, saying "Loading the history…", "The history couldn't be
  loaded." or "No days are loaded yet; the first start fills them in." until then. Every
  page sits inside it. `loadedDays(days, latest)` drops days past the latest fully loaded
  one; `postsIn(history, range)` counts a range's posts and comments.
- `explore/ExplorePage` — reads the history through `HistoryGate`, takes the range from the address (`rangeFrom`: kept if it fits inside the history,
  otherwise the last seven days, atlas OPEN-26), and shows the range in words, the slider,
  the dot plot, the topics panel and a **Generate report for …** button, which starts a run
  (`POST /api/runs`), puts its id in the address and shows `RunProgress` below the plot. While a new range loads, the previous range's map and topics
  stay on screen. It listens to the live `ingestion` events (`useLiveEvents`) and, on each
  `day.finished`, refetches everything it shows (see *How it works*).
- `explore/RangeSlider` — two handles over the history with each day's posts as a bar behind
  them, and the presets **Last 7 days**, **Last 14 days**, **All 8 weeks** (the first and last
  labels are built from `DEFAULT_DAYS` and `HISTORY_WEEKS`). Each handle is a `RangeHandle`
  and the presets are `PresetButtons`, both inside the same file. A handle changes the range
  only when it is let go (pointer up or key up), so the map isn't recomputed mid-drag.
- `explore/DotPlot` — every post and comment in the range as a dot (`GET /api/map`), coloured
  by its thread's topic, "Recomputing map…" while a new map is fetched. Each new map is lined
  up with the one shown before (`alignTo`) so staying dots glide. Hovering shows a card
  (author, day, thread title, excerpt, topic), every part HTML-escaped (`escapeHtml`) because
  people wrote it; a dot whose topic isn't in the range's topics list reads "A smaller
  topic", and one whose thread has no topic yet reads "No topic yet"; clicking opens the post
  or comment on Reddit (`redditLink`). Hovering a topic in the panel fades every other
  topic's dots.
- `explore/TopicsPanel` — the range's topics busiest first (`GET /api/topics`): colour, label
  (the description on hover), a sparkline of the daily engagement (the period before the range
  drawn faint, so the line shows what the badge compares), posts and comments, and
  the badge **New**, **Rising**, **Steady** or **Fading**. Hovering a row, or moving the
  keyboard focus onto it, highlights that topic on the dot plot; the topic's name links to
  its Topic detail page with the range in the address. `BADGES` (the badge words) is shared
  with Topic detail.
- `topic/TopicPage` — one topic (`GET /api/topics/{id}`), with the range from the address
  (or the last seven days, as on Explore): a **← Back to Explore** link keeping the range;
  the name with its badge (taken from `GET /api/topics` for the same range, so it matches
  Explore; "Quiet in these days" when the topic had nothing in the range); description,
  keywords as chips, first and last day seen; the engagement chart; **Typical posts**, three
  cards (u/author · day, title, excerpt, **Open on Reddit**); and **How this topic was
  built**, the tagging decisions oldest first, written by `describeDecision` ("minted · 9
  threads", "attached · 1 thread", or just "attached" when its threads were all decided
  again later) with each reason. A topic that doesn't exist reads "There is no such topic."
- `topic/EngagementChart` — the topic's engagement on every loaded day
  (`engagementSeries`): posts, comments and upvotes as stacked areas and distinct people as
  a line, on one axis, with the range shaded.
- `retrievals/RetrievalsPage` — the Retrieval stats page (`GET /api/retrievals`): the
  range's slider (the same `RangeSlider` as Explore) and the range in words; the agent as
  two buttons, **Report agent** (the default, atlas plate 31) and **Tagging agent**, and a
  **Run** list ("All runs" and each run that retrieved the range's posts); then the bars and
  the table. When the chosen agent has retrieved none of the range's posts it says so; for
  the report agent it also explains that reports retrieve posts when one is generated, and
  offers **Show the tagging agent's retrievals**, which switches the filter.
- `retrievals/TopicBars` — retrievals per topic as labelled horizontal bars, the
  `TOPICS_CHARTED` (12) most retrieved, threads with no topic yet as `NO_TOPIC_YET`.
- `retrievals/RetrievalTable` — the most retrieved posts (TanStack Table): rank, post (its
  excerpt, linking to Reddit), author, topic (linking to Topic detail with the range), times
  retrieved, last retrieved (`whenRetrieved`, "19 Oct, 07:48" in UTC) and retrieved by. It
  opens sorted by rank; clicking a column heading sorts by it, clicking again reverses it,
  and the heading carries `aria-sort`.
- `TopBar` — the app's name, the **Explore** and **Retrieval stats** links (each keeping
  the range in the address, the current screen's in teal), `IngestionStatus`,
  `BackendStatus` and `ThemeToggle` (light or dark, starting from the system's choice).
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
- `runs/RunProgress` — below Explore's plot once a run is started: two lanes, "A · without
  our data" and "B · with retrieval", each listing its steps ("Writing the report…",
  "Predicting the range: done (41s)") and version B's tool calls with how many posts each
  returned, from the run's live events (`run-<id>`). While the run is going it also rereads
  the run's state (`GET /api/runs/{run_id}`) every three seconds, in case an event was
  missed; it shows "Measuring…" or the reason a run stopped, and when the run has finished
  it links to **Read the report** and **See the comparison**.
- `runs/ReportPage` — the Document screen, `/runs/<id>/report`: the masthead (the range,
  which version, the model, a link to the comparison), the document's Markdown, and beside
  it its topics with rank and direction, what it expected for the range, and its reasoning.
  Version B unless the address says `?version=A`.
- `runs/ComparisonPage` — the Comparison screen, `/runs/<id>/comparison`: the scoreboard; a
  table of the range's main topics with each one's measured direction and what A and B said
  of it (rank and direction), with the topics a version invented in red rows below; and both
  documents side by side, each linking to its own Document page.
- `runs/useFinishedRun(runId)` — a finished run's result, or the line to show instead
  (loading, still going, stopped with its reason, or gone: runs are kept for a day).

Logic, each in its own small module with its own tests:
- `explore/range.ts` — `DayRange`, `rangeFrom`, `lastDays`, `addDays`, `describeDays`
  ("12 Oct – 18 Oct 2026"), `describeRange` ("12 Oct – 18 Oct 2026 · 1,097 posts"), `shortRange` ("12–18 Oct",
  "28 Sept – 4 Oct") and `dayAndMonth` ("12 Oct"); `DEFAULT_DAYS = 7`, `PRESETS`.
- `topic/engagement.ts` — `engagementSeries(history, daily)`: one value a day for every
  loaded day, zero on the days the topic was quiet; days outside the history are left off.
- `topic/chart.ts` — `createEngagementChart(element)`: ECharts behind the same kind of small
  interface as the dot plot's (`show({series, range})`, `resize()`, `dispose()`).
  `SERIES_COLOURS` (posts `#0d9488`, comments `#d97706`, upvotes `#3b82f6`, people
  `#db2777`) passed the dataviz palette check (lightness, colour-blind separation and
  contrast) on both the light and the dark page.
- `runs/runEvents.ts` — `folded(progress, event)`: folds a run's live events into the
  progress panel's two lanes; `lineFor(event)` writes one line, such as
  `search(“winterizing”)` and then `→ 15 posts`.
- `runs/scoreboard.ts` — `scoreboard(a, b)`: each measurement as A against B in words (main
  topics found, topics invented, order of importance as close, partly or poor with its
  number, directions right, prediction score, tokens and time, posts looked at).
- `retrievals/search.ts` — `Agent`, `DEFAULT_AGENT = "report"`, `AGENT_NAMES`,
  `retrievalSearch`.
- `api/fetchOrThrow.ts` — `fetchOrThrow(url, options)`: every generated call goes through
  it (orval's mutator); an answer that isn't a success is thrown as an `ApiError` with its
  `status` and `detail`, so React Query reports it as an error rather than handing a page
  an error's body as data.
- `explore/align.ts` — `alignTo(previous, next)`: the turn (or turn after a flip), scale and
  shift that best carries the new map onto the old on the posts both share; with fewer than
  three shared posts the new map is left as it is.
- `explore/colours.ts` — `topicColours(ids)`: the twelve busiest topics get their own colour
  (`PALETTE`), the rest share `OTHER_TOPIC`; `NO_TOPIC` for posts whose thread waits for a
  decision.
- `explore/links.ts` — `redditLink(post)`. `explore/html.ts` — `escapeHtml(text)`.
- `community.ts` — `SUBREDDIT` and `HISTORY_WEEKS`, used by the links, the presets and the
  loading line.
- `explore/uiState.ts` — the browser-only state (Zustand): which topic is highlighted. The
  theme is not here; `ThemeToggle` keeps it itself and sets the `dark` class on `<html>`.
- `explore/chart.ts` — `createScatter(element, open)`: ECharts behind a small interface of
  our own (`show(dots)`, `resize()`, `dispose()`), so tests swap it for a stand-in.

## How it works
React with TanStack Query and TanStack Router, styled with Tailwind (dark mode by a class
on `<html>`), built by Vite and served by `vite preview` on port 5173 inside its container
(published on your computer as `PORT`, see [environment](environment.md)), which passes
`/api` through to the API container.

The Explore page also listens to the live `ingestion` events: each `day.finished` refetches
everything it shows, so during a first start the history widens and the topics fill in
without a reload.

The API calls and their types are **generated** from the backend's OpenAPI description
(atlas OPEN-1) by orval into `src/api/generated.ts` (React Query hooks such as
`useReportTopics`, named after the backend's route functions). The description is kept in
`frontend/openapi.json`. After changing a route or a response shape, refresh both with the
app running. This runs on your own computer, not in Docker, and needs Node 22 and
`npm ci` run once in `frontend/`:

```bash
curl -s http://localhost:5173/api/openapi.json | python3 -m json.tool > frontend/openapi.json
cd frontend && npm run api && npx prettier --write src/api/generated.ts
```

The description can also be written without the app running, from the API's stand-ins,
from `backend/`: `docker compose run --rm --no-deps -v $PWD/src:/srv/src -v
$PWD/tests:/srv/tests api python -c "import json; from tests.stand_ins import
stand_in_services; from voices.api.main import create_app;
print(json.dumps(create_app(stand_in_services()).openapi(), indent=2))" >
../frontend/openapi.json`.

The backend answers 503 with the same body when something is down, so the status reads the
body either way.

## Uses
[api](api.md) (`GET /api/health`, `GET /api/ingestion`, `GET /api/days`, `GET /api/topics`,
`GET /api/map`, `GET /api/topics/{topic_id}`, `GET /api/retrievals`, `POST /api/runs`,
`GET /api/runs/{run_id}`), [events](events.md) (`GET /api/streams/ingestion/events` and
`GET /api/streams/run-<id>/events`), [explore](explore.md), [topics](topics.md),
[retrievals](retrievals.md) and [report](report.md) (the shapes those routes return).

## Used by
The reviewer's browser.

## Configuration and data
`API_URL` (default `http://api:8000`) — where `/api` is passed to. Pinned libraries:
React 18.3.1, TanStack Query 5.62.8, Router 1.170.38 and Table 8.21.3 (the long-standing
version 8; version 9 came out in August 2026), Zustand 5.0.15, ECharts 6.1.0,
Tailwind 4.3.3, react-markdown 10.1.0 (renders the model's Markdown, never raw HTML); orval 8.34.0 and MSW 2.15.0 for development. Tests: `npm test` (Vitest,
offline: the Explore, Topic detail and Retrieval stats pages run against MSW, a stand-in
backend, in `src/test/standInBackend.ts`, with each chart swapped for a recorder and
`EventSource` for a stand-in (one that can announce a finished day on Explore,
`SilentEventSource` elsewhere); `src/test/openApp.tsx` opens the whole app at an address and
`src/test/renderInRouter.tsx` renders a part with links inside a router; the status parts
and `fetchOrThrow` replace `fetch` and `EventSource`; the Document and Comparison screens
read a fixed finished run, `FINISHED_RUN` in `src/runs/fixtures.ts`, from the same stand-in
backend).
Lint: `npm run lint` (ESLint + Prettier).
