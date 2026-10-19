"""Reads for the Retrieval stats page (atlas plate 31, screen 5): the retrieval_events the
agents' search and lookup tools record, counted by post, by topic and by run."""

from sqlalchemy import ColumnElement, Engine, Select, func, nulls_last, select

from voices.db.models import Post, RetrievalEvent, Thread, Topic
from voices.db.post_columns import excerpt, written_between, written_on
from voices.explore.day_range import DayRange
from voices.retrievals.shapes import Agent, RetrievalFilter, RetrievedPost, TopicRetrievals

EXCERPT_CHARACTERS = 160  # one table cell's worth

times_retrieved = func.count(RetrievalEvent.id).label("times_retrieved")
last_retrieved = func.max(RetrievalEvent.at).label("last_retrieved")


class RetrievalStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    def most_retrieved(self, which: RetrievalFilter, limit: int) -> list[RetrievedPost]:
        """The most retrieved first; ties go to the one retrieved most recently."""
        query = (
            _counted(which, *_post_columns(), times_retrieved, last_retrieved)
            .group_by(Post.source_id, Thread.source_id, Topic.id)
            .order_by(times_retrieved.desc(), last_retrieved.desc(), Post.source_id)
            .limit(limit)
        )
        with self.engine.connect() as connection:
            return [RetrievedPost(**r._mapping) for r in connection.execute(query)]

    def per_topic(self, which: RetrievalFilter) -> list[TopicRetrievals]:
        """The most retrieved first; posts whose thread has no topic yet count together."""
        query = (
            _counted(which, Thread.topic_id, Topic.label, times_retrieved)
            .group_by(Thread.topic_id, Topic.label)
            .order_by(times_retrieved.desc(), nulls_last(Topic.label))
        )
        with self.engine.connect() as connection:
            return [TopicRetrievals(**r._mapping) for r in connection.execute(query)]

    def runs(self, agent: Agent, days: DayRange) -> list[str]:
        """The agent's runs that retrieved any post written in the range, newest first."""
        query = (
            select(RetrievalEvent.run)
            .join(Post, Post.source_id == RetrievalEvent.post_source_id)
            .where(RetrievalEvent.agent == agent, *written_between(days.start, days.end))
            .group_by(RetrievalEvent.run)
            .order_by(last_retrieved.desc(), RetrievalEvent.run)
        )
        with self.engine.connect() as connection:
            return list(connection.scalars(query))


def _counted(which: RetrievalFilter, *columns: ColumnElement) -> Select:
    """The filter's retrievals, each with its post, the post's thread and the thread's topic."""
    return (
        select(*columns)
        .select_from(RetrievalEvent)
        .join(Post, Post.source_id == RetrievalEvent.post_source_id)
        .join(Thread, Thread.source_id == Post.thread_source_id)
        .outerjoin(Topic, Topic.id == Thread.topic_id)
        .where(*_matching(which))
    )


def _matching(which: RetrievalFilter) -> list[ColumnElement[bool]]:
    conditions = [
        RetrievalEvent.agent == which.agent,
        *written_between(which.days.start, which.days.end),
    ]
    if which.run is not None:
        conditions.append(RetrievalEvent.run == which.run)
    return conditions


def _post_columns() -> list[ColumnElement]:
    return [
        Post.source_id.label("post_id"),
        Post.thread_source_id.label("thread_id"),
        Post.kind,
        Post.author,
        written_on().label("day"),
        excerpt(EXCERPT_CHARACTERS),
        Thread.topic_id,
        Topic.label.label("topic_label"),
    ]
