"""The Sync now button: asks the worker for a catch-up on demand (atlas plate 40).

It works out which days are missing exactly as the catch-up does, so the answer says what
the catch-up will fetch, and a day still inside its six hours is never asked for.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel

from voices.config import HISTORY_DAYS
from voices.ingestion.catch_up import completes_at, last_complete_day, missing_days
from voices.tasks import Queue

CATCH_UP_TASK = "voices.catch_up"  # the worker's task (voices.worker.app.catch_up)

SyncReason = Literal["days_missing", "nothing_new", "already_running"]


class SyncAnswer(BaseModel):
    queued: bool
    reason: SyncReason
    missing_days: list[date]  # what the catch-up will fetch, oldest first
    next_complete_day: date  # the first day not yet complete
    next_complete_at: datetime  # when it becomes complete, in UTC


@dataclass(frozen=True)
class CatchUpProgress:
    """What a sync reads before asking: the days done, and whether a catch-up is busy."""

    done_days: Callable[[], set[date]]
    busy: Callable[[], bool]


class SyncNow:
    def __init__(self, progress: CatchUpProgress, queue: Queue):
        self.progress = progress
        self.queue = queue

    def request(self, now: datetime) -> SyncAnswer:
        """Queue a catch-up when a complete day is missing and none is busy; say what it will
        fetch, or why nothing was queued."""
        last_complete = last_complete_day(now)
        missing = missing_days(last_complete, self.progress.done_days(), HISTORY_DAYS)
        reason = self._reason_for(missing)
        if reason == "days_missing":
            self.queue(CATCH_UP_TASK, [])
        next_day = last_complete + timedelta(days=1)
        return SyncAnswer(
            queued=reason == "days_missing",
            reason=reason,
            missing_days=missing,
            next_complete_day=next_day,
            next_complete_at=completes_at(next_day),
        )

    def _reason_for(self, missing: list[date]) -> SyncReason:
        if self.progress.busy():
            return "already_running"
        return "days_missing" if missing else "nothing_new"


def a_catch_up_is_busy(ingestion_status: dict, backfill_progress: dict | None) -> bool:
    """A day is being loaded, or the first boot is still preparing the seed before its
    catch-up; either way a catch-up holds the worker's lock, so a second would do nothing."""
    return ingestion_status["running_day"] is not None or backfill_progress is not None
