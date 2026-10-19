"""Column expressions the stores share when they read posts: when a post or thread was
written, and the opening words it is shown by."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import ColumnElement, Date, cast, func
from sqlalchemy.orm import InstrumentedAttribute

from voices.db.models import Post, Thread

SHORT_EXCERPT_CHARACTERS = 160  # one line's worth: a hover card or a table cell


def written_on(column: InstrumentedAttribute[datetime]) -> ColumnElement[date]:
    """The day a timestamp column falls on, in UTC: when a post or a thread was written."""
    return cast(func.timezone("UTC", column), Date)


def written_between(first_day: date, last_day: date) -> list[ColumnElement[bool]]:
    """Written on any day from the first to the last, both included (UTC)."""
    return [
        Post.created_at >= _start_of(first_day),
        Post.created_at < _start_of(last_day + timedelta(days=1)),
    ]


def excerpt(characters: int) -> ColumnElement[str]:
    """The post's opening words, or its thread's title for a post with no text (a link).
    Needs the post's thread joined."""
    text = func.coalesce(func.nullif(Post.body, ""), Thread.title)
    return func.left(text, characters).label("excerpt")


def _start_of(day: date) -> datetime:
    return datetime.combine(day, time(), UTC)
