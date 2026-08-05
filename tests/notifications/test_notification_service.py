from __future__ import annotations

from unittest.mock import Mock

import pytest

from notifications.models import (
    DeliveryStatus,
    NotificationResult,
    NotificationType,
)
from notifications.notification_service import (
    NotificationService,
)


def build_result() -> NotificationResult:
    return NotificationResult(
        notification_type=NotificationType.BUY,
        status=DeliveryStatus.SENT,
        subject="subject",
        recipients=("test@example.com",),
        attempts_count=1,
        attempts=(),
        sent_at=None,
        error_message=None,
    )


def test_send_trade_notification() -> None:
    template_builder = Mock()
    email_sender = Mock()

    template_builder.build.return_value = Mock()
    email_sender.send.return_value = build_result()

    service = NotificationService(
        template_builder=template_builder,
        email_sender=email_sender,
    )

    result = service.send_trade_notification(
        notification_type=NotificationType.BUY,
        ticker="META",
        recipients=("test@example.com",),
    )

    assert result.status == DeliveryStatus.SENT
    assert template_builder.build.called
    assert email_sender.send.called


def test_send_report_notification() -> None:
    template_builder = Mock()
    email_sender = Mock()

    template_builder.build.return_value = Mock()
    email_sender.send.return_value = build_result()

    service = NotificationService(
        template_builder=template_builder,
        email_sender=email_sender,
    )

    result = service.send_report_notification(
        notification_type=NotificationType.DAILY_REPORT,
        subject_ticker="REPORT",
        report_text="Daily summary",
        recipients=("test@example.com",),
    )

    assert result.status == DeliveryStatus.SENT


def test_trade_notification_requires_recipient() -> None:
    service = NotificationService(
        template_builder=Mock(),
        email_sender=Mock(),
    )

    with pytest.raises(
        ValueError,
        match="At least one email recipient",
    ):
        service.send_trade_notification(
            notification_type=NotificationType.BUY,
            ticker="META",
            recipients=(),
        )


def test_report_notification_requires_recipient() -> None:
    service = NotificationService(
        template_builder=Mock(),
        email_sender=Mock(),
    )

    with pytest.raises(
        ValueError,
        match="At least one email recipient",
    ):
        service.send_report_notification(
            notification_type=NotificationType.DAILY_REPORT,
            subject_ticker="REPORT",
            report_text="summary",
            recipients=(),
        )
        