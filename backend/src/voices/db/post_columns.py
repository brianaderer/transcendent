"""Column expressions the stores share when they read posts: when a post was written, and
the opening words it is shown by."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import ColumnElement, Date, cast, func

from voices.db.models import Post, Thread


def written_on() -> ColumnElement[date]:
    """The day the post was written, in UTC."""
    return cast(func.timezone("UTC", Post.created_at), Date)


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
