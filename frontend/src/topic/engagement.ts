/** A topic's daily engagement laid over the whole history, for its chart (atlas plate 31). */

import type { EngagementDay } from "../api/generated";

export type EngagementSeries = {
  days: string[];
  posts: number[];
  comments: number[];
  upvotes: number[];
  people: number[];
};

const QUIET_DAY = { posts: 0, comments: 0, upvotes: 0, people: 0 };

/** One value a day for every day of the history, zero on the days the topic was quiet. */
export function engagementSeries(history: string[], daily: EngagementDay[]): EngagementSeries {
  const byDay = new Map(daily.map((day) => [day.day, day]));
  const each = history.map((day) => byDay.get(day) ?? QUIET_DAY);
  return {
    days: history,
    posts: each.map((day) => day.posts),
    comments: each.map((day) => day.comments),
    upvotes: each.map((day) => day.upvotes),
    people: each.map((day) => day.people),
  };
}
