"""First-start setup: wait for Postgres, then bring the tables up to date with Alembic.

Run by the `setup` service in Docker Compose on every start (atlas plate 04). Migrations
that have already run are skipped, so a second start changes nothing.
"""

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import psycopg
from alembic import command
from alembic.config import Config

from voices.config import load_settings
from voices.log import configure_logging, log_event

ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"
CONNECT_TRIES = 30
PAUSE_BETWEEN_TRIES_SECONDS = 1.0

logger = logging.getLogger(__name__)
T = TypeVar("T")


class DatabaseNotReady(Exception):
    pass


def wait_for_database_then_migrate(database_url: str) -> None:
    connection = retry_connecting(
        lambda: psycopg.connect(database_url),
        tries=CONNECT_TRIES,
        pause_seconds=PAUSE_BETWEEN_TRIES_SECONDS,
    )
    connection.close()
    command.upgrade(alembic_config(database_url), "head")
    log_event(logger, "setup.tables_ready")


def retry_connecting(connect: Callable[[], T], tries: int, pause_seconds: float) -> T:
    last_error: Exception | None = None
    for attempt in range(1, tries + 1):
        try:
            return connect()
        except (ConnectionError, psycopg.OperationalError) as error:
            last_error = error
            log_event(logger, "setup.database_not_ready", attempt=attempt)
            time.sleep(pause_seconds)
    raise DatabaseNotReady(f"no database after {tries} tries") from last_error


def alembic_config(database_url: str) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", sqlalchemy_url(database_url))
    return config


def sqlalchemy_url(database_url: str) -> str:
    """SQLAlchemy needs the driver named in the address; the rest of the code doesn't."""
    return database_url.replace("postgresql://", "postgresql+psycopg://", 1)


def main() -> None:
    settings = load_settings()
    configure_logging(settings.service_name, settings.log_dir)
    wait_for_database_then_migrate(settings.database_url)


if __name__ == "__main__":
    main()
