import { folded, lineFor, STARTING } from "./runEvents";

test("each version's steps and tool calls become lines in its own lane", () => {
  const events = [
    { type: "step.started", version: "B", phase: "write" },
    {
      type: "tool.called",
      version: "B",
      phase: "write",
      tool: "search",
      arguments: { term: "winterizing" },
    },
    { type: "tool.returned", version: "B", phase: "write", tool: "search", posts: 15 },
    { type: "step.started", version: "A", phase: "write" },
  ];

  const progress = events.reduce(folded, STARTING);

  expect(progress.lanes.B.lines).toEqual([
    "Writing the report…",
    "search(“winterizing”)",
    "  → 15 posts",
  ]);
  expect(progress.lanes.A.lines).toEqual(["Writing the report…"]);
});

test("a version is done once its prediction is", () => {
  const progress = [{ type: "step.finished", version: "A", phase: "predict", seconds: 9 }].reduce(
    folded,
    STARTING,
  );

  expect(progress.lanes.A.done).toBe(true);
  expect(progress.lanes.B.done).toBe(false);
});

test("measuring until the run finishes; or failed with the reason", () => {
  const measured = folded(STARTING, { type: "measurement.done", name: "topics_found", A: 2, B: 8 });
  expect(measured.measuring).toBe(true);
  expect(folded(measured, { type: "run.finished" }).measuring).toBe(false);
  expect(folded(STARTING, { type: "run.failed", reason: "no key" }).failed).toBe("no key");
});

test("events with no line, such as usage, change nothing", () => {
  expect(lineFor({ type: "usage", version: "A", phase: "write" })).toBeNull();
  expect(folded(STARTING, { type: "usage", version: "A" })).toEqual(STARTING);
});
