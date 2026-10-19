import { describeStep, foldedStep, type DayStep } from "./daySteps";

const DAY = "2026-10-18";

function fold(...events: object[]): DayStep | null {
  return events.reduce<DayStep | null>(
    (step, event) => foldedStep(step, event as { type: string }),
    null,
  );
}

test("each step names what it is working through", () => {
  const said = (event: object) => describeStep(fold({ type: "day.step", day: DAY, ...event })!);

  expect(said({ step: "fetching" })).toBe("fetching posts");
  expect(said({ step: "embedding", posts: 204 })).toBe("embedding 204 posts");
  expect(said({ step: "grouping", threads: 12 })).toBe("grouping 12 threads");
  expect(said({ step: "tagging", groups: 7 })).toBe("tagging: 0 of 7 groups decided");
  expect(said({ step: "applying" })).toBe("saving");
});

test("tagging counts the decisions as they are made", () => {
  const step = fold(
    { type: "day.step", day: DAY, step: "tagging", groups: 7 },
    { type: "decision.made", group: "group-1" },
    { type: "decision.made", group: "group-2" },
    { type: "decision.made", group: "group-3" },
  );

  expect(describeStep(step!)).toBe("tagging: 3 of 7 groups decided");
});

test("a new step starts its own count", () => {
  const step = fold(
    { type: "day.step", day: DAY, step: "tagging", groups: 2 },
    { type: "decision.made" },
    { type: "day.step", day: DAY, step: "applying" },
    { type: "day.step", day: "2026-10-19", step: "tagging", groups: 4 },
  );

  expect(step).toEqual({ day: "2026-10-19", step: "tagging", count: 4, decided: 0 });
});

test("the step is forgotten once the day finishes or fails", () => {
  const started = { type: "day.step", day: DAY, step: "fetching" };

  expect(fold(started, { type: "day.finished", day: DAY })).toBeNull();
  expect(fold(started, { type: "day.failed", day: DAY })).toBeNull();
});

test("events about other things leave the step as it was", () => {
  const started = { type: "day.step", day: DAY, step: "grouping", threads: 5 };

  expect(fold(started, { type: "backfill.progress" })).toEqual(fold(started));
});
