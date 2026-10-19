import { useEffect, useRef, useState } from "react";

import type { MapPoint, TopicInRange } from "../api/generated";
import { alignTo } from "./align";
import { createScatter, type Dot, type Scatter } from "./chart";
import { colourOf } from "./colours";
import { escapeHtml } from "./html";
import { redditLink } from "./links";
import { useUiState } from "./uiState";

type Props = {
  points: MapPoint[];
  topics: TopicInRange[];
  colours: Map<number, string>;
  recomputing: boolean;
};

/** Every post in the range as a dot, coloured by topic (atlas plate 31, the dot plot). */
export function DotPlot({ points, topics, colours, recomputing }: Props) {
  const placed = useAlignedPlaces(points);
  const [plotArea, scatter] = useScatter();
  const highlighted = useUiState((state) => state.highlightedTopic);

  useEffect(() => {
    const style = { colours, labels: new Map(topics.map((t) => [t.id, t.label])), highlighted };
    scatter.current?.show(placed.map((point) => dotFor(point, style)));
  }, [placed, topics, colours, highlighted, scatter]);

  return (
    <figure className="relative">
      <div ref={plotArea} className="h-[60vh] min-h-80 w-full" data-testid="dot-plot" />
      {recomputing && (
        <p className="absolute top-2 left-2 text-sm text-slate-500">Recomputing map…</p>
      )}
      <figcaption className="mt-2 text-sm text-slate-500">
        Each dot is a post. Posts close together mean similar things.
      </figcaption>
    </figure>
  );
}

/** Each new map lined up with the last one shown, so the dots that stay glide. */
function useAlignedPlaces(points: MapPoint[]): MapPoint[] {
  const [placed, setPlaced] = useState<MapPoint[]>([]);
  useEffect(() => setPlaced((previous) => alignTo(previous, points)), [points]);
  return placed;
}

/** The chart, created once in the plot's area and disposed with it. */
function useScatter() {
  const plotArea = useRef<HTMLDivElement>(null);
  const scatter = useRef<Scatter | null>(null);
  useEffect(() => {
    if (!plotArea.current) return;
    const chart = createScatter(plotArea.current, (link) => window.open(link, "_blank"));
    scatter.current = chart;
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, []);
  return [plotArea, scatter] as const;
}

/** What every dot shares: the topics' colours and names, and which topic is highlighted. */
type DotStyle = {
  colours: Map<number, string>;
  labels: Map<number, string>;
  highlighted: number | null;
};

function dotFor(point: MapPoint, { colours, labels, highlighted }: DotStyle): Dot {
  const topic = point.thread_topic_id;
  return {
    id: point.id,
    x: point.x,
    y: point.y,
    colour: colourOf(topic, colours),
    faded: highlighted !== null && topic !== highlighted,
    card: hoverCard(point, topicName(topic, labels)),
    link: redditLink(point),
  };
}

function topicName(topic: number | null, labels: Map<number, string>): string {
  if (topic === null) return "No topic yet";
  return labels.get(topic) ?? "A smaller topic";
}

function hoverCard(point: MapPoint, topicLabel: string): string {
  return [
    `<strong>u/${escapeHtml(point.author)}</strong> · ${escapeHtml(point.day)}`,
    `<em>${escapeHtml(point.thread_title)}</em>`,
    `<span style="white-space:normal">${escapeHtml(point.excerpt)}</span>`,
    escapeHtml(topicLabel),
  ].join("<br/>");
}
