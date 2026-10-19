from fastapi.testclient import TestClient

from tests.stand_ins import FakeSync, stand_in_services
from voices.api.main import create_app


def test_sync_now_asks_for_a_catch_up_and_answers_with_what_it_will_fetch():
    sync = FakeSync()

    response = TestClient(create_app(stand_in_services(sync=sync))).post("/api/catch-up")

    assert sync.asked_at is not None
    assert response.json() == {
        "queued": True,
        "reason": "days_missing",
        "missing_days": ["2026-10-19"],
        "next_complete_day": "2026-10-20",
        "next_complete_at": "2026-10-21T06:00:00Z",
    }
