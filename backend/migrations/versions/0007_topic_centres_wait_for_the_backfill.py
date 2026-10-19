"""topic centres wait for the backfill

The boot seed brings topics without their centres; the worker's backfill rebuilds each
from its threads' embeddings (atlas plate 07), so until then a centre may be missing.

Revision ID: 0007
Revises: 0006
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("topics", "centroid", nullable=True)


def downgrade() -> None:
    op.alter_column("topics", "centroid", nullable=False)
