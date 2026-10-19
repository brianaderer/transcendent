import type { EngagementDay } from "../api/generated";
import { engagementSeries } from "./engagement";

const HISTORY = ["2026-10-12", "2026-10-13", "2026-10-14"];

function day(on: string, posts: number): EngagementDay {
  return { day: on, posts, comments: posts * 2, upvotes: posts * 3, people: posts };
}

test("every day of the history gets a value, zero on the quiet days", () => {
  const series = engagementSeries(HISTORY, [day("2026-10-13", 2)]);

  expect(series.days).toEqual(HISTORY);
  expect(series.posts).toEqual([0, 2, 0]);
  expect(series.comments).toEqual([0, 4, 0]);
  expect(series.upvotes).toEqual([0, 6, 0]);
  expect(series.people).toEqual([0, 2, 0]);
});

test("days outside the history are left off", () => {
  const series = engagementSeries(HISTORY, [day("2026-10-11", 5), day("2026-10-14", 1)]);

  expect(series.posts).toEqual([0, 0, 1]);
});

test("a topic with no engagement is a flat line along the history", () => {
  expect(engagementSeries(HISTORY, []).people).toEqual([0, 0, 0]);
});
