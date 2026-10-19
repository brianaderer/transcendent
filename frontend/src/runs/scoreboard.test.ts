import { FINISHED_RUN } from "./fixtures";
import { scoreboard } from "./scoreboard";

const [a, b] = FINISHED_RUN.result!.versions;

test("each measurement reads as A against B", () => {
  const rows = Object.fromEntries(scoreboard(a, b).map((row) => [row.measurement, [row.a, row.b]]));

  expect(rows["Main topics found"]).toEqual(["1 of 10", "8 of 10"]);
  expect(rows["Topics invented"]).toEqual(["1", "0"]);
  expect(rows["Order of importance"]).toEqual(["too few to rank", "close (0.83)"]);
  expect(rows["Prediction score"]).toEqual(["20%", "60%"]);
  expect(rows["Tokens and time"]).toEqual(["2.1k · 12s", "2.1k · 12s"]);
  expect(rows["Posts looked at"]).toEqual(["0", "2"]);
});
