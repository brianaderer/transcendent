import type { SyncAnswer } from "./api/generated";
import { shortDate } from "./ingestion";

/** What the Sync now button says it asked for (atlas plate 40). */
export function describeSync(answer: SyncAnswer): string {
  switch (answer.reason) {
    case "days_missing":
      return `Fetching ${describeDays(answer.missing_days)}…`;
    case "nothing_new":
      return `Nothing new: ${shortDate(answer.next_complete_day)} can be fetched after ${whenComplete(answer.next_complete_at)}`;
    case "already_running":
      return "A catch-up is already running";
  }
}

function describeDays(days: string[]): string {
  if (days.length === 1) return shortDate(days[0]);
  return `${days.length} days, ${shortDate(days[0])} to ${shortDate(days[days.length - 1])}`;
}

/** "06:00 UTC on 21 Oct": days become complete at a fixed hour of UTC, so it is named in UTC. */
function whenComplete(isoMoment: string): string {
  const [day, time] = isoMoment.split("T");
  return `${time.slice(0, 5)} UTC on ${shortDate(day)}`;
}
