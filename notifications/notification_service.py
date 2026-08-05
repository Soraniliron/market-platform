from __future__ import annotations

from config.settings import EMAIL_TO
from notifications.email_sender import EmailSender
from notifications.email_templates import EmailTemplateBuilder
from notifications.models import (
    NotificationResult,
    NotificationType,
)


class NotificationService:
    def __init__(
        self,
        template_builder: EmailTemplateBuilder | None = None,
        email_sender: EmailSender | None = None,
    ) -> None:
        self.template_builder = (
            template_builder
            or EmailTemplateBuilder()
        )

        self.email_sender = (
            email_sender
            or EmailSender()
        )

    def send_trade_notification(
        self,
        notification_type: NotificationType,
        ticker: str,
        entry: float | None = None,
        stop: float | None = None,
        tp1: float | None = None,
        tp2: float | None = None,
        reason: str = "",
        recipients: tuple[str, ...] | None = None,
    ) -> NotificationResult:
        resolved_recipients = (
            recipients
            if recipients is not None
            else EMAIL_TO
        )

        if not resolved_recipients:
            raise ValueError(
                "At least one email recipient is required"
            )

        if (
            notification_type
            not in {
                NotificationType.LEADING_CANDIDATE,
                NotificationType.BUY,
                NotificationType.WATCH,
                NotificationType.WAIT,
                NotificationType.AVOID,
                NotificationType.NO_TRADE,
                NotificationType.ENTRY_CANCELLED,
                NotificationType.TP1,
                NotificationType.TP2,
                NotificationType.STOP,
                NotificationType.SYSTEM_ERROR,
            }
        ):
            raise ValueError(
                "Unsupported trade notification type"
            )

        message = self.template_builder.build(
            notification_type=notification_type,
            recipients=resolved_recipients,
            ticker=ticker.upper(),
            entry=entry,
            stop=stop,
            tp1=tp1,
            tp2=tp2,
            reason=reason,
        )

        return self.email_sender.send(
            notification_type=notification_type,
            message=message,
        )

    def send_report_notification(
        self,
        notification_type: NotificationType,
        subject_ticker: str,
        report_text: str,
        recipients: tuple[str, ...] | None = None,
    ) -> NotificationResult:
        resolved_recipients = (
            recipients
            if recipients is not None
            else EMAIL_TO
        )

        if not resolved_recipients:
            raise ValueError(
                "At least one email recipient is required"
            )

        if notification_type not in {
            NotificationType.DAILY_REPORT,
            NotificationType.MONTHLY_REPORT,
        }:
            raise ValueError(
                "Unsupported report notification type"
            )

        message = self.template_builder.build(
            notification_type=notification_type,
            recipients=resolved_recipients,
            ticker=subject_ticker,
            reason=report_text,
        )

        return self.email_sender.send(
            notification_type=notification_type,
            message=message,
        )
        