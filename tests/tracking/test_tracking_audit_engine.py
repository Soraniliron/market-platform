from __future__ import annotations

from tracking.audit_engine import AuditEngine
from tracking.models import (
    AuditEvent,
    DecisionType,
)


def test_create_record() -> None:
    engine = AuditEngine()

    record = engine.create_record(
        ticker="META",
        event=AuditEvent.DECISION,
        decision=DecisionType.BUY,
        score=91.5,
        reason="Best candidate",
        input_data={"score": 91.5},
        output_data={"decision": "BUY"},
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
    )

    assert record.ticker == "META"
    assert record.event == AuditEvent.DECISION
    assert record.decision == DecisionType.BUY
    assert record.score == 91.5
    assert record.entry_price == 100.0


def test_save_and_load_records(
    tmp_path,
) -> None:
    engine = AuditEngine()

    file_path = (
        tmp_path / "audit.jsonl"
    )

    record = engine.create_record(
        ticker="AAPL",
        event=AuditEvent.SIGNAL,
        decision=DecisionType.WATCH,
        score=82.0,
        reason="Waiting",
        input_data={},
        output_data={},
    )

    engine.save_record(
        record,
        file_path,
    )

    loaded = engine.load_records(
        file_path,
    )

    assert len(loaded) == 1
    assert loaded[0].ticker == "AAPL"
    assert loaded[0].decision == DecisionType.WATCH


def test_invalid_score() -> None:
    engine = AuditEngine()

    try:
        engine.create_record(
            ticker="META",
            event=AuditEvent.SCAN,
            decision=DecisionType.WATCH,
            score=150.0,
            reason="Invalid",
            input_data={},
            output_data={},
        )
    except ValueError as error:
        assert (
            "score must be between 0 and 100"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )
        