"""A schema of its own for a database test that needs empty tables, made beside the real
ones in the same database and dropped afterwards, so the real rows are never touched."""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text

from voices.config import load_settings
from voices.db.address import sqlalchemy_url
from voices.db.models import Base


@contextmanager
def scratch_schema() -> Iterator[Engine]:
    """An engine whose tables are fresh, empty copies in a new schema (pgvector's types still
    come from `public`)."""
    url = sqlalchemy_url(load_settings().database_url)
    name = f"test_scratch_{uuid.uuid4().hex[:12]}"
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f"CREATE SCHEMA {name}"))
    scratch = create_engine(url, connect_args={"options": f"-csearch_path={name},public"})
    try:
        Base.metadata.create_all(scratch, checkfirst=False)  # the public tables are visible too
        yield scratch
    finally:
        scratch.dispose()
        with admin.begin() as connection:
            connection.execute(text(f"DROP SCHEMA {name} CASCADE"))
        admin.dispose()
