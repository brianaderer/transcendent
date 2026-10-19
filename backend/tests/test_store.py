"""Needs a real database: run with the stack up, docker compose run --rm api pytest -m database"""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import delete, select

from voices.config import load_settings
from voices.db.models import EMBEDDING_DIMENSIONS, IngestedDay, Post, PostUpvotesDaily, Thread
from voices.db.store import connect_store
from voices.ingestion.day import DayBatch, EmbeddedItem, NewThread
from voices.ingestion.items import Item

pytestmark = pytest.mark.database

DAY = date(1999, 1, 2)  # far outside any real history, so the test can't touch real rows
AT = datetime(1999, 1, 2, 12, tzinfo=UTC)
VECTOR = [0.0] * EMBEDDING_DIMENSIONS
OTHER_DAY = date(1999, 1, 3)


@pytest.fixture
def store():
    store = connect_store(load_settings().database_url)
    yield store
    with store.engine.begin() as connection:
        connection.execute(
            delete(PostUpvotesDaily).where(PostUpvotesDaily.post_source_id.like("test-%"))
        )
        connection.execute(delete(Post).where(Post.source_id.like("test-%")))
        connection.execute(delete(Thread).where(Thread.source_id.like("test-%")))
        connection.execute(delete(IngestedDay).where(IngestedDay.day == DAY))


def batch(upvotes):
    post = Item("test-p", "test-p", "post", "salty", AT, "", 3, None, title="Which anchor?")
    return DayBatch(
        DAY, [NewThread("test-p", "Which anchor?", AT)], [EmbeddedItem(post, VECTOR)], upvotes
    )


def upvotes_of(store, post_id):
    with store.engine.connect() as connection:
        total = connection.scalar(select(Post.upvotes).where(Post.source_id == post_id))
        daily = dict(
            connection.execute(
                select(PostUpvotesDaily.day, PostUpvotesDaily.count).where(
                    PostUpvotesDaily.post_source_id == post_id
                )
            ).all()
        )
    return total, daily


def test_a_saved_day_can_be_found_again_and_saving_it_twice_adds_nothing(store):
    store.save_day(batch({}))
    store.save_day(batch({}))

    assert store.known_post_ids(["test-p", "test-missing"]) == {"test-p"}
    assert store.known_thread_ids(["test-p"]) == {"test-p"}


def test_a_thread_is_first_seen_on_the_day_it_is_saved_not_the_day_it_started(store):
    old = NewThread("test-old", "Old thread", datetime(1990, 5, 1, tzinfo=UTC))
    store.save_day(DayBatch(DAY, [old], [], {}))

    with store.engine.connect() as connection:
        first_seen = connection.scalar(
            select(Thread.first_seen_on).where(Thread.source_id == "test-old")
        )
    assert first_seen == DAY


def test_saving_the_same_day_twice_does_not_double_its_upvotes(store):
    store.save_day(batch({"test-p": 2}))
    store.save_day(batch({"test-p": 2}))

    assert upvotes_of(store, "test-p") == (2, {DAY: 2})


def test_upvotes_from_different_days_add_up(store):
    store.save_day(batch({"test-p": 2}))
    store.save_day(DayBatch(OTHER_DAY, [], [], {"test-p": 1}))

    assert upvotes_of(store, "test-p") == (3, {DAY: 2, OTHER_DAY: 1})


def test_the_ledger_remembers_done_days_and_why_a_day_failed(store):
    store.mark_running(DAY)
    store.mark_failed(DAY, "archive down")
    assert DAY not in store.done_days()

    store.mark_running(DAY)
    store.mark_done(DAY, {"stored": 1})
    assert DAY in store.done_days()


def test_redoing_a_day_that_no_longer_upvotes_a_post_takes_that_days_upvotes_away(store):
    store.save_day(batch({"test-p": 2}))
    store.save_day(DayBatch(DAY, [], [], {}))

    assert upvotes_of(store, "test-p") == (0, {})
