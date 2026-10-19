/**
 * Folds a run's live events into what the progress panel shows (atlas plate 41): for each
 * version, its steps, tool calls and their results as they happen, and the run's state.
 */
import type { RunState } from "../api/generated";
import type { LiveEvent } from "../useLiveEvents";
import type { Version } from "./versions";

export type Lane = { lines: string[]; done: boolean };
export type Progress = {
  lanes: Record<Version, Lane>;
  measuring: boolean;
  failed: string | null;
};

export const STARTING: Progress = {
  lanes: { A: { lines: [], done: false }, B: { lines: [], done: false } },
  measuring: false,
  failed: null,
};

/** The run's own stream; must match `stream_of` in backend/src/voices/report/runs.py. */
export function runStream(runId: string): string {
  return `run-${runId}`;
}

const UNEXPLAINED_FAILURE = "the run failed";

const PHASE_NAMES: Record<string, string> = {
  write: "Writing the report",
  predict: "Predicting the range",
};

export function folded(progress: Progress, event: LiveEvent): Progress {
  switch (event.type) {
    case "run.finished":
      return { ...progress, measuring: false };
    case "run.failed":
      return { ...progress, failed: String(event.reason ?? UNEXPLAINED_FAILURE) };
    case "measurement.done":
      return { ...progress, measuring: true };
    default:
      return withLine(progress, event);
  }
}

/** Why the run stopped, or null while it hasn't: the live event's reason if one came, else the
 * reason kept with the run's state (the event may have been missed). */
export function whyTheRunStopped(progress: Progress, runState?: RunState): string | null {
  if (progress.failed) return progress.failed;
  if (runState?.state !== "failed") return null;
  return runState.reason ?? UNEXPLAINED_FAILURE;
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
