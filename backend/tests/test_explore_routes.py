from datetime import date

from fastapi.testclient import TestClient

from tests.stand_ins import FakeExplore, no_events
from voices.api.main import SMALLEST_RESPONSE_TO_COMPRESS, ApiServices, create_app
from voices.explore.day_range import DayRange


def client(explore=None):
    services = ApiServices({}, dict, no_events, explore or FakeExplore())
    return TestClient(create_app(services))


def test_days_are_posts_per_day_across_the_history():
    body = client().get("/api/days").json()

    assert body == {"days": [{"day": "2026-10-12", "posts": 4}], "latest_day": "2026-10-12"}


def test_topics_are_asked_for_the_range_in_the_address():
    explore = FakeExplore()

    body = client(explore).get("/api/topics?start=2026-10-12&end=2026-10-13").json()

    assert explore.asked == DayRange(date(2026, 10, 12), date(2026, 10, 13))
    assert body[0]["direction"] == "rising"
    assert body[0]["daily"] == [5, 2]


def test_the_map_sends_each_point_with_its_place():
    body = client().get("/api/map?start=2026-10-12&end=2026-10-12").json()

    assert (body["points"][0]["x"], body["points"][0]["thread_topic_id"]) == (0.5, 1)


def test_a_range_that_ends_before_it_starts_is_a_bad_request():
    for route in ["topics", "map"]:
        response = client().get(f"/api/{route}?start=2026-10-13&end=2026-10-12")

        assert response.status_code == 422
        assert "ends before it starts" in response.json()["detail"]


def test_a_range_needs_both_ends():
    assert client().get("/api/map?start=2026-10-12").status_code == 422


def test_a_large_map_is_sent_compressed():
    big = FakeExplore(points=SMALLEST_RESPONSE_TO_COMPRESS // 100)

    response = client(big).get(
        "/api/map?start=2026-10-12&end=2026-10-12", headers={"Accept-Encoding": "gzip"}
    )

    assert response.headers["content-encoding"] == "gzip"
