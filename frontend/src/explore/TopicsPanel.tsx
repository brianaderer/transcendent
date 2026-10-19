import { Link, useSearch } from "@tanstack/react-router";

import type { TopicInRange } from "../api/generated";
import { colourOf } from "./colours";
import { useUiState } from "./uiState";

export const BADGES: Record<TopicInRange["direction"], string> = {
  new: "New",
  rising: "Rising",
  steady: "Steady",
  fading: "Fading",
};

type Props = { topics: TopicInRange[]; colours: Map<number, string> };

/** The range's topics, busiest first (atlas plate 31): hovering one highlights its dots, and
 * clicking its name opens its Topic detail page with the same range. */
export function TopicsPanel({ topics, colours }: Props) {
  const highlightTopic = useUiState((state) => state.highlightTopic);
  const { start, end } = useSearch({ strict: false });
  if (topics.length === 0)
    return <p className="text-sm text-slate-500">No topics in these days.</p>;
  return (
    <ol className="divide-y divide-slate-200 dark:divide-slate-700" aria-label="Topics">
      {topics.map((topic) => (
        <li
          key={topic.id}
          className="flex items-center gap-3 py-2"
          onMouseEnter={() => highlightTopic(topic.id)}
          onMouseLeave={() => highlightTopic(null)}
          onFocus={() => highlightTopic(topic.id)}
          onBlur={() => highlightTopic(null)}
          tabIndex={0}
          title={topic.description}
        >
          <span
            className="h-3 w-3 shrink-0 rounded-full"
            style={{ background: colourOf(topic.id, colours) }}
          />
          <Link
            to="/topics/$topicId"
            params={{ topicId: String(topic.id) }}
            search={{ start, end }}
            className="min-w-0 flex-1 truncate text-sm hover:underline"
          >
            {topic.label}
          </Link>
          <Sparkline values={topic.daily} />
          <span className="w-10 text-right text-xs tabular-nums text-slate-500">{topic.posts}</span>
          <span className="w-14 text-right text-xs font-medium">{BADGES[topic.direction]}</span>
        </li>
      ))}
    </ol>
  );
}

const SPARK_WIDTH = 60;
const SPARK_HEIGHT = 16;

/** The topic's engagement on each day of the range. */
export function Sparkline({ values }: { values: number[] }) {
  const highest = Math.max(1, ...values);
  const step = values.length > 1 ? SPARK_WIDTH / (values.length - 1) : 0;
  const points = values
    .map((value, day) => `${day * step},${SPARK_HEIGHT - (value / highest) * SPARK_HEIGHT}`)
    .join(" ");
  return (
    <svg width={SPARK_WIDTH} height={SPARK_HEIGHT} aria-hidden="true" className="shrink-0">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth={1.5} />
    </svg>
  );
}
