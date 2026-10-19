"""Needs a real database: docker compose run --rm api pytest -m database"""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import delete, insert

from voices.config import load_settings
from voices.db.explore_store import EXCERPT_CHARACTERS, ExploreStore
from voices.db.models import (
    DAY_DONE,
    DAY_RUNNING,
    EMBEDDING_DIMENSIONS,
    IngestedDay,
    Post,
    Thread,
    Topic,
    TopicDailyEngagement,
)
from voices.db.store import connect_store

pytestmark = pytest.mark.database

DAY = date(1999, 1, 4)  # far outside any real history, so the test can't touch real rows
AT = datetime(1999, 1, 4, 23, 30, tzinfo=UTC)
NEXT = datetime(1999, 1, 5, 0, 30, tzinfo=UTC)
# Ledger days later than any real one, so they decide the latest day while the test runs.
LEDGER_DONE, LEDGER_RUNNING = date(2999, 1, 4), date(2999, 1, 5)
VECTOR = [1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 1)


def post(source_id, at, body="Carry a spare impeller.", kind="comment"):
    return {
        "source_id": source_id,
        "thread_source_id": "test-t",
        "kind": kind,
        "author": "salty",
        "created_at": at,
        "body": body,
        "embedding": VECTOR,
    }


@pytest.fixture
def store():
    engine = connect_store(load_settings().database_url).engine
    with engine.begin() as connection:
        topic_id = connection.scalar(
            insert(Topic)
            .values(
                label="test-impellers",
                description="Engine impellers.",
                centroid=VECTOR,
                first_seen=DAY,
                last_seen=DAY,
            )
            .returning(Topic.id)
        )
        connection.execute(
            insert(Thread),
            [
                {
                    "source_id": "test-t",
                    "title": "Impellers",
                    "created_at": AT,
                    "first_seen_on": DAY,
                    "topic_id": topic_id,
                }
            ],
        )
        connection.execute(
            insert(Post),
            [
                post("test-t", AT, body="", kind="post"),
                post("test-c", AT, body="x" * 500),
                post("test-n", NEXT),
            ],
        )
        connection.execute(
            insert(TopicDailyEngagement),
            [{"topic_id": topic_id, "day": DAY, "posts": 1, "comments": 2, "upvotes": 3}],
        )
        connection.execute(
            insert(IngestedDay),
            [
                {"day": LEDGER_DONE, "status": DAY_DONE},
                {"day": LEDGER_RUNNING, "status": DAY_RUNNING},
            ],
        )
    yield ExploreStore(engine), topic_id
    with engine.begin() as connection:
        connection.execute(delete(TopicDailyEngagement).where(TopicDailyEngagement.day == DAY))
        connection.execute(delete(Post).where(Post.source_id.like("test-%")))
        connection.execute(delete(Thread).where(Thread.source_id.like("test-%")))
        connection.execute(delete(Topic).where(Topic.label.like("test-%")))
        connection.execute(
            delete(IngestedDay).where(IngestedDay.day.in_([LEDGER_DONE, LEDGER_RUNNING]))
        )


def test_posts_are_counted_by_the_day_they_were_written_in_utc(store):
    explore, _ = store

    counts = {c.day: c.posts for c in explore.posts_per_day()}

    assert (counts[DAY], counts[date(1999, 1, 5)]) == (2, 1)


def test_a_topics_engagement_is_its_posts_comments_and_upvotes(store):
    explore, topic_id = store

    [row] = explore.topic_days(DAY, DAY)

    assert (row.topic_id, row.engagement, row.posts) == (topic_id, 6, 3)


def test_a_ranges_posts_come_with_their_thread_and_topic_and_end_with_its_last_day(store):
    explore, topic_id = store

    posts = explore.posts_in(DAY, DAY)

    assert [p.id for p in posts] == ["test-c", "test-t"]  # same time: by id
    assert {p.thread_topic_id for p in posts} == {topic_id}


def test_a_posts_embedding_comes_back_as_the_list_of_floats_it_was_saved_as(store):
    explore, _ = store

    [post, *_] = explore.posts_in(DAY, DAY)

    assert post.embedding == VECTOR  # each value exact at half precision
    assert all(type(value) is float for value in post.embedding)


def test_a_post_with_no_text_is_shown_by_its_title_and_long_text_is_cut(store):
    explore, _ = store

    excerpts = {p.id: p.excerpt for p in explore.posts_in(DAY, DAY)}

    assert excerpts["test-t"] == "Impellers"
    assert len(excerpts["test-c"]) == EXCERPT_CHARACTERS


def test_topics_are_read_by_id(store):
    explore, topic_id = store

    [info] = explore.topics([topic_id])

    assert (info.label, info.first_seen) == ("test-impellers", DAY)


def test_the_latest_day_counts_only_finished_days(store):
    explore, _ = store

    assert explore.latest_day() == LEDGER_DONE
