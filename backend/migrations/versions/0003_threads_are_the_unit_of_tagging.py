"""threads are the unit of tagging (atlas OPEN-29)

Revision ID: 0003
Revises: 0002
"""

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "threads", sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True)
    )
    op.add_column("threads", sa.Column("topic_id", sa.BigInteger(), nullable=True))
    op.add_column("threads", sa.Column("cluster_decision_id", sa.BigInteger(), nullable=True))
    op.add_column("threads", sa.Column("stage", sa.Text(), server_default="new", nullable=False))
    op.create_check_constraint(
        "thread_stage", "threads", "stage IN ('new', 'decided_once', 'settled')"
    )
    op.create_foreign_key(None, "threads", "topics", ["topic_id"], ["id"])
    op.create_foreign_key(None, "threads", "cluster_decisions", ["cluster_decision_id"], ["id"])
    op.create_index(op.f("ix_threads_topic_id"), "threads", ["topic_id"], unique=False)
    op.drop_index(op.f("ix_posts_topic_id"), table_name="posts")
    op.drop_constraint("post_status", "posts", type_="check")
    op.drop_column("posts", "cluster_decision_id")
    op.drop_column("posts", "topic_similarity")
    op.drop_column("posts", "topic_id")
    op.drop_column("posts", "status")
    op.add_column(
        "topic_daily_engagement",
        sa.Column("revived_threads", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("topic_daily_engagement", "revived_threads")
    op.add_column("posts", sa.Column("status", sa.Text(), server_default="pending", nullable=False))
    op.add_column("posts", sa.Column("topic_id", sa.BigInteger(), nullable=True))
    op.add_column("posts", sa.Column("topic_similarity", sa.Float(), nullable=True))
    op.add_column("posts", sa.Column("cluster_decision_id", sa.BigInteger(), nullable=True))
    op.create_check_constraint("post_status", "posts", "status IN ('pending', 'tagged')")
    op.create_foreign_key(None, "posts", "topics", ["topic_id"], ["id"])
    op.create_foreign_key(None, "posts", "cluster_decisions", ["cluster_decision_id"], ["id"])
    op.create_index(op.f("ix_posts_topic_id"), "posts", ["topic_id"], unique=False)
    op.drop_index(op.f("ix_threads_topic_id"), table_name="threads")
    op.drop_constraint("thread_stage", "threads", type_="check")
    op.drop_column("threads", "stage")
    op.drop_column("threads", "cluster_decision_id")
    op.drop_column("threads", "topic_id")
    op.drop_column("threads", "embedding")
