import type { MapPoint } from "../api/generated";

/** Where a dot opens: the post, or the comment, on Reddit. */
export function redditLink(post: Pick<MapPoint, "id" | "thread_id" | "kind">): string {
  const thread = `https://www.reddit.com/r/sailing/comments/${post.thread_id}/`;
  return post.kind === "comment" ? `${thread}comment/${post.id}/` : thread;
}

export function escapeHtml(text: string): string {
  const entities: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  return text.replace(/[&<>"']/g, (character) => entities[character]);
}
