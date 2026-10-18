"""The one ingestion operation: process every complete day not yet done, oldest first.

First start, the daily 06:00 run and waking up after downtime all call this; only the number
of missing days differs (atlas plate 40).
"""

from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Protocol

HISTORY_DAYS = 56  # eight weeks (atlas OPEN-7)
ARCHIVE_CATCH_UP_HOURS = 6  # a day is complete once it's over and the archive has had this long


class Ledger(Protocol):
    def done_days(self) -> set[date]: ...
    def mark_running(self, day: date) -> None: ...
    def mark_done(self, day: date, counts: dict[str, int]) -> None: ...
    def mark_failed(self, day: date, error: str) -> None: ...


Emit = Callable[..., None]


def run_catch_up(
    now: datetime,
    ledger: Ledger,
    process: Callable[[date], dict[str, int]],
    emit: Emit,
    history_days: int = HISTORY_DAYS,
) -> None:
    days = missing_days(last_complete_day(now), ledger.done_days(), history_days)
    emit("ingestion", "catch_up.started", days=len(days))
    for number, day in enumerate(days, start=1):
        _process_one(day, ledger, process, emit, f"{number} of {len(days)}")
    emit("ingestion", "catch_up.finished", days=len(days))


def _process_one(day: date, ledger: Ledger, process, emit: Emit, progress: str) -> None:
    ledger.mark_running(day)
    emit("ingestion", "day.started", day=day.isoformat(), progress=progress)
    try:
        counts = process(day)
    except Exception as error:
        ledger.mark_failed(day, repr(error))
        emit("ingestion", "day.failed", day=day.isoformat(), error=repr(error))
        raise
    ledger.mark_done(day, counts)
    emit("ingestion", "day.finished", day=day.isoformat(), progress=progress, counts=counts)


def last_complete_day(now: datetime) -> date:
    return (now - timedelta(hours=ARCHIVE_CATCH_UP_HOURS)).date() - timedelta(days=1)


def missing_days(last_complete: date, done: set[date], history_days: int) -> list[date]:
    first = last_complete - timedelta(days=history_days - 1)
    every_day = (first + timedelta(days=n) for n in range(history_days))
    return [day for day in every_day if day not in done]
