import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { describeStep, foldedStep, type DayStep } from "./daySteps";
import {
  describeIngestion,
  fetchIngestionStatus,
  type IngestionStatus as Status,
} from "./ingestion";
import { SyncNow } from "./SyncNow";
import { type LiveEvent, useLiveEvents } from "./useLiveEvents";

const INGESTION_QUERY = ["ingestion"];

/** The loading line, and the Sync now button beside it. */
export function IngestionStatus({ answerShownMs }: { answerShownMs?: number }) {
  const queryClient = useQueryClient();
  const status = useQuery({ queryKey: INGESTION_QUERY, queryFn: fetchIngestionStatus });
  const [step, setStep] = useState<DayStep | null>(null);
  const followEvent = useCallback(
    (event: LiveEvent) => {
      setStep((current) => foldedStep(current, event));
      queryClient.invalidateQueries({ queryKey: INGESTION_QUERY });
    },
    [queryClient],
  );
  useLiveEvents("ingestion", followEvent);

  if (status.isPending) return <p>Checking the history…</p>;
  if (status.isError) return <p>History status unavailable</p>;
  return (
    <>
      <p>{describeIngestion(status.data, stepOfTheRunningDay(status.data, step))}</p>
      <SyncNow busy={aCatchUpIsBusy(status.data)} answerShownMs={answerShownMs} />
    </>
  );
}

/** The live step, while it belongs to the day the status says is loading. */
function stepOfTheRunningDay(status: Status, step: DayStep | null): string | null {
  return step && step.day === status.running_day ? describeStep(step) : null;
}

/** Matches `a_catch_up_is_busy` in backend/src/voices/ingestion/sync_now.py. */
function aCatchUpIsBusy(status: Status): boolean {
  return status.running_day !== null || status.backfill !== null;
}
