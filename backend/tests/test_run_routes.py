from datetime import date

from fastapi.testclient import TestClient

from tests.stand_ins import FakeRuns, stand_in_services
from voices.api.main import create_app
from voices.explore.day_range import DayRange


def client(runs):
    return TestClient(create_app(stand_in_services(runs=runs)))


def test_starting_a_run_for_a_range_answers_with_its_id_and_stream():
    runs = FakeRuns()

    body = client(runs).post("/api/runs", json={"start": "2026-10-12", "end": "2026-10-18"}).json()

    assert runs.started == DayRange(date(2026, 10, 12), date(2026, 10, 18))
    assert body == {"run_id": "0123456789ab", "stream": "run-0123456789ab"}


def test_a_backwards_range_is_refused():
    response = client(FakeRuns()).post(
        "/api/runs", json={"start": "2026-10-18", "end": "2026-10-12"}
    )

    assert response.status_code == 422


def test_a_runs_state_is_read_back():
    assert client(FakeRuns()).get("/api/runs/0123456789ab").json()["state"] == "running"


def test_an_unknown_run_is_not_found():
    assert client(FakeRuns()).get("/api/runs/ffffffffffff").status_code == 404


def test_a_runs_live_events_have_a_stream_and_other_names_still_do_not():
    events = client(FakeRuns())

    assert events.get("/api/streams/run-0123456789ab/events").status_code == 200
    assert events.get("/api/streams/run-xyz/events").status_code == 404
