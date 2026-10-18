import { describeIngestion, type IngestionStatus } from "./ingestion";

const base: IngestionStatus = {
  days_done: 0,
  days_wanted: 56,
  posts: 0,
  latest_day: null,
  running_day: null,
  failed_day: null,
  failed_reason: null,
};

test("says history is loading, with progress, while days remain", () => {
  const status = { ...base, days_done: 23, posts: 9412, running_day: "2026-09-15" };

  expect(describeIngestion(status)).toBe("Loading r/sailing history: 23 of 56 days · 9,412 posts");
});

test("says the history is up to date once every day is in", () => {
  const status = { ...base, days_done: 56, posts: 21480, latest_day: "2026-10-17" };

  expect(describeIngestion(status)).toBe("History up to date through 17 Oct · 21,480 posts");
});

test("says where loading stopped, and why, when a day failed", () => {
  const status = {
    ...base,
    days_done: 3,
    failed_day: "2026-08-26",
    failed_reason: "OPENROUTER_API_KEY is not set in .env (README step 3)",
  };

  expect(describeIngestion(status)).toBe(
    "Loading stopped at 26 Aug: OPENROUTER_API_KEY is not set in .env (README step 3). " +
      "It will try again at the next catch-up",
  );
});

test("says it is waiting before the first day starts", () => {
  expect(describeIngestion(base)).toBe("Waiting to start loading r/sailing history");
});
