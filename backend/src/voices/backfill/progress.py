"""Where the backfill keeps how far it has got, so `GET /api/ingestion` can say so to a page
opened mid-way (atlas plate 07). Kept in Redis while the backfill runs and cleared when it
finishes; one left behind by a stopped worker is overwritten when the backfill starts again."""

import json
from typing import Protocol

PROGRESS_KEY = "backfill:progress"


class Redis(Protocol):
    def set(self, key: str, value: str) -> object: ...
    def get(self, key: str) -> bytes | None: ...
    def exists(self, key: str) -> int: ...
    def delete(self, key: str) -> object: ...


class RedisBackfillProgress:
    def __init__(self, redis: Redis):
        self.redis = redis

    def record(self, what: str, done: int, total: int) -> None:
        self.redis.set(PROGRESS_KEY, json.dumps({"what": what, "done": done, "total": total}))

    def read(self) -> dict | None:
        """What is being prepared (posts, threads or topics), how many are done and of how
        many; None when no backfill is under way."""
        value = self.redis.get(PROGRESS_KEY)
        return json.loads(value) if value else None

    def recorded(self) -> bool:
        return self.redis.exists(PROGRESS_KEY) > 0

    def clear(self) -> None:
        self.redis.delete(PROGRESS_KEY)
