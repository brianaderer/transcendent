from datetime import UTC, datetime

from voices.ingestion.items import comment_from_archive, post_from_archive


def test_a_post_becomes_a_thread_starter_with_its_title_and_text():
    raw = {
        "id": "abc",
        "author": "salty",
        "created_utc": 1792022474,
        "title": "Which anchor?",
        "selftext": "Plough or Rocna for a 32ft sloop?",
        "score": 7,
    }

    post = post_from_archive(raw)

    assert post.source_id == "abc"
    assert post.thread_source_id == "abc"
    assert post.kind == "post"
    assert post.body == "Which anchor?\n\nPlough or Rocna for a 32ft sloop?"
    assert post.created_at == datetime(2026, 10, 15, 0, 1, 14, tzinfo=UTC)
    assert post.parent_source_id is None


def test_a_link_post_with_no_text_keeps_just_its_title():
    raw = {
        "id": "abc",
        "author": "salty",
        "created_utc": 1792022474,
        "title": "Sunset",
        "selftext": "",
    }

    assert post_from_archive(raw).body == "Sunset"


def test_a_comment_knows_its_thread_and_what_it_replies_to():
    raw = {
        "id": "c1",
        "author": "deckhand",
        "created_utc": 1792022474,
        "body": "Rocna, every time.",
        "score": 3,
        "parent_id": "t1_c0",
        "link_id": "t3_abc",
    }

    comment = comment_from_archive(raw)

    assert comment.kind == "comment"
    assert comment.thread_source_id == "abc"
    assert comment.parent_source_id == "c0"
    assert comment.reddit_score == 3
