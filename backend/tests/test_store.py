"""Needs a real database: run with the stack up, docker compose run --rm api pytest -m database"""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import delete, select

from voices.config import load_settings
from voices.db.models import EMBEDDING_DIMENSIONS, IngestedDay, Post, PostUpvotesDaily, Thread
from voices.db.store import connect_store
from voices.ingestion.day import DayBatch, EmbeddedItem
from voices.ingestion.day import Thread as NewThread
from voices.ingestion.items import Item

pytestmark = pytest.mark.database

DAY = date(1999, 1, 2)  # far outside any real history, so the test can't touch real rows
AT = datetime(1999, 1, 2, 12, tzinfo=UTC)
VECTOR = [0.0] * EMBEDDING_DIMENSIONS


@pytest.fixture
def store():
    store = connect_store(load_settings().database_url)
    yield store
    with store.engine.begin() as connection:
        connection.execute(delete(PostUpvotesDaily).where(PostUpvotesDaily.day == DAY))
        connection.execute(delete(Post).where(Post.source_id.like("test-%")))
        connection.execute(delete(Thread).where(Thread.source_id.like("test-%")))
        connection.execute(delete(IngestedDay).where(IngestedDay.day == DAY))


def batch(upvotes):
    post = Item("test-p", "test-p", "post", "salty", AT, "Which anchor?", 3, None, "Which anchor?")
    return DayBatch(
        DAY, [NewThread("test-p", "Which anchor?", AT)], [EmbeddedItem(post, VECTOR)], upvotes
    )


def test_a_saved_day_can_be_found_again_and_saving_it_twice_adds_nothing(store):
    store.save_day(batch({}))
    store.save_day(batch({}))

    assert store.known_post_ids(["test-p", "test-missing"]) == {"test-p"}
    assert store.known_thread_ids(["test-p"]) == {"test-p"}


def test_agreeing_replies_add_to_the_post_and_to_that_days_count(store):
    store.save_day(batch({"test-p": 2}))
    store.save_day(DayBatch(DAY, [], [], {"test-p": 1}))

    with store.engine.connect() as connection:
        assert connection.scalar(select(Post.upvotes).where(Post.source_id == "test-p")) == 3
        assert (
            connection.scalar(
                select(PostUpvotesDaily.count).where(PostUpvotesDaily.post_source_id == "test-p")
            )
            == 3
        )


def test_the_ledger_remembers_done_days_and_why_a_day_failed(store):
    store.mark_running(DAY)
    store.mark_failed(DAY, "archive down")
    assert DAY not in store.done_days()

    store.mark_running(DAY)
    store.mark_done(DAY, {"stored": 1})
    assert DAY in store.done_days()
