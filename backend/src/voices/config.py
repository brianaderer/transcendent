"""Settings read from the environment (the `.env` file under Docker Compose)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://voices:voices@postgres:5432/voices"
    redis_url: str = "redis://redis:6379/0"
    log_dir: str = "/var/log/voices"
    openrouter_api_key: str = ""
    service_name: str = ""  # each container sets its own, so log lines say which one
    model_dir: str = "/home/voices/.cache/models"  # on the model-cache volume


def load_settings() -> Settings:
    return Settings()
