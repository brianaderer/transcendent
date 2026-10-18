"""One line of JSON per event, from every service, with the same fields everywhere.

Atlas plate 05: everything is logged, for developers only. A trace id ties together
everything one run or one day job does, across services.
"""

import json
import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)

# Attributes every LogRecord has; anything else on a record came from log_event's fields.
_STANDARD_ATTRIBUTES = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        line = {
            "time": _utc_timestamp(record.created),
            "service": self.service,
            "level": record.levelname.lower(),
            "event": record.getMessage(),
            "trace_id": _trace_id.get(),
            **_extra_fields(record),
        }
        if record.exc_info:
            line["error"] = self.formatException(record.exc_info)
        return json.dumps(line, default=str)


def log_event(logger: logging.Logger, event: str, **fields: object) -> None:
    logger.info(event, extra=fields)


@contextmanager
def tracing(trace_id: str) -> Iterator[None]:
    token = _trace_id.set(trace_id)
    try:
        yield
    finally:
        _trace_id.reset(token)


def configure_logging(service: str, log_dir: str) -> None:
    """Send every log line to standard output and to `<log_dir>/<service>.jsonl`."""
    formatter = JsonFormatter(service)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(log_dir) / f"{service}.jsonl"),
    ]
    for handler in handlers:
        handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)


def _utc_timestamp(created: float) -> str:
    return datetime.fromtimestamp(created, UTC).isoformat(timespec="milliseconds")[:-6] + "Z"


def _extra_fields(record: logging.LogRecord) -> dict[str, object]:
    return {k: v for k, v in vars(record).items() if k not in _STANDARD_ATTRIBUTES}
