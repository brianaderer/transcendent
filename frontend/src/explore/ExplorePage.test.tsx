import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryHistory, RouterProvider } from "@tanstack/react-router";
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import type { Map as PostMap, TopicInRange } from "../api/generated";
import { buildRouter } from "../router";
import { standInBackend } from "../test/standInBackend";
import type { Dot } from "./chart";
import { addDays } from "./range";
import { useUiState } from "./uiState";

const shown: Dot[][] = [];
vi.mock("./chart", () => ({
  createScatter: () => ({ show: (dots: Dot[]) => shown.push(dots), resize() {}, dispose() {} }),
}));

const DAYS = Array.from({ length: 56 }, (_, n) => ({ day: addDays("2026-08-24", n), posts: 10 }));
let latestDay: string | null = "2026-10-18";
let daysServed = DAYS;
const asked: string[] = [];
const NAVIGATION_SETTLES_MS = 50; // long enough for a navigation, had one been made

function topic(id: number, label: string, direction: TopicInRange["direction"]): TopicInRange {
  return {
    id,
    label,
    description: "d",
    first_seen: "2026-09-01",
    engagement: 9,
    posts: 4,
    daily: [1, 2],
    direction,
  };
}

const MAP: PostMap = {
  points: ["p1", "p2"].map((id, n) => ({
    id,
    thread_id: "t1",
    kind: "post",
    author: "salty",
    day: "2026-10-12",
    thread_title: "Impellers <b>",
    excerpt: "Why?",
    thread_topic_id: n === 0 ? 1 : null,
    x: n,
    y: 0,
  })),
};

standInBackend(
  http.get("*/api/days", () => HttpResponse.json({ days: daysServed, latest_day: latestDay })),
  http.get("*/api/topics", ({ request }) => {
    asked.push(new URL(request.url).search);
    return HttpResponse.json([topic(1, "Impellers", "rising"), topic(2, "Anchoring", "new")]);
  }),
  http.get("*/api/map", () => HttpResponse.json(MAP)),
  http.get("*/api/health", () => HttpResponse.json({ status: "ok", checks: {} })),
  http.get("*/api/ingestion", () =>
    HttpResponse.json({ days_done: 56, days_wanted: 56, posts: 560, latest_day: "2026-10-18" }),
  ),
);

class FakeEventSource {
  static opened: FakeEventSource[] = [];
  onmessage: ((event: MessageEvent) => void) | null = null;
  constructor(public url: string) {
    FakeEventSource.opened.push(this);
  }
  close() {}
}

function announce(event: object) {
  const data = JSON.stringify(event);
  for (const source of FakeEventSource.opened)
    source.onmessage?.(new MessageEvent("message", { data }));
}

beforeEach(() => {
  vi.stubGlobal("EventSource", FakeEventSource);
  FakeEventSource.opened = [];
  useUiState.setState({ highlightedTopic: null });
  latestDay = "2026-10-18";
  daysServed = DAYS;
  asked.length = 0;
  shown.length = 0;
});
afterEach(() => vi.unstubAllGlobals());

function openExplore(address = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = buildRouter(createMemoryHistory({ initialEntries: [address] }));
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

test("opens on the last seven days, said in words, with the range's topics and badges", async () => {
  openExplore();

  expect(await screen.findByText("12 Oct – 18 Oct 2026 · 70 posts")).toBeInTheDocument();
  const topics = await screen.findByRole("list", { name: "Topics" });
  expect(within(topics).getByText("Impellers")).toBeInTheDocument();
  expect(within(topics).getByText("Rising")).toBeInTheDocument();
  expect(within(topics).getByText("New")).toBeInTheDocument();
  expect(asked).toContain("?start=2026-10-12&end=2026-10-18");
});

test("a range in the address is the range shown", async () => {
  openExplore("/?start=2026-09-01&end=2026-09-02");

  expect(await screen.findByText("1 Sept – 2 Sept 2026 · 20 posts")).toBeInTheDocument();
});

test("a preset changes the range in the address and asks for its topics", async () => {
  const router = openExplore();
  await screen.findByText(/12 Oct – 18 Oct/);

  fireEvent.click(screen.getByRole("button", { name: "Last 14 days" }));

  expect(await screen.findByText("5 Oct – 18 Oct 2026 · 140 posts")).toBeInTheDocument();
  expect(router.state.location.search).toEqual({ start: "2026-10-05", end: "2026-10-18" });
  expect(asked).toContain("?start=2026-10-05&end=2026-10-18");
});

test("moving a handle changes the range only when it is let go", async () => {
  const router = openExplore();
  await screen.findByText(/12 Oct – 18 Oct/);
  const firstDay = screen.getByRole("slider", { name: "First day" });

  fireEvent.change(firstDay, { target: { value: "50" } });
  await new Promise((resolve) => setTimeout(resolve, NAVIGATION_SETTLES_MS));
  expect(router.state.location.search).toEqual({});
  fireEvent.keyUp(firstDay);

  expect(await screen.findByText("13 Oct – 18 Oct 2026 · 60 posts")).toBeInTheDocument();
  expect(router.state.location.search).toEqual({ start: "2026-10-13", end: "2026-10-18" });
});

test("every post is a dot coloured by its topic, with its hover card escaped", async () => {
  openExplore();

  await screen.findByRole("list", { name: "Topics" });
  await vi.waitFor(() => expect(shown.at(-1)).toHaveLength(2));
  const [tagged, waiting] = shown.at(-1)!;
  expect(tagged.colour).not.toBe(waiting.colour);
  expect(tagged.card).toContain("Impellers &lt;b&gt;");
  expect(tagged.link).toBe("https://www.reddit.com/r/sailing/comments/t1/");
});

test("hovering a topic fades every other topic's dots", async () => {
  openExplore();
  const topics = await screen.findByRole("list", { name: "Topics" });
  await vi.waitFor(() => expect(shown.at(-1)).toHaveLength(2));

  act(() => {
    fireEvent.mouseEnter(within(topics).getByText("Impellers").closest("li")!);
  });

  await vi.waitFor(() => expect(shown.at(-1)!.map((dot) => dot.faded)).toEqual([false, true]));
  expect(useUiState.getState().highlightedTopic).toBe(1);
});

test("before any day has loaded, the page says the first start fills them in", async () => {
  latestDay = null;

  openExplore();

  expect(await screen.findByText(/No days are loaded yet/)).toBeInTheDocument();
});

test("days past the latest fully loaded one are left off the history", async () => {
  daysServed = [...DAYS, { day: "2026-10-19", posts: 999 }];

  openExplore();

  expect(await screen.findByText("12 Oct – 18 Oct 2026 · 70 posts")).toBeInTheDocument();
});

test("when a day finishes loading, the page takes it in without a reload", async () => {
  latestDay = "2026-10-17";
  openExplore();
  await screen.findByText(/11 Oct – 17 Oct/);

  latestDay = "2026-10-18";
  act(() => announce({ type: "day.finished", day: "2026-10-18" }));

  expect(await screen.findByText(/12 Oct – 18 Oct/)).toBeInTheDocument();
});

test("the Generate report button names the range and waits for the next build step", async () => {
  openExplore();

  const button = await screen.findByRole("button", { name: "Generate report for 12–18 Oct" });
  expect(button).toBeDisabled();
});
