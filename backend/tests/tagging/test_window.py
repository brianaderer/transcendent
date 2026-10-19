from datetime import date

from voices.tagging.window import third_day, window_start


def test_a_thread_first_seen_on_a_day_has_its_third_day_two_days_later():
    assert third_day(date(1999, 1, 30)) == date(1999, 2, 1)


def test_the_window_ending_on_a_thread_s_third_day_starts_on_its_first():
    first = date(1999, 1, 30)

    assert window_start(third_day(first)) == first
