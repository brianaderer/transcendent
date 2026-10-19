import type { MapPoint } from "../api/generated";
import { SUBREDDIT } from "../community";

/** Where a dot opens: the post, or the comment, on Reddit. */
export function redditLink(post: Pick<MapPoint, "id" | "thread_id" | "kind">): string {
  const thread = `https://www.reddit.com/r/${SUBREDDIT}/comments/${post.thread_id}/`;
  return post.kind === "comment" ? `${thread}comment/${post.id}/` : thread;
}
