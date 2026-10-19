from datetime import date

from fastapi.testclient import TestClient

from voices.api.main import ApiServices, create_app
from voices.explore.explore import InvalidRange
from voices.explore.shapes import DayCount, Days, Map, MapPoint, Topic


async def no_events(_stream):
    return
    yield  # never reached; its presence makes this an (empty) async generator


class FakeExplore:
    def __init__(self):
        self.asked = None

    def days(self):
        return Days(days=[DayCount(day=date(2026, 10, 12), posts=4)], latest_day=date(2026, 10, 12))

    def topics(self, start, end):
        self.asked = (start, end)
        if end < start:
            raise InvalidRange("the range ends before it starts")
        return [
            Topic(
                id=1,
                label="Impellers",
                description="d",
                first_seen=date(2026, 9, 1),
                engagement=7,
                posts=2,
                daily=[5, 2],
                direction="rising",
            )
        ]

    def map(self, start, end):
        point = MapPoint(
            id="a",
            thread_id="a",
            kind="post",
            author="salty",
            day=start,
            title="Impellers",
            excerpt="Why?",
            topic_id=1,
            x=0.5,
            y=-0.5,
        )
        return Map(points=[point])


def client(explore=None):
    services = ApiServices({}, dict, no_events, explore or FakeExplore())
    return TestClient(create_app(services))


def test_days_are_posts_per_day_across_the_history():
    body = client().get("/api/days").json()

    assert body == {"days": [{"day": "2026-10-12", "posts": 4}], "latest_day": "2026-10-12"}


def test_topics_are_asked_for_the_range_in_the_address():
    explore = FakeExplore()

    body = client(explore).get("/api/topics?start=2026-10-12&end=2026-10-13").json()

    assert explore.asked == (date(2026, 10, 12), date(2026, 10, 13))
    assert body[0]["direction"] == "rising" and body[0]["daily"] == [5, 2]


def test_the_map_sends_each_point_with_its_place():
    body = client().get("/api/map?start=2026-10-12&end=2026-10-12").json()

    assert body["points"][0]["x"] == 0.5 and body["points"][0]["topic_id"] == 1


def test_a_range_that_ends_before_it_starts_is_a_bad_request():
    response = client().get("/api/topics?start=2026-10-13&end=2026-10-12")

    assert response.status_code == 422
    assert "ends before it starts" in response.json()["detail"]


def test_a_range_needs_both_ends():
    assert client().get("/api/map?start=2026-10-12").status_code == 422
