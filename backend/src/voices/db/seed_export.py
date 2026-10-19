"""Writes the boot seed's data file from the database (atlas plate 07).

    python -m voices.db.seed_export <path>

Every table is read with its columns written out here, not taken from the table models, so
the file is a fixed snapshot of the schema it was taken on. Embeddings and topic centres are
left out (the worker's backfill rebuilds them), and so is each tagging decision's prompt,
which is the bulk of the data and only there for tracing. Topics with no threads are left
out too: their centre can't be rebuilt.
"""

import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import Connection, Engine, create_engine, text

from voices.config import load_settings
from voices.db.address import sqlalchemy_url
from voices.db.seed_snapshot import SeedTable, Snapshot, write_snapshot

PROMPT_LEFT_OUT = "(left out of the seed)"  # the column can't be empty, and this says why
TOPICS_WITH_THREADS = "SELECT topic_id FROM threads WHERE topic_id IS NOT NULL"


def published_author(author: str) -> str:
    """Every author name passes through here on its way into the seed. Names are kept as
    they are until Brian decides about usernames in a public repo (atlas OPEN-37); hiding
    them is a change to this one line."""
    return author


@dataclass(frozen=True)
class TableExport:
    """How one table is read for the seed: each column with the SQL that gives its value,
    the rows to take and their order, and any value to pass through a function first."""

    name: str
    columns: dict[str, str]
    rows: str
    published: dict[str, Callable[[str], str]] = field(default_factory=dict)


def _as_stored(*names: str) -> dict[str, str]:
    return {name: name for name in names}


SEED_TABLES = (
    TableExport(
        "topics",
        _as_stored("id", "label", "description", "keywords", "first_seen", "last_seen"),
        f"FROM topics WHERE id IN ({TOPICS_WITH_THREADS}) ORDER BY id",
    ),
    TableExport(
        "cluster_decisions",
        {
            **_as_stored("id", "day", "decision"),
            "topic_id": f"CASE WHEN topic_id IN ({TOPICS_WITH_THREADS}) THEN topic_id END",
            **_as_stored("reason", "candidate_tags"),
            "prompt": f"'{PROMPT_LEFT_OUT}'",
            **_as_stored("model"),
        },
        "FROM cluster_decisions ORDER BY id",
    ),
    TableExport(
        "threads",
        _as_stored(
            "source_id",
            "title",
            "created_at",
            "first_seen_on",
            "topic_id",
            "cluster_decision_id",
            "stage",
        ),
        "FROM threads ORDER BY source_id",
    ),
    TableExport(
        "posts",
        _as_stored(
            "source_id",
            "thread_source_id",
            "kind",
            "author",
            "created_at",
            "body",
            "reddit_score",
            "upvotes",
            "parent_source_id",
        ),
        "FROM posts ORDER BY source_id",
        published={"author": published_author},
    ),
    TableExport(
        "post_upvotes_daily",
        _as_stored("post_source_id", "day", "count"),
        "FROM post_upvotes_daily ORDER BY post_source_id, day",
    ),
    TableExport(
        "topic_daily_engagement",
        _as_stored(
            "topic_id",
            "day",
            "posts",
            "comments",
            "upvotes",
            "unique_authors",
            "new_threads",
            "revived_threads",
            "unanswered_questions",
        ),
        f"FROM topic_daily_engagement WHERE topic_id IN ({TOPICS_WITH_THREADS}) "
        "ORDER BY topic_id, day",
    ),
    TableExport(
        "retrieval_events",
        _as_stored("id", "post_source_id", "run", "agent", "tool", "at"),
        "FROM retrieval_events ORDER BY id",
    ),
    TableExport(
        "noise_threads",
        _as_stored("source_id", "deleted_on"),
        "FROM noise_threads ORDER BY source_id",
    ),
    TableExport(
        "ingested_days",
        _as_stored("day", "status", "counts", "started_at", "finished_at", "error"),
        "FROM ingested_days ORDER BY day",
    ),
)


def snapshot_of(connection: Connection) -> Snapshot:
    """Every seeded table, in the order they load in."""
    return Snapshot([_table_snapshot(connection, table) for table in SEED_TABLES])


def export_seed(engine: Engine, path: Path) -> None:
    with engine.connect() as connection:
        write_snapshot(snapshot_of(connection), path)


def _table_snapshot(connection: Connection, table: TableExport) -> SeedTable:
    selected = ", ".join(f"{sql} AS {name}" for name, sql in table.columns.items())
    rows = connection.execute(text(f"SELECT {selected} {table.rows}")).mappings()
    columns = list(table.columns)
    return SeedTable(table.name, columns, [_published_row(table, row) for row in rows])


def _published_row(table: TableExport, row) -> list:
    return [table.published.get(column, _unchanged)(row[column]) for column in table.columns]


def _unchanged(value):
    return value


def main(arguments: list[str]) -> None:
    if len(arguments) != 1:
        sys.exit("usage: python -m voices.db.seed_export <path>")
    engine = create_engine(sqlalchemy_url(load_settings().database_url))
    export_seed(engine, Path(arguments[0]))


if __name__ == "__main__":
    main(sys.argv[1:])
