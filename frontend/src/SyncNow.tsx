import { useEffect } from "react";

import { useSyncNow } from "./api/generated";
import { describeSync } from "./sync";

const ANSWER_SHOWN_MS = 8000; // long enough to read; the loading line takes over after

/**
 * Asks the worker for the daily catch-up now (atlas plate 40) and says, briefly, what it
 * will fetch. The live ingestion events then move the loading line beside it.
 */
export function SyncNow({ busy, answerShownMs = ANSWER_SHOWN_MS }: SyncNowProps) {
  const sync = useSyncNow();
  const { isSuccess, isError, reset } = sync;
  useEffect(() => {
    if (!isSuccess && !isError) return;
    const timer = setTimeout(reset, answerShownMs);
    return () => clearTimeout(timer);
  }, [isSuccess, isError, reset, answerShownMs]);

  return (
    <>
      <button
        type="button"
        disabled={busy || sync.isPending}
        onClick={() => sync.mutate()}
        className="rounded border border-slate-300 px-2 py-0.5 font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
      >
        Sync now
      </button>
      {sync.data && <p>{describeSync(sync.data)}</p>}
      {sync.isError && <p className="text-red-600">Sync now couldn't reach the worker</p>}
    </>
  );
}

type SyncNowProps = {
  /** A day is loading or the seed is being prepared: a catch-up is already at work. */
  busy: boolean;
  answerShownMs?: number;
};
