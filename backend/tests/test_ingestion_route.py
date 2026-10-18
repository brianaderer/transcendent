from fastapi.testclient import TestClient

from voices.api.main import ApiServices, create_app


def test_ingestion_status_reports_what_the_ledger_says():
    status = {"days_done": 23, "days_wanted": 56, "posts": 9412, "latest_day": "2026-09-14"}
    services = ApiServices(health_checks={}, ingestion_status=lambda: status, event_stream=None)

    response = TestClient(create_app(services)).get("/api/ingestion")

    assert response.json() == status
