from __future__ import annotations

import json
import logging

import pytest

from logs.logger import (
    JsonFormatter,
    log_event,
    logger,
)


def test_json_formatter_builds_valid_json() -> None:
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="market-platform",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Scan completed",
        args=(),
        exc_info=None,
    )

    record.event_name = "SCAN_COMPLETED"
    record.event_data = {
        "ticker": "META",
        "score": 91.5,
    }

    formatted = formatter.format(record)
    payload = json.loads(formatted)

    assert payload["level"] == "INFO"
    assert payload["message"] == "Scan completed"
    assert payload["event"] == "SCAN_COMPLETED"
    assert payload["ticker"] == "META"
    assert payload["score"] == 91.5
    assert "timestamp" in payload


def test_json_formatter_includes_exception() -> None:
    formatter = JsonFormatter()

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="market-platform",
        level=logging.ERROR,
        pathname=__file__,
        lineno=20,
        msg="Pipeline failed",
        args=(),
        exc_info=exc_info,
    )

    formatted = formatter.format(record)
    payload = json.loads(formatted)

    assert payload["level"] == "ERROR"
    assert "RuntimeError: boom" in payload["exception"]


def test_log_event_writes_structured_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(
        logging.INFO,
        logger="market-platform",
    )

    log_event(
        "SIGNAL_CREATED",
        message="Signal created",
        ticker="META",
        status="buy",
        score=90.0,
    )

    matching_records = [
        record
        for record in caplog.records
        if getattr(
            record,
            "event_name",
            None,
        )
        == "SIGNAL_CREATED"
    ]

    assert len(matching_records) == 1

    record = matching_records[0]

    assert record.getMessage() == "Signal created"
    assert record.event_data["ticker"] == "META"
    assert record.event_data["status"] == "buy"
    assert record.event_data["score"] == 90.0


def test_log_event_rejects_empty_event_name() -> None:
    with pytest.raises(
        ValueError,
        match="event_name must not be empty",
    ):
        log_event("")
        