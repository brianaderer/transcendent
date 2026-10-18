import io
import json
import logging

from voices.log import JsonFormatter, log_event, tracing


def capture(service="api"):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter(service))
    logger = logging.getLogger(f"test.{id(stream)}")
    logger.handlers = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger, stream


def lines(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_each_event_is_one_json_line_with_the_standard_fields():
    logger, stream = capture(service="worker")

    log_event(logger, "day.fetched", posts=12)

    [line] = lines(stream)
    assert line["service"] == "worker"
    assert line["level"] == "info"
    assert line["event"] == "day.fetched"
    assert line["posts"] == 12
    assert line["time"].endswith("Z")


def test_events_inside_a_trace_carry_its_id():
    logger, stream = capture()

    with tracing("run-42"):
        log_event(logger, "run.started")
    log_event(logger, "after")

    inside, outside = lines(stream)
    assert inside["trace_id"] == "run-42"
    assert outside["trace_id"] is None


def test_an_exception_is_logged_with_its_full_error():
    logger, stream = capture()

    try:
        raise ValueError("bad day")
    except ValueError:
        logger.exception("day.failed")

    [line] = lines(stream)
    assert line["level"] == "error"
    assert "ValueError: bad day" in line["error"]
