"""Keeps each range's map in Redis, so a range is flattened once until a new day arrives."""

from collections.abc import Iterable
from typing import Protocol

KEPT_SECONDS = 2 * 24 * 60 * 60  # a key names the latest day, so older maps just age out
MAP_KEY_PREFIX = "map:"


class Redis(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def set(self, key: str, value: str, ex: int) -> object: ...
    def scan_iter(self, match: str) -> Iterable[bytes | str]: ...
    def delete(self, key: bytes | str) -> object: ...


class RedisMapCache:
    def __init__(self, redis: Redis):
        self.redis = redis

    def get(self, key: str) -> str | None:
        value = self.redis.get(key)
        return value.decode() if value else None

    def put(self, key: str, value: str) -> None:
        self.redis.set(key, value, ex=KEPT_SECONDS)

    def forget_all(self) -> None:
        """Drops every kept map. The backfill calls this when it finishes, so no map drawn
        while the vectors were still coming back is shown again (atlas plate 07)."""
        for key in self.redis.scan_iter(match=f"{MAP_KEY_PREFIX}*"):
            self.redis.delete(key)
