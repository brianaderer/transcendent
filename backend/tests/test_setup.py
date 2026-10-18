import pytest

from voices.db.setup import DatabaseNotReady, wait_for


def test_waiting_returns_as_soon_as_the_attempt_succeeds():
    attempts = iter([ConnectionError(), ConnectionError(), "connected"])

    def connect():
        outcome = next(attempts)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    assert wait_for(connect, tries=5, pause_seconds=0) == "connected"


def test_waiting_gives_up_after_the_last_try():
    def connect():
        raise ConnectionError("refused")

    with pytest.raises(DatabaseNotReady):
        wait_for(connect, tries=3, pause_seconds=0)
