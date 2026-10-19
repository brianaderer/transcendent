/** The comparison's scoreboard (atlas plate 31, screen 3): each measurement as A against B. */
import type { Scores, VersionResult } from "../api/generated";

export type ScoreRow = { measurement: string; a: string; b: string };

export function scoreboard(a: VersionResult, b: VersionResult): ScoreRow[] {
  return MEASUREMENTS.map(({ measurement, shown }) => ({
    measurement,
    a: shown(a),
    b: shown(b),
  }));
}

const MEASUREMENTS: { measurement: string; shown: (v: VersionResult) => string }[] = [
  {
    measurement: "Main topics found",
    shown: ({ scores: s }) => `${s.topics_found} of ${s.main_topics}`,
  },
  { measurement: "Topics invented", shown: ({ scores: s }) => String(s.topics_invented) },
  { measurement: "Order of importance", shown: ({ scores: s }) => agreement(s) },
  {
    measurement: "Direction right",
    shown: ({ scores: s }) => `${s.directions_right} of ${s.directions_named}`,
  },
  {
    measurement: "Prediction score",
    shown: ({ scores: s }) => `${Math.round(s.prediction_score * 100)}%`,
  },
  {
    measurement: "Tokens and time",
    shown: (v) => `${thousands(v.input_tokens + v.output_tokens)} · ${Math.round(v.seconds)}s`,
  },
  { measurement: "Posts looked at", shown: (v) => String(v.posts_seen.length) },
];

/** Spearman's rank agreement in words; it needs two or more found topics. */
function agreement(scores: Scores): string {
  const value = scores.order_agreement;
  if (value === null || value === undefined) return "too few to rank";
  return `${value >= 0.7 ? "close" : value >= 0.3 ? "partly" : "poor"} (${value.toFixed(2)})`;
}

function thousands(count: number): string {
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k` : String(count);
}
