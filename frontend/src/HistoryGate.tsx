import type { ReactNode } from "react";

import { type DayCount, useReportDays } from "./api/generated";
import type { DayRange } from "./explore/range";

/**
 * Reads the loaded history (`GET /api/days`) and shows its page only once at least one day
 * has loaded; until then it says why there is nothing to show. Every page that works on a
 * date range sits inside it.
 */
export function HistoryGate({ children }: { children: (history: DayCount[]) => ReactNode }) {
  const days = useReportDays();
  if (days.isPending) return <p>Loading the history…</p>;
  if (days.isError) return <p>The history couldn't be loaded.</p>;
  const history = loadedDays(days.data.days, days.data.latest_day);
  if (history.length === 0) return <p>No days are loaded yet; the first start fills them in.</p>;
  return <>{children(history)}</>;
}

/** Days past the latest fully loaded one are still filling in, so they are left off. */
export function loadedDays(days: DayCount[], latest: string | null): DayCount[] {
  return latest ? days.filter((day) => day.day <= latest) : [];
}

/** Posts and comments written in the range. */
export function postsIn(history: DayCount[], range: DayRange): number {
  return history
    .filter((day) => range.start <= day.day && day.day <= range.end)
    .reduce((sum, day) => sum + day.posts, 0);
}
