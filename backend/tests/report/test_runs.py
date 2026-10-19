from datetime import date

import pytest

from tests.stand_ins import FakeRedis
from voices.explore.day_range import DayRange
from voices.report.launcher import COMPARE_TASK, RunLauncher
from voices.report.runs import (
    KEPT_SECONDS,
    RunNotFound,
    RunStore,
    is_run_stream,
    new_run_id,
    stream_of,
)


def test_a_started_run_is_marked_running_and_queued_with_its_range():
    queued, store = [], RunStore(FakeRedis())

    started = RunLauncher(store, lambda name, args: queued.append((name, args))).start(
        DayRange(date(2026, 10, 12), date(2026, 10, 18))
    )

    assert queued == [(COMPARE_TASK, [started.run_id, "2026-10-12", "2026-10-18"])]
    assert started.stream == f"run-{started.run_id}"
    assert store.state(started.run_id).state == "running"


def test_a_failed_run_keeps_its_reason_for_a_day():
    redis = FakeRedis()
    store = RunStore(redis)

    store.mark_failed("abc", "OPENROUTER_API_KEY is not set")

    assert store.state("abc").reason == "OPENROUTER_API_KEY is not set"
    assert redis.expiries["run:abc"] == KEPT_SECONDS


def test_a_run_never_started_is_not_found():
    with pytest.raises(RunNotFound):
        RunStore(FakeRedis()).state("nope")


def test_a_runs_own_stream_is_recognised_and_other_names_are_not():
    run_id = new_run_id()

    assert is_run_stream(stream_of(run_id))
    assert not is_run_stream("run-abc")
    assert not is_run_stream(f"{stream_of(run_id)}0")
    assert not is_run_stream("ingestion")
