"""The boot seed's data file (atlas plate 07): one row set per table, each with its column
names written out, as gzipped JSON. Embeddings are never in it; the worker's backfill
rebuilds them."""

import gzip
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

SNAPSHOT_FORMAT = "voices-seed/1"


@dataclass(frozen=True)
class SeedTable:
    """One table's rows, each a list of values in the order of `columns`."""

    name: str
    columns: list[str]
    rows: list[list]


@dataclass(frozen=True)
class Snapshot:
    """Tables in the order they load in: a table comes after every table it points to."""

    tables: list[SeedTable]


class UnknownSnapshotFormat(Exception):
    pass


def write_snapshot(snapshot: Snapshot, path: Path) -> None:
    """Writes the same bytes for the same snapshot (no timestamp in the gzip header), so a
    snapshot written twice doesn't show as changed."""
    document = {"format": SNAPSHOT_FORMAT, "tables": [vars(table) for table in snapshot.tables]}
    encoded = json.dumps(document, separators=(",", ":"), default=_as_iso_text).encode()
    path.write_bytes(gzip.compress(encoded, mtime=0))


def read_snapshot(path: Path) -> Snapshot:
    """Reads a gzipped (`.gz`) or plain JSON snapshot. Raises UnknownSnapshotFormat for any
    other kind of file."""
    raw = path.read_bytes()
    document = json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)
    if document.get("format") != SNAPSHOT_FORMAT:
        raise UnknownSnapshotFormat(f"{path} is not a {SNAPSHOT_FORMAT} snapshot")
    return Snapshot([SeedTable(**table) for table in document["tables"]])


def _as_iso_text(value: object) -> str:
    if isinstance(value, date | datetime):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} can't go into a snapshot")
