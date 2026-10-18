import pytest

from voices.worker import app as worker


def test_the_worker_logs_under_its_container_name(monkeypatch):
    calls = []
    monkeypatch.setattr(worker, "configure_logging", lambda *args: calls.append(args))

    worker.use_json_logging()

    assert calls == [(worker.settings.service_name, worker.settings.log_dir)]


def test_a_failed_catch_up_tries_again_by_itself_in_ten_minutes(monkeypatch):
    def fail():
        raise RuntimeError("archive down")

    retried = []
    monkeypatch.setattr(worker, "catch_up_now", fail)
    monkeypatch.setattr(worker.catch_up, "retry", lambda **kw: retried.append(kw) or RuntimeError())

    with pytest.raises(RuntimeError):
        worker.catch_up.run()

    assert retried[0]["countdown"] == worker.RETRY_FAILED_CATCH_UP_SECONDS == 600
