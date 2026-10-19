"""Needs a real database: docker compose run --rm api pytest -m database. The rows are made in
a scratch schema, so the real rows are never touched."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import insert, select

from tests.scratch_schema import scratch_schema
from voices.backfill.backfill import PostText, Tally, UnencodedThread
from voices.db.backfill_store import BackfillStore
from voices.db.models import EMBEDDING_DIMENSIONS, Post, Thread, Topic

pytestmark = pytest.mark.database

DAY = date(1999, 1, 2)
AT = datetime(1999, 1, 2, 12, tzinfo=UTC)


def vector(lead):
    return [lead, 1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 2)


def fill(engine):
    with engine.begin() as connection:
        connection.execute(
            insert(Topic),
            [
                {
                    "id": 1,
                    "label": "Seeded",
                    "description": "",
                    "centroid": None,
                    "first_seen": DAY,
                    "last_seen": DAY,
                },
                {
                    "id": 2,
                    "label": "Kept",
                    "description": "",
                    "centroid": vector(9.0),
                    "first_seen": DAY,
                    "last_seen": DAY,
                },
            ],
        )
        connection.execute(
            insert(Thread),
            [
                {
                    "source_id": "test-a",
                    "title": "A",
                    "created_at": AT,
                    "first_seen_on": DAY,
                    "topic_id": 1,
                    "stage": "settled",
                    "embedding": vector(1.0),
                },
                {
                    "source_id": "test-b",
                    "title": "B",
                    "created_at": AT,
                    "first_seen_on": DAY,
                    "topic_id": 1,
                    "stage": "decided_once",
                    "embedding": vector(3.0),
                },
                {
                    "source_id": "test-c",
                    "title": "C",
                    "created_at": AT,
                    "first_seen_on": DAY,
                    "topic_id": 2,
                    "stage": "settled",
                    "embedding": None,
                },
            ],
        )
        connection.execute(
            insert(Post),
            [
                {
                    "source_id": source_id,
                    "thread_source_id": "test-a",
                    "kind": "comment",
                    "author": "salty",
                    "created_at": AT,
                    "body": body,
                    "embedding": embedding,
                }
                for source_id, body, embedding in [
                    ("test-p3", "three", None),
                    ("test-p1", "one", None),
                    ("test-p2", "two", vector(1.0)),
                ]
            ],
        )


@pytest.fixture
def store():
    with scratch_schema() as engine:
        fill(engine)
        yield BackfillStore(engine)


def test_each_kind_is_tallied_as_filled_of_all(store):
    assert store.posts_tally() == Tally(done=1, total=3)
    assert store.threads_tally() == Tally(done=2, total=3)
    assert store.topics_tally() == Tally(done=1, total=2)


def test_posts_without_embeddings_come_in_id_order_a_batch_at_a_time(store):
    assert store.posts_without_embeddings(1) == [PostText("test-p1", "one")]
    assert [p.source_id for p in store.posts_without_embeddings(5)] == ["test-p1", "test-p3"]


def test_saved_post_embeddings_fill_the_posts(store):
    store.save_post_embeddings({"test-p1": vector(2.0), "test-p3": vector(2.0)})

    assert store.posts_tally() == Tally(done=3, total=3)
    assert store.posts_without_embeddings(5) == []


def test_threads_without_embeddings_come_with_their_first_day_and_stage(store):
    assert store.threads_without_embeddings(5) == [UnencodedThread("test-c", DAY, "settled")]


def test_threads_are_read_and_saved_the_way_tagging_does(store):
    (thread,) = store.threads_as_of(DAY, ["test-c"])
    store.save_thread_embeddings({thread.source_id: vector(5.0)})

    assert thread.post == "C"
    assert store.threads_tally() == Tally(done=3, total=3)


def test_a_missing_centre_becomes_the_average_of_its_threads_and_others_stay(store):
    store.rebuild_missing_centres()

    with store.engine.connect() as connection:
        centres = dict(connection.execute(select(Topic.id, Topic.centroid)).all())
    assert centres[1].to_list()[:2] == [2.0, 1.0]
    assert centres[2].to_list()[0] == 9.0
