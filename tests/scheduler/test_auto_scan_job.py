from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

from decision.models import (
    DecisionStatus,
    TradingSignal,
)
from notifications.models import (
    DeliveryStatus,
    NotificationResult,
    NotificationType,
)
from scheduler.jobs import AutoScanJob


def build_signal() -> TradingSignal:
    return TradingSignal(
        ticker="META",
        status=DecisionStatus.BUY,
        score=90.0,
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        reason="Test",
    )


def build_notification_result() -> NotificationResult:
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


def test_no_signal() -> None:
    scanner = Mock()
    decision_engine = Mock()
    signal_builder = Mock()

    scanner.scan_home_list.return_value = []

    decision_engine.decide.return_value = Mock(
        reason="No candidates"
    )

    signal_builder.build.return_value = None

    job = AutoScanJob(
        scanner=scanner,
        decision_engine=decision_engine,
        signal_builder=signal_builder,
        notification_service=Mock(),
        signal_guard=Mock(),
    )

    result = job.run(
        timeframe_minutes=15,
        recipients=("test@example.com",),
    )

    assert result["status"] == "no_signal"
    assert result["signal"] is None
    assert result["notification"] is None


def test_duplicate_signal() -> None:
    scanner = Mock()
    decision_engine = Mock()
    signal_builder = Mock()
    notification_service = Mock()
    signal_guard = Mock()

    scanner.scan_home_list.return_value = []

    decision_engine.decide.return_value = Mock(
        reason="BUY"
    )

    signal_builder.build.return_value = (
        build_signal()
    )

    signal_guard.check.return_value = Mock(
        allowed=False,
    )

    job = AutoScanJob(
        scanner=scanner,
        decision_engine=decision_engine,
        signal_builder=signal_builder,
        notification_service=notification_service,
        signal_guard=signal_guard,
    )

    result = job.run(
        timeframe_minutes=15,
        recipients=("test@example.com",),
    )

    assert (
        result["status"]
        == "duplicate_blocked"
    )
    assert result["signal"]["ticker"] == "META"
    assert result["notification"] is None

    notification_service.send_trade_notification.assert_not_called()


def test_completed_signal() -> None:
    scanner = Mock()
    decision_engine = Mock()
    signal_builder = Mock()
    notification_service = Mock()
    signal_guard = Mock()

    scanner.scan_home_list.return_value = []

    decision_engine.decide.return_value = Mock(
        reason="BUY"
    )

    signal_builder.build.return_value = (
        build_signal()
    )

    signal_guard.check.return_value = Mock(
        allowed=True,
    )

    notification_service.send_trade_notification.return_value = (
        build_notification_result()
    )

    job = AutoScanJob(
        scanner=scanner,
        decision_engine=decision_engine,
        signal_builder=signal_builder,
        notification_service=notification_service,
        signal_guard=signal_guard,
    )

    result = job.run(
        timeframe_minutes=15,
        recipients=("test@example.com",),
    )

    assert result["status"] == "completed"
    assert result["signal"]["ticker"] == "META"
    assert (
        result["notification"]["status"]
        == DeliveryStatus.SENT
    )

    notification_service.send_trade_notification.assert_called_once()
    