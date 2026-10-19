from datetime import UTC, date, datetime, timedelta

from voices.config import HISTORY_DAYS
from voices.ingestion.sync_now import (
    CATCH_UP_TASK,
    CatchUpProgress,
    SyncNow,
    a_catch_up_is_busy,
)

MORNING_OF_THE_20TH = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)  # the 19th is complete


def history_through(last_day):
    return {last_day - timedelta(days=n) for n in range(HISTORY_DAYS)}


def sync_with(done, busy=False):
    queued = []
    progress = CatchUpProgress(done_days=lambda: done, busy=lambda: busy)
    sync = SyncNow(progress, lambda name, arguments: queued.append((name, arguments)))
    return sync, queued


def test_a_complete_day_not_yet_loaded_queues_the_catch_up_and_names_the_day():
    sync, queued = sync_with(history_through(date(2026, 10, 18)))

    answer = sync.request(MORNING_OF_THE_20TH)

    assert queued == [(CATCH_UP_TASK, [])]
    assert answer.queued is True
    assert answer.reason == "days_missing"
    assert answer.missing_days == [date(2026, 10, 19)]


def test_nothing_is_queued_when_every_complete_day_is_loaded_and_the_next_one_is_named():
    sync, queued = sync_with(history_through(date(2026, 10, 19)))

    answer = sync.request(MORNING_OF_THE_20TH)

    assert queued == []
    assert answer.queued is False
    assert answer.reason == "nothing_new"
    assert answer.missing_days == []
    assert answer.next_complete_day == date(2026, 10, 20)
    assert answer.next_complete_at == datetime(2026, 10, 21, 6, 0, tzinfo=UTC)


def test_a_day_still_inside_its_six_hours_is_not_fetched():
    sync, queued = sync_with(history_through(date(2026, 10, 18)))

    answer = sync.request(datetime(2026, 10, 20, 5, 59, tzinfo=UTC))

    assert queued == []
    assert answer.reason == "nothing_new"
    assert answer.next_complete_day == date(2026, 10, 19)


def test_nothing_is_queued_while_a_catch_up_is_busy_but_the_missing_days_are_still_named():
    sync, queued = sync_with(history_through(date(2026, 10, 18)), busy=True)

    answer = sync.request(MORNING_OF_THE_20TH)

    assert queued == []
    assert answer.queued is False
    assert answer.reason == "already_running"
    assert answer.missing_days == [date(2026, 10, 19)]


def test_a_catch_up_is_busy_while_a_day_is_running_or_the_seed_is_being_prepared():
    idle = {"running_day": None}
    preparing = {"what": "posts", "done": 1, "total": 9}

    assert a_catch_up_is_busy(idle, None) is False
    assert a_catch_up_is_busy({"running_day": "2026-10-19"}, None) is True
    assert a_catch_up_is_busy(idle, preparing) is True
