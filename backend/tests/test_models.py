import pytest
from pgvector.sqlalchemy import HALFVEC

from voices.db.models import EMBEDDING_DIMENSIONS, Base


def table(name):
    return Base.metadata.tables[name]


def test_every_planned_table_is_described():
    assert set(Base.metadata.tables) == {
        "threads",
        "topics",
        "cluster_decisions",
        "posts",
        "post_upvotes_daily",
        "topic_daily_engagement",
        "noise_threads",
        "retrieval_events",
        "ingested_days",
    }


@pytest.mark.parametrize(
    ("table_name", "column"),
    [("posts", "embedding"), ("threads", "embedding"), ("topics", "centroid")],
)
def test_embeddings_are_half_precision_at_the_embedding_model_size(table_name, column):
    embedding_type = table(table_name).c[column].type

    assert isinstance(embedding_type, HALFVEC)
    assert embedding_type.dim == EMBEDDING_DIMENSIONS


def test_a_thread_points_to_its_topic_and_the_decision_that_tagged_it():
    columns = table("threads").c

    assert {key.target_fullname for key in columns.topic_id.foreign_keys} == {"topics.id"}
    assert {key.target_fullname for key in columns.cluster_decision_id.foreign_keys} == {
        "cluster_decisions.id"
    }


def test_a_post_has_no_topic_of_its_own():
    assert "topic_id" not in table("posts").c


def test_posts_keep_reddit_score_and_agreeing_reply_upvotes_as_separate_columns():
    posts = table("posts")

    assert {"reddit_score", "upvotes"} <= set(posts.c.keys())


def test_daily_engagement_has_one_row_per_topic_per_day():
    keys = [column.name for column in table("topic_daily_engagement").primary_key]

    assert keys == ["topic_id", "day"]


def test_a_topic_centre_may_be_missing_until_the_backfill_rebuilds_it():
    """The seed brings topics without their centres (atlas plate 07)."""
    assert table("topics").c.centroid.nullable
