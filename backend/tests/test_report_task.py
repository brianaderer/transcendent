from datetime import date

import pytest

from tests.stand_ins import FakeRedis
from voices.explore.day_range import DayRange
from voices.report.comparison_run import RunResult
from voices.report.runs import RunStore
from voices.worker.report_task import RunJob, RunRecord, run_and_keep_result

JOB = RunJob("abc123", DayRange(date(2026, 10, 12), date(2026, 10, 18)))


class FinishingComparison:
    def run(self, run_id, days):
        return RunResult(
            run_id=run_id,
            start=days.start,
            end=days.end,
            model="m",
            main_topics=[],
            instructions={},
            versions=[],
        )


class FailingComparison:
    def run(self, run_id, days):
        raise RuntimeError("the model is unreachable")


def _record():
    announced = []
    record = RunRecord(RunStore(FakeRedis()), lambda kind, **body: announced.append((kind, body)))
    return record, announced


def _record_noting_the_state_when_announced():
    seen = []
    runs = RunStore(FakeRedis())
    record = RunRecord(runs, lambda kind, **body: seen.append(runs.state(JOB.run_id).state))
    runs.mark_running(JOB.run_id)
    return record, seen


def test_a_finished_run_keeps_its_result():
    record, announced = _record()

    run_and_keep_result(FinishingComparison(), record, JOB)

    kept = record.runs.state(JOB.run_id)
    assert kept.state == "finished"
    assert kept.result.run_id == JOB.run_id
    assert announced == [("run.finished", {})]


def test_finished_is_announced_only_once_the_result_can_be_read():
    record, seen_when_announced = _record_noting_the_state_when_announced()

    run_and_keep_result(FinishingComparison(), record, JOB)

    assert seen_when_announced == ["finished"]


def test_failed_is_announced_only_once_the_failure_can_be_read():
    record, seen_when_announced = _record_noting_the_state_when_announced()

    with pytest.raises(RuntimeError):
        run_and_keep_result(FailingComparison(), record, JOB)

    assert seen_when_announced == ["failed"]


def test_a_failed_run_is_marked_failed_announced_and_raised():
    record, announced = _record()

    with pytest.raises(RuntimeError, match="unreachable"):
        run_and_keep_result(FailingComparison(), record, JOB)

    kept = record.runs.state(JOB.run_id)
    assert (kept.state, kept.reason) == ("failed", "the model is unreachable")
    assert announced == [("run.failed", {"reason": "the model is unreachable"})]
