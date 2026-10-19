"""threads deleted as noise are remembered

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "noise_threads",
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("deleted_on", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("source_id"),
    )


def downgrade() -> None:
    op.drop_table("noise_threads")
