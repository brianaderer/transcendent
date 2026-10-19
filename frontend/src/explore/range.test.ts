import { addDays, describeRange, lastDays, rangeFrom, shortRange } from "./range";

const HISTORY = Array.from({ length: 56 }, (_, n) => addDays("2026-08-24", n)); // to 18 Oct

test("the page opens on the last seven days of the history", () => {
  expect(rangeFrom({}, HISTORY)).toEqual({ start: "2026-10-12", end: "2026-10-18" });
});

test("a range in the address is kept when it fits the history", () => {
  const asked = { start: "2026-09-01", end: "2026-09-03" };

  expect(rangeFrom(asked, HISTORY)).toEqual(asked);
});

test("a range outside the history, or backwards, falls back to the last seven days", () => {
  const lastWeek = { start: "2026-10-12", end: "2026-10-18" };

  expect(rangeFrom({ start: "2026-08-01", end: "2026-08-30" }, HISTORY)).toEqual(lastWeek);
  expect(rangeFrom({ start: "2026-09-03", end: "2026-09-01" }, HISTORY)).toEqual(lastWeek);
  expect(rangeFrom({ start: "2026-09-03" }, HISTORY)).toEqual(lastWeek);
});

test("the all-weeks preset covers the whole history", () => {
  expect(lastDays(HISTORY, Number.POSITIVE_INFINITY)).toEqual({
    start: "2026-08-24",
    end: "2026-10-18",
  });
});

test("a short history gives as many days as it has", () => {
  expect(lastDays(HISTORY.slice(0, 3), 7)).toEqual({ start: "2026-08-24", end: "2026-08-26" });
});

test("a range is described in words with its posts", () => {
  const range = { start: "2026-10-12", end: "2026-10-18" };

  expect(describeRange(range, 1097)).toBe("12 Oct – 18 Oct 2026 · 1,097 posts");
});

test("the button names the range briefly, across a month too", () => {
  expect(shortRange({ start: "2026-10-12", end: "2026-10-18" })).toBe("12–18 Oct");
  expect(shortRange({ start: "2026-09-28", end: "2026-10-04" })).toBe("28 Sept – 4 Oct");
});
