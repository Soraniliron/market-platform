from __future__ import annotations

from notifications.models import (
    EmailMessage,
    NotificationType,
)


class EmailTemplateBuilder:
    def build(
        self,
        notification_type: NotificationType,
        recipients: tuple[str, ...],
        ticker: str = "",
        entry: float | None = None,
        stop: float | None = None,
        tp1: float | None = None,
        tp2: float | None = None,
        reason: str = "",
    ) -> EmailMessage:
        subject = self._subject(
            notification_type,
            ticker,
        )

        body = self._body(
            notification_type,
            ticker=ticker,
            entry=entry,
            stop=stop,
            tp1=tp1,
            tp2=tp2,
            reason=reason,
        )

        return EmailMessage(
            subject=subject,
            body_text=body,
            body_html=None,
            recipients=recipients,
        )

    @staticmethod
    def _subject(
        notification_type: NotificationType,
        ticker: str,
    ) -> str:
        return (
            f"IDB PRIME | "
            f"{notification_type.value.upper()} | "
            f"{ticker}"
        )

    @staticmethod
    def _body(
        notification_type: NotificationType,
        ticker: str,
        entry: float | None,
        stop: float | None,
        tp1: float | None,
        tp2: float | None,
        reason: str,
    ) -> str:
        return (
            f"Notification: {notification_type.value}\n\n"
            f"Ticker: {ticker}\n"
            f"Entry: {entry}\n"
            f"Stop: {stop}\n"
            f"TP1: {tp1}\n"
            f"TP2: {tp2}\n\n"
            f"Reason:\n{reason}"
        )
        