import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import { describeIngestion, fetchIngestionStatus } from "./ingestion";
import { useLiveEvents } from "./useLiveEvents";

const INGESTION_QUERY = ["ingestion"];

export function IngestionStatus() {
  const queryClient = useQueryClient();
  const status = useQuery({ queryKey: INGESTION_QUERY, queryFn: fetchIngestionStatus });
  const refresh = useCallback(
    () => queryClient.invalidateQueries({ queryKey: INGESTION_QUERY }),
    [queryClient],
  );
  useLiveEvents("ingestion", refresh);

  if (status.isPending) return <p>Checking the history…</p>;
  if (status.isError) return <p>History status unavailable</p>;
  return <p>{describeIngestion(status.data)}</p>;
}
