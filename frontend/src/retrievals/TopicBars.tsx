import type { TopicRetrievals } from "../api/generated";

export const TOPICS_CHARTED = 12; // the busiest topics; the rest are in the table
const BAR_COLOUR = "#0d9488";
export const NO_TOPIC_YET = "No topic yet"; // a thread waiting for its tagging decision

/** Retrievals per topic as horizontal bars, the most retrieved first, each labelled. */
export function TopicBars({ topics }: { topics: TopicRetrievals[] }) {
  const charted = topics.slice(0, TOPICS_CHARTED);
  const most = Math.max(1, ...charted.map((topic) => topic.times_retrieved));
  return (
    <ol aria-label="Retrievals per topic" className="space-y-1">
      {charted.map((topic) => (
        <li
          key={topic.topic_id ?? "none"}
          className="grid grid-cols-[minmax(0,14rem)_1fr_3rem] items-center gap-2 text-sm"
          title={`${label(topic)}: ${topic.times_retrieved} retrievals`}
        >
          <span className="truncate">{label(topic)}</span>
          <span className="h-3 rounded-r bg-slate-100 dark:bg-slate-800">
            <span
              className="block h-3 rounded-r"
              style={{
                width: `${(topic.times_retrieved / most) * 100}%`,
                background: BAR_COLOUR,
              }}
            />
          </span>
          <span className="text-right tabular-nums text-slate-500">{topic.times_retrieved}</span>
        </li>
      ))}
    </ol>
  );
}

function label(topic: TopicRetrievals): string {
  return topic.label ?? NO_TOPIC_YET;
}
