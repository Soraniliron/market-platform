import pytest

from earnings.audit_engine import create_audit_record
from earnings.replay_engine import (
    replay_audit_record,
    replay_audit_records,
)


def test_replay_audit_record_matches_original_output() -> None:
    record = create_audit_record(
        ticker="MSFT",
        event_type="ANALYSIS",
        status="SUCCESS",
        input_data={
            "value": 10,
        },
        output_data={
            "result": 20,
        },
    )

    def handler(
        input_data: dict,
    ) -> dict:
        return {
            "result": input_data["value"] * 2,
        }

    result = replay_audit_record(
        record,
        handler,
    )

    assert result.audit_id == record.audit_id
    assert result.ticker == "MSFT"
    assert result.event_type == "ANALYSIS"
    assert result.original_status == "SUCCESS"
    assert result.replay_status == "SUCCESS"
    assert result.original_output == {
        "result": 20,
    }
    assert result.replay_output == {
        "result": 20,
    }
    assert result.matched is True


def test_replay_audit_record_detects_mismatch() -> None:
    record = create_audit_record(
        ticker="JPM",
        event_type="ANALYSIS",
        status="SUCCESS",
        input_data={
            "value": 10,
        },
        output_data={
            "result": 20,
        },
    )

    def handler(
        input_data: dict,
    ) -> dict:
        return {
            "result": input_data["value"] * 3,
        }

    result = replay_audit_record(
        record,
        handler,
    )

    assert result.replay_status == "SUCCESS"
    assert result.replay_output == {
        "result": 30,
    }
    assert result.matched is False


def test_replay_audit_record_handles_handler_error() -> None:
    record = create_audit_record(
        ticker="BAC",
        event_type="ANALYSIS",
        status="SUCCESS",
        input_data={},
        output_data={},
    )

    def handler(
        input_data: dict,
    ) -> dict:
        raise RuntimeError(
            "replay failed"
        )

    result = replay_audit_record(
        record,
        handler,
    )

    assert result.replay_status == "FAILED"
    assert result.replay_output == {
        "error": "replay failed",
    }
    assert result.matched is False


def test_replay_audit_record_rejects_non_callable_handler() -> None:
    record = create_audit_record(
        ticker="MSFT",
        event_type="ANALYSIS",
        status="SUCCESS",
        input_data={},
        output_data={},
    )

    with pytest.raises(
        ValueError,
        match="handler must be callable",
    ):
        replay_audit_record(
            record,
            None,
        )


def test_replay_audit_record_rejects_non_dictionary_output() -> None:
    record = create_audit_record(
        ticker="MSFT",
        event_type="ANALYSIS",
        status="SUCCESS",
        input_data={},
        output_data={},
    )

    def handler(
        input_data: dict,
    ):
        return "invalid"

    with pytest.raises(
        ValueError,
        match="handler must return a dictionary",
    ):
        replay_audit_record(
            record,
            handler,
        )


def test_replay_audit_records_uses_matching_handlers() -> None:
    first_record = create_audit_record(
        ticker="MSFT",
        event_type="ANALYSIS",
        status="SUCCESS",
        input_data={
            "value": 5,
        },
        output_data={
            "result": 10,
        },
    )

    second_record = create_audit_record(
        ticker="JPM",
        event_type="ENTRY_UPDATE",
        status="SUCCESS",
        input_data={
            "price": 100,
        },
        output_data={
            "entry": 95,
        },
    )

    handlers = {
        "ANALYSIS": lambda input_data: {
            "result": input_data["value"] * 2,
        },
        "ENTRY_UPDATE": lambda input_data: {
            "entry": input_data["price"] - 5,
        },
    }

    results = replay_audit_records(
        [
            first_record,
            second_record,
        ],
        handlers,
    )

    assert len(results) == 2
    assert results[0].matched is True
    assert results[1].matched is True


def test_replay_audit_records_skips_missing_handler() -> None:
    record = create_audit_record(
        ticker="MSFT",
        event_type="UNKNOWN_EVENT",
        status="SUCCESS",
        input_data={},
        output_data={},
    )

    results = replay_audit_records(
        [record],
        {},
    )

    assert len(results) == 1
    assert results[0].replay_status == "SKIPPED"
    assert results[0].replay_output == {
        "reason": "NO_HANDLER",
    }
    assert results[0].matched is False
