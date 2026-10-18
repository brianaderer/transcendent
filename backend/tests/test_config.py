from voices.config import load_settings


def test_settings_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db:5432/x")
    monkeypatch.setenv("REDIS_URL", "redis://q:6379/0")
    monkeypatch.setenv("LOG_DIR", "/tmp/logs")

    settings = load_settings()

    assert settings.database_url == "postgresql://u:p@db:5432/x"
    assert settings.redis_url == "redis://q:6379/0"
    assert settings.log_dir == "/tmp/logs"


def test_the_model_key_may_be_missing_until_a_model_is_called(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    assert load_settings().openrouter_api_key == ""


def test_service_name_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("SERVICE_NAME", "beat")

    assert load_settings().service_name == "beat"
