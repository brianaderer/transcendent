"""Needs a real database: docker compose run --rm api pytest -m database"""

from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import delete, select

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


def vector(lead):
    return [lead] + [0.0] * (EMBEDDING_DIMENSIONS - 1)


@pytest.fixture
def store():
    engine = connect_store(load_settings().database_url).engine
    tagging = TaggingStore(engine)
    with engine.begin() as connection:
        connection.execute(
            Thread.__table__.insert(),
            [{"source_id": "test-t", "title": "Impellers", "created_at": AT}],
        )
        connection.execute(
            Post.__table__.insert(),
            [
                {
                    "source_id": f"test-{n}",
                    "thread_source_id": "test-t",
                    "kind": kind,
                    "author": f"a{n}",
                    "created_at": AT,
                    "body": body,
                    "embedding": vector(1.0),
                    "parent_source_id": parent,
                }
                for n, kind, body, parent in [
                    (1, "post", "Why does my impeller fail?", None),
                    (2, "comment", "Run it dry and it dies.", "test-1"),
                    (3, "comment", "Carry a spare.", "test-1"),
                    (4, "post", "Anyone sailed to Bermuda?", None),
                ]
            ],
        )
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
        connection.execute(delete(ClusterDecision).where(ClusterDecision.reason.like("test-%")))
        connection.execute(delete(Topic).where(Topic.label.like("test-%")))
        connection.execute(delete(Thread).where(Thread.source_id.like("test-%")))


def decided(action, ids, label="test-impellers", topic_id=None, name="c1"):
    brief = ClusterBrief(name, DAY.isoformat(), vector(1.0), [], [], ids)
    decision = Decision(
        action=action,
        label=label,
        description="Engine impellers failing.",
        topic_id=topic_id,
        reason="test-reason",
    )
    return DecidedCluster(brief, decision, prompt="p", model="m")


def topic_of(store, post_id):
    with store.engine.connect() as connection:
        return connection.scalar(select(Post.topic_id).where(Post.source_id == post_id))


def test_the_window_holds_the_days_posts_with_their_embeddings(store):
    posts = [p for p in store.window_posts(DAY, DAY) if p.source_id.startswith("test-")]

    assert sorted(p.source_id for p in posts) == ["test-1", "test-2", "test-3", "test-4"]
    assert len(posts[0].embedding) == EMBEDDING_DIMENSIONS


def test_minting_creates_a_topic_and_tags_the_clusters_posts(store):
    counts = store.apply_decisions(
        DAY, [decided("mint", ["test-1", "test-2"])], {"c1": ["impeller"]}
    )

    topic_id = topic_of(store, "test-1")
    assert topic_id and topic_of(store, "test-2") == topic_id
    assert counts == {"attached": 2, "minted": 1, "noise_deleted": 0, "left_waiting": 0}


def test_attaching_joins_an_existing_topic_and_noise_is_deleted(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})
    topic_id = topic_of(store, "test-1")

    counts = store.apply_decisions(
        DAY,
        [
            decided("attach", ["test-2"], topic_id=topic_id, name="c2"),
            decided("noise", ["test-3"], name="c3"),
        ],
        {},
    )

    assert topic_of(store, "test-2") == topic_id
    with pytest.raises(PostNotFound):
        store.lookup_post("test-3")
    assert counts["noise_deleted"] == 1


def test_posts_left_waiting_before_the_window_expire(store):
    assert store.delete_expired_pending(before=date(1999, 1, 4)) >= 4
    assert not [p for p in store.window_posts(DAY, DAY) if p.source_id.startswith("test-")]


def test_daily_engagement_counts_posts_comments_people_and_open_questions(store):
    everything = ["test-1", "test-2", "test-3", "test-4"]
    store.apply_decisions(DAY, [decided("mint", everything)], {})
    topic_id = topic_of(store, "test-1")

    store.rebuild_engagement(DAY, DAY)

    with store.engine.connect() as connection:
        row = connection.execute(
            select(TopicDailyEngagement).where(TopicDailyEngagement.topic_id == topic_id)
        ).one()
    assert (row.posts, row.comments, row.unique_authors, row.new_threads) == (2, 2, 4, 2)
    assert row.unanswered_questions == 1  # the Bermuda question; the impeller one has replies


def test_search_finds_posts_by_meaning_and_retrievals_are_recorded(store):
    hits = store.search_posts(vector(1.0), DAY, DAY, limit=5)
    store.record_retrievals([hits[0]["post_id"]], "test-run", "tagging", "search")

    assert hits[0]["post_id"].startswith("test-")
    with store.engine.connect() as connection:
        assert (
            connection.scalar(select(RetrievalEvent.tool).where(RetrievalEvent.run == "test-run"))
            == "search"
        )


def test_attaching_to_a_topic_that_does_not_exist_leaves_the_posts_waiting(store):
    counts = store.apply_decisions(DAY, [decided("attach", ["test-2"], topic_id=-1)], {})

    assert topic_of(store, "test-2") is None
    assert store.lookup_post("test-2")["post_id"] == "test-2"
    assert counts["left_waiting"] == 1 and counts["noise_deleted"] == 0


def test_a_merged_mint_joins_the_topic_minted_earlier_in_the_run(store):
    first = decided("mint", ["test-1"], name="c1")
    twin = replace(decided("mint", ["test-2"], name="c2"), merged_into="c1")

    counts = store.apply_decisions(DAY, [first, twin], {})

    assert topic_of(store, "test-2") == topic_of(store, "test-1")
    assert counts["minted"] == 1


def other_axis():
    return [0.0, 1.0] + [0.0] * (EMBEDDING_DIMENSIONS - 2)


def test_attaching_moves_last_seen_to_the_day(store):
    store.apply_decisions(date(1999, 1, 1), [decided("mint", ["test-1"])], {})
    topic_id = topic_of(store, "test-1")

    store.apply_decisions(DAY, [decided("attach", ["test-2"], topic_id=topic_id, name="c2")], {})

    with store.engine.connect() as connection:
        assert connection.scalar(select(Topic.last_seen).where(Topic.id == topic_id)) == DAY


def test_attaching_moves_the_topics_centre_to_the_average_of_its_posts(store):
    minted_off_axis = replace(
        decided("mint", ["test-1"]),
        brief=ClusterBrief("c1", DAY.isoformat(), other_axis(), [], [], ["test-1"]),
    )
    store.apply_decisions(DAY, [minted_off_axis], {})
    topic_id = topic_of(store, "test-1")

    [candidate] = [c for c in store.nearest_topics(vector(1.0), 50) if c.topic_id == topic_id]

    assert candidate.similarity == 1.0  # moved from the other axis onto its post's direction


def test_candidate_topics_count_posts_from_the_last_week(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1", "test-2"])], {})
    topic_id = topic_of(store, "test-1")

    [candidate] = [c for c in store.nearest_topics(vector(1.0), 50) if c.topic_id == topic_id]

    assert candidate.posts_last_week == 2


def test_left_waiting_counts_only_posts_that_were_waiting(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})

    counts = store.apply_decisions(DAY, [decided("attach", ["test-1", "test-2"], topic_id=-1)], {})

    assert counts["left_waiting"] == 1  # test-1 already had a topic


def test_upvotes_count_on_a_day_with_no_new_posts(store):
    store.apply_decisions(DAY, [decided("mint", ["test-1"])], {})
    topic_id = topic_of(store, "test-1")
    later = date(1999, 1, 5)
    with store.engine.begin() as connection:
        connection.execute(
            PostUpvotesDaily.__table__.insert(),
            [{"post_source_id": "test-1", "day": later, "count": 4}],
        )

    store.rebuild_engagement(later, later)

    with store.engine.connect() as connection:
        row = connection.execute(
            select(TopicDailyEngagement).where(
                TopicDailyEngagement.topic_id == topic_id, TopicDailyEngagement.day == later
            )
        ).one()
    assert (row.posts, row.comments, row.upvotes) == (0, 0, 4)
