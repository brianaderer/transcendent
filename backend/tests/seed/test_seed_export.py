"""Needs a real database: docker compose run --rm api pytest -m database. The rows are made in
a scratch schema, so the real rows are never touched."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import insert, select

from tests.scratch_schema import scratch_schema
from voices.db.models import (
    EMBEDDING_DIMENSIONS,
    ClusterDecision,
    IngestedDay,
    Post,
    Thread,
    Topic,
    TopicDailyEngagement,
)
from voices.db.seed_export import PROMPT_LEFT_OUT, export_seed, snapshot_of
from voices.db.seed_load import load_seed

pytestmark = pytest.mark.database

DAY = date(1999, 1, 2)
AT = datetime(1999, 1, 2, 12, tzinfo=UTC)
VECTOR = [0.5] * EMBEDDING_DIMENSIONS


def topic(topic_id, label):
    return {
        "id": topic_id,
        "label": label,
        "description": "d",
        "keywords": ["k"],
        "centroid": VECTOR,
        "first_seen": DAY,
        "last_seen": DAY,
    }


def decision(decision_id, topic_id):
    return {
        "id": decision_id,
        "day": DAY,
        "decision": "mint",
        "topic_id": topic_id,
        "reason": "r",
        "prompt": "the whole prompt",
        "model": "m",
    }


def fill(engine):
    """Topic 1 has a thread; topic 2 has none left, so its centre couldn't be rebuilt."""
    with engine.begin() as connection:
        connection.execute(insert(Topic), [topic(2, "Gone"), topic(1, "Anchors")])
        connection.execute(insert(ClusterDecision), [decision(11, 1), decision(12, 2)])
        connection.execute(
            insert(Thread),
            [
                {
                    "source_id": "test-b",
                    "title": "Which anchor?",
                    "created_at": AT,
                    "first_seen_on": DAY,
                    "embedding": VECTOR,
                    "topic_id": 1,
                    "cluster_decision_id": 11,
                    "stage": "settled",
                }
            ],
        )
        connection.execute(
            insert(Post),
            [
                {
                    "source_id": source_id,
                    "thread_source_id": "test-b",
                    "kind": kind,
                    "author": "salty",
                    "created_at": AT,
                    "body": "text",
                    "embedding": VECTOR,
                }
                for source_id, kind in [("test-b", "post"), ("test-a", "comment")]
            ],
        )
        connection.execute(
            insert(TopicDailyEngagement),
            [{"topic_id": 1, "day": DAY, "posts": 1}, {"topic_id": 2, "day": DAY, "posts": 3}],
        )
        connection.execute(insert(IngestedDay).values(day=DAY, status="done", counts={"n": 1}))


@pytest.fixture
def engine():
    with scratch_schema() as scratch:
        fill(scratch)
        yield scratch


def seeded(engine):
    with engine.connect() as connection:
        return {table.name: table for table in snapshot_of(connection).tables}


def column_values(table, column):
    position = table.columns.index(column)
    return [row[position] for row in table.rows]


def test_no_embedding_or_centre_is_written(engine):
    tables = seeded(engine)

    every_column = {column for table in tables.values() for column in table.columns}
    assert "embedding" not in every_column
    assert "centroid" not in every_column


def test_a_decision_keeps_its_record_but_not_its_prompt(engine):
    decisions = seeded(engine)["cluster_decisions"]

    assert column_values(decisions, "id") == [11, 12]
    assert set(column_values(decisions, "prompt")) == {PROMPT_LEFT_OUT}


def test_a_topic_with_no_threads_is_left_out_with_its_engagement(engine):
    tables = seeded(engine)

    assert column_values(tables["topics"], "id") == [1]
    assert column_values(tables["topic_daily_engagement"], "topic_id") == [1]
    assert column_values(tables["cluster_decisions"], "topic_id") == [1, None]


def test_rows_are_in_a_fixed_order(engine):
    assert column_values(seeded(engine)["posts"], "source_id") == ["test-a", "test-b"]


def test_tables_come_in_the_order_they_load_in(engine):
    assert list(seeded(engine)) == [
        "topics",
        "cluster_decisions",
        "threads",
        "posts",
        "post_upvotes_daily",
        "topic_daily_engagement",
        "retrieval_events",
        "noise_threads",
        "ingested_days",
    ]


def test_an_exported_seed_loads_into_an_empty_database_as_it_was(engine, tmp_path):
    path = tmp_path / "seed.json.gz"
    export_seed(engine, path)

    with scratch_schema() as empty:
        with empty.begin() as connection:
            load_seed(connection, path)
        with empty.connect() as connection:
            posts = connection.execute(select(Post.source_id, Post.author, Post.created_at)).all()
            day = connection.execute(select(IngestedDay.day, IngestedDay.counts)).one()
    assert sorted(posts) == [("test-a", "salty", AT), ("test-b", "salty", AT)]
    assert tuple(day) == (DAY, {"n": 1})
