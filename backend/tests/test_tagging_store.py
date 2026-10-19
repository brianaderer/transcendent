"""Needs a real database: docker compose run --rm api pytest -m database"""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, insert, select

from voices.config import load_settings
from voices.db.models import (
    EMBEDDING_DIMENSIONS,
    ClusterDecision,
    Post,
    PostUpvotesDaily,
    RetrievalEvent,
    Thread,
    Topic,
    TopicDailyEngagement,
)
from voices.db.store import connect_store
from voices.db.tagging_store import PostNotFound, TaggingStore
from voices.tagging.decisions import ClusterBrief, DecidedCluster, Decision

pytestmark = pytest.mark.database

DAY = date(1999, 1, 3)
AT = datetime(1999, 1, 3, 12, tzinfo=UTC)
THIRD_DAY = DAY + timedelta(days=2)


def vector(lead):
    return [lead] + [0.0] * (EMBEDDING_DIMENSIONS - 1)


def other_axis():
    return [0.0, 1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 2)


def post(source_id, thread, kind, body, at=AT, parent=None, score=1):
    return {
        "source_id": source_id,
        "thread_source_id": thread,
        "kind": kind,
        "author": f"a-{source_id}",
        "created_at": at,
        "body": body,
        "reddit_score": score,
        "embedding": vector(1.0),
        "parent_source_id": parent,
    }


@pytest.fixture
def store():
    engine = connect_store(load_settings().database_url).engine
    tagging = TaggingStore(engine)
    with engine.begin() as connection:
        connection.execute(
            insert(Thread),
            [
                {"source_id": "test-1", "title": "Impellers", "created_at": AT},
                {"source_id": "test-4", "title": "Bermuda?", "created_at": AT},
            ],
        )
        connection.execute(
            insert(Post),
            [
                post("test-1", "test-1", "post", "Why does my impeller fail?"),
                post(
                    "test-2",
                    "test-1",
                    "comment",
                    "Run it dry and it dies.",
                    parent="test-1",
                    score=9,
                ),
                post("test-3", "test-1", "comment", "Carry a spare.", parent="test-1", score=2),
                post("test-4", "test-4", "post", "Anyone sailed to Bermuda?"),
            ],
        )
    tagging.save_thread_embeddings({"test-1": vector(1.0), "test-4": vector(1.0)})
    yield tagging
    with engine.begin() as connection:
        topic_ids = select(Topic.id).where(Topic.label.like("test-%"))
        connection.execute(delete(RetrievalEvent).where(RetrievalEvent.run.like("test-%")))
        connection.execute(
            delete(TopicDailyEngagement).where(TopicDailyEngagement.topic_id.in_(topic_ids))
        )
        connection.execute(
            delete(PostUpvotesDaily).where(PostUpvotesDaily.post_source_id.like("test-%"))
        )
        connection.execute(delete(Post).where(Post.source_id.like("test-%")))
        connection.execute(delete(Thread).where(Thread.source_id.like("test-%")))
        connection.execute(delete(ClusterDecision).where(ClusterDecision.reason.like("test-%")))
        connection.execute(delete(Topic).where(Topic.label.like("test-%")))


def decided(action, ids, label="test-impellers", topic_id=None, name="g1", centroid=None):
    brief = ClusterBrief(name, DAY.isoformat(), centroid or vector(1.0), [], [], ids)
    decision = Decision(
        action=action,
        label=label,
        description="Engine impellers failing.",
        topic_id=topic_id,
        reason="test-reason",
    )
    return DecidedCluster(brief, decision, prompt="p", model="m")


def topic_of(store, thread_id):
    with store.engine.connect() as connection:
        return connection.scalar(select(Thread.topic_id).where(Thread.source_id == thread_id))


def ours(threads):
    return sorted(t.source_id for t in threads if t.source_id.startswith("test-"))


def engagement(store, topic_id, day):
    with store.engine.connect() as connection:
        return connection.execute(
            select(TopicDailyEngagement).where(
                TopicDailyEngagement.topic_id == topic_id, TopicDailyEngagement.day == day
            )
        ).one()


def test_new_threads_are_due_on_their_first_day_with_their_replies_best_first(store):
    due = {t.source_id: t for t in store.threads_due(DAY) if t.source_id.startswith("test-")}

    assert sorted(due) == ["test-1", "test-4"]
    assert due["test-1"].post == "Why does my impeller fail?"
    assert [reply.body for reply in due["test-1"].replies] == [
        "Run it dry and it dies.",
        "Carry a spare.",
    ]


def test_a_thread_decided_on_its_first_day_is_due_again_on_its_third(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})

    assert ours(store.threads_due(DAY)) == ["test-4"]
    assert ours(store.threads_due(DAY + timedelta(days=1))) == []
    assert ours(store.threads_due(THIRD_DAY)) == ["test-1", "test-4"]


def test_a_thread_decided_on_its_third_day_is_never_due_again(store):
    store.apply_decisions(THIRD_DAY, [decided("mint", ["test-1"])], {})

    assert "test-1" not in ours(store.threads_due(THIRD_DAY))


def test_minting_creates_a_topic_and_tags_the_threads(store):
    counts = store.apply_decisions(
        DAY, [decided("mint", ["test-1", "test-4"])], {"g1": ["impeller"]}
    )

    topic_id = topic_of(store, "test-1")
    assert topic_id and topic_of(store, "test-4") == topic_id
    assert counts == {
        "attached": 2,
        "minted": 1,
        "noise_waiting": 0,
        "noise_deleted": 0,
        "left_waiting": 0,
    }


def test_attaching_joins_an_existing_topic(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})
    topic_id = topic_of(store, "test-1")

    store.apply_decisions(DAY, [decided("attach", ["test-4"], topic_id=topic_id, name="g2")], {})

    assert topic_of(store, "test-4") == topic_id


def test_noise_on_a_threads_first_day_waits_for_its_third(store):
    counts = store.apply_decisions(DAY, [decided("noise", ["test-1"])], {})

    assert store.lookup_post("test-2")["post_id"] == "test-2"
    assert counts["noise_waiting"] == 1
    assert "test-1" in ours(store.threads_due(THIRD_DAY))


def test_noise_on_a_threads_third_day_deletes_it_with_its_comments(store):
    counts = store.apply_decisions(THIRD_DAY, [decided("noise", ["test-1"])], {})

    with pytest.raises(PostNotFound):
        store.lookup_post("test-2")
    assert counts["noise_deleted"] == 1


def test_attaching_to_a_topic_that_does_not_exist_leaves_the_threads_waiting(store):
    counts = store.apply_decisions(DAY, [decided("attach", ["test-4"], topic_id=-1)], {})

    assert topic_of(store, "test-4") is None
    assert counts["left_waiting"] == 1 and counts["noise_deleted"] == 0


def test_a_merged_mint_joins_the_topic_minted_earlier_in_the_run(store):
    first = decided("mint", ["test-1"], name="g1")
    twin = replace(decided("mint", ["test-4"], name="g2"), merged_into="g1")

    counts = store.apply_decisions(DAY, [first, twin], {})

    assert topic_of(store, "test-4") == topic_of(store, "test-1")
    assert counts["minted"] == 1


def test_a_merged_mint_before_its_twin_raises(store):
    twin = replace(decided("mint", ["test-4"], name="g2"), merged_into="g1")

    with pytest.raises(RuntimeError, match="not minted yet"):
        store.apply_decisions(DAY, [twin, decided("mint", ["test-1"], name="g1")], {})


def test_attaching_moves_last_seen_to_the_day(store):
    store.apply_decisions(date(1999, 1, 1), [decided("mint", ["test-1"])], {})
    topic_id = topic_of(store, "test-1")

    store.apply_decisions(DAY, [decided("attach", ["test-4"], topic_id=topic_id, name="g2")], {})

    with store.engine.connect() as connection:
        assert connection.scalar(select(Topic.last_seen).where(Topic.id == topic_id)) == DAY


def test_a_topics_centre_moves_to_the_average_of_its_threads(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"], centroid=other_axis())], {})
    topic_id = topic_of(store, "test-1")

    [candidate] = [c for c in store.nearest_topics(vector(1.0), 50) if c.topic_id == topic_id]

    assert candidate.similarity == 1.0  # moved from the other axis onto its thread's direction


def test_a_thread_moved_on_its_third_day_leaves_its_old_topic_and_joins_the_new(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1", "test-4"])], {})
    first_topic = topic_of(store, "test-1")
    store.apply_decisions(THIRD_DAY, [decided("mint", ["test-4"], label="test-bermuda")], {})

    assert topic_of(store, "test-4") not in (None, first_topic)
    assert topic_of(store, "test-1") == first_topic


def test_candidate_topics_count_posts_from_the_last_week(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})
    topic_id = topic_of(store, "test-1")

    [candidate] = [c for c in store.nearest_topics(vector(1.0), 50) if c.topic_id == topic_id]

    assert candidate.posts_last_week == 3  # the post and its two comments


def test_typical_threads_are_the_closest_to_the_centre(store):
    store.save_thread_embeddings({"test-4": other_axis()})

    typical = store.typical_threads(["test-1", "test-4"], vector(1.0), limit=1)

    assert [(t.source_id, t.text) for t in typical] == [("test-1", "Why does my impeller fail?")]


def test_daily_engagement_counts_posts_comments_people_and_open_questions(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1", "test-4"])], {})
    topic_id = topic_of(store, "test-1")

    store.rebuild_engagement(DAY, DAY)

    row = engagement(store, topic_id, DAY)
    assert (row.posts, row.comments, row.unique_authors, row.new_threads) == (2, 2, 4, 2)
    assert row.unanswered_questions == 1  # the Bermuda question; the impeller one has replies


def test_a_comment_arriving_days_later_counts_for_its_threads_topic_on_its_own_day(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})
    later = DAY + timedelta(days=5)
    with store.engine.begin() as connection:
        connection.execute(
            insert(Post),
            [post("test-5", "test-1", "comment", "Still failing.", at=AT + timedelta(days=5))],
        )

    store.rebuild_engagement(later, later)

    row = engagement(store, topic_of(store, "test-1"), later)
    assert (row.posts, row.comments, row.revived_threads) == (0, 1, 0)


def test_upvotes_count_on_a_day_with_no_new_posts(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})
    later = date(1999, 1, 5)
    with store.engine.begin() as connection:
        connection.execute(
            insert(PostUpvotesDaily), [{"post_source_id": "test-1", "day": later, "count": 4}]
        )

    store.rebuild_engagement(later, later)

    row = engagement(store, topic_of(store, "test-1"), later)
    assert (row.posts, row.comments, row.upvotes) == (0, 0, 4)


def test_search_finds_posts_by_meaning_and_retrievals_are_recorded(store):
    hits = store.search_posts(vector(1.0), DAY, DAY, limit=5)
    store.record_retrievals([hits[0]["post_id"]], "test-run", "tagging", "search")

    assert hits[0]["post_id"].startswith("test-")
    with store.engine.connect() as connection:
        assert (
            connection.scalar(select(RetrievalEvent.tool).where(RetrievalEvent.run == "test-run"))
            == "search"
        )


def test_looking_up_an_unknown_post_raises(store):
    with pytest.raises(PostNotFound):
        store.lookup_post("test-nope")


def centre_of(store, topic_id):
    [candidate] = [c for c in store.nearest_topics(vector(1.0), 50) if c.topic_id == topic_id]
    return candidate.similarity


def test_noise_on_a_threads_third_day_moves_the_centre_of_the_topic_it_leaves(store):
    store.save_thread_embeddings({"test-1": other_axis()})
    store.apply_decisions(DAY, [decided("mint", ["test-1", "test-4"])], {})
    topic_id = topic_of(store, "test-1")

    store.apply_decisions(THIRD_DAY, [decided("noise", ["test-1"])], {})

    assert centre_of(store, topic_id) == 1.0  # now only test-4, on the first axis


def test_attaching_to_a_missing_topic_on_a_threads_third_day_keeps_its_first_days_topic(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})
    first_topic = topic_of(store, "test-1")

    counts = store.apply_decisions(THIRD_DAY, [decided("attach", ["test-1"], topic_id=-1)], {})

    assert topic_of(store, "test-1") == first_topic
    assert "test-1" not in ours(store.threads_due(THIRD_DAY))  # settled: not decided again
    assert counts["left_waiting"] == 1


@pytest.mark.parametrize(("days_later", "revived"), [(7, 0), (8, 1)])
def test_a_thread_counts_as_revived_only_after_seven_days(store, days_later, revived):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})
    later = DAY + timedelta(days=days_later)
    with store.engine.begin() as connection:
        comment = post("test-5", "test-1", "comment", "Back.", at=AT + timedelta(days=days_later))
        connection.execute(insert(Post), [comment])

    store.rebuild_engagement(later, later)

    assert engagement(store, topic_of(store, "test-1"), later).revived_threads == revived
