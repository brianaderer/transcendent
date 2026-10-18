from fastapi.testclient import TestClient

from voices.api.main import create_app


def client_with(database_up, queue_up):
    checks = {"database": lambda: database_up, "queue": lambda: queue_up}
    return TestClient(create_app(checks))


def test_health_is_ok_when_every_dependency_answers():
    response = client_with(database_up=True, queue_up=True).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": True, "queue": True}}


def test_health_names_the_dependency_that_is_down():
    response = client_with(database_up=True, queue_up=False).get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "checks": {"database": True, "queue": False}}
