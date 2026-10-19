"""Keeps each range's map in Redis, so a range is flattened once until a new day arrives."""

from typing import Protocol

KEPT_SECONDS = 2 * 24 * 60 * 60  # a key names the latest day, so older maps just age out


class Redis(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def set(self, key: str, value: str, ex: int) -> object: ...


class RedisMapCache:
    def __init__(self, redis: Redis):
        self.redis = redis

    def get(self, key: str) -> str | None:
        value = self.redis.get(key)
        return value.decode() if value else None

    def put(self, key: str, value: str) -> None:
        self.redis.set(key, value, ex=KEPT_SECONDS)
