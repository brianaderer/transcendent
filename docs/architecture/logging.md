# logging

**Source:** `backend/src/voices/log.py`   ·   **Tests:** `backend/tests/test_log.py`

## Purpose
Everything is logged, for developers only, as one line of JSON per event with the same
fields from every service. Plan: [atlas plate 05](../atlas/05-logging.md).

## Public interface
- `configure_logging(service, log_dir)` — sends every log line to standard output and to
  `<log_dir>/<service>.jsonl`.
- `log_event(logger, event, **fields)` — logs one named event with extra fields.
- `tracing(trace_id)` — a `with` block; every event logged inside it carries that trace id.
- `JsonFormatter(service)` — the formatter behind the above.

## How it works
Each line has `time` (UTC), `service`, `level`, `event`, `trace_id`, any extra fields, and
`error` with the full traceback when an exception is logged. An extra field that
shares a name with a standard one is dropped, so it can never overwrite it. The trace id lives in a
context variable, so it follows the code that runs inside a `tracing` block.

## Uses
Python's standard `logging`.

## Used by
[api](api.md), [worker](worker.md), [database](database.md) (setup).

## Configuration and data
`LOG_DIR` (default `/var/log/voices`), on the `logs` volume. Read the files with
`docker compose exec api ls /var/log/voices`, or live with `docker compose logs`.
