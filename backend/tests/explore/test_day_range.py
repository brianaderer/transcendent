from datetime import date

import pytest

from voices.explore.day_range import DayRange, InvalidRange


def test_a_range_counts_both_its_first_and_last_day():
    days = DayRange(date(2026, 10, 12), date(2026, 10, 14))

    assert days.length == 3
    assert list(days.days()) == [date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)]


def test_the_period_before_has_the_same_length_and_ends_the_day_before():
    before = DayRange(date(2026, 10, 12), date(2026, 10, 14)).period_before()

    assert before == DayRange(date(2026, 10, 9), date(2026, 10, 11))


def test_a_single_day_is_a_range():
    assert DayRange(date(2026, 10, 12), date(2026, 10, 12)).length == 1


def test_a_range_that_ends_before_it_starts_is_refused():
    with pytest.raises(InvalidRange):
        DayRange(date(2026, 10, 14), date(2026, 10, 12))
