/**
 * Folds a run's live events into what the progress panel shows (atlas plate 41): for each
 * version, its steps, tool calls and their results as they happen, and the run's state.
 */
import type { LiveEvent } from "../useLiveEvents";

export type Version = "A" | "B";
export type Lane = { lines: string[]; done: boolean };
export type Progress = {
  lanes: Record<Version, Lane>;
  measuring: boolean;
  finished: boolean;
  failed: string | null;
};

export const STARTING: Progress = {
  lanes: { A: { lines: [], done: false }, B: { lines: [], done: false } },
  measuring: false,
  finished: false,
  failed: null,
};

const PHASE_NAMES: Record<string, string> = {
  write: "Writing the report",
  predict: "Predicting the range",
};

export function folded(progress: Progress, event: LiveEvent): Progress {
  switch (event.type) {
    case "run.finished":
      return { ...progress, measuring: false, finished: true };
    case "run.failed":
      return { ...progress, failed: String(event.reason ?? "the run failed") };
    case "measurement.done":
      return { ...progress, measuring: true };
    default:
      return withLine(progress, event);
  }
}

function withLine(progress: Progress, event: LiveEvent): Progress {
  const version = event.version as Version | undefined;
  const line = lineFor(event);
  if (!version || !line) return progress;
  const lane = progress.lanes[version];
  const done = lane.done || (event.type === "step.finished" && event.phase === "predict");
  return {
    ...progress,
    lanes: { ...progress.lanes, [version]: { lines: [...lane.lines, line], done } },
  };
}

/** One line of a lane, e.g. "search(“winterizing”) → 15 posts". */
export function lineFor(event: LiveEvent): string | null {
  const phase = PHASE_NAMES[String(event.phase)] ?? String(event.phase);
  switch (event.type) {
    case "step.started":
      return `${phase}…`;
    case "step.finished":
      return `${phase}: done (${event.seconds}s)`;
    case "tool.called":
      return `${event.tool}(${argumentsOf(event.arguments)})`;
    case "tool.returned":
      return `  → ${event.posts} posts`;
    default:
      return null;
  }
}

function argumentsOf(value: unknown): string {
  const values = Object.values((value as Record<string, unknown>) ?? {});
  return values.map((v) => `“${String(v)}”`).join(", ");
}
