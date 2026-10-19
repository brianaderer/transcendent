import io
import json
import logging

import pytest

from voices.log import JsonFormatter, configure_logging, log_event, tracing


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


@pytest.fixture
def restore_root_logging():
    saved_handlers, saved_level = logging.root.handlers[:], logging.root.level
    yield
    for handler in logging.root.handlers:
        handler.close()
    logging.root.handlers, logging.root.level = saved_handlers, saved_level


def test_configure_logging_writes_json_lines_to_the_service_file(tmp_path, restore_root_logging):
    log_dir = tmp_path / "not-yet-created"

    configure_logging("api", str(log_dir))
    log_event(logging.getLogger("test.file"), "api.started")

    [line] = [json.loads(text) for text in (log_dir / "api.jsonl").read_text().splitlines()]
    assert line["event"] == "api.started"


def test_extra_fields_cannot_overwrite_the_standard_ones():
    logger, stream = capture(service="api")

    with tracing("run-1"):
        log_event(logger, "x", service="other", trace_id="forged")

    [line] = lines(stream)
    assert line["service"] == "api"
    assert line["trace_id"] == "run-1"


def test_a_service_must_name_itself_before_logging(tmp_path):
    with pytest.raises(ValueError):
        configure_logging("", str(tmp_path))


@pytest.mark.parametrize("field", ["name", "msg", "args", "levelname", "message"])
def test_a_field_named_like_a_log_record_attribute_is_logged_as_given(field):
    logger, stream = capture()

    log_event(logger, "measurement.done", **{field: "topics_found"})

    [line] = lines(stream)
    assert line[field] == "topics_found"
    assert line["event"] == "measurement.done"


def test_a_line_carries_only_the_fields_it_was_given():
    logger, stream = capture()
    standard = {"time", "service", "level", "event", "trace_id"}

    log_event(logger, "plain", run_id="r")
    log_event(logger, "clashing", name="n")

    plain, clashing = lines(stream)
    assert set(plain) == standard | {"run_id"}
    assert set(clashing) == standard | {"name"}
