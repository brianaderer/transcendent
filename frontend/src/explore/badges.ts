import type { TopicInRange } from "../api/generated";

/** The word each topic is badged with for a range: which way its engagement is moving. */
export const BADGES: Record<TopicInRange["direction"], string> = {
  new: "New",
  rising: "Rising",
  steady: "Steady",
  fading: "Fading",
};
