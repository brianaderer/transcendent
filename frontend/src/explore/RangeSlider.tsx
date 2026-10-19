import { useState } from "react";

import type { DayCount } from "../api/generated";
import { type DayRange, lastDays, PRESETS } from "./range";

type Props = { history: DayCount[]; range: DayRange; onChange: (range: DayRange) => void };

const HISTOGRAM_HEIGHT = 40;
const THUMB_ROOM_PX = 16; // below the bars, where the handles sit
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
  const last = days.length - 1;
  return (
    <div className="space-y-2">
      <div className="relative" style={{ height: HISTOGRAM_HEIGHT + THUMB_ROOM_PX }}>
        <Histogram history={history} from={from} to={to} />
        <RangeHandle
          label="First day"
          value={from}
          max={last}
          onLetGo={letGo}
          onMove={(index) => setDraft([Math.min(index, to), to])}
        />
        <RangeHandle
          label="Last day"
          value={to}
          max={last}
          onLetGo={letGo}
          onMove={(index) => setDraft([from, Math.max(index, from)])}
        />
      </div>
      <PresetButtons days={days} onChange={onChange} />
    </div>
  );
}

type HandleProps = {
  label: string;
  value: number;
  max: number;
  onMove: (index: number) => void;
  onLetGo: () => void;
};

/** One handle; both lie over the same track, so only their thumbs take the pointer. */
function RangeHandle({ label, value, max, onMove, onLetGo }: HandleProps) {
  return (
    <input
      type="range"
      aria-label={label}
      min={0}
      max={max}
      value={value}
      onChange={(event) => onMove(Number(event.target.value))}
      onPointerUp={onLetGo}
      onKeyUp={onLetGo}
      className={`pointer-events-none absolute inset-x-0 bottom-0 w-full appearance-none bg-transparent ${THUMB}`}
    />
  );
}

function PresetButtons({
  days,
  onChange,
}: {
  days: string[];
  onChange: (range: DayRange) => void;
}) {
  return (
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
