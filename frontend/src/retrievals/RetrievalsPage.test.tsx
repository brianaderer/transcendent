import { fireEvent, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import type { RankedPost, RetrievalStats } from "../api/generated";
import { addDays } from "../explore/range";
import { openApp, SilentEventSource } from "../test/openApp";
import { standInBackend } from "../test/standInBackend";
import { TOPICS_CHARTED } from "./TopicBars";

const DAYS = Array.from({ length: 56 }, (_, n) => ({ day: addDays("2026-08-24", n), posts: 10 }));
const asked: URLSearchParams[] = [];

function post(rank: number, id: string, times: number, topic: string | null): RankedPost {
  return {
    rank,
    post_id: id,
    thread_id: "t1",
    kind: "comment",
    author: `sailor-${id}`,
    day: "2026-10-13",
    excerpt: `Excerpt ${id}`,
    topic_id: topic === null ? null : rank,
    topic_label: topic,
    times_retrieved: times,
    last_retrieved: "2026-10-19T07:48:44Z",
  };
}

const TAGGING: RetrievalStats = {
  agent: "tagging",
  runs: ["tagging-2026-10-18", "tagging-2026-10-17"],
  total: 15,
  posts: [post(1, "a", 8, "Impellers"), post(2, "b", 5, "Anchoring"), post(3, "c", 2, null)],
  topics: [
    { topic_id: 1, label: "Impellers", times_retrieved: 10 },
    { topic_id: null, label: null, times_retrieved: 5 },
  ],
};

function nothingFor(agent: RetrievalStats["agent"]): RetrievalStats {
  return { agent, runs: [], total: 0, posts: [], topics: [] };
}

let answer: (agent: string) => RetrievalStats = (agent) =>
  agent === "tagging" ? TAGGING : nothingFor("report");

standInBackend(
  http.get("*/api/days", () => HttpResponse.json({ days: DAYS, latest_day: "2026-10-18" })),
  http.get("*/api/retrievals", ({ request }) => {
    const search = new URL(request.url).searchParams;
    asked.push(search);
    return HttpResponse.json(answer(search.get("agent") ?? "report"));
  }),
  http.get("*/api/health", () => HttpResponse.json({ status: "ok", checks: {} })),
  http.get("*/api/ingestion", () =>
    HttpResponse.json({ days_done: 56, days_wanted: 56, posts: 560, latest_day: "2026-10-18" }),
  ),
);

beforeEach(() => {
  vi.stubGlobal("EventSource", SilentEventSource);
  asked.length = 0;
  answer = (agent) => (agent === "tagging" ? TAGGING : nothingFor("report"));
});
afterEach(() => vi.unstubAllGlobals());

function lastAsked(): Record<string, string> {
  return Object.fromEntries(asked.at(-1)!.entries());
}

function columnOf(name: string): string[] {
  const table = screen.getByRole("table", { name: "Most retrieved posts" });
  const headers = within(table)
    .getAllByRole("columnheader")
    .map((h) => h.textContent);
  const column = headers.findIndex((header) => header?.startsWith(name));
  return within(table)
    .getAllByRole("row")
    .slice(1)
    .map((row) => within(row).getAllByRole("cell")[column].textContent ?? "");
}

test("opens on the report agent's retrievals for the last seven days", async () => {
  openApp("/retrievals");

  await screen.findByText(/hasn't retrieved any/);
  expect(lastAsked()).toEqual({ start: "2026-10-12", end: "2026-10-18", agent: "report" });
  expect(screen.getByRole("button", { name: "Report agent" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
});

test("with no report retrievals, one click switches to the tagging agent's", async () => {
  const router = openApp("/retrievals");

  fireEvent.click(
    await screen.findByRole("button", { name: "Show the tagging agent's retrievals" }),
  );

  expect(await screen.findByRole("table", { name: "Most retrieved posts" })).toBeInTheDocument();
  expect(router.state.location.search).toMatchObject({ agent: "tagging" });
  expect(lastAsked().agent).toBe("tagging");
});

test("the range in the address is the range counted", async () => {
  openApp("/retrievals?start=2026-10-01&end=2026-10-07&agent=tagging");

  expect(await screen.findByText("1 Oct – 7 Oct 2026 · 70 posts")).toBeInTheDocument();
  expect(lastAsked()).toMatchObject({ start: "2026-10-01", end: "2026-10-07" });
});

test("the table lists the most retrieved posts by rank, with their topic and agent", async () => {
  openApp("/retrievals?agent=tagging");

  await screen.findByRole("table", { name: "Most retrieved posts" });
  expect(columnOf("Rank")).toEqual(["1", "2", "3"]);
  expect(columnOf("Topic")).toEqual(["Impellers", "Anchoring", "No topic yet"]);
  expect(columnOf("Retrieved by")).toEqual(["Tagging agent", "Tagging agent", "Tagging agent"]);
  expect(columnOf("Last retrieved")[0]).toBe("19 Oct, 07:48");
});

test("clicking a column heading sorts by it, and again reverses it", async () => {
  openApp("/retrievals?agent=tagging");
  await screen.findByRole("table", { name: "Most retrieved posts" });

  fireEvent.click(screen.getByRole("button", { name: "Topic" }));
  const firstSort = columnOf("Topic");
  fireEvent.click(screen.getByRole("button", { name: /^Topic/ }));

  expect(firstSort).toEqual([...firstSort].sort());
  expect(columnOf("Topic")).toEqual([...firstSort].reverse());
});

test("a topic in the table opens its detail page with the same range", async () => {
  openApp("/retrievals?agent=tagging&start=2026-10-01&end=2026-10-07");

  const link = await screen.findByRole("link", { name: "Impellers" });
  expect(link).toHaveAttribute("href", "/topics/1?start=2026-10-01&end=2026-10-07");
});

test("the bars show retrievals per topic, threads with no topic counted together", async () => {
  openApp("/retrievals?agent=tagging");

  const bars = await screen.findByRole("list", { name: "Retrievals per topic" });
  const rows = within(bars)
    .getAllByRole("listitem")
    .map((bar) => bar.textContent);
  expect(rows).toEqual(["Impellers10", "No topic yet5"]);
});

test("no more than twelve topics are drawn as bars", async () => {
  const many = Array.from({ length: 20 }, (_, n) => ({
    topic_id: n,
    label: `Topic ${n}`,
    times_retrieved: 20 - n,
  }));
  answer = () => ({ ...TAGGING, topics: many });

  openApp("/retrievals?agent=tagging");

  const bars = await screen.findByRole("list", { name: "Retrievals per topic" });
  expect(within(bars).getAllByRole("listitem")).toHaveLength(TOPICS_CHARTED);
});

test("choosing a run asks for that run's retrievals only", async () => {
  openApp("/retrievals?agent=tagging");
  await screen.findByRole("option", { name: "tagging-2026-10-17" });
  const runs = screen.getByRole("combobox", { name: "Run" });

  fireEvent.change(runs, { target: { value: "tagging-2026-10-17" } });

  await vi.waitFor(() => expect(lastAsked().run).toBe("tagging-2026-10-17"));
});

test("the tagging agent with nothing in the range says so, without offering to switch", async () => {
  answer = () => nothingFor("tagging");

  openApp("/retrievals?agent=tagging");

  expect(await screen.findByText(/tagging agent hasn't retrieved any/)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Show the tagging/ })).not.toBeInTheDocument();
});
