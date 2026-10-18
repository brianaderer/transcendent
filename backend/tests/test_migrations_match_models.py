"""Needs a real database, so it is marked `database` and left out of the default run.

Run it with the stack up: docker compose run --rm api pytest -m database
"""

import pytest
from alembic import command

from voices.config import load_settings
from voices.db.setup import alembic_config


@pytest.mark.database
def test_the_migrations_match_the_models():
    command.check(alembic_config(load_settings().database_url))
