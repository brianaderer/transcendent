/**
 * Folds the ingestion stream's live events into the step the day being loaded has reached
 * (atlas plate 41): `day.step` starts a step, `decision.made` counts the tagging's
 * decisions, and the day finishing or failing ends it.
 */
import type { LiveEvent } from "./useLiveEvents";

export type StepName = "fetching" | "checking" | "embedding" | "grouping" | "tagging" | "applying";

export type DayStep = {
  day: string;
  step: StepName;
  count: number | null; // posts to embed, threads to group, or groups to decide
  decided: number;
};

/** The field each step's `day.step` event carries its number in. */
const COUNTED_AS: Partial<Record<StepName, string>> = {
  checking: "replies",
  embedding: "posts",
  grouping: "threads",
  tagging: "groups",
};

export function foldedStep(step: DayStep | null, event: LiveEvent): DayStep | null {
  switch (event.type) {
    case "day.step":
      return stepStarted(event);
    case "decision.made":
      return step && { ...step, decided: step.decided + 1 };
    case "day.finished":
    case "day.failed":
      return null;
    default:
      return step;
  }
}

function stepStarted(event: LiveEvent): DayStep {
  const step = event.step as StepName;
  const field = COUNTED_AS[step];
  const count = field ? Number(event[field]) : null;
  return { day: String(event.day), step, count, decided: 0 };
}

/** "embedding 204 posts", "tagging: 3 of 7 groups decided" and so on. */
export function describeStep({ step, count, decided }: DayStep): string {
  switch (step) {
    case "fetching":
      return "fetching posts";
    case "checking":
      return `checking ${count} replies for agreement`;
    case "embedding":
      return `embedding ${count} posts`;
    case "grouping":
      return `grouping ${count} threads`;
    case "tagging":
      return `tagging: ${decided} of ${count} groups decided`;
    case "applying":
      return "saving";
  }
}
