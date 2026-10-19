import { type RunResult, useReportRun } from "../api/generated";

/** A finished run's result, or what to say instead while it isn't one. */
export function useFinishedRun(runId: string): { result: RunResult } | { notice: string } {
  const run = useReportRun(runId);
  if (run.isPending) return { notice: "Loading the run…" };
  // A run that is gone answers 404, which fetchOrThrow turns into an error.
  if (run.isError || !run.data?.state)
    return { notice: "This run isn't available: runs are kept for a day." };
  if (run.data.state === "failed") return { notice: `The run stopped: ${run.data.reason}` };
  if (run.data.state === "running" || !run.data.result)
    return { notice: "The run is still going…" };
  return { result: run.data.result };
}
