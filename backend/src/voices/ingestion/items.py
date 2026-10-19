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
    text: str  # what the author wrote; a post's title is kept apart from it
    reddit_score: int
    parent_source_id: str | None
    title: str | None = None  # posts only

    @property
    def body(self) -> str:
        """What is embedded and stored: a post's title, then its text when it has any."""
        return "\n\n".join(part for part in (self.title, self.text) if part)


def post_from_archive(raw: dict) -> Item:
    title = raw.get("title", "")
    text = raw.get("selftext") or ""
    return Item(
        source_id=raw["id"],
        thread_source_id=raw["id"],
        kind="post",
        author=raw["author"],
        created_at=_utc(raw["created_utc"]),
        text=text,
        reddit_score=raw.get("score", 0),
        parent_source_id=None,
        title=title,
    )


def comment_from_archive(raw: dict) -> Item:
    return Item(
        source_id=raw["id"],
        thread_source_id=_without_kind_prefix(raw["link_id"]),
        kind="comment",
        author=raw["author"],
        created_at=_utc(raw["created_utc"]),
        text=raw.get("body", ""),
        reddit_score=raw.get("score", 0),
        parent_source_id=_without_kind_prefix(raw["parent_id"]),
    )


def _utc(epoch_seconds: int) -> datetime:
    return datetime.fromtimestamp(epoch_seconds, UTC)


def _without_kind_prefix(reddit_name: str) -> str:
    """Reddit names things "t3_abc" (a post) or "t1_abc" (a comment); we keep just the id."""
    return reddit_name.split("_", 1)[1]
