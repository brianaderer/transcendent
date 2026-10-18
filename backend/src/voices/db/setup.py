"""First-start setup: wait for Postgres, then create the tables if they don't exist.

Run once by the `setup` service in Docker Compose (atlas plate 04).
"""

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import psycopg

from voices.config import load_settings
from voices.log import configure_logging, log_event

SCHEMA_FILE = Path(__file__).with_name("schema.sql")
CONNECT_TRIES = 30
PAUSE_BETWEEN_TRIES_SECONDS = 1.0

logger = logging.getLogger(__name__)
T = TypeVar("T")


class DatabaseNotReady(Exception):
    pass


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


def wait_for_database_then_create_tables(database_url: str) -> None:
    connection = retry_connecting(
        lambda: psycopg.connect(database_url),
        tries=CONNECT_TRIES,
        pause_seconds=PAUSE_BETWEEN_TRIES_SECONDS,
    )
    with connection:
        connection.execute(SCHEMA_FILE.read_text())
    log_event(logger, "setup.tables_ready")


def main() -> None:
    settings = load_settings()
    configure_logging(settings.service_name, settings.log_dir)
    wait_for_database_then_create_tables(settings.database_url)


if __name__ == "__main__":
    main()
