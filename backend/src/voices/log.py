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

# Attributes every LogRecord has; anything else on a record came from a caller's `extra`.
_STANDARD_ATTRIBUTES = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}
# A log_event field named like one of the record's own attributes (`name`, `msg`, ...) travels
# under this one attribute instead, so it can't collide; the line still shows it as given.
_CLASHING_FIELDS = "clashing_fields"


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        # Extra fields go first so they can never overwrite the standard ones.
        line = {
            **_extra_fields(record),
            "time": _utc_timestamp(record.created),
            "service": self.service,
            "level": record.levelname.lower(),
            "event": record.getMessage(),
            "trace_id": _trace_id.get(),
        }
        if record.exc_info:
            line["error"] = self.formatException(record.exc_info)
        return json.dumps(line, default=str)


def log_event(logger: logging.Logger, event: str, **fields: object) -> None:
    clashing = {k: v for k, v in fields.items() if k in _STANDARD_ATTRIBUTES}
    others = {k: v for k, v in fields.items() if k not in clashing}
    logger.info(event, extra={**others, _CLASHING_FIELDS: clashing})


@contextmanager
def tracing(trace_id: str) -> Iterator[None]:
    token = _trace_id.set(trace_id)
    try:
        yield
    finally:
        _trace_id.reset(token)


def configure_logging(service: str, log_dir: str) -> None:
    """Send every log line to standard output and to `<log_dir>/<service>.jsonl`."""
    if not service:
        raise ValueError("a service must name itself (SERVICE_NAME) before it logs")
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
    moment = datetime.fromtimestamp(created, UTC).isoformat(timespec="milliseconds")
    return moment.replace("+00:00", "Z")


def _extra_fields(record: logging.LogRecord) -> dict[str, object]:
    extras = {k: v for k, v in vars(record).items() if k not in _STANDARD_ATTRIBUTES}
    clashing = extras.pop(_CLASHING_FIELDS, {})
    return {**extras, **clashing}
