"""threads count their days from when they were first seen

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# A thread already stored was first seen with its earliest stored post or comment.
BACKFILL = """
UPDATE threads t SET first_seen_on = coalesce(
    (SELECT min((p.created_at AT TIME ZONE 'UTC')::date) FROM posts p
     WHERE p.thread_source_id = t.source_id),
    (t.created_at AT TIME ZONE 'UTC')::date)
"""


def upgrade() -> None:
    op.add_column("threads", sa.Column("first_seen_on", sa.Date(), nullable=True))
    op.execute(BACKFILL)
    op.alter_column("threads", "first_seen_on", nullable=False)


def downgrade() -> None:
    op.drop_column("threads", "first_seen_on")
