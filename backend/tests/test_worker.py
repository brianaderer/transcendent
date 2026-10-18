from voices.worker import app as worker


def test_the_worker_logs_under_its_container_name(monkeypatch):
    calls = []
    monkeypatch.setattr(worker, "configure_logging", lambda *args: calls.append(args))

    worker.use_json_logging()

    assert calls == [(worker.settings.service_name, worker.settings.log_dir)]
