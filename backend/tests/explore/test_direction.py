from datetime import date

import pytest

from voices.explore.direction import direction

START = date(2026, 10, 12)


def test_a_topic_first_seen_inside_the_range_is_new():
    assert direction(first_seen=START, start=START, now=3, before=40) == "new"


@pytest.mark.parametrize(
    ("now", "before", "expected"),
    [(126, 100, "rising"), (125, 100, "steady"), (75, 100, "steady"), (74, 100, "fading")],
)
def test_a_change_of_more_than_a_quarter_either_way_counts(now, before, expected):
    assert direction(first_seen=date(2026, 9, 1), start=START, now=now, before=before) == expected


def test_a_topic_back_from_silence_is_rising():
    assert direction(first_seen=date(2026, 9, 1), start=START, now=2, before=0) == "rising"
