"""ingested days record why a day failed

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ingested_days", sa.Column("error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ingested_days", "error")
