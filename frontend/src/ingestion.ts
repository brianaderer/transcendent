export type IngestionStatus = {
  days_done: number;
  days_wanted: number;
  posts: number;
  latest_day: string | null;
  running_day: string | null;
  failed_day: string | null;
  failed_reason: string | null;
};

export async function fetchIngestionStatus(): Promise<IngestionStatus> {
  const response = await fetch("/api/ingestion");
  return (await response.json()) as IngestionStatus;
}

/** One sentence on how far the history has loaded (atlas plate 04: first start shows progress). */
export function describeIngestion(status: IngestionStatus): string {
  if (status.failed_day) {
    const why = status.failed_reason ? `: ${withoutErrorName(status.failed_reason)}` : "";
    return `Loading stopped at ${shortDate(status.failed_day)}${why}. It will try again at the next catch-up`;
  }
  if (status.days_done >= status.days_wanted && status.latest_day) {
    return `History up to date through ${shortDate(status.latest_day)} · ${count(status.posts)} posts`;
  }
  if (status.days_done === 0 && !status.running_day) {
    return "Waiting to start loading r/sailing history";
  }
  return `Loading r/sailing history: ${status.days_done} of ${status.days_wanted} days · ${count(status.posts)} posts`;
}

function shortDate(isoDay: string): string {
  const [year, month, day] = isoDay.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
}

function count(n: number): string {
  return n.toLocaleString("en-US");
}

/** "MissingModelKey: OPENROUTER_API_KEY is not set…" reads better without the error's name. */
function withoutErrorName(reason: string): string {
  return reason.replace(/^[A-Za-z]+: /, "");
}
