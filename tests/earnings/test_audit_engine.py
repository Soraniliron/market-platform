import json

import pytest

from earnings.audit_engine import (
    audit_record_to_dict,
    create_audit_record,
    load_audit_records,
    save_audit_record,
)


def test_create_audit_record() -> None:
    record = create_audit_record(
        ticker="MSFT",
        event_type="EARNINGS_ANALYSIS",
        status="SUCCESS",
        input_data={
            "cycles_count": 12,
        },
        output_data={
            "entry_price": 390.0,
            "exit_price": 430.0,
        },
        metadata={
            "source": "manual",
        },
    )

    assert record.ticker == "MSFT"
    assert record.event_type == "EARNINGS_ANALYSIS"
    assert record.status == "SUCCESS"
    assert record.audit_id
    assert record.created_at
    assert record.input_data["cycles_count"] == 12
    assert record.output_data["entry_price"] == 390.0
    assert record.metadata["source"] == "manual"


def test_audit_record_to_dict() -> None:
    record = create_audit_record(
        ticker="JPM",
        event_type="ENTRY_UPDATE",
        status="SUCCESS",
        input_data={},
        output_data={
            "entry_price": 280.0,
        },
    )

    result = audit_record_to_dict(record)

    assert result["ticker"] == "JPM"
    assert result["event_type"] == "ENTRY_UPDATE"
    assert result["metadata"] == {}


def test_save_and_load_audit_records(
    tmp_path,
) -> None:
    file_path = tmp_path / "audit.jsonl"

    first_record = create_audit_record(
        ticker="MSFT",
        event_type="ANALYSIS",
        status="SUCCESS",
        input_data={
            "cycles_count": 12,
        },
        output_data={
            "entry_price": 390.0,
        },
    )

    second_record = create_audit_record(
        ticker="JPM",
        event_type="ANALYSIS",
        status="REJECTED",
        input_data={
            "cycles_count": 5,
        },
        output_data={
            "reason": "INSUFFICIENT_SAMPLE",
        },
    )

    save_audit_record(
        first_record,
        file_path,
    )

    save_audit_record(
        second_record,
        file_path,
    )

    loaded_records = load_audit_records(
        file_path
    )

    assert len(loaded_records) == 2
    assert loaded_records[0] == first_record
    assert loaded_records[1] == second_record


def test_load_missing_file_returns_empty_list(
    tmp_path,
) -> None:
    file_path = tmp_path / "missing.jsonl"

    assert load_audit_records(
        file_path
    ) == []


def test_load_invalid_json_raises_error(
    tmp_path,
) -> None:
    file_path = tmp_path / "audit.jsonl"

    file_path.write_text(
        '{"ticker": "MSFT"}\ninvalid-json\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid audit record at line 1",
    ):
        load_audit_records(file_path)


def test_saved_record_is_valid_json(
    tmp_path,
) -> None:
    file_path = tmp_path / "audit.jsonl"

    record = create_audit_record(
        ticker="MSFT",
        event_type="ANALYSIS",
        status="SUCCESS",
        input_data={},
        output_data={},
    )

    save_audit_record(
        record,
        file_path,
    )

    line = file_path.read_text(
        encoding="utf-8",
    ).strip()

    parsed = json.loads(line)

    assert parsed["audit_id"] == record.audit_id
    assert parsed["ticker"] == "MSFT"


def test_rejects_empty_ticker() -> None:
    with pytest.raises(
        ValueError,
        match="ticker must not be empty",
    ):
        create_audit_record(
            ticker="",
            event_type="ANALYSIS",
            status="SUCCESS",
            input_data={},
            output_data={},
        )
