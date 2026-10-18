"""Live events to the frontend (atlas plate 41): published on Redis, streamed as SSE.

Events are live only and never stored; logs are the permanent record (plate 05).
"""

import json
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Protocol

from voices.log import log_event

HEARTBEAT_SECONDS = 15  # keeps idle connections open through proxies

logger = logging.getLogger(__name__)


class Publisher(Protocol):
    def publish(self, channel: str, message: str) -> object: ...


class RedisEvents:
    def __init__(self, redis: Publisher):
        self.redis = redis

    def emit(self, stream: str, event_type: str, **body: object) -> None:
        event = {"type": event_type, "time": _now(), **body}
        self.redis.publish(channel_for(stream), json.dumps(event, default=str))
        log_event(logger, event_type, stream=stream, **body)


def channel_for(stream: str) -> str:
    return f"events:{stream}"


def as_server_sent_event(message: str) -> str:
    return f"data: {message}\n\n"


async def server_sent_events(redis_url: str, stream: str) -> AsyncIterator[str]:
    """Every event published on the stream from now on, with a heartbeat while it's quiet."""
    import redis.asyncio as aioredis

    connection = aioredis.Redis.from_url(redis_url)
    async with connection.pubsub() as subscription:
        await subscription.subscribe(channel_for(stream))
        while True:
            message = await subscription.get_message(
                ignore_subscribe_messages=True, timeout=HEARTBEAT_SECONDS
            )
            yield as_server_sent_event(message["data"].decode()) if message else ": heartbeat\n\n"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
