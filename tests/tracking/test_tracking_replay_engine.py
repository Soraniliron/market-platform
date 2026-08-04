from __future__ import annotations

from datetime import datetime

from tracking.models import (
    AuditEvent,
    AuditRecord,
    DecisionType,
)
from tracking.replay_engine import ReplayEngine


def build_record() -> AuditRecord:
    return AuditRecord(
        audit_id="1",
        created_at=datetime.utcnow(),
        ticker="META",
        event=AuditEvent.DECISION,
        decision=DecisionType.BUY,
        score=90.0,
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        reason="Test",
        input_data={"value": 1},
        output_data={"decision": "BUY"},
    )


def test_matching_replay() -> None:
    engine = ReplayEngine()

    result = engine.replay_record(
        build_record(),
        lambda _: {"decision": "BUY"},
    )

    assert result.matched is True
    assert result.status == "matched"


def test_mismatching_replay() -> None:
    engine = ReplayEngine()

    result = engine.replay_record(
        build_record(),
        lambda _: {"decision": "WAIT"},
    )

    assert result.matched is False
    assert result.status == "mismatched"


def test_failed_replay() -> None:
    engine = ReplayEngine()

    def handler(_):
        raise RuntimeError("boom")

    result = engine.replay_record(
        build_record(),
        handler,
    )

    assert result.status == "failed"


def test_skipped_replay() -> None:
    engine = ReplayEngine()

    result = engine.replay_records(
        [build_record()],
        {},
    )

    assert len(result) == 1
    assert result[0].status == "skipped"
    