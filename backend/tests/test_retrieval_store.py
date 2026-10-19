"""Needs a real database: docker compose run --rm api pytest -m database"""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, insert

from voices.config import load_settings
from voices.db.models import EMBEDDING_DIMENSIONS, Post, RetrievalEvent, Thread, Topic
from voices.db.post_columns import SHORT_EXCERPT_CHARACTERS
from voices.db.retrieval_store import RetrievalStore
from voices.db.store import connect_store
from voices.explore.day_range import DayRange
from voices.retrievals.shapes import RetrievalFilter

pytestmark = pytest.mark.database

DAY = date(1999, 3, 1)  # far outside any real history, so the test can't touch real rows
DAYS = DayRange(DAY, DAY)
AT = datetime(1999, 3, 1, 12, tzinfo=UTC)
PREFIX = "test-rs-"
# Retrieval times later than any real one; the latest decides which run is newest.
EARLY, LATE, LATEST = (datetime(2999, 1, day, tzinfo=UTC) for day in (1, 2, 3))


def a_post(name, thread, written=AT, body="Carry a spare impeller."):
    return {
        "source_id": PREFIX + name,
        "thread_source_id": PREFIX + thread,
        "kind": "comment",
        "author": f"author-{name}",
        "created_at": written,
        "body": body,
    }


def retrievals(name, count, run="one", agent="tagging", at=EARLY):
    one = {"post_source_id": PREFIX + name, "run": PREFIX + run, "agent": agent, "tool": "search"}
    return [{**one, "at": at} for _ in range(count)]


def add_rows(connection, topic_id):
    connection.execute(
        insert(Thread),
        [
            {"source_id": PREFIX + name, "title": "Impellers", "created_at": AT,
             "first_seen_on": DAY, "topic_id": topic}
            for name, topic in (("tagged", topic_id), ("waiting", None))
        ],
    )  # fmt: skip
    connection.execute(
        insert(Post),
        [
            a_post("busy", "tagged", body="x" * 500),
            a_post("quiet", "tagged"),
            a_post("tied", "tagged"),
            a_post("untagged", "waiting"),
            a_post("next-day", "tagged", written=AT + timedelta(days=1)),
        ],
    )
    connection.execute(
        insert(RetrievalEvent),
        [
            *retrievals("busy", 3),
            *retrievals("busy", 1, run="two", at=LATEST),
            *retrievals("quiet", 2, at=LATE),
            *retrievals("tied", 2),
            *retrievals("untagged", 1),
            *retrievals("next-day", 5),
            *retrievals("quiet", 7, run="report", agent="report"),
        ],
    )


@pytest.fixture
def store():
    engine = connect_store(load_settings().database_url).engine
    with engine.begin() as connection:
        topic_id = connection.scalar(
            insert(Topic)
            .values(
                label="test-rs-impellers",
                description="d",
                centroid=[1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 1),
                first_seen=DAY,
                last_seen=DAY,
            )
            .returning(Topic.id)
        )
        add_rows(connection, topic_id)
    yield RetrievalStore(engine), topic_id
    with engine.begin() as connection:
        connection.execute(delete(RetrievalEvent).where(RetrievalEvent.run.like(f"{PREFIX}%")))
        connection.execute(delete(Post).where(Post.source_id.like(f"{PREFIX}%")))
        connection.execute(delete(Thread).where(Thread.source_id.like(f"{PREFIX}%")))
        connection.execute(delete(Topic).where(Topic.id == topic_id))


def tagging(run=None):
    return RetrievalFilter(agent="tagging", days=DAYS, run=run)


def test_posts_are_counted_most_retrieved_first_and_ties_go_to_the_latest(store):
    retrieval_store, _ = store

    posts = retrieval_store.most_retrieved(tagging(), 10)

    names = [(p.post_id.removeprefix(PREFIX), p.times_retrieved) for p in posts]
    assert names == [("busy", 4), ("quiet", 2), ("tied", 2), ("untagged", 1)]


def test_a_retrieved_post_comes_with_its_topic_and_its_last_retrieval(store):
    retrieval_store, topic_id = store

    busy, *_, untagged = retrieval_store.most_retrieved(tagging(), 10)

    assert (busy.topic_id, busy.topic_label, busy.last_retrieved) == (
        topic_id,
        "test-rs-impellers",
        LATEST,
    )
    assert (busy.day, len(busy.excerpt)) == (DAY, SHORT_EXCERPT_CHARACTERS)
    assert (untagged.topic_id, untagged.topic_label) == (None, None)


def test_the_table_stops_at_the_limit(store):
    retrieval_store, _ = store

    assert len(retrieval_store.most_retrieved(tagging(), 2)) == 2


def test_only_the_named_run_counts_when_one_is_named(store):
    retrieval_store, _ = store

    [busy] = retrieval_store.most_retrieved(tagging(run=f"{PREFIX}two"), 10)

    assert (busy.post_id, busy.times_retrieved) == (f"{PREFIX}busy", 1)


def test_only_the_named_agents_retrievals_count(store):
    retrieval_store, _ = store

    [quiet] = retrieval_store.most_retrieved(RetrievalFilter(agent="report", days=DAYS), 10)

    assert quiet.times_retrieved == 7


def test_retrievals_per_topic_count_threads_waiting_for_a_topic_together(store):
    retrieval_store, topic_id = store

    topics = retrieval_store.per_topic(tagging())

    assert [(t.topic_id, t.times_retrieved) for t in topics] == [(topic_id, 8), (None, 1)]


def test_runs_are_the_agents_runs_on_the_ranges_posts_newest_first(store):
    retrieval_store, _ = store

    assert retrieval_store.runs("tagging", DAYS) == [f"{PREFIX}two", f"{PREFIX}one"]
    assert retrieval_store.runs("report", DAYS) == [f"{PREFIX}report"]
