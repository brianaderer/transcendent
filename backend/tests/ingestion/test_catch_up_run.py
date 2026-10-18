from datetime import UTC, date, datetime

import pytest

from voices.ingestion.catch_up import CatchUp

NOW = datetime(2026, 10, 18, 7, tzinfo=UTC)


class FakeLedger:
    def __init__(self, done=()):
        self.done, self.marks = set(done), []

    def done_days(self):
        return self.done

    def mark_running(self, day):
        self.marks.append(("running", day))

    def mark_done(self, day, counts):
        self.marks.append(("done", day))

    def mark_failed(self, day, error):
        self.marks.append(("failed", day))


class Recorder:
    def __init__(self):
        self.events = []

    def __call__(self, event_type, **body):
        self.events.append((event_type, body.get("day")))


def test_each_missing_day_is_processed_oldest_first_and_marked_done():
    ledger, events, processed = FakeLedger(), Recorder(), []

    CatchUp(ledger, lambda day: processed.append(day) or {}, events).run(NOW, history_days=2)

    assert processed == [date(2026, 10, 16), date(2026, 10, 17)]
    assert ("done", date(2026, 10, 17)) in ledger.marks
    assert events.events[0] == ("catch_up.started", None)
    assert events.events[-1] == ("catch_up.finished", None)


def test_a_failing_day_is_marked_failed_and_stops_the_catch_up():
    ledger, events = FakeLedger(), Recorder()

    def process(day):
        raise RuntimeError("archive down")

    with pytest.raises(RuntimeError):
        CatchUp(ledger, process, events).run(NOW, history_days=2)

    assert ledger.marks == [("running", date(2026, 10, 16)), ("failed", date(2026, 10, 16))]
    assert ("day.failed", "2026-10-16") in events.events
