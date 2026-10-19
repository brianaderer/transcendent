"""Starts comparison runs for the API and reads their state back (atlas plate 70)."""

from collections.abc import Callable

from pydantic import BaseModel

from voices.explore.day_range import DayRange
from voices.report.runs import RunState, RunStore, new_run_id, stream_of

COMPARE_TASK = "voices.compare"  # the worker's task (voices.worker.app.compare)

Queue = Callable[[str, list[str]], object]  # a task's name and its arguments


class RunStarted(BaseModel):
    run_id: str
    stream: str  # where the run's live events come (GET /api/streams/{stream}/events)


class RunLauncher:
    def __init__(self, store: RunStore, queue: Queue):
        self.store = store
        self.queue = queue

    def start(self, days: DayRange) -> RunStarted:
        run_id = new_run_id()
        self.store.mark_running(run_id)
        self.queue(COMPARE_TASK, [run_id, days.start.isoformat(), days.end.isoformat()])
        return RunStarted(run_id=run_id, stream=stream_of(run_id))

    def state(self, run_id: str) -> RunState:
        return self.store.state(run_id)
