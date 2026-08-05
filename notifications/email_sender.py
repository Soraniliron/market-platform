from __future__ import annotations

import smtplib
import time
from datetime import datetime, timezone
from email.message import EmailMessage as SMTPEmailMessage

from config.settings import (
    EMAIL_ENABLED,
    EMAIL_FROM,
    EMAIL_MAX_RETRIES,
    EMAIL_RETRY_DELAY_SECONDS,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USERNAME,
)
from notifications.models import (
    DeliveryAttempt,
    DeliveryStatus,
    EmailMessage,
    NotificationResult,
    NotificationType,
)


class EmailSender:
    def send(
        self,
        notification_type: NotificationType,
        message: EmailMessage,
    ) -> NotificationResult:
        if not EMAIL_ENABLED:
            return NotificationResult(
                notification_type=notification_type,
                status=DeliveryStatus.SKIPPED,
                subject=message.subject,
                recipients=message.recipients,
                attempts_count=0,
                attempts=(),
                sent_at=None,
                error_message="Email delivery is disabled",
            )

        attempts: list[DeliveryAttempt] = []

        for attempt_number in range(
            1,
            EMAIL_MAX_RETRIES + 1,
        ):
            attempted_at = datetime.now(
                timezone.utc
            )

            try:
                self._send_once(message)

                attempt = DeliveryAttempt(
                    attempt_number=attempt_number,
                    attempted_at=attempted_at,
                    successful=True,
                    error_message=None,
                )

                attempts.append(attempt)

                sent_at = datetime.now(
                    timezone.utc
                )

                return NotificationResult(
                    notification_type=notification_type,
                    status=DeliveryStatus.SENT,
                    subject=message.subject,
                    recipients=message.recipients,
                    attempts_count=len(attempts),
                    attempts=tuple(attempts),
                    sent_at=sent_at,
                    error_message=None,
                )

            except Exception as error:
                attempt = DeliveryAttempt(
                    attempt_number=attempt_number,
                    attempted_at=attempted_at,
                    successful=False,
                    error_message=str(error),
                )

                attempts.append(attempt)

                if attempt_number < EMAIL_MAX_RETRIES:
                    time.sleep(
                        EMAIL_RETRY_DELAY_SECONDS
                    )

        last_error = (
            attempts[-1].error_message
            if attempts
            else "Unknown email delivery error"
        )

        return NotificationResult(
            notification_type=notification_type,
            status=DeliveryStatus.FAILED,
            subject=message.subject,
            recipients=message.recipients,
            attempts_count=len(attempts),
            attempts=tuple(attempts),
            sent_at=None,
            error_message=last_error,
        )

    @staticmethod
    def _send_once(
        message: EmailMessage,
    ) -> None:
        smtp_message = SMTPEmailMessage()

        smtp_message["Subject"] = (
            message.subject
        )
        smtp_message["From"] = EMAIL_FROM
        smtp_message["To"] = ", ".join(
            message.recipients
        )

        smtp_message.set_content(
            message.body_text
        )

        if message.body_html is not None:
            smtp_message.add_alternative(
                message.body_html,
                subtype="html",
            )

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=30,
        ) as server:
            if SMTP_USE_TLS:
                server.starttls()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD,
            )

            server.send_message(
                smtp_message
            )
            