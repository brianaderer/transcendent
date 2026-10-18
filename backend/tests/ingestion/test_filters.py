from datetime import UTC, datetime

import pytest

from voices.ingestion.filters import is_unwanted
from voices.ingestion.items import Item


def item(author="salty", body="Rocna, every time."):
    return Item("c1", "abc", "comment", author, datetime(2026, 10, 15, tzinfo=UTC), body, 1, "abc")


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
