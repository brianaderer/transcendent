import pytest

from voices.bakeoff.sample_store import SampleStore
from voices.db.tagging_store import PostNotFound


def test_search_finds_posts_and_comments_by_meaning(sample, embedder):
    store = SampleStore(sample, embedder)

    hits = store.search_posts(embedder.embed_query("stolen"), None, None, limit=3)

    assert {hit["post_id"] for hit in hits} == {"t1", "t2", "c1"}


def test_lookup_reads_a_comment_with_its_thread_and_what_it_replies_to(sample, embedder):
    post = SampleStore(sample, embedder).lookup_post("c1")

    assert (post["text"], post["thread"], post["replies_to"]) == (
        "Stolen again?",
        "Stolen boat in NYC",
        "t1",
    )


def test_looking_up_an_unknown_post_raises(sample, embedder):
    with pytest.raises(PostNotFound):
        SampleStore(sample, embedder).lookup_post("nope")


def test_a_cases_brief_shows_its_threads_and_the_nearest_topic_first(sample, embedder):
    store = SampleStore(sample, embedder)

    brief = store.brief(sample.cases[0])

    assert brief.member_ids == ["t1", "t2"]
    assert brief.candidates[0].label == "Stolen boats"
    assert {post.source_id for post in brief.typical_posts} == {"t1", "t2"}


def test_searching_topics_finds_the_closest_by_meaning(sample, embedder):
    [nearest, *_] = SampleStore(sample, embedder).search_topics(embedder.embed_query("learn"), 5)

    assert nearest["label"] == "Learning to sail"
