import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import type { TopicDetail, TopicInRange } from "../api/generated";
import { addDays } from "../explore/range";
import { openApp, SilentEventSource } from "../test/openApp";
import { standInBackend } from "../test/standInBackend";
import type { EngagementPicture } from "./chart";
import { describeDecision } from "./TopicPage";

const shown: EngagementPicture[] = [];
vi.mock("./chart", () => ({
  createEngagementChart: () => ({
    show: (picture: EngagementPicture) => shown.push(picture),
    resize() {},
    dispose() {},
  }),
}));

const DAYS = Array.from({ length: 56 }, (_, n) => ({ day: addDays("2026-08-24", n), posts: 10 }));

const TOPIC: TopicDetail = {
  id: 7,
  label: "Impellers",
  description: "Raw-water pump failures.",
  keywords: ["impeller", "pump"],
  first_seen: "2026-08-25",
  last_seen: "2026-10-18",
  daily: [{ day: "2026-10-13", posts: 2, comments: 5, upvotes: 1, people: 4 }],
  typical_posts: [
    {
      post_id: "abc",
      thread_id: "abc",
      kind: "post",
      author: "saltyketch",
      day: "2026-10-08",
      title: "Third impeller this season",
      excerpt: "Carrying two spares now.",
    },
  ],
  decisions: [
    { day: "2026-08-25", decision: "mint", threads: 9, reason: "A new conversation." },
    { day: "2026-08-27", decision: "attach", threads: 0, reason: "Same subject." },
  ],
};

let topicsInRange: TopicInRange[] = [];

standInBackend(
  http.get("*/api/days", () => HttpResponse.json({ days: DAYS, latest_day: "2026-10-18" })),
  http.get("*/api/topics/7", () => HttpResponse.json(TOPIC)),
  http.get("*/api/topics/8", () =>
    HttpResponse.json({ detail: "no topic with id 8" }, { status: 404 }),
  ),
  http.get("*/api/topics", () => HttpResponse.json(topicsInRange)),
  http.get("*/api/health", () => HttpResponse.json({ status: "ok", checks: {} })),
  http.get("*/api/ingestion", () =>
    HttpResponse.json({ days_done: 56, days_wanted: 56, posts: 560, latest_day: "2026-10-18" }),
  ),
);

beforeEach(() => {
  vi.stubGlobal("EventSource", SilentEventSource);
  shown.length = 0;
  topicsInRange = [];
});
afterEach(() => vi.unstubAllGlobals());

test("shows the topic's name, description, keywords and the days it was seen", async () => {
  openApp("/topics/7");

  expect(await screen.findByRole("heading", { name: "Impellers" })).toBeInTheDocument();
  expect(screen.getByText("Raw-water pump failures.")).toBeInTheDocument();
  const keywords = screen.getByRole("list", { name: "Keywords" });
  expect(
    within(keywords)
      .getAllByRole("listitem")
      .map((k) => k.textContent),
  ).toEqual(["impeller", "pump"]);
  expect(screen.getByText("First seen 25 Aug · last seen 18 Oct")).toBeInTheDocument();
});

test("the chart spans the whole history and shades the range in the address", async () => {
  openApp("/topics/7?start=2026-10-01&end=2026-10-07");

  await vi.waitFor(() => expect(shown.at(-1)).toBeDefined());
  const { series, range } = shown.at(-1)!;
  expect(series.days).toHaveLength(56);
  expect(series.people[series.days.indexOf("2026-10-13")]).toBe(4);
  expect(range).toEqual({ start: "2026-10-01", end: "2026-10-07" });
});

test("with no range in the address, the last seven days are shaded, as on Explore", async () => {
  openApp("/topics/7");

  await vi.waitFor(() => expect(shown.at(-1)).toBeDefined());
  expect(shown.at(-1)!.range).toEqual({ start: "2026-10-12", end: "2026-10-18" });
});

test("the badge is the topic's badge on Explore for the same range", async () => {
  topicsInRange = [
    {
      id: 7,
      label: "Impellers",
      description: "d",
      first_seen: "2026-08-25",
      engagement: 9,
      posts: 4,
      daily: [],
      daily_before: [],
      direction: "rising",
    },
  ];

  openApp("/topics/7");

  expect(await screen.findByText("Rising")).toBeInTheDocument();
});

test("a topic with nothing in the range says it was quiet", async () => {
  openApp("/topics/7");

  expect(await screen.findByText("Quiet in these days")).toBeInTheDocument();
});

test("typical posts show their author, date and excerpt, and open on Reddit", async () => {
  openApp("/topics/7");

  const posts = await screen.findByRole("region", { name: "Typical posts" });
  expect(within(posts).getByText("u/saltyketch · 8 Oct")).toBeInTheDocument();
  expect(within(posts).getByText("Carrying two spares now.")).toBeInTheDocument();
  expect(within(posts).getByRole("link", { name: "Open on Reddit" })).toHaveAttribute(
    "href",
    "https://www.reddit.com/r/sailing/comments/abc/",
  );
});

test("the timeline lists the tagging decisions oldest first, with their reasons", async () => {
  openApp("/topics/7");

  const timeline = await screen.findByRole("region", { name: "How this topic was built" });
  const steps = within(timeline)
    .getAllByRole("listitem")
    .map((step) => step.textContent);
  expect(steps).toEqual([
    "25 Aug · minted · 9 threads — A new conversation.",
    "27 Aug · attached — Same subject.",
  ]);
});

test("the back link returns to Explore with the same range", async () => {
  openApp("/topics/7?start=2026-10-01&end=2026-10-07");

  expect(await screen.findByRole("link", { name: "← Back to Explore" })).toHaveAttribute(
    "href",
    "/?start=2026-10-01&end=2026-10-07",
  );
});

test("a topic that doesn't exist says so", async () => {
  openApp("/topics/8");

  expect(await screen.findByText("There is no such topic.")).toBeInTheDocument();
});

test("one thread is a thread, not threads", () => {
  expect(describeDecision({ decision: "attach", threads: 1 })).toBe("attached · 1 thread");
});

test("the top bar's Retrieval stats link keeps the range", async () => {
  openApp("/topics/7?start=2026-10-01&end=2026-10-07");

  expect(await screen.findByRole("link", { name: "Retrieval stats" })).toHaveAttribute(
    "href",
    "/retrievals?start=2026-10-01&end=2026-10-07",
  );
});
