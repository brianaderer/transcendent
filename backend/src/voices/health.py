"""Checks that the services the API depends on are answering."""

import logging

import psycopg
import redis

from voices.log import log_event

CHECK_TIMEOUT_SECONDS = 2

logger = logging.getLogger(__name__)


def database_is_reachable(database_url: str) -> bool:
    try:
        with psycopg.connect(database_url, connect_timeout=CHECK_TIMEOUT_SECONDS) as connection:
            connection.execute("SELECT 1")
        return True
    except psycopg.Error as error:
        log_event(logger, "health.database_unreachable", error=str(error))
        return False


def queue_is_reachable(redis_url: str) -> bool:
    try:
        queue = redis.Redis.from_url(redis_url, socket_connect_timeout=CHECK_TIMEOUT_SECONDS)
        return bool(queue.ping())
    except redis.RedisError as error:
        log_event(logger, "health.queue_unreachable", error=str(error))
        return False
