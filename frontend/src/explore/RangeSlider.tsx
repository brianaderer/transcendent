import { useState } from "react";

import type { DayCount } from "../api/generated";
import { type DayRange, lastDays, PRESETS } from "./range";

type Props = { history: DayCount[]; range: DayRange; onChange: (range: DayRange) => void };

const HISTOGRAM_HEIGHT = 40;
const THUMB =
  "[&::-webkit-slider-thumb]:pointer-events-auto [&::-moz-range-thumb]:pointer-events-auto";

/**
 * Two handles over the history, with each day's posts as a bar behind them (atlas plate 31).
 * The range is only changed when a handle is let go, so the map isn't recomputed mid-drag.
 */
export function RangeSlider({ history, range, onChange }: Props) {
  const days = history.map((day) => day.day);
  const [draft, setDraft] = useState<[number, number] | null>(null);
  const [from, to] = draft ?? [days.indexOf(range.start), days.indexOf(range.end)];
  const letGo = () => {
    if (draft) onChange({ start: days[draft[0]], end: days[draft[1]] });
    setDraft(null);
  };
  const handle = (label: string, value: number, moved: (index: number) => [number, number]) => (
    <input
      type="range"
      aria-label={label}
      min={0}
      max={days.length - 1}
      value={value}
      onChange={(event) => setDraft(moved(Number(event.target.value)))}
      onPointerUp={letGo}
      onKeyUp={letGo}
      className={`pointer-events-none absolute inset-x-0 bottom-0 w-full appearance-none bg-transparent ${THUMB}`}
    />
  );
  return (
    <div className="space-y-2">
      <div className="relative" style={{ height: HISTOGRAM_HEIGHT + 16 }}>
        <Histogram history={history} from={from} to={to} />
        {handle("First day", from, (index) => [Math.min(index, to), to])}
        {handle("Last day", to, (index) => [from, Math.max(index, from)])}
      </div>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            className="rounded-full border border-slate-300 px-3 py-1 text-xs hover:border-teal-600 dark:border-slate-600"
            onClick={() => onChange(lastDays(days, preset.days))}
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function Histogram({ history, from, to }: { history: DayCount[]; from: number; to: number }) {
  const busiest = Math.max(1, ...history.map((day) => day.posts));
  return (
    <div className="flex items-end gap-px" style={{ height: HISTOGRAM_HEIGHT }} aria-hidden="true">
      {history.map((day, index) => (
        <div
          key={day.day}
          className={
            index >= from && index <= to
              ? "flex-1 bg-teal-600/70"
              : "flex-1 bg-slate-300 dark:bg-slate-700"
          }
          style={{ height: `${(day.posts / busiest) * 100}%` }}
        />
      ))}
    </div>
  );
}
