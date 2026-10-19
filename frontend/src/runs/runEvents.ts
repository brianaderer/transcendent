/**
 * Folds a run's live events into what the progress panel shows (atlas plate 41): for each
 * version, its steps, tool calls and their results as they happen, and the run's state.
 */
import type { RunState } from "../api/generated";
import type { LiveEvent } from "../useLiveEvents";
import type { Version } from "./versions";

export type Stage = "waiting" | "write" | "predict" | "done";
export type Lane = { lines: string[]; stage: Stage; toolCallsThisStage: number };
export type Progress = {
  lanes: Record<Version, Lane>;
  measuring: boolean;
  failed: string | null;
};

const NEW_LANE: Lane = { lines: [], stage: "waiting", toolCallsThisStage: 0 };

export const STARTING: Progress = {
  lanes: { A: { ...NEW_LANE }, B: { ...NEW_LANE } },
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
      return withEventInItsLane(progress, event);
  }
}

/** Why the run stopped, or null while it hasn't: the live event's reason if one came, else the
 * reason kept with the run's state (the event may have been missed). */
export function whyTheRunStopped(progress: Progress, runState?: RunState): string | null {
  if (progress.failed) return progress.failed;
  if (runState?.state !== "failed") return null;
  return runState.reason ?? UNEXPLAINED_FAILURE;
}

function withEventInItsLane(progress: Progress, event: LiveEvent): Progress {
  const version = event.version as Version | undefined;
  const line = lineFor(event);
  if (!version || !line) return progress;
  const lane = progress.lanes[version];
  const stage = stageAfter(lane.stage, event);
  const moved: Lane = {
    lines: [...lane.lines, line],
    stage,
    toolCallsThisStage: toolCallsIn(stage, lane, event),
  };
  return { ...progress, lanes: { ...progress.lanes, [version]: moved } };
}

function stageAfter(stage: Stage, event: LiveEvent): Stage {
  if (stage === "done" || isPredictionFinished(event)) return "done";
  if (event.type === "step.started" && isWorkingStage(event.phase)) return event.phase;
  return stage;
}

function toolCallsIn(stage: Stage, lane: Lane, event: LiveEvent): number {
  const before = stage === lane.stage ? lane.toolCallsThisStage : 0;
  return before + (event.type === "tool.called" ? 1 : 0);
}

function isPredictionFinished(event: LiveEvent): boolean {
  return event.type === "step.finished" && event.phase === "predict";
}

function isWorkingStage(phase: unknown): phase is "write" | "predict" {
  return phase === "write" || phase === "predict";
}

/** Where a lane's bar stands: each phase's share of the bar fills with its tool calls, up to the
 * writer's cap (backend report/writer.py MAX_TOOL_CALLS), so a busy phase visibly moves. */
export function laneProgress(lane: Lane): { percent: number; label: string } {
  if (lane.stage === "done") return { percent: 100, label: "Done" };
  if (lane.stage === "waiting") return { percent: 0, label: "Waiting to start" };
  const within = Math.min(lane.toolCallsThisStage, TOOL_CALL_CAP) / TOOL_CALL_CAP;
  const percent = Math.round(PHASE_START[lane.stage] + within * PHASE_SHARE);
  const calls = `${lane.toolCallsThisStage} tool call${lane.toolCallsThisStage === 1 ? "" : "s"}`;
  return { percent, label: `${PHASE_NAMES[lane.stage]} · ${calls}` };
}

const TOOL_CALL_CAP = 20; // the writer's MAX_TOOL_CALLS
const PHASE_SHARE = 40; // percent of the bar each phase fills
const PHASE_START: Record<"write" | "predict", number> = { write: 10, predict: 55 };

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
