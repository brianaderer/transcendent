"""Settings read from the environment (the `.env` file under Docker Compose)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://voices:voices@postgres:5432/voices"
    redis_url: str = "redis://redis:6379/0"
    log_dir: str = "/var/log/voices"
    openrouter_api_key: str = ""


def load_settings() -> Settings:
    return Settings()
