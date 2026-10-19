import { keepPreviousData } from "@tanstack/react-query";
import { useNavigate, useSearch } from "@tanstack/react-router";

import { type DayCount, type RetrievalStats, useReportRetrievals } from "../api/generated";
import { type DayRange, describeRange, rangeFrom } from "../explore/range";
import { RangeSlider } from "../explore/RangeSlider";
import { HistoryGate, postsIn } from "../HistoryGate";
import { RetrievalTable } from "./RetrievalTable";
import { type Agent, AGENT_NAMES, DEFAULT_AGENT, type RetrievalSearch } from "./search";
import { TopicBars } from "./TopicBars";

const AGENTS = Object.keys(AGENT_NAMES) as Agent[];

/** Which stored posts the agents retrieved most (atlas plate 31, screen 5; CLAUDE.md §7). */
export function RetrievalsPage() {
  return <HistoryGate>{(history) => <RetrievalsInRange history={history} />}</HistoryGate>;
}

function RetrievalsInRange({ history }: { history: DayCount[] }) {
  const asked = useSearch({ from: "/retrievals" });
  const navigate = useNavigate({ from: "/retrievals" });
  const range = rangeFrom(
    asked,
    history.map((day) => day.day),
  );
  const agent = asked.agent ?? DEFAULT_AGENT;
  const choose = (chosen: RetrievalSearch) =>
    navigate({ search: { ...range, agent, run: asked.run, ...chosen } });
  const stats = useReportRetrievals(
    { ...range, agent, run: asked.run },
    { query: { placeholderData: keepPreviousData } },
  );

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h2 className="font-serif text-2xl font-semibold">Retrieval stats</h2>
        <p className="max-w-3xl text-sm text-slate-600 dark:text-slate-400">
          Every time an agent's search or lookup tool hands it a stored post, the post is counted.
          These are the posts written in the chosen days, most retrieved first.
        </p>
      </header>
      <section aria-label="Date range" className="space-y-1">
        <RangeSlider history={history} range={range} onChange={choose} />
        <p className="text-sm font-medium">{describeRange(range, postsIn(history, range))}</p>
      </section>
      <Filters agent={agent} run={asked.run} runs={stats.data?.runs ?? []} onChange={choose} />
      {stats.isPending && <p>Counting retrievals…</p>}
      {stats.isError && <p>The retrieval counts couldn't be loaded.</p>}
      {stats.data && (
        <Counts
          stats={stats.data}
          range={range}
          onShowTagging={() => choose({ agent: "tagging", run: undefined })}
        />
      )}
    </div>
  );
}

type FiltersProps = {
  agent: Agent;
  run: string | undefined;
  runs: string[];
  onChange: (chosen: RetrievalSearch) => void;
};

/** The agent, as two buttons so the other one is always in view, and the run. */
function Filters({ agent, run, runs, onChange }: FiltersProps) {
  return (
    <section aria-label="Filters" className="flex flex-wrap items-center gap-4 text-sm">
      <div role="group" aria-label="Agent" className="flex gap-1">
        {AGENTS.map((each) => (
          <button
            key={each}
            type="button"
            aria-pressed={each === agent}
            onClick={() => onChange({ agent: each, run: undefined })}
            className="rounded-md border border-slate-300 px-3 py-1 aria-pressed:bg-teal-700 aria-pressed:text-white dark:border-slate-600"
          >
            {AGENT_NAMES[each]}
          </button>
        ))}
      </div>
      <label className="flex items-center gap-2">
        Run
        <select
          value={run ?? ""}
          onChange={(event) => onChange({ run: event.target.value || undefined })}
          className="rounded-md border border-slate-300 bg-transparent px-2 py-1 dark:border-slate-600"
        >
          <option value="">All runs</option>
          {runs.map((each) => (
            <option key={each} value={each}>
              {each}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}

type CountsProps = { stats: RetrievalStats; range: DayRange; onShowTagging: () => void };

function Counts({ stats, range, onShowTagging }: CountsProps) {
  if (stats.total === 0) return <NoRetrievals agent={stats.agent} onShowTagging={onShowTagging} />;
  return (
    <>
      <section aria-label="Retrievals per topic" className="space-y-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Retrievals per topic · {stats.total.toLocaleString("en-US")} in all
        </h3>
        <TopicBars topics={stats.topics} />
      </section>
      <RetrievalTable posts={stats.posts} agent={stats.agent} range={range} />
    </>
  );
}

/** Today only the tagging agent has retrieved anything until a report is generated. */
function NoRetrievals({ agent, onShowTagging }: { agent: Agent; onShowTagging: () => void }) {
  return (
    <div className="space-y-3 rounded-lg border border-dashed border-slate-300 p-6 dark:border-slate-700">
      <p>
        The {AGENT_NAMES[agent].toLowerCase()} hasn't retrieved any of the posts written in these
        days.
      </p>
      {agent === "report" && (
        <>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            The report agent retrieves posts when a report is generated for a range on Explore. The
            tagging agent retrieves them every day while it sorts threads into topics.
          </p>
          <button
            type="button"
            onClick={onShowTagging}
            className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white"
          >
            Show the tagging agent's retrievals
          </button>
        </>
      )}
    </div>
  );
}
