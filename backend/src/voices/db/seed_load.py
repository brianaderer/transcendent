"""Loads the boot seed's data file into an empty database (atlas plate 07).

Called by the seed migration, the last one, with the data file kept beside it:

    def upgrade() -> None:
        load_seed(op.get_bind(), Path(__file__).with_name("NNNN_seed_snapshot.json.gz"))

Rows go in with plain SQL under the column names the file carries, not through the table
models, so the snapshot loads as it was taken. Ids are kept, and every id counter is moved
past the loaded rows so the next new topic, decision or retrieval doesn't collide with one.
"""

import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Connection, text

from voices.db.seed_snapshot import SeedTable, read_snapshot
from voices.log import log_event

ROWS_PER_INSERT = 1000
SQL_NAME = re.compile(r"[a-z_]+")  # the file's table and column names go into SQL as written

logger = logging.getLogger(__name__)


class UnsafeName(Exception):
    pass


def load_seed(connection: Connection, data_file: Path) -> None:
    """Loads the snapshot unless the database already holds a day, so a database that was
    filled by its own catch-up, or seeded before, is left as it is."""
    if _has_any_day(connection):
        log_event(logger, "seed.skipped", reason="the database already has days")
        return
    snapshot = read_snapshot(data_file)
    for table in snapshot.tables:
        _insert_rows(connection, table)
    _move_id_counters_past_loaded_rows(connection, [table.name for table in snapshot.tables])
    log_event(logger, "seed.loaded", rows={t.name: len(t.rows) for t in snapshot.tables})


def _has_any_day(connection: Connection) -> bool:
    return connection.scalar(text("SELECT EXISTS (SELECT 1 FROM ingested_days)"))


def _insert_rows(connection: Connection, table: SeedTable) -> None:
    """Postgres turns each JSON row into the table's own row type, so days, times, arrays and
    JSON columns arrive with their proper types; columns the file doesn't name take their
    defaults."""
    name, columns = _safe(table.name), ", ".join(_safe(column) for column in table.columns)
    statement = text(
        f"INSERT INTO {name} ({columns}) SELECT {columns}"
        f" FROM json_populate_recordset(NULL::{name}, CAST(:rows AS json))"
    )
    for chunk in _chunks(table.rows, ROWS_PER_INSERT):
        records = [dict(zip(table.columns, row, strict=True)) for row in chunk]
        connection.execute(statement, {"rows": json.dumps(records)})


def _move_id_counters_past_loaded_rows(connection: Connection, table_names: list[str]) -> None:
    counted = connection.execute(
        text(
            "SELECT table_name, column_name FROM information_schema.columns"
            " WHERE table_schema = current_schema() AND table_name = ANY(:names)"
            " AND column_default LIKE 'nextval(%'"
        ),
        {"names": table_names},
    ).all()
    for table_name, column_name in counted:
        table, column = _safe(table_name), _safe(column_name)
        connection.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence(:table, :column),"
                f" coalesce(max({column}), 0) + 1, false) FROM {table}"
            ),
            {"table": table, "column": column},
        )


def _chunks(rows: list[list], size: int) -> Iterator[list[list]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def _safe(name: str) -> str:
    if not SQL_NAME.fullmatch(name):
        raise UnsafeName(f"{name!r} can't be used as a table or column name")
    return name
