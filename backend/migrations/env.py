"""How Alembic connects: the address comes from DATABASE_URL, the tables from voices.db.models."""

from alembic import context
from sqlalchemy import create_engine

from voices.config import load_settings
from voices.db.address import sqlalchemy_url
from voices.db.models import Base


def database_address() -> str:
    """setup.py passes the address in; running the alembic command directly falls back to
    DATABASE_URL."""
    return context.config.get_main_option("sqlalchemy.url") or sqlalchemy_url(
        load_settings().database_url
    )


def run_migrations() -> None:
    with create_engine(database_address()).connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
