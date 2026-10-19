"""Links to posts on Reddit, built from the ids every stored post keeps, so a report's quotes
can point at the real post (atlas OPEN-16). The frontend's map builds the same links
(`frontend/src/explore/links.ts`)."""

SUBREDDIT = "sailing"
COMMUNITY_URL = f"https://www.reddit.com/r/{SUBREDDIT}/"


def post_link(post_id: str, thread_id: str, kind: str) -> str:
    """A post opens its thread; a comment opens itself within its thread."""
    thread = f"{COMMUNITY_URL}comments/{thread_id}/"
    return f"{thread}comment/{post_id}/" if kind == "comment" else thread
