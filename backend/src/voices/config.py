"""Settings read from the environment (the `.env` file under Docker Compose)."""

from pydantic_settings import BaseSettings

HISTORY_DAYS = 56  # how far back the app keeps r/sailing: eight weeks (atlas OPEN-7)


class Settings(BaseSettings):
    database_url: str = "postgresql://voices:voices@postgres:5432/voices"
    redis_url: str = "redis://redis:6379/0"
    log_dir: str = "/var/log/voices"
    openrouter_api_key: str = ""
    model_name: str = "anthropic/claude-sonnet-5.5"  # through OpenRouter (atlas OPEN-5)
    service_name: str = ""  # each container sets its own, so log lines say which one
    model_dir: str = "/home/voices/.cache/models"  # on the model-cache volume


def load_settings() -> Settings:
    return Settings()
