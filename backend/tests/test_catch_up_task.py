import pytest

from voices.worker.catch_up_task import CATCH_UP_LOCK, catch_up_once, forget_stale_catch_up


class FakeLock:
    def __init__(self, free):
        self.free, self.released = free, False

    def acquire(self, blocking):
        assert blocking is False
        return self.free

    def release(self):
        self.released = True


def test_a_catch_up_runs_when_no_other_is_running_and_then_frees_the_lock():
    lock, ran = FakeLock(free=True), []

    assert catch_up_once(lock, lambda: ran.append(True)) is True
    assert ran == [True]
    assert lock.released


def test_a_second_catch_up_does_nothing_while_one_is_running():
    lock, ran = FakeLock(free=False), []

    assert catch_up_once(lock, lambda: ran.append(True)) is False
    assert ran == []


def test_the_lock_is_freed_even_when_the_catch_up_fails():
    lock = FakeLock(free=True)

    def fail():
        raise RuntimeError("archive down")

    with pytest.raises(RuntimeError):
        catch_up_once(lock, fail)

    assert lock.released


def test_a_lock_left_by_a_crashed_worker_is_cleared_when_a_worker_starts():
    class FakeRedis:
        def __init__(self):
            self.deleted = []

        def delete(self, key):
            self.deleted.append(key)

    redis_client = FakeRedis()

    forget_stale_catch_up(redis_client)

    assert redis_client.deleted == [CATCH_UP_LOCK]
