"""seed snapshot

Revision ID: 0008
Revises: 0007
"""

from pathlib import Path

from alembic import op

from voices.db.seed_load import load_seed

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    load_seed(op.get_bind(), Path(__file__).with_name("0008_seed_snapshot.json.gz"))


def downgrade() -> None:
    """The seeded rows stay: they are data the app has since built on."""
