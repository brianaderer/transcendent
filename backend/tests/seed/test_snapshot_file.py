import gzip
import json
from datetime import UTC, date, datetime

import pytest

from voices.db.seed_snapshot import (
    SNAPSHOT_FORMAT,
    SeedTable,
    Snapshot,
    UnknownSnapshotFormat,
    read_snapshot,
    write_snapshot,
)


def snapshot():
    return Snapshot(
        [
            SeedTable("topics", ["id", "label", "first_seen"], [[1, "Anchors", date(1999, 1, 2)]]),
            SeedTable(
                "posts",
                ["source_id", "created_at"],
                [["test-p", datetime(1999, 1, 2, 12, tzinfo=UTC)]],
            ),
        ]
    )


def test_a_written_snapshot_reads_back_with_days_and_times_as_iso_text(tmp_path):
    path = tmp_path / "seed.json.gz"

    write_snapshot(snapshot(), path)

    assert read_snapshot(path) == Snapshot(
        [
            SeedTable("topics", ["id", "label", "first_seen"], [[1, "Anchors", "1999-01-02"]]),
            SeedTable(
                "posts", ["source_id", "created_at"], [["test-p", "1999-01-02T12:00:00+00:00"]]
            ),
        ]
    )


def test_the_file_is_gzipped_json_naming_its_format(tmp_path):
    path = tmp_path / "seed.json.gz"

    write_snapshot(snapshot(), path)

    assert json.loads(gzip.decompress(path.read_bytes()))["format"] == SNAPSHOT_FORMAT


def test_the_same_snapshot_writes_the_same_bytes_every_time(tmp_path):
    first, second = tmp_path / "a.json.gz", tmp_path / "b.json.gz"

    write_snapshot(snapshot(), first)
    write_snapshot(snapshot(), second)

    assert first.read_bytes() == second.read_bytes()


def test_a_plain_json_snapshot_reads_too(tmp_path):
    path = tmp_path / "seed.json"
    path.write_text(json.dumps({"format": SNAPSHOT_FORMAT, "tables": []}))

    assert read_snapshot(path) == Snapshot([])


def test_a_file_in_another_format_is_refused(tmp_path):
    path = tmp_path / "seed.json"
    path.write_text(json.dumps({"format": "something-else", "tables": []}))

    with pytest.raises(UnknownSnapshotFormat):
        read_snapshot(path)
