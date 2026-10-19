"""Needs a real database: docker compose run --rm api pytest -m database. Each test loads into
its own scratch schema, so the real rows are never touched."""

import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import func, insert, select

from tests.scratch_schema import scratch_schema
from voices.db.models import (
    ClusterDecision,
    IngestedDay,
    Post,
    RetrievalEvent,
    Thread,
    Topic,
    TopicDailyEngagement,
)
from voices.db.seed_load import UnsafeName, load_seed
from voices.db.seed_snapshot import SNAPSHOT_FORMAT

pytestmark = pytest.mark.database

FIXTURE = Path(__file__).parent.parent / "fixtures" / "seed_snapshot.json"


@pytest.fixture
def engine():
    with scratch_schema() as scratch:
        yield scratch


def load(engine, data_file=FIXTURE):
    with engine.begin() as connection:
        load_seed(connection, data_file)


def count(engine, table):
    with engine.connect() as connection:
        return connection.scalar(select(func.count()).select_from(table))


def test_every_table_in_the_file_is_loaded_with_its_ids(engine):
    load(engine)

    with engine.connect() as connection:
        topic_ids = set(connection.scalars(select(Topic.id)))
        thread_topics = dict(connection.execute(select(Thread.source_id, Thread.topic_id)).all())
    assert topic_ids == {5, 9}
    assert thread_topics == {"test-a": 5, "test-b": 9}
    assert count(engine, Post) == 3
    assert count(engine, TopicDailyEngagement) == 2
    assert count(engine, IngestedDay) == 2


def test_rows_arrive_with_their_types(engine):
    load(engine)

    with engine.connect() as connection:
        topic = connection.execute(select(Topic).where(Topic.id == 5)).one()
        tags = connection.scalar(
            select(ClusterDecision.candidate_tags).where(ClusterDecision.id == 4)
        )
        reply = connection.execute(select(Post).where(Post.source_id == "test-a1")).one()
    assert topic.keywords == ["anchor", "holding"]
    assert topic.first_seen == date(1999, 1, 1)
    assert topic.centroid is None
    assert tags == [{"topic_id": 5, "label": "Anchors"}]
    assert reply.parent_source_id == "test-a"
    assert reply.created_at.hour == 11
    assert reply.embedding is None


def test_the_next_new_topic_decision_and_retrieval_come_after_the_loaded_ones(engine):
    load(engine)

    with engine.begin() as connection:
        topic = connection.scalar(
            insert(Topic)
            .values(
                label="New", description="", first_seen=date(1999, 1, 4), last_seen=date(1999, 1, 4)
            )
            .returning(Topic.id)
        )
        decision = connection.scalar(
            insert(ClusterDecision)
            .values(day=date(1999, 1, 4), decision="noise", reason="", prompt="", model="m")
            .returning(ClusterDecision.id)
        )
        retrieval = connection.scalar(
            insert(RetrievalEvent)
            .values(post_source_id="test-a", run="r", agent="report", tool="search")
            .returning(RetrievalEvent.id)
        )
    assert (topic, decision, retrieval) == (10, 5, 9)


def test_a_database_that_already_has_days_is_left_as_it_is(engine):
    with engine.begin() as connection:
        connection.execute(insert(IngestedDay).values(day=date(1999, 3, 1), status="done"))

    load(engine)

    assert count(engine, Topic) == 0
    assert count(engine, IngestedDay) == 1


def test_loading_twice_loads_once(engine):
    load(engine)
    load(engine)

    assert count(engine, Post) == 3


def test_a_table_name_that_is_not_a_plain_name_is_refused(engine, tmp_path):
    bad = tmp_path / "bad.json"
    table = {"name": "topics; drop", "columns": [], "rows": [[]]}
    bad.write_text(json.dumps({"format": SNAPSHOT_FORMAT, "tables": [table]}))

    with pytest.raises(UnsafeName):
        load(engine, bad)
