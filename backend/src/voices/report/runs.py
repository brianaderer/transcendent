"""Where a comparison run's state is kept while the page needs it (atlas OPEN-24): running,
finished with its result, or failed with its reason. Kept in Redis for a day, then gone; there
is no run history."""

import json
import uuid
from typing import Literal, Protocol

from pydantic import BaseModel

from voices.report.comparison_run import RunResult

KEPT_SECONDS = 24 * 60 * 60
RUN_ID_HEX_DIGITS = 12


class RunState(BaseModel):
    state: Literal["running", "finished", "failed"]
    result: RunResult | None = None
    reason: str | None = None  # why it failed, in plain words


class Redis(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def set(self, key: str, value: str, ex: int) -> object: ...


class RunNotFound(Exception):
    pass


def new_run_id() -> str:
    return uuid.uuid4().hex[:RUN_ID_HEX_DIGITS]


def stream_of(run_id: str) -> str:
    """The live-event stream a run is announced on (atlas plate 41)."""
    return f"run-{run_id}"


class RunStore:
    def __init__(self, redis: Redis):
        self.redis = redis

    def mark_running(self, run_id: str) -> None:
        self._put(run_id, RunState(state="running"))

    def mark_finished(self, run_id: str, result: RunResult) -> None:
        self._put(run_id, RunState(state="finished", result=result))

    def mark_failed(self, run_id: str, reason: str) -> None:
        self._put(run_id, RunState(state="failed", reason=reason))

    def state(self, run_id: str) -> RunState:
        """Raises RunNotFound for a run never started, or older than a day."""
        stored = self.redis.get(_key(run_id))
        if stored is None:
            raise RunNotFound(run_id)
        return RunState.model_validate(json.loads(stored))

    def _put(self, run_id: str, state: RunState) -> None:
        self.redis.set(_key(run_id), state.model_dump_json(), ex=KEPT_SECONDS)


def _key(run_id: str) -> str:
    return f"run:{run_id}"
