"""How Alembic connects: the address comes from DATABASE_URL, the tables from voices.db.models."""

from alembic import context
from sqlalchemy import create_engine

from voices.config import load_settings
from voices.db.models import Base
from voices.db.setup import sqlalchemy_url


def database_address() -> str:
    return context.config.get_main_option("sqlalchemy.url") or sqlalchemy_url(
        load_settings().database_url
    )


def run_migrations() -> None:
    with create_engine(database_address()).connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
