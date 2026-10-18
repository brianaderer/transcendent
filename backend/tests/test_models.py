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
        "retrieval_events",
        "ingested_days",
    }


def test_posts_carry_one_embedding_and_the_decision_that_tagged_them():
    posts = table("posts")

    assert posts.c.embedding.type.dim == EMBEDDING_DIMENSIONS
    assert posts.c.cluster_decision_id.foreign_keys


def test_reddit_score_and_our_upvotes_are_kept_apart():
    posts = table("posts")

    assert {"reddit_score", "upvotes"} <= set(posts.c.keys())


def test_daily_engagement_has_one_row_per_topic_per_day():
    keys = [column.name for column in table("topic_daily_engagement").primary_key]

    assert keys == ["topic_id", "day"]
