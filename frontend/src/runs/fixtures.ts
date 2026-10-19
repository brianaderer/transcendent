/** A finished run as the API returns it, for the runs' tests. */
import type { RunState, VersionResult } from "../api/generated";

const SCORES = {
  main_topics: 10,
  topics_found: 8,
  topics_invented: 0,
  order_agreement: 0.83,
  directions_named: 8,
  directions_right: 7,
  predicted_named: 5,
  predicted_prominent: 4,
  predicted_never_came_up: 1,
  predicted_direction_right: 3,
  prediction_score: 0.6,
};

function version(name: "A" | "B", overrides: Partial<VersionResult>): VersionResult {
  return {
    version: name,
    document: `## The period in brief\n\nVersion ${name} on winterizing.`,
    topics: [{ name: "Winterizing", rank: 1, direction: "rising" }],
    predicted: [{ name: "Winterizing", direction: "rising" }],
    prediction_reasoning: "Haul-out season.",
    scores: SCORES,
    report_matches: { Winterizing: 1 },
    prediction_matches: { Winterizing: 1 },
    tool_calls: name === "B" ? 6 : 0,
    posts_seen: name === "B" ? ["p1", "p2"] : [],
    input_tokens: 1500,
    output_tokens: 600,
    seconds: 12.4,
    ...overrides,
  };
}

export const FINISHED_RUN: RunState = {
  state: "finished",
  reason: null,
  result: {
    run_id: "0123456789ab",
    start: "2026-10-12",
    end: "2026-10-18",
    model: "anthropic/claude-sonnet-5.5",
    instructions: { write: "Write…", predict: "Predict…" },
    main_topics: [
      {
        topic_id: 1,
        label: "Winterizing",
        description: "d",
        rank: 1,
        engagement: 90,
        direction: "rising",
      },
      {
        topic_id: 2,
        label: "Anchoring",
        description: "d",
        rank: 2,
        engagement: 40,
        direction: "fading",
      },
    ],
    versions: [
      version("A", {
        topics: [
          { name: "Winterizing", rank: 1, direction: "steady" },
          { name: "Safety at sea", rank: 2, direction: "steady" },
        ],
        report_matches: { Winterizing: 1, "Safety at sea": null },
        scores: {
          ...SCORES,
          topics_found: 1,
          topics_invented: 1,
          order_agreement: null,
          prediction_score: 0.2,
        },
      }),
      version("B", {}),
    ],
  },
};
