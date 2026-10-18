from fastapi.testclient import TestClient

from voices.api.main import ApiServices, create_app


async def two_events(_stream):
    yield "data: one\n\n"
    yield "data: two\n\n"


def client_with(status=dict):
    return TestClient(create_app(ApiServices({}, status, two_events)))


def test_ingestion_status_reports_what_the_ledger_says_and_how_many_days_are_wanted():
    status = {"days_done": 23, "posts": 9412, "latest_day": "2026-09-14"}

    response = client_with(lambda: status).get("/api/ingestion")

    assert response.json() == {**status, "days_wanted": 56}


def test_the_ingestion_stream_sends_each_event_as_it_comes():
    response = client_with().get("/api/streams/ingestion/events")

    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == "data: one\n\ndata: two\n\n"


def test_an_unknown_stream_is_not_found():
    assert client_with().get("/api/streams/nope/events").status_code == 404
