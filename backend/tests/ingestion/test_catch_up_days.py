from datetime import UTC, date, datetime

from voices.ingestion.catch_up import last_complete_day, missing_days


def test_a_day_counts_as_complete_six_hours_after_it_ends():
    assert last_complete_day(datetime(2026, 10, 18, 6, 0, tzinfo=UTC)) == date(2026, 10, 17)
    assert last_complete_day(datetime(2026, 10, 18, 5, 59, tzinfo=UTC)) == date(2026, 10, 16)


def test_an_empty_database_is_missing_the_whole_history_oldest_first():
    days = missing_days(last_complete=date(2026, 10, 17), done=set(), history_days=56)

    assert len(days) == 56
    assert days[0] == date(2026, 8, 23)
    assert days[-1] == date(2026, 10, 17)


def test_only_days_not_yet_done_are_missing():
    done = {date(2026, 10, 15), date(2026, 10, 16)}

    assert missing_days(date(2026, 10, 17), done, history_days=3) == [date(2026, 10, 17)]


def test_nothing_is_missing_when_every_day_is_done():
    done = {date(2026, 10, 16), date(2026, 10, 17)}

    assert missing_days(date(2026, 10, 17), done, history_days=2) == []
