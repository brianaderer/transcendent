import { useEffect, useRef } from "react";

import type { DayRange } from "../explore/range";
import type { EngagementSeries } from "./engagement";
import { createEngagementChart, type EngagementChart as Chart } from "./chart";

type Props = { series: EngagementSeries; range: DayRange };

/** Daily engagement across the history as stacked areas, people as a line, the range shaded. */
export function EngagementChart({ series, range }: Props) {
  const area = useRef<HTMLDivElement>(null);
  const chart = useRef<Chart | null>(null);

  useEffect(() => {
    if (!area.current) return;
    const created = createEngagementChart(area.current);
    chart.current = created;
    const resize = () => created.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      created.dispose();
    };
  }, []);

  useEffect(() => {
    chart.current?.show({ series, range });
  }, [series, range]);

  return (
    <figure>
      <div
        ref={area}
        className="h-72 w-full"
        role="img"
        aria-label="Daily engagement across the history"
      />
      <figcaption className="mt-1 text-sm text-slate-500">
        Posts, comments and upvotes each day, stacked; the line is how many different people wrote.
        The shaded days are the range chosen on Explore.
      </figcaption>
    </figure>
  );
}
