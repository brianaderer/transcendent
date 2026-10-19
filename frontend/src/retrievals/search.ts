/** The Retrieval stats page's filters as they sit in the address (atlas plate 31, screen 5). */

import { ReportRetrievalsAgent } from "../api/generated";
import type { DayRange } from "../explore/range";

export type Agent = ReportRetrievalsAgent;

export const DEFAULT_AGENT: Agent = "report"; // the plate's default: what the report looked at

export const AGENT_NAMES: Record<Agent, string> = {
  report: "Report agent",
  tagging: "Tagging agent",
};

export type RetrievalFilters = { agent?: Agent; run?: string };
export type RetrievalSearch = Partial<DayRange> & RetrievalFilters;

/** The agent and run in the address; an agent that doesn't exist is dropped. */
export function retrievalSearch(search: Record<string, unknown>): RetrievalFilters {
  return {
    agent: isAgent(search.agent) ? search.agent : undefined,
    run: typeof search.run === "string" && search.run !== "" ? search.run : undefined,
  };
}

function isAgent(value: unknown): value is Agent {
  return typeof value === "string" && value in AGENT_NAMES;
}
