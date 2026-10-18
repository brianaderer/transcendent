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


def test_post_embeddings_have_the_embedding_model_size():
    assert table("posts").c.embedding.type.dim == EMBEDDING_DIMENSIONS


def test_a_post_points_to_the_cluster_decision_that_tagged_it():
    foreign_keys = table("posts").c.cluster_decision_id.foreign_keys

    assert {key.target_fullname for key in foreign_keys} == {"cluster_decisions.id"}


def test_posts_keep_reddit_score_and_agreeing_reply_upvotes_as_separate_columns():
    posts = table("posts")

    assert {"reddit_score", "upvotes"} <= set(posts.c.keys())


def test_daily_engagement_has_one_row_per_topic_per_day():
    keys = [column.name for column in table("topic_daily_engagement").primary_key]

    assert keys == ["topic_id", "day"]
