import pytest
from alembic.script import ScriptDirectory

from voices.db.address import sqlalchemy_url
from voices.db.setup import DatabaseNotReady, alembic_config, retry_connecting


def test_retrying_returns_as_soon_as_an_attempt_succeeds():
    attempts = iter([ConnectionError(), ConnectionError(), "connected"])

    def connect():
        outcome = next(attempts)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    assert retry_connecting(connect, tries=5, pause_seconds=0) == "connected"


def test_retrying_gives_up_after_the_last_try():
    def connect():
        raise ConnectionError("refused")

    with pytest.raises(DatabaseNotReady):
        retry_connecting(connect, tries=3, pause_seconds=0)


def test_retrying_with_no_tries_gives_up_at_once():
    with pytest.raises(DatabaseNotReady):
        retry_connecting(lambda: "never called", tries=0, pause_seconds=0)


def test_the_database_address_names_the_driver_sqlalchemy_should_use():
    url = sqlalchemy_url("postgresql://voices:voices@postgres:5432/voices")

    assert url == "postgresql+psycopg://voices:voices@postgres:5432/voices"


def test_alembic_finds_its_settings_and_exactly_one_latest_migration():
    config = alembic_config("postgresql://u:p@nowhere/db")

    assert len(ScriptDirectory.from_config(config).get_heads()) == 1
