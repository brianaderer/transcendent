import { COMMUNITY_URL, HISTORY_WEEKS, SUBREDDIT } from "./community";

/** Says which community the app is reading, in the top bar on every screen. */
export function CommunityHeadline() {
  return (
    <p className="text-xs text-slate-500 dark:text-slate-400">
      <a
        href={COMMUNITY_URL}
        target="_blank"
        rel="noreferrer"
        className="font-medium text-teal-700 hover:underline dark:text-teal-400"
      >
        r/{SUBREDDIT}
      </a>{" "}
      on Reddit · the last {HISTORY_WEEKS} weeks of its posts
    </p>
  );
}
