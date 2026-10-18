"""Needs a real database, so it is marked `database` and left out of the default run.

Run it with the stack up: docker compose run --rm api pytest -m database
"""

import psycopg
import pytest
from alembic import command

from voices.config import load_settings
from voices.db.setup import alembic_config


def database_is_up(database_url: str) -> bool:
    try:
        psycopg.connect(database_url, connect_timeout=2).close()
        return True
    except psycopg.OperationalError:
        return False


@pytest.mark.database
def test_the_migrations_match_the_models():
    database_url = load_settings().database_url
    if not database_is_up(database_url):
        pytest.skip("no database reachable")

    command.check(alembic_config(database_url))
