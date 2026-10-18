import { describeHealth } from "./health";

test("describes a healthy backend", () => {
  expect(describeHealth({ status: "ok", checks: { database: true, queue: true } })).toBe(
    "Backend running",
  );
});

test("names every service that is down", () => {
  expect(describeHealth({ status: "degraded", checks: { database: false, queue: false } })).toBe(
    "Not answering: database, queue",
  );
});
