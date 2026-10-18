from voices.config import load_settings


def test_each_container_names_itself_in_the_logs(monkeypatch):
    monkeypatch.setenv("SERVICE_NAME", "beat")

    assert load_settings().service_name == "beat"
