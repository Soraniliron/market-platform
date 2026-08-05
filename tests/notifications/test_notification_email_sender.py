from __future__ import annotations

from unittest.mock import patch

from notifications.email_sender import EmailSender
from notifications.models import (
    DeliveryStatus,
    EmailMessage,
    NotificationType,
)


def build_message() -> EmailMessage:
    return EmailMessage(
        subject="IDB PRIME | BUY | META",
        body_text="Test body",
        recipients=("test@example.com",),
    )


@patch(
    "notifications.email_sender.EMAIL_ENABLED",
    False,
)
def test_send_skips_when_email_disabled() -> None:
    sender = EmailSender()

    result = sender.send(
        notification_type=NotificationType.BUY,
        message=build_message(),
    )

    assert result.status == DeliveryStatus.SKIPPED
    assert result.attempts_count == 0
    assert result.sent_at is None
    assert (
        result.error_message
        == "Email delivery is disabled"
    )


@patch(
    "notifications.email_sender.EMAIL_ENABLED",
    True,
)
@patch(
    "notifications.email_sender.EMAIL_MAX_RETRIES",
    3,
)
@patch(
    "notifications.email_sender.EMAIL_RETRY_DELAY_SECONDS",
    0,
)
def test_send_succeeds_on_first_attempt() -> None:
    sender = EmailSender()

    with patch.object(
        sender,
        "_send_once",
        return_value=None,
    ) as mocked_send:
        result = sender.send(
            notification_type=NotificationType.BUY,
            message=build_message(),
        )

    assert result.status == DeliveryStatus.SENT
    assert result.attempts_count == 1
    assert result.sent_at is not None
    assert result.error_message is None
    assert mocked_send.call_count == 1


@patch(
    "notifications.email_sender.EMAIL_ENABLED",
    True,
)
@patch(
    "notifications.email_sender.EMAIL_MAX_RETRIES",
    3,
)
@patch(
    "notifications.email_sender.EMAIL_RETRY_DELAY_SECONDS",
    0,
)
def test_send_retries_then_succeeds() -> None:
    sender = EmailSender()

    with patch.object(
        sender,
        "_send_once",
        side_effect=[
            RuntimeError("first failure"),
            None,
        ],
    ) as mocked_send:
        result = sender.send(
            notification_type=NotificationType.BUY,
            message=build_message(),
        )

    assert result.status == DeliveryStatus.SENT
    assert result.attempts_count == 2
    assert result.attempts[0].successful is False
    assert result.attempts[1].successful is True
    assert mocked_send.call_count == 2


@patch(
    "notifications.email_sender.EMAIL_ENABLED",
    True,
)
@patch(
    "notifications.email_sender.EMAIL_MAX_RETRIES",
    3,
)
@patch(
    "notifications.email_sender.EMAIL_RETRY_DELAY_SECONDS",
    0,
)
def test_send_fails_after_all_retries() -> None:
    sender = EmailSender()

    with patch.object(
        sender,
        "_send_once",
        side_effect=RuntimeError(
            "permanent failure"
        ),
    ) as mocked_send:
        result = sender.send(
            notification_type=NotificationType.SYSTEM_ERROR,
            message=build_message(),
        )

    assert result.status == DeliveryStatus.FAILED
    assert result.attempts_count == 3
    assert result.sent_at is None
    assert (
        result.error_message
        == "permanent failure"
    )
    assert mocked_send.call_count == 3
    