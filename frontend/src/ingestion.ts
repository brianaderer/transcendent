import { SUBREDDIT } from "./community";

/** How far the first boot has got rebuilding the seed's vectors (atlas plate 07). */
export type BackfillProgress = {
  what: "posts" | "threads" | "topics";
  done: number;
  total: number;
};

export type IngestionStatus = {
  days_done: number;
  days_wanted: number;
  posts: number;
  latest_day: string | null;
  running_day: string | null;
  failed_day: string | null;
  failed_reason: string | null;
  backfill: BackfillProgress | null;
};

export async function fetchIngestionStatus(): Promise<IngestionStatus> {
  const response = await fetch("/api/ingestion");
  return (await response.json()) as IngestionStatus;
}

/**
 * One sentence on how far the history has loaded (atlas plates 04 and 07): first the seed's
 * preparation while its vectors are rebuilt, then the catch-up's days.
 */
export function describeIngestion(status: IngestionStatus): string {
  if (status.backfill) {
    const { what, done, total } = status.backfill;
    return `Preparing the history: ${count(done)} of ${count(total)} ${what}`;
  }
  if (status.failed_day) {
    const why = status.failed_reason ?? "the reason wasn't recorded";
    return `Loading stopped at ${shortDate(status.failed_day)}: ${why}`;
  }
  if (status.days_done >= status.days_wanted && status.latest_day) {
    return describeFullHistory(status, status.latest_day);
  }

  if (status.days_done === 0 && !status.running_day) {
    return `Waiting to start loading r/${SUBREDDIT} history`;
  }
  return `Loading r/${SUBREDDIT} history: ${status.days_done} of ${status.days_wanted} days · ${count(status.posts)} posts`;
}

/** The history counts as full while the daily run loads yesterday, so name that day. */
function describeFullHistory(status: IngestionStatus, latestDay: string): string {
  if (status.running_day) {
    return `Loading ${shortDate(status.running_day)} · history up to date through ${shortDate(latestDay)}`;
  }
  return `History up to date through ${shortDate(latestDay)} · ${count(status.posts)} posts`;
}

function shortDate(isoDay: string): string {
  const [year, month, day] = isoDay.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
}

function count(n: number): string {
  return n.toLocaleString("en-US");
}
