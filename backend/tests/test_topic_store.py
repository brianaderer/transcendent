"""Needs a real database: docker compose run --rm api pytest -m database"""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, insert

from voices.config import load_settings
from voices.db.models import (
    EMBEDDING_DIMENSIONS,
    ClusterDecision,
    Post,
    Thread,
    Topic,
    TopicDailyEngagement,
)
from voices.db.store import connect_store
from voices.db.tagging_store import UNKNOWN_AUTHOR
from voices.db.topic_store import CARD_EXCERPT_CHARACTERS, TopicStore
from voices.topics.topic_detail import TopicNotFound

pytestmark = pytest.mark.database

DAY = date(1999, 2, 1)  # far outside any real history, so the test can't touch real rows
AT = datetime(1999, 2, 1, 23, 30, tzinfo=UTC)  # still 1 Feb in UTC
PREFIX = "test-td-"
NO_SUCH_TOPIC = -1


def vector(*lead):
    return list(lead) + [0.0] * (EMBEDDING_DIMENSIONS - len(lead))


def thread(name, topic_id, embedding, decision=None):
    return {
        "source_id": PREFIX + name,
        "title": f"Title {name}",
        "created_at": AT,
        "first_seen_on": DAY,
        "topic_id": topic_id,
        "embedding": embedding,
        "cluster_decision_id": decision,
    }


def opening_post(name, body):
    return {
        "source_id": PREFIX + name,
        "thread_source_id": PREFIX + name,
        "kind": "post",
        "author": f"author-{name}",
        "created_at": AT,
        "body": body,
    }


def engagement(topic_id, day, posts, comments, upvotes, people):
    counts = {"posts": posts, "comments": comments, "upvotes": upvotes, "unique_authors": people}
    return {"topic_id": topic_id, "day": day, **counts}


def add_decision(connection, topic_id, day, decision):
    values = {"day": day, "decision": decision, "topic_id": topic_id, "prompt": "p", "model": "m"}
    return connection.scalar(
        insert(ClusterDecision)
        .values(**values, reason=f"{decision} on {day}")
        .returning(ClusterDecision.id)
    )


def add_topic(connection):
    return connection.scalar(
        insert(Topic)
        .values(
            label="test-td-impellers",
            description="Engine impellers.",
            keywords=["impeller", "pump"],
            centroid=vector(1.0),
            first_seen=DAY,
            last_seen=DAY + timedelta(days=2),
        )
        .returning(Topic.id)
    )


@pytest.fixture
def topic():
    engine = connect_store(load_settings().database_url).engine
    with engine.begin() as connection:
        topic_id = add_topic(connection)
        later = add_decision(connection, topic_id, DAY + timedelta(days=1), "attach")
        first = add_decision(connection, topic_id, DAY, "mint")
        add_decision(connection, topic_id, DAY + timedelta(days=2), "attach")  # since re-decided
        connection.execute(
            insert(Thread),
            [
                thread("near", topic_id, vector(1.0, 0.1), first),
                thread("far", topic_id, vector(0.1, 1.0), first),
                thread("removed", topic_id, vector(1.0, 0.5), later),  # its post isn't stored
                thread("unencoded", topic_id, None, later),
            ],
        )
        connection.execute(
            insert(Post),
            [
                opening_post("near", "x" * 500),
                opening_post("far", "Far away."),
                opening_post("unencoded", "Not encoded yet."),
            ],
        )
        connection.execute(
            insert(TopicDailyEngagement),
            [
                engagement(topic_id, DAY + timedelta(days=1), 1, 0, 0, 1),
                engagement(topic_id, DAY, 1, 2, 3, 2),
            ],
        )
    yield TopicStore(engine), topic_id
    with engine.begin() as connection:
        connection.execute(delete(Post).where(Post.source_id.like(f"{PREFIX}%")))
        connection.execute(delete(Thread).where(Thread.source_id.like(f"{PREFIX}%")))
        connection.execute(
            delete(TopicDailyEngagement).where(TopicDailyEngagement.topic_id == topic_id)
        )
        connection.execute(delete(ClusterDecision).where(ClusterDecision.topic_id == topic_id))
        connection.execute(delete(Topic).where(Topic.id == topic_id))


def test_a_topics_summary_has_its_keywords_and_the_days_it_was_seen(topic):
    store, topic_id = topic

    summary = store.summary(topic_id)

    assert (summary.label, summary.keywords) == ("test-td-impellers", ["impeller", "pump"])
    assert (summary.first_seen, summary.last_seen) == (DAY, DAY + timedelta(days=2))


def test_a_topic_that_does_not_exist_is_not_found(topic):
    store, _ = topic

    with pytest.raises(TopicNotFound):
        store.summary(NO_SUCH_TOPIC)


def test_engagement_is_each_day_oldest_first_with_its_distinct_people(topic):
    store, topic_id = topic

    first, second = store.engagement(topic_id)

    assert (first.day, first.posts, first.comments, first.upvotes, first.people) == (
        DAY,
        1,
        2,
        3,
        2,
    )
    assert second.day == DAY + timedelta(days=1)


def test_typical_posts_are_the_threads_closest_to_the_centre_closest_first(topic):
    store, topic_id = topic

    cards = store.typical_posts(topic_id, 3)

    assert [c.post_id for c in cards] == [f"{PREFIX}near", f"{PREFIX}removed", f"{PREFIX}far"]


def test_typical_posts_stop_at_the_limit(topic):
    store, topic_id = topic

    assert len(store.typical_posts(topic_id, 1)) == 1


def test_a_typical_post_is_cut_to_a_cards_length_and_dated_in_utc(topic):
    store, topic_id = topic

    near = store.typical_posts(topic_id, 1)[0]

    assert (near.author, near.day, near.kind) == ("author-near", DAY, "post")
    assert len(near.excerpt) == CARD_EXCERPT_CHARACTERS


def test_a_thread_whose_post_is_not_stored_is_shown_by_its_title(topic):
    store, topic_id = topic

    removed = store.typical_posts(topic_id, 2)[1]

    assert (removed.author, removed.excerpt) == (UNKNOWN_AUTHOR, "Title removed")


def test_decisions_are_oldest_first_with_the_threads_that_carry_them(topic):
    store, topic_id = topic

    decisions = store.decisions(topic_id)

    assert [(d.day, d.decision, d.threads) for d in decisions] == [
        (DAY, "mint", 2),
        (DAY + timedelta(days=1), "attach", 2),
        (DAY + timedelta(days=2), "attach", 0),
    ]
    assert decisions[0].reason == f"mint on {DAY}"
