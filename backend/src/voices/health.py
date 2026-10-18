"""Checks that the services the API depends on are answering."""

import psycopg
import redis


def database_is_reachable(database_url: str) -> bool:
    try:
        with psycopg.connect(database_url, connect_timeout=2) as connection:
            connection.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False


def queue_is_reachable(redis_url: str) -> bool:
    try:
        return bool(redis.Redis.from_url(redis_url, socket_connect_timeout=2).ping())
    except redis.RedisError:
        return False
