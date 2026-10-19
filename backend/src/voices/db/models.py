"""The tables, described once, in Python. Alembic builds its migrations from these.

The plan behind them is atlas plate 21 (topics and engagement) and plate 40 (ingested_days).
"""

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIMENSIONS = 768  # the size nomic-embed-text produces (atlas OPEN-5)


class Base(DeclarativeBase):
    pass


class Thread(Base):
    """A post and its comments: the unit that is encoded, grouped and tagged (atlas OPEN-29).
    Its comments take its topic, including comments that arrive later."""

    __tablename__ = "threads"
    __table_args__ = (
        CheckConstraint("stage IN ('new', 'decided_once', 'settled')", name="thread_stage"),
    )

    source_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Its first and third days count from here: a thread started before the history, or whose
    # post was removed, is first seen with its first stored comment (atlas OPEN-30).
    first_seen_on: Mapped[date] = mapped_column(Date)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), index=True)
    cluster_decision_id: Mapped[int | None] = mapped_column(ForeignKey("cluster_decisions.id"))
    # new: not decided yet; decided_once: decided on its first day; settled: decided on its third
    stage: Mapped[str] = mapped_column(Text, server_default="new")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    label: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    centroid: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date] = mapped_column(Date)


class ClusterDecision(Base):
    __tablename__ = "cluster_decisions"
    __table_args__ = (
        CheckConstraint("decision IN ('attach', 'mint', 'noise')", name="decision_kind"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    day: Mapped[date] = mapped_column(Date)
    decision: Mapped[str] = mapped_column(Text)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"))
    reason: Mapped[str] = mapped_column(Text)
    candidate_tags: Mapped[list[dict]] = mapped_column(JSONB, server_default="[]")
    prompt: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)


class Post(Base):
    """A post or a comment, embedded whole, once. Its topic is its thread's."""

    __tablename__ = "posts"
    __table_args__ = (CheckConstraint("kind IN ('post', 'comment')", name="post_kind"),)

    source_id: Mapped[str] = mapped_column(Text, primary_key=True)
    thread_source_id: Mapped[str] = mapped_column(ForeignKey("threads.source_id"))
    kind: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    body: Mapped[str] = mapped_column(Text)
    reddit_score: Mapped[int] = mapped_column(Integer, server_default="0")
    upvotes: Mapped[int] = mapped_column(Integer, server_default="0")  # agreeing replies
    parent_source_id: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))


class PostUpvotesDaily(Base):
    __tablename__ = "post_upvotes_daily"

    post_source_id: Mapped[str] = mapped_column(
        ForeignKey("posts.source_id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    count: Mapped[int] = mapped_column(Integer)


class TopicDailyEngagement(Base):
    __tablename__ = "topic_daily_engagement"

    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    posts: Mapped[int] = mapped_column(Integer, server_default="0")
    comments: Mapped[int] = mapped_column(Integer, server_default="0")
    upvotes: Mapped[int] = mapped_column(Integer, server_default="0")
    unique_authors: Mapped[int] = mapped_column(Integer, server_default="0")
    new_threads: Mapped[int] = mapped_column(Integer, server_default="0")
    revived_threads: Mapped[int] = mapped_column(Integer, server_default="0")
    unanswered_questions: Mapped[int] = mapped_column(Integer, server_default="0")


class NoiseThread(Base):
    """A thread deleted as noise, kept as its id only so a comment arriving on it later is
    dropped at intake instead of bringing the thread back (atlas OPEN-31)."""

    __tablename__ = "noise_threads"

    source_id: Mapped[str] = mapped_column(Text, primary_key=True)
    deleted_on: Mapped[date] = mapped_column(Date)


class RetrievalEvent(Base):
    __tablename__ = "retrieval_events"
    __table_args__ = (
        CheckConstraint("agent IN ('report', 'tagging')", name="retrieval_agent"),
        CheckConstraint("tool IN ('search', 'lookup')", name="retrieval_tool"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_source_id: Mapped[str] = mapped_column(ForeignKey("posts.source_id", ondelete="CASCADE"))
    run: Mapped[str] = mapped_column(Text)
    agent: Mapped[str] = mapped_column(Text)
    tool: Mapped[str] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


DAY_RUNNING, DAY_DONE, DAY_FAILED = "running", "done", "failed"  # an ingested day's status
DAY_STATUSES = (DAY_RUNNING, DAY_DONE, DAY_FAILED)


class IngestedDay(Base):
    """One row per day the catch-up has processed (atlas plate 40)."""

    __tablename__ = "ingested_days"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join(f"'{status}'" for status in DAY_STATUSES)})",
            name="ingested_day_status",
        ),
    )

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    status: Mapped[str] = mapped_column(Text)
    counts: Mapped[dict[str, int]] = mapped_column(JSONB, server_default="{}")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)  # why the day failed, when it did
