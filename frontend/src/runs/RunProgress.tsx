import { Link } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useReducer } from "react";

import { getReportRunQueryKey, useReportRun } from "../api/generated";
import { Spinner } from "../Spinner";
import { type LiveEvent, useLiveEvents } from "../useLiveEvents";
import {
  folded,
  type Lane,
  type Progress,
  laneProgress,
  runStream,
  STARTING,
  whyTheRunStopped,
} from "./runEvents";
import { VERSION_ORDER, VERSIONS } from "./versions";

const STATE_CHECK_MS = 3000; // in case a live event was missed, the run's state is read again

/** Both versions' work as it happens, then links to the results (atlas plate 31, screen 1). */
export function RunProgress({ runId }: { runId: string }) {
  const [progress, fold] = useReducer(folded, STARTING);
  const queryClient = useQueryClient();
  const onEvent = useCallback(
    (event: LiveEvent) => {
      fold(event);
      if (event.type === "run.finished" || event.type === "run.failed") {
        // The result is kept before this is announced, so read it now rather than at the next check.
        queryClient.invalidateQueries({ queryKey: getReportRunQueryKey(runId) });
      }
    },
    [queryClient, runId],
  );
  useLiveEvents(runStream(runId), onEvent);
  const run = useReportRun(runId, {
    query: {
      refetchInterval: (query) => (query.state.data?.state === "running" ? STATE_CHECK_MS : false),
    },
  });
  const state = run.data?.state;
  const failed = whyTheRunStopped(progress, run.data);

  return (
    <section
      aria-label="Report progress"
      className="mt-4 rounded-md border border-slate-200 p-4 dark:border-slate-700"
    >
      <div className="grid gap-4 md:grid-cols-2">
        {VERSION_ORDER.map((version) => (
          <LaneView
            key={version}
            title={`${version} · ${VERSIONS[version].short}`}
            lane={progress.lanes[version]}
          />
        ))}
      </div>
      {isScoring(progress) && state === "running" && !failed && (
        <p className="mt-3 flex items-center gap-1.5 text-sm">
          <Spinner />
          Scoring both versions…
        </p>
      )}
      {failed && <p className="mt-3 text-sm text-red-600">The run stopped: {failed}</p>}
      {state === "finished" && (
        <p className="mt-3 flex gap-4 text-sm font-medium">
          <Link
            to="/runs/$runId/report"
            params={{ runId }}
            className="text-teal-700 dark:text-teal-400"
          >
            Read the report
          </Link>
          <Link
            to="/runs/$runId/comparison"
            params={{ runId }}
            className="text-teal-700 dark:text-teal-400"
          >
            See the comparison
          </Link>
        </p>
      )}
    </section>
  );
}

function LaneView({ title, lane }: { title: string; lane: Lane }) {
  return (
    <div>
      <h3 className="mb-1 text-sm font-semibold">{title}</h3>
      <LaneBar lane={lane} />
      <ol className="max-h-48 overflow-y-auto font-mono text-xs text-slate-600 dark:text-slate-300">
        {lane.lines.map((line, n) => (
          <li key={n} className="whitespace-pre-wrap">
            {line}
          </li>
        ))}
      </ol>
    </div>
  );
}

/** The lane's progress, fed live by the run's events. */
function LaneBar({ lane }: { lane: Lane }) {
  const { percent, label } = laneProgress(lane);
  return (
    <div className="mb-2">
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className="h-1.5 w-full overflow-hidden rounded bg-slate-200 dark:bg-slate-700"
      >
        <div
          className="h-full bg-teal-600 transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-slate-500">{label}</p>
    </div>
  );
}

/** Both versions have answered; their topics are being matched and scored. */
function isScoring(progress: Progress): boolean {
  return progress.measuring || VERSION_ORDER.every((v) => progress.lanes[v].stage === "done");
}
