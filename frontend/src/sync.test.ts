import type { SyncAnswer } from "./api/generated";
import { describeSync } from "./sync";

const LATER = { next_complete_day: "2026-10-20", next_complete_at: "2026-10-21T06:00:00Z" };

function answer(reason: SyncAnswer["reason"], missing_days: string[]): SyncAnswer {
  return { queued: reason === "days_missing", reason, missing_days, ...LATER };
}

test("names the one day a sync will fetch", () => {
  expect(describeSync(answer("days_missing", ["2026-10-19"]))).toBe("Fetching 19 Oct…");
});

test("names the first and last of several days a sync will fetch", () => {
  const days = ["2026-10-17", "2026-10-18", "2026-10-19"];

  expect(describeSync(answer("days_missing", days))).toBe("Fetching 3 days, 17 Oct to 19 Oct…");
});

test("says when the next day can be fetched when nothing new is complete", () => {
  expect(describeSync(answer("nothing_new", []))).toBe(
    "Nothing new: 20 Oct can be fetched after 06:00 UTC on 21 Oct",
  );
});

test("says a catch-up is already running", () => {
  expect(describeSync(answer("already_running", ["2026-10-19"]))).toBe(
    "A catch-up is already running",
  );
});
