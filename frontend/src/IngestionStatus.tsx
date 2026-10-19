import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import {
  describeIngestion,
  fetchIngestionStatus,
  type IngestionStatus as Status,
} from "./ingestion";
import { SyncNow } from "./SyncNow";
import { useLiveEvents } from "./useLiveEvents";

const INGESTION_QUERY = ["ingestion"];

/** The loading line, and the Sync now button beside it. */
export function IngestionStatus({ answerShownMs }: { answerShownMs?: number }) {
  const queryClient = useQueryClient();
  const status = useQuery({ queryKey: INGESTION_QUERY, queryFn: fetchIngestionStatus });
  const refresh = useCallback(
    () => queryClient.invalidateQueries({ queryKey: INGESTION_QUERY }),
    [queryClient],
  );
  useLiveEvents("ingestion", refresh);

  if (status.isPending) return <p>Checking the history…</p>;
  if (status.isError) return <p>History status unavailable</p>;
  return (
    <>
      <p>{describeIngestion(status.data)}</p>
      <SyncNow busy={aCatchUpIsBusy(status.data)} answerShownMs={answerShownMs} />
    </>
  );
}

/** Matches `a_catch_up_is_busy` in backend/src/voices/ingestion/sync_now.py. */
function aCatchUpIsBusy(status: Status): boolean {
  return status.running_day !== null || status.backfill !== null;
}
