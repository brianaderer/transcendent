import { HISTORY_WEEKS, SUBREDDIT } from "./community";

const COMMUNITY_URL = `https://www.reddit.com/r/${SUBREDDIT}/`;

/** Says which community the app is reading, in the top bar on every screen. */
export function CommunityHeadline() {
  return (
    <p className="text-sm text-slate-600 dark:text-slate-300">
      <a
        href={COMMUNITY_URL}
        target="_blank"
        rel="noreferrer"
        className="font-semibold text-teal-700 hover:underline dark:text-teal-400"
      >
        r/{SUBREDDIT}
      </a>{" "}
      on Reddit · the last {HISTORY_WEEKS} weeks of its posts
    </p>
  );
}
