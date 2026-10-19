# logging

**Source:** `backend/src/voices/log.py`   ·   **Tests:** `backend/tests/test_log.py`

## Purpose
Everything is logged, for developers only, as one line of JSON per event with the same
fields from every service. Plan: [atlas plate 05](../atlas/05-logging.md).

## Public interface
- `configure_logging(service, log_dir)` — sends every log line to standard output and to
  `<log_dir>/<service>.jsonl`. Raises `ValueError` if `service` is empty, so a container
  that forgets `SERVICE_NAME` fails at start instead of logging under the wrong name.
- `log_event(logger, event, **fields)` — logs one named event with extra fields. A field may
  have any name, including one Python's log records use themselves (`name`, `msg`, ...): those
  travel apart inside the record and still appear on the line as given.
- `tracing(trace_id)` — a `with` block; every event logged inside it carries that trace id.
- `JsonFormatter(service)` — the formatter behind the above.

## How it works
Each line has `time` (UTC), `service`, `level`, `event`, `trace_id`, any extra fields, and
`error` with the full traceback when an exception is logged. An extra field named like one
of the line's own fields (`time`, `service`, `level`, `event`, `trace_id`) is dropped, so it
can never overwrite it. A field named like an attribute of Python's log record (`name`,
`msg`, ...) is carried inside the record under one side attribute, `clashing_fields`, and put
back on the line under its own name; the side attribute itself never appears. The trace id
lives in a context variable, so it follows the code that runs inside a `tracing` block; code
run in another thread carries it only when the thread runs in a copy of the context (as the
worker's `in_parallel` does).

## Uses
Python's standard `logging`.

## Used by
[api](api.md) (and `voices/health.py`), [worker](worker.md), [database](database.md) (setup),
[ingestion](ingestion.md) (archive retries), [tagging](tagging.md) (every turn of the
tagging agent, `tagging.turn`, everything sent back to the agent, `tagging.answer`, and
each decision, `tagging.decided`), [report](report.md) (each comparison run under the trace
id `run-<id>`, in both versions' threads too, and `run.failed` with the reason), [events](events.md)
(every emitted event is also logged).

## Configuration and data
`LOG_DIR` (default `/var/log/voices`), on the `logs` volume. Read the files with
`docker compose exec api ls /var/log/voices`, or live with `docker compose logs`.
