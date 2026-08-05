from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    LEADING_CANDIDATE = "leading_candidate"
    BUY = "buy"
    WATCH = "watch"
    WAIT = "wait"
    AVOID = "avoid"
    NO_TRADE = "no_trade"
    ENTRY_CANCELLED = "entry_cancelled"
    TP1 = "tp1"
    TP2 = "tp2"
    STOP = "stop"
    DAILY_REPORT = "daily_report"
    MONTHLY_REPORT = "monthly_report"
    SYSTEM_ERROR = "system_error"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class EmailMessage:
    subject: str
    body_text: str
    recipients: tuple[str, ...]
    body_html: str | None = None


@dataclass(frozen=True)
class DeliveryAttempt:
    attempt_number: int
    attempted_at: datetime
    successful: bool
    error_message: str | None = None


@dataclass(frozen=True)
class NotificationResult:
    notification_type: NotificationType
    status: DeliveryStatus
    subject: str
    recipients: tuple[str, ...]
    attempts_count: int
    attempts: tuple[DeliveryAttempt, ...]
    sent_at: datetime | None
    error_message: str | None
    