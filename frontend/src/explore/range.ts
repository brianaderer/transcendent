/** Date ranges on the Explore page (atlas plate 31): whole days, written as ISO dates. */

import { HISTORY_WEEKS } from "../community";

export type DayRange = { start: string; end: string };

export const DEFAULT_DAYS = 7; // the page opens on the last seven days (atlas OPEN-26)

export const PRESETS: { label: string; days: number }[] = [
  { label: `Last ${DEFAULT_DAYS} days`, days: DEFAULT_DAYS },
  { label: "Last 14 days", days: 14 },
  { label: `All ${HISTORY_WEEKS} weeks`, days: Number.POSITIVE_INFINITY },
];

const DAY_MS = 24 * 60 * 60 * 1000;

export function addDays(day: string, count: number): string {
  return new Date(Date.parse(`${day}T00:00:00Z`) + count * DAY_MS).toISOString().slice(0, 10);
}

/** The last `count` days of the history (or all of it), ending on its last day. */
export function lastDays(history: string[], count: number): DayRange {
  const end = history[history.length - 1];
  const first = history[0];
  const start = addDays(end, 1 - Math.min(count, history.length));
  return { start: start < first ? first : start, end };
}

/** The range in the address if it fits inside the history, otherwise the last seven days. */
export function rangeFrom(asked: Partial<DayRange>, history: string[]): DayRange {
  const first = history[0];
  const last = history[history.length - 1];
  const { start, end } = asked;
  if (start && end && first <= start && start <= end && end <= last) return { start, end };
  return lastDays(history, DEFAULT_DAYS);
}

/** "12 Oct – 18 Oct 2026 · 1,097 posts" */
export function describeRange(range: DayRange, posts: number): string {
  return `${describeDays(range)} · ${posts.toLocaleString("en-US")} posts`;
}

/** "12 Oct – 18 Oct 2026" */
export function describeDays(range: DayRange): string {
  return `${dayAndMonth(range.start)} – ${dayAndMonth(range.end)} ${range.end.slice(0, 4)}`;
}

/** "12–18 Oct", or "28 Sept – 4 Oct" across a month: for the Generate report button. */
export function shortRange(range: DayRange): string {
  const [startDay, startMonth] = dayAndMonth(range.start).split(" ");
  const end = dayAndMonth(range.end);
  return startMonth === end.split(" ")[1]
    ? `${startDay}–${end}`
    : `${startDay} ${startMonth} – ${end}`;
}

function dayAndMonth(day: string): string {
  const date = new Date(`${day}T00:00:00Z`);
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
}
