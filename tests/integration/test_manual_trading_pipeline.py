from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import Mock

from decision.models import (
    DecisionResult,
    DecisionStatus,
    RankedCandidate,
    TradingSignal,
)
from execution.models import EntryContext
from execution.risk_engine import (
    PositionSizeResult,
    RiskContext,
    RiskStatus,
)
from integration.pipeline import (
    ManualTradingPipeline,
)
from notifications.models import (
    DeliveryStatus,
    NotificationResult,
    NotificationType,
)
from scanner.models import (
    ScanResult,
    ScanStatus,
)
from tracking.models import (
    AuditEvent,
    AuditRecord,
    DecisionType,
)


def build_scan_result() -> ScanResult:
    return ScanResult(
        ticker="META",
        status=ScanStatus.STRONG,
        score=90.0,
        price=100.0,
        change_percent=2.5,
        volume=500_000.0,
        vwap=99.5,
        above_vwap=True,
        reason="Strong setup",
    )


def build_decision() -> DecisionResult:
    scan_result = build_scan_result()

    candidate = RankedCandidate(
        rank=1,
        ticker="META",
        score=90.0,
        status=DecisionStatus.BUY,
        scan_result=scan_result,
        reason="Best candidate",
    )

    return DecisionResult(
        candidates_count=1,
        ranked_candidates=(candidate,),
        top_candidate=candidate,
        decision_status=DecisionStatus.BUY,
        reason="BUY | top=META",
    )


def build_signal() -> TradingSignal:
    return TradingSignal(
        ticker="META",
        status=DecisionStatus.BUY,
        score=90.0,
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        reason="Entry confirmed",
    )


def build_entry_context() -> EntryContext:
    return EntryContext(
        current_price=100.0,
        breakout_level=99.5,
        vwap=99.0,
        current_volume=300_000.0,
        average_volume_same_window=200_000.0,
        atr=1.0,
        recent_swing_low=98.0,
        spy_aligned=True,
        qqq_aligned=True,
        chart_quality_score=85.0,
        decision_score=90.0,
        minutes_from_market_open=30,
        maximum_entry_delay_minutes=60,
    )


def build_risk_context() -> RiskContext:
    return RiskContext(
        account_equity=100_000.0,
        available_cash=50_000.0,
        maximum_risk_percent=1.0,
        maximum_position_percent=20.0,
        daily_realized_pnl=0.0,
        maximum_daily_loss_percent=3.0,
        maximum_liquidity_value=10_000.0,
        existing_position_value=0.0,
    )


def build_position_size() -> PositionSizeResult:
    return PositionSizeResult(
        ticker="META",
        status=RiskStatus.REDUCED,
        quantity=100,
        position_value=10_000.0,
        total_position_value=10_000.0,
        risk_per_share=2.0,
        total_risk=200.0,
        maximum_risk_value=1_000.0,
        maximum_position_value=20_000.0,
        maximum_allowed_value=10_000.0,
        reason="position limited by liquidity",
    )


def build_notification() -> NotificationResult:
    return NotificationResult(
        notification_type=NotificationType.BUY,
        status=DeliveryStatus.SENT,
        subject="IDB PRIME | BUY | META",
        recipients=("test@example.com",),
        attempts_count=1,
        attempts=(),
        sent_at=datetime.now(timezone.utc),
        error_message=None,
    )


def build_audit_record() -> AuditRecord:
    return AuditRecord(
        audit_id="audit-1",
        created_at=datetime.now(timezone.utc),
        ticker="META",
        event=AuditEvent.SIGNAL,
        decision=DecisionType.BUY,
        score=90.0,
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        reason="Entry confirmed",
        input_data={},
        output_data={},
    )


def test_pipeline_completes_buy_flow() -> None:
    scanner = Mock()
    decision_engine = Mock()
    signal_builder = Mock()
    risk_engine = Mock()
    notification_service = Mock()
    audit_engine = Mock()

    scanner.scan_home_list.return_value = [
        build_scan_result()
    ]

    decision_engine.decide.return_value = (
        build_decision()
    )

    signal_builder.build.return_value = (
        build_signal()
    )

    signal_builder.entry_engine.build_trade_plan.return_value = Mock()

    risk_engine.calculate_position_size.return_value = (
        build_position_size()
    )

    notification_service.send_trade_notification.return_value = (
        build_notification()
    )

    audit_engine.create_record.return_value = (
        build_audit_record()
    )

    pipeline = ManualTradingPipeline(
        scanner=scanner,
        decision_engine=decision_engine,
        signal_builder=signal_builder,
        risk_engine=risk_engine,
        notification_service=notification_service,
        audit_engine=audit_engine,
    )

    result = pipeline.run(
        timeframe_minutes=15,
        start_date=date(2026, 8, 5),
        end_date=date(2026, 8, 5),
        entry_context=build_entry_context(),
        risk_context=build_risk_context(),
        recipients=("test@example.com",),
    )

    assert result.success is True
    assert result.signal is not None
    assert result.signal.ticker == "META"
    assert result.position_size is not None
    assert result.notification is not None
    assert result.audit_record is not None

    scanner.scan_home_list.assert_called_once()
    decision_engine.decide.assert_called_once()
    signal_builder.build.assert_called_once()
    risk_engine.calculate_position_size.assert_called_once()
    notification_service.send_trade_notification.assert_called_once()
    audit_engine.create_record.assert_called_once()


def test_pipeline_handles_no_signal() -> None:
    scanner = Mock()
    decision_engine = Mock()
    signal_builder = Mock()
    audit_engine = Mock()

    scanner.scan_home_list.return_value = []

    decision = DecisionResult(
        candidates_count=0,
        ranked_candidates=(),
        top_candidate=None,
        decision_status=DecisionStatus.AVOID,
        reason="No eligible candidates",
    )

    decision_engine.decide.return_value = decision
    signal_builder.build.return_value = None
    audit_engine.create_record.return_value = (
        build_audit_record()
    )

    pipeline = ManualTradingPipeline(
        scanner=scanner,
        decision_engine=decision_engine,
        signal_builder=signal_builder,
        risk_engine=Mock(),
        notification_service=Mock(),
        audit_engine=audit_engine,
    )

    result = pipeline.run(
        timeframe_minutes=15,
        start_date=date(2026, 8, 5),
        end_date=date(2026, 8, 5),
    )

    assert result.success is True
    assert result.signal is None
    assert result.position_size is None
    assert result.notification is None
    assert result.audit_record is not None


def test_pipeline_rejects_buy_without_risk_context() -> None:
    scanner = Mock()
    decision_engine = Mock()
    signal_builder = Mock()

    scanner.scan_home_list.return_value = [
        build_scan_result()
    ]

    decision_engine.decide.return_value = (
        build_decision()
    )

    signal_builder.build.return_value = (
        build_signal()
    )

    pipeline = ManualTradingPipeline(
        scanner=scanner,
        decision_engine=decision_engine,
        signal_builder=signal_builder,
        risk_engine=Mock(),
        notification_service=Mock(),
        audit_engine=Mock(),
    )

    result = pipeline.run(
        timeframe_minutes=15,
        start_date=date(2026, 8, 5),
        end_date=date(2026, 8, 5),
        entry_context=build_entry_context(),
        risk_context=None,
    )

    assert result.success is False
    assert (
        result.metadata["error"]
        == "risk_context is required for a BUY signal"
    )


def test_pipeline_converts_risk_rejection_to_avoid() -> None:
    scanner = Mock()
    decision_engine = Mock()
    signal_builder = Mock()
    risk_engine = Mock()
    notification_service = Mock()
    audit_engine = Mock()

    scanner.scan_home_list.return_value = [
        build_scan_result()
    ]

    decision_engine.decide.return_value = (
        build_decision()
    )

    signal_builder.build.return_value = (
        build_signal()
    )

    signal_builder.entry_engine.build_trade_plan.return_value = Mock()

    risk_engine.calculate_position_size.return_value = (
        PositionSizeResult(
            ticker="META",
            status=RiskStatus.REJECTED,
            quantity=0,
            position_value=0.0,
            total_position_value=0.0,
            risk_per_share=2.0,
            total_risk=0.0,
            maximum_risk_value=0.0,
            maximum_position_value=0.0,
            maximum_allowed_value=0.0,
            reason="Daily loss limit reached",
        )
    )

    notification_service.send_trade_notification.return_value = (
        build_notification()
    )

    audit_engine.create_record.return_value = (
        build_audit_record()
    )

    pipeline = ManualTradingPipeline(
        scanner=scanner,
        decision_engine=decision_engine,
        signal_builder=signal_builder,
        risk_engine=risk_engine,
        notification_service=notification_service,
        audit_engine=audit_engine,
    )

    result = pipeline.run(
        timeframe_minutes=15,
        start_date=date(2026, 8, 5),
        end_date=date(2026, 8, 5),
        entry_context=build_entry_context(),
        risk_context=build_risk_context(),
        recipients=("test@example.com",),
    )

    assert result.success is True
    assert result.signal is not None
    assert (
        result.signal.status
        == DecisionStatus.AVOID
    )
    assert (
        "Daily loss limit reached"
        in result.signal.reason
    )
    