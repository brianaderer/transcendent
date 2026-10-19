import threading
import time

import pytest

from voices.log import _trace_id, tracing
from voices.report.graph import every_version_at_once

BOTH_STARTED_WITHIN_SECONDS = 5


def test_each_versions_work_runs_inside_the_runs_trace():
    with tracing("run-abc"):
        seen = every_version_at_once(lambda version: (version, _trace_id.get()))

    assert seen == [("A", "run-abc"), ("B", "run-abc")]


def test_both_versions_run_at_once():
    both_started = threading.Barrier(2, timeout=BOTH_STARTED_WITHIN_SECONDS)

    def wait_for_the_other(version):
        both_started.wait()  # breaks, raising, if the other version never starts alongside
        return version

    assert every_version_at_once(wait_for_the_other) == ["A", "B"]


def test_results_come_back_in_the_order_of_the_versions_even_when_a_finishes_last():
    def a_finishes_last(version):
        time.sleep(0.2 if version == "A" else 0)
        return version.lower()

    assert every_version_at_once(a_finishes_last) == ["a", "b"]


def test_a_versions_failure_is_raised_as_it_was():
    def b_fails(version):
        if version == "B":
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        return version

    with pytest.raises(RuntimeError, match="^OPENROUTER_API_KEY is not set$"):
        every_version_at_once(b_fails)
