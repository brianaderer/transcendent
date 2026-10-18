import psycopg
import redis

from voices import health


class RefusingRedis:
    def ping(self):
        raise redis.ConnectionError("refused")


class AnsweringRedis:
    def ping(self):
        return True


class AnsweringConnection:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, _sql):
        return None


def refuse(*_args, **_kwargs):
    raise psycopg.OperationalError("refused")


def test_database_check_is_false_when_postgres_refuses(monkeypatch):
    monkeypatch.setattr(health.psycopg, "connect", refuse)

    assert health.database_is_reachable("postgresql://x") is False


def test_database_check_is_true_when_postgres_answers(monkeypatch):
    monkeypatch.setattr(health.psycopg, "connect", lambda *_a, **_k: AnsweringConnection())

    assert health.database_is_reachable("postgresql://x") is True


def test_queue_check_is_false_when_redis_refuses(monkeypatch):
    monkeypatch.setattr(health.redis.Redis, "from_url", lambda *_a, **_k: RefusingRedis())

    assert health.queue_is_reachable("redis://x") is False


def test_queue_check_is_true_when_redis_answers(monkeypatch):
    monkeypatch.setattr(health.redis.Redis, "from_url", lambda *_a, **_k: AnsweringRedis())

    assert health.queue_is_reachable("redis://x") is True
