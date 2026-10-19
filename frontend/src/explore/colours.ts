/** Topic colours on the dot plot and topics panel (atlas plate 31, "Colours"). */

export const PALETTE = [
  "#0f766e",
  "#d97706",
  "#2563eb",
  "#be185d",
  "#65a30d",
  "#7c3aed",
  "#0891b2",
  "#b45309",
  "#4338ca",
  "#15803d",
  "#c2410c",
  "#0369a1",
]; // the twelve biggest topics in the range get their own
export const OTHER_TOPIC = "#94a3b8"; // every smaller topic shares this
export const NO_TOPIC = "#cbd5e1"; // a post whose thread waits for a decision

/** Each topic's colour, given the range's topics busiest first. */
export function topicColours(topicIds: number[]): Map<number, string> {
  return new Map(topicIds.map((id, rank) => [id, PALETTE[rank] ?? OTHER_TOPIC]));
}

export function colourOf(topicId: number | null, colours: Map<number, string>): string {
  if (topicId === null) return NO_TOPIC;
  return colours.get(topicId) ?? OTHER_TOPIC;
}
