import { keepPreviousData, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useCallback, useMemo } from "react";

import { type DayCount, useReportMap, useReportTopics } from "../api/generated";
import { HistoryGate, postsIn } from "../HistoryGate";
import { type LiveEvent, useLiveEvents } from "../useLiveEvents";
import { topicColours } from "./colours";
import { DotPlot } from "./DotPlot";
import { type DayRange, describeRange, rangeFrom, shortRange } from "./range";
import { RangeSlider } from "./RangeSlider";
import { TopicsPanel } from "./TopicsPanel";

/** The main page (atlas plate 31, screen 1): one date range governs everything on it. */
export function ExplorePage() {
  useRefreshWhenADayIsLoaded();
  return <HistoryGate>{(history) => <ExploreRange history={history} />}</HistoryGate>;
}

function ExploreRange({ history }: { history: DayCount[] }) {
  const asked = useSearch({ from: "/" });
  const navigate = useNavigate({ from: "/" });
  const range = rangeFrom(
    asked,
    history.map((day) => day.day),
  );
  const topics = useReportTopics(range, { query: { placeholderData: keepPreviousData } });
  const map = useReportMap(range, { query: { placeholderData: keepPreviousData } });
  const shownTopics = useMemo(() => topics.data ?? [], [topics.data]);
  const colours = useMemo(() => topicColours(shownTopics.map((t) => t.id)), [shownTopics]);
  const choose = (chosen: DayRange) => navigate({ search: chosen });

  return (
    <div className="space-y-4">
      <section aria-label="Date range" className="space-y-1">
        <RangeSlider history={history} range={range} onChange={choose} />
        <p className="text-sm font-medium">{describeRange(range, postsIn(history, range))}</p>
      </section>
      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <section aria-label="Map of the posts">
          <DotPlot
            points={map.data?.points ?? []}
            topics={shownTopics}
            colours={colours}
            recomputing={map.isFetching}
          />
          <GenerateReport range={range} />
        </section>
        <section aria-label="Topics in the range">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Topics
          </h2>
          <TopicsPanel topics={shownTopics} colours={colours} />
        </section>
      </div>
    </div>
  );
}

/** Will start a report and its comparison for the range (atlas plate 70); off for now. */
function GenerateReport({ range }: { range: DayRange }) {
  return (
    <div className="mt-3 flex items-center justify-end gap-3">
      <button
        type="button"
        disabled
        className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white opacity-50"
      >
        Generate report for {shortRange(range)}
      </button>
    </div>
  );
}

/** During a first start, each finished day widens the history and changes its topics. */
function useRefreshWhenADayIsLoaded() {
  const queryClient = useQueryClient();
  const refresh = useCallback(
    (event: LiveEvent) => {
      if (event.type === "day.finished") queryClient.invalidateQueries();
    },
    [queryClient],
  );
  useLiveEvents("ingestion", refresh);
}
