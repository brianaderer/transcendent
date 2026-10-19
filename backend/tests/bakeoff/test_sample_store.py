import pytest

from tests.bakeoff.conftest import thread
from voices.bakeoff.sample import Comment
from voices.bakeoff.sample_store import THREAD_TEXT_CHARACTERS, SampleStore, thread_text
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


def test_thread_text_keeps_only_the_best_scored_comments():
    comments = [Comment(f"c{n}", "u", f"reply{n}", "t", score=n) for n in range(6)]

    text = thread_text(thread("t", "The post", comments))

    assert "reply5" in text and "reply1" in text and "reply0" not in text


def test_thread_text_is_cut_at_the_character_limit():
    long_reply = Comment("c", "u", "x" * THREAD_TEXT_CHARACTERS, "t", score=1)

    assert len(thread_text(thread("t", "The post", [long_reply]))) == THREAD_TEXT_CHARACTERS
