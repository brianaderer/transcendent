from datetime import date

from fastapi.testclient import TestClient

from tests.stand_ins import FakeRetrievals, stand_in_services
from voices.api.main import create_app
from voices.explore.day_range import DayRange
from voices.retrievals.shapes import RetrievalFilter

WEEK = "start=2026-10-12&end=2026-10-18"
DAYS = DayRange(date(2026, 10, 12), date(2026, 10, 18))


def client(**chosen):
    return TestClient(create_app(stand_in_services(**chosen)))


def test_a_topic_is_sent_with_its_engagement_typical_posts_and_decisions():
    body = client().get("/api/topics/1").json()

    assert (body["label"], body["keywords"], body["last_seen"]) == (
        "Impellers",
        ["impeller"],
        "2026-10-12",
    )
    assert body["daily"][0] == {
        "day": "2026-10-12",
        "posts": 1,
        "comments": 2,
        "upvotes": 3,
        "people": 2,
    }
    assert body["typical_posts"][0]["author"] == "salty"
    assert body["decisions"][0] == {
        "day": "2026-10-12",
        "decision": "mint",
        "threads": 3,
        "reason": "New.",
    }


def test_a_topic_that_does_not_exist_is_not_found():
    response = client().get("/api/topics/2")

    assert response.status_code == 404
    assert response.json()["detail"] == "no topic with id 2"


def test_retrievals_are_the_report_agents_from_every_run_unless_asked_otherwise():
    retrievals = FakeRetrievals()

    body = client(retrievals=retrievals).get(f"/api/retrievals?{WEEK}").json()

    assert retrievals.asked == RetrievalFilter(agent="report", days=DAYS, run=None)
    assert body == {"agent": "report", "runs": [], "total": 0, "posts": [], "topics": []}


def test_retrievals_can_be_asked_for_one_agent_and_one_run():
    retrievals = FakeRetrievals()

    client(retrievals=retrievals).get(f"/api/retrievals?{WEEK}&agent=tagging&run=r1")

    assert retrievals.asked == RetrievalFilter(agent="tagging", days=DAYS, run="r1")


def test_an_agent_that_does_not_exist_is_a_bad_request():
    assert client().get(f"/api/retrievals?{WEEK}&agent=nobody").status_code == 422


def test_a_retrieval_range_that_ends_before_it_starts_is_a_bad_request():
    response = client().get("/api/retrievals?start=2026-10-18&end=2026-10-12")

    assert response.status_code == 422


def test_the_new_operations_are_named_after_their_route_functions():
    paths = client().get("/api/openapi.json").json()["paths"]

    assert paths["/api/topics/{topic_id}"]["get"]["operationId"] == "report_topic"
    assert paths["/api/retrievals"]["get"]["operationId"] == "report_retrievals"
