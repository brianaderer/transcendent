from datetime import date, timedelta

import pytest

from voices.explore.day_range import DayRange
from voices.explore.direction import direction, is_new

DAYS = DayRange(date(2026, 10, 12), date(2026, 10, 18))


def test_a_topic_first_seen_inside_the_range_is_new():
    assert is_new(DAYS.start, DAYS)
    assert direction(new=True, now=3, before=40) == "new"


def test_a_topic_first_seen_the_day_before_the_range_is_not_new():
    assert not is_new(DAYS.start - timedelta(days=1), DAYS)


@pytest.mark.parametrize(
    ("now", "before", "expected"),
    [(126, 100, "rising"), (125, 100, "steady"), (75, 100, "steady"), (74, 100, "fading")],
)
def test_a_change_of_more_than_a_quarter_either_way_counts(now, before, expected):
    assert direction(new=False, now=now, before=before) == expected


def test_a_topic_back_from_silence_is_rising():
    assert direction(new=False, now=2, before=0) == "rising"
