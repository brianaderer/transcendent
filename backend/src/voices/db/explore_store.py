"""Reads for the Explore page (atlas plate 31): posts per day, topics' daily engagement, and
the posts of a range with their embeddings."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import Date, Engine, cast, func, select

from voices.db.models import IngestedDay, Post, Thread, Topic, TopicDailyEngagement
from voices.explore.shapes import DayCount, MapPost, TopicDay, TopicInfo

EXCERPT_CHARACTERS = 160  # enough for the hover card


class ExploreStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    def posts_per_day(self) -> list[DayCount]:
        """Posts and comments written each day, by the day in UTC."""
        written_on = cast(func.timezone("UTC", Post.created_at), Date).label("day")
        query = select(written_on, func.count()).group_by(written_on).order_by(written_on)
        with self.engine.connect() as connection:
            return [DayCount(day=d, posts=n) for d, n in connection.execute(query)]

    def latest_day(self) -> date | None:
        query = select(func.max(IngestedDay.day)).where(IngestedDay.status == "done")
        with self.engine.connect() as connection:
            return connection.scalar(query)

    def topic_days(self, first_day: date, last_day: date) -> list[TopicDay]:
        """Each topic's engagement (posts, comments and upvotes) on each day it had any."""
        row = TopicDailyEngagement
        query = select(
            row.topic_id,
            row.day,
            (row.posts + row.comments + row.upvotes).label("engagement"),
            (row.posts + row.comments).label("posts"),
        ).where(row.day.between(first_day, last_day))
        with self.engine.connect() as connection:
            return [TopicDay(**r._mapping) for r in connection.execute(query)]

    def topics(self, ids: Sequence[int]) -> list[TopicInfo]:
        query = select(Topic.id, Topic.label, Topic.description, Topic.first_seen).where(
            Topic.id.in_(ids)
        )
        with self.engine.connect() as connection:
            return [TopicInfo(**r._mapping) for r in connection.execute(query)]

    def posts_in(self, first_day: date, last_day: date) -> list[MapPost]:
        """Every embedded post and comment written in the range, oldest first, with its
        thread's title and topic."""
        query = (
            select(
                Post.source_id.label("id"),
                Post.thread_source_id.label("thread_id"),
                Post.kind,
                Post.author,
                Post.created_at,
                Thread.title,
                _excerpt(),
                Thread.topic_id,
                Post.embedding,
            )
            .join(Thread, Thread.source_id == Post.thread_source_id)
            .where(Post.created_at >= _start_of(first_day))
            .where(Post.created_at < _start_of(last_day + timedelta(days=1)))
            .where(Post.embedding.is_not(None))
            .order_by(Post.created_at, Post.source_id)
        )
        with self.engine.connect() as connection:
            return [_map_post(r._mapping) for r in connection.execute(query)]


def _excerpt():
    """The post's opening words, or its thread's title for a post with no text (a link)."""
    text = func.coalesce(func.nullif(Post.body, ""), Thread.title)
    return func.left(text, EXCERPT_CHARACTERS).label("excerpt")


def _start_of(day: date) -> datetime:
    return datetime.combine(day, time(), UTC)


def _map_post(row) -> MapPost:
    fields = {k: v for k, v in row.items() if k not in ("created_at", "embedding")}
    day = row["created_at"].astimezone(UTC).date()
    return MapPost(**fields, day=day, embedding=[float(v) for v in row["embedding"]])
