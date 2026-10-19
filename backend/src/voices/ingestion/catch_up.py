"""The one ingestion operation: process every complete day not yet done, oldest first.

First start, the daily 06:00 run and waking up after downtime all call this; only the number
of missing days differs (atlas plate 40).
"""

from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from typing import Protocol

from voices.config import HISTORY_DAYS

ARCHIVE_CATCH_UP_HOURS = 6  # a day is complete once it's over and the archive has had this long


class Ledger(Protocol):
    def done_days(self) -> set[date]: ...
    def mark_running(self, day: date) -> None: ...
    def mark_done(self, day: date, counts: dict[str, int]) -> None: ...
    def mark_failed(self, day: date, error: str) -> None: ...


class Emit(Protocol):
    """Sends one live event on the ingestion stream (atlas plate 41)."""

    def __call__(self, event_type: str, **body: object) -> None: ...


def announce_step(emit: Emit, day: date, step: str, **numbers: int) -> None:
    """A step of the day's work is starting (`day.step`, atlas plate 41), with how much it
    has to get through: posts to embed, threads to group, groups to decide."""
    emit("day.step", day=day.isoformat(), step=step, **numbers)


ProcessDay = Callable[[date], dict[str, int]]


class CatchUp:
    def __init__(self, ledger: Ledger, process: ProcessDay, emit: Emit):
        self.ledger = ledger
        self.process = process
        self.emit = emit

    def run(self, now: datetime, history_days: int = HISTORY_DAYS) -> None:
        """Process the missing days in order; stop at the first that fails."""
        days = missing_days(last_complete_day(now), self.ledger.done_days(), history_days)
        self.emit("catch_up.started", days=len(days))
        for number, day in enumerate(days, start=1):
            self._process_one(day, progress=f"{number} of {len(days)}")
        self.emit("catch_up.finished", days=len(days))

    def _process_one(self, day: date, progress: str) -> None:
        self.ledger.mark_running(day)
        self.emit("day.started", day=day.isoformat(), progress=progress)
        try:
            counts = self.process(day)
        except Exception as error:
            reason = str(error) or type(error).__name__
            self.ledger.mark_failed(day, reason)
            self.emit("day.failed", day=day.isoformat(), error=reason)
            raise
        self.ledger.mark_done(day, counts)
        self.emit("day.finished", day=day.isoformat(), progress=progress, counts=counts)


def last_complete_day(now: datetime) -> date:
    return (now - timedelta(hours=ARCHIVE_CATCH_UP_HOURS)).date() - timedelta(days=1)


def completes_at(day: date) -> datetime:
    """The moment `day` becomes complete: last_complete_day returns it from then on."""
    day_ends = datetime.combine(day + timedelta(days=1), time(), UTC)
    return day_ends + timedelta(hours=ARCHIVE_CATCH_UP_HOURS)


def missing_days(last_complete: date, done: set[date], history_days: int) -> list[date]:
    first = last_complete - timedelta(days=history_days - 1)
    every_day = (first + timedelta(days=n) for n in range(history_days))
    return [day for day in every_day if day not in done]
