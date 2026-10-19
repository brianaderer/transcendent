/** The comparison's two versions (atlas plate 70) and the words every page names them by. */
import { SUBREDDIT } from "../community";

export type Version = "A" | "B";
export type VersionNames = {
  /** Finishes a phrase: "Written without our data", "A · without our data". */
  short: string;
  /** Heads the version's column on the comparison. */
  long: string;
};

export const VERSIONS: Record<Version, VersionNames> = {
  A: { short: "without our data", long: "Without our data — the model on its own" },
  B: {
    short: "with retrieval",
    long: `With retrieval — the model searching r/${SUBREDDIT}'s posts`,
  },
};

/** The versions in the order the pages show them. */
export const VERSION_ORDER = Object.keys(VERSIONS) as Version[];

export function isVersion(value: unknown): value is Version {
  return typeof value === "string" && Object.hasOwn(VERSIONS, value);
}
