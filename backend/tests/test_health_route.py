from fastapi.testclient import TestClient

from voices.api.main import ApiServices, create_app


async def no_events(_stream):
    return
    yield


def services_with(checks):
    return ApiServices(health_checks=checks, ingestion_status=dict, event_stream=no_events)


def client_with(database_up, queue_up):
    checks = {"database": lambda: database_up, "queue": lambda: queue_up}
    return TestClient(create_app(services_with(checks)))


def test_health_is_ok_when_every_dependency_answers():
    response = client_with(database_up=True, queue_up=True).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": True, "queue": True}}


def test_health_names_the_dependency_that_is_down():
    response = client_with(database_up=True, queue_up=False).get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "checks": {"database": True, "queue": False}}


def test_every_request_is_logged_with_its_outcome(caplog):
    caplog.set_level("INFO")

    client_with(database_up=True, queue_up=True).get("/api/health")

    [record] = [r for r in caplog.records if r.getMessage() == "api.request"]
    assert (record.method, record.path, record.status) == ("GET", "/api/health", 200)


def test_a_request_that_fails_is_still_logged(caplog):
    def broken_check():
        raise RuntimeError("check crashed")

    client = TestClient(
        create_app(services_with({"database": broken_check})), raise_server_exceptions=False
    )
    caplog.set_level("INFO")

    client.get("/api/health")

    [record] = [r for r in caplog.records if r.getMessage() == "api.request_failed"]
    assert record.path == "/api/health"
