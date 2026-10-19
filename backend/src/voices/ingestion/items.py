"""Posts and comments as the ingestion code passes them around, converted from the archive."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class Item:
    source_id: str
    thread_source_id: str
    kind: str  # "post" or "comment"
    author: str
    created_at: datetime
    body: str
    reddit_score: int
    parent_source_id: str | None
    text: str  # what the author wrote: a post's text without its title, a comment's body
    title: str | None = None  # posts only


def post_from_archive(raw: dict) -> Item:
    title = raw.get("title", "")
    text = raw.get("selftext") or ""
    return Item(
        source_id=raw["id"],
        thread_source_id=raw["id"],
        kind="post",
        author=raw["author"],
        created_at=_utc(raw["created_utc"]),
        body=f"{title}\n\n{text}" if text else title,
        reddit_score=raw.get("score", 0),
        parent_source_id=None,
        text=text,
        title=title,
    )


def comment_from_archive(raw: dict) -> Item:
    return Item(
        source_id=raw["id"],
        thread_source_id=_without_kind_prefix(raw["link_id"]),
        kind="comment",
        author=raw["author"],
        created_at=_utc(raw["created_utc"]),
        body=raw.get("body", ""),
        reddit_score=raw.get("score", 0),
        parent_source_id=_without_kind_prefix(raw["parent_id"]),
        text=raw.get("body", ""),
    )


def _utc(epoch_seconds: int) -> datetime:
    return datetime.fromtimestamp(epoch_seconds, UTC)


def _without_kind_prefix(reddit_name: str) -> str:
    """Reddit names things "t3_abc" (a post) or "t1_abc" (a comment); we keep just the id."""
    return reddit_name.split("_", 1)[1]
