"""Reads for the Topic detail page (atlas plate 31, screen 4): one topic, its daily
engagement, the threads closest to its centre, and the tagging decisions that built it."""

from sqlalchemy import Date, Engine, cast, func, literal, select

from voices.db.models import ClusterDecision, Post, Thread, Topic, TopicDailyEngagement
from voices.db.post_columns import excerpt
from voices.db.tagging_store import UNKNOWN_AUTHOR
from voices.topics.shapes import EngagementDay, PostCard, TopicDecision, TopicSummary
from voices.topics.topic_detail import TopicNotFound

CARD_EXCERPT_CHARACTERS = 280  # a few lines on a post card


class TopicStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    def summary(self, topic_id: int) -> TopicSummary:
        """Raises TopicNotFound for an id with no topic."""
        query = select(
            Topic.id,
            Topic.label,
            Topic.description,
            Topic.keywords,
            Topic.first_seen,
            Topic.last_seen,
        ).where(Topic.id == topic_id)
        with self.engine.connect() as connection:
            row = connection.execute(query).first()
        if row is None:
            raise TopicNotFound(topic_id)
        return TopicSummary(**row._mapping)

    def engagement(self, topic_id: int) -> list[EngagementDay]:
        """Each day the topic had any engagement, oldest first."""
        row = TopicDailyEngagement
        query = (
            select(row.day, row.posts, row.comments, row.upvotes)
            .add_columns(row.unique_authors.label("people"))
            .where(row.topic_id == topic_id)
            .order_by(row.day)
        )
        with self.engine.connect() as connection:
            return [EngagementDay(**r._mapping) for r in connection.execute(query)]

    def typical_posts(self, topic_id: int, limit: int) -> list[PostCard]:
        """The opening posts of the topic's threads closest to its centre, closest first."""
        query = (
            select(*_card_columns())
            .outerjoin(Post, Post.source_id == Thread.source_id)  # a thread's post shares its id
            .where(Thread.topic_id == topic_id, Thread.embedding.is_not(None))
            .order_by(Thread.embedding.cosine_distance(_centre_of(topic_id)), Thread.source_id)
            .limit(limit)
        )
        with self.engine.connect() as connection:
            return [PostCard(**r._mapping) for r in connection.execute(query)]

    def decisions(self, topic_id: int) -> list[TopicDecision]:
        """The decisions that minted the topic or attached threads to it, oldest first, each
        with the threads that carry it now."""
        decision = ClusterDecision
        query = (
            select(
                decision.day,
                decision.decision,
                func.count(Thread.source_id).label("threads"),
                decision.reason,
            )
            .outerjoin(Thread, Thread.cluster_decision_id == decision.id)
            .where(decision.topic_id == topic_id)
            .group_by(decision.id)
            .order_by(decision.day, decision.id)
        )
        with self.engine.connect() as connection:
            return [TopicDecision(**r._mapping) for r in connection.execute(query)]


def _card_columns() -> list:
    return [
        Thread.source_id.label("post_id"),
        Thread.source_id.label("thread_id"),
        literal("post").label("kind"),
        func.coalesce(Post.author, UNKNOWN_AUTHOR).label("author"),
        cast(func.timezone("UTC", Thread.created_at), Date).label("day"),
        Thread.title,
        excerpt(CARD_EXCERPT_CHARACTERS),
    ]


def _centre_of(topic_id: int):
    return select(Topic.centroid).where(Topic.id == topic_id).scalar_subquery()
