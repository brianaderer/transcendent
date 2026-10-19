from voices.log import _trace_id, tracing
from voices.worker.report_task import in_parallel


def test_both_versions_run_inside_the_runs_trace():
    def trace_seen(version):
        return (version, _trace_id.get())

    with tracing("run-abc"):
        seen = list(in_parallel(trace_seen, ["A", "B"]))

    assert seen == [("A", "run-abc"), ("B", "run-abc")]


def test_results_come_back_in_the_order_of_the_versions():
    assert list(in_parallel(str.lower, ["B", "A"])) == ["b", "a"]
