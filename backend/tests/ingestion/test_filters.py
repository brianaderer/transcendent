from datetime import UTC, datetime

import pytest

from voices.ingestion.filters import REMOVED_TEXT, is_unwanted
from voices.ingestion.items import Item, post_from_archive


def item(author="salty", body="Rocna, every time."):
    at = datetime(2026, 10, 15, tzinfo=UTC)
    return Item("c1", "abc", "comment", author, at, body, 1, "abc", text=body)


@pytest.mark.parametrize("body", ["[deleted]", "[removed]", "[ Removed by Reddit ]"])
def test_removed_text_is_dropped(body):
    assert is_unwanted(item(body=body))


def test_a_deleted_author_is_dropped():
    assert is_unwanted(item(author="[deleted]"))


@pytest.mark.parametrize("author", ["AutoModerator", "RemindMeBot", "haikusbot"])
def test_bots_are_dropped(author):
    assert is_unwanted(item(author=author))


def test_an_ordinary_comment_is_kept():
    assert not is_unwanted(item())


def archived_post(**fields):
    raw = {"id": "p1", "author": "salty", "created_utc": 1787000000, "title": "Free sailboat"}
    return post_from_archive({**raw, **fields})


@pytest.mark.parametrize("text", sorted(REMOVED_TEXT))
def test_a_post_whose_text_was_removed_is_dropped_though_its_title_survives(text):
    assert is_unwanted(archived_post(selftext=text))


def test_a_post_with_only_a_title_is_kept():
    assert not is_unwanted(archived_post())
