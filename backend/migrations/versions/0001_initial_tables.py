"""initial tables

Revision ID: 0001
Revises:
"""

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The embedding columns need pgvector, so the extension comes first.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "ingested_days",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "counts", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('running', 'done', 'failed')", name="ingested_day_status"),
        sa.PrimaryKeyConstraint("day"),
    )
    op.create_table(
        "threads",
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("source_id"),
    )
    op.create_table(
        "topics",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("keywords", sa.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("centroid", pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=False),
        sa.Column("first_seen", sa.Date(), nullable=False),
        sa.Column("last_seen", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cluster_decisions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "candidate_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.CheckConstraint("decision IN ('attach', 'mint', 'noise')", name="decision_kind"),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "topic_daily_engagement",
        sa.Column("topic_id", sa.BigInteger(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("posts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comments", sa.Integer(), server_default="0", nullable=False),
        sa.Column("upvotes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unique_authors", sa.Integer(), server_default="0", nullable=False),
        sa.Column("new_threads", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unanswered_questions", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.PrimaryKeyConstraint("topic_id", "day"),
    )
    op.create_table(
        "posts",
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("thread_source_id", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("reddit_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("upvotes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("parent_source_id", sa.Text(), nullable=True),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
        sa.Column("status", sa.Text(), server_default="pending", nullable=False),
        sa.Column("topic_id", sa.BigInteger(), nullable=True),
        sa.Column("topic_similarity", sa.Float(), nullable=True),
        sa.Column("cluster_decision_id", sa.BigInteger(), nullable=True),
        sa.CheckConstraint("kind IN ('post', 'comment')", name="post_kind"),
        sa.CheckConstraint("status IN ('pending', 'tagged')", name="post_status"),
        sa.ForeignKeyConstraint(
            ["cluster_decision_id"],
            ["cluster_decisions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["thread_source_id"],
            ["threads.source_id"],
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.PrimaryKeyConstraint("source_id"),
    )
    op.create_index(op.f("ix_posts_created_at"), "posts", ["created_at"], unique=False)
    op.create_index(op.f("ix_posts_topic_id"), "posts", ["topic_id"], unique=False)
    op.create_table(
        "post_upvotes_daily",
        sa.Column("post_source_id", sa.Text(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["post_source_id"], ["posts.source_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_source_id", "day"),
    )
    op.create_table(
        "retrieval_events",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("post_source_id", sa.Text(), nullable=False),
        sa.Column("run", sa.Text(), nullable=False),
        sa.Column("agent", sa.Text(), nullable=False),
        sa.Column("tool", sa.Text(), nullable=False),
        sa.Column(
            "at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("agent IN ('report', 'tagging')", name="retrieval_agent"),
        sa.CheckConstraint("tool IN ('search', 'lookup')", name="retrieval_tool"),
        sa.ForeignKeyConstraint(["post_source_id"], ["posts.source_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("retrieval_events")
    op.drop_table("post_upvotes_daily")
    op.drop_index(op.f("ix_posts_topic_id"), table_name="posts")
    op.drop_index(op.f("ix_posts_created_at"), table_name="posts")
    op.drop_table("posts")
    op.drop_table("topic_daily_engagement")
    op.drop_table("cluster_decisions")
    op.drop_table("topics")
    op.drop_table("threads")
    op.drop_table("ingested_days")
