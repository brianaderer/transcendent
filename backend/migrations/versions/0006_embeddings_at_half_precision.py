"""embeddings at half precision

Posts, threads and topic centres keep their embeddings as pgvector's halfvec: two bytes
a number instead of four, so the vectors take half the space (atlas OPEN-34).

Revision ID: 0006
Revises: 0005
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

EMBEDDING_COLUMNS = [("posts", "embedding"), ("threads", "embedding"), ("topics", "centroid")]


def upgrade() -> None:
    _store_embeddings_as("halfvec(768)")


def downgrade() -> None:
    _store_embeddings_as("vector(768)")


def _store_embeddings_as(column_type: str) -> None:
    for table, column in EMBEDDING_COLUMNS:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {column_type}"
            f" USING {column}::{column_type}"
        )
