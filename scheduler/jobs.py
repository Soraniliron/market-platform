from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any

from decision.decision_engine import DecisionEngine
from logs.logger import logger
from notifications.models import NotificationType
from notifications.notification_service import (
    NotificationService,
)
from scanner.scanner_engine import MarketScanner
from scheduler.signal_guard import (
    DuplicateSignalGuard,
)
from signals.signal_builder import SignalBuilder


class AutoScanJob:
    def __init__(
        self,
        scanner: MarketScanner | None = None,
        decision_engine: DecisionEngine | None = None,
        signal_builder: SignalBuilder | None = None,
        notification_service: NotificationService | None = None,
        signal_guard: DuplicateSignalGuard | None = None,
    ) -> None:
        self.scanner = (
            scanner
            or MarketScanner()
        )

        self.decision_engine = (
            decision_engine
            or DecisionEngine()
        )

        self.signal_builder = (
            signal_builder
            or SignalBuilder()
        )

        self.notification_service = (
            notification_service
            or NotificationService()
        )

        self.signal_guard = (
            signal_guard
            or DuplicateSignalGuard()
        )

    def run(
        self,
        timeframe_minutes: int,
        contexts: dict[str, Any] | None = None,
        recipients: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        today = date.today()

        scan_results = (
            self.scanner.scan_home_list(
                timeframe_minutes=timeframe_minutes,
                start_date=today,
                end_date=today,
                contexts=contexts,
            )
        )

        decision = (
            self.decision_engine.decide(
                scan_results=scan_results,
                limit=3,
            )
        )

        signal = self.signal_builder.build(
            decision=decision,
            entry_context=None,
        )

        if signal is None:
            logger.info(
                "Auto scan completed with no signal"
            )

            return {
                "status": "no_signal",
                "decision": decision.reason,
                "signal": None,
                "notification": None,
            }

        guard_result = self.signal_guard.check(
            ticker=signal.ticker,
            status=signal.status.value,
            entry_price=signal.entry_price,
            stop_price=signal.stop_price,
            tp1_price=signal.tp1_price,
            tp2_price=signal.tp2_price,
            now=datetime.now(timezone.utc),
        )

        if not guard_result.allowed:
            logger.info(
                "Duplicate signal blocked for %s",
                signal.ticker,
            )

            return {
                "status": "duplicate_blocked",
                "decision": decision.reason,
                "signal": asdict(signal),
                "notification": None,
            }

        notification_type = (
            self._resolve_notification_type(
                signal.status.value
            )
        )

        notification_result = (
            self.notification_service
            .send_trade_notification(
                notification_type=(
                    notification_type
                ),
                ticker=signal.ticker,
                entry=signal.entry_price,
                stop=signal.stop_price,
                tp1=signal.tp1_price,
                tp2=signal.tp2_price,
                reason=signal.reason,
                recipients=recipients,
            )
        )

        logger.info(
            "Auto scan completed for %s with status %s",
            signal.ticker,
            signal.status.value,
        )

        return {
            "status": "completed",
            "decision": decision.reason,
            "signal": asdict(signal),
            "notification": asdict(
                notification_result
            ),
        }

    @staticmethod
    def _resolve_notification_type(
        signal_status: str,
    ) -> NotificationType:
        mapping = {
            "buy": NotificationType.BUY,
            "watch": NotificationType.WATCH,
            "wait": NotificationType.WAIT,
            "avoid": NotificationType.AVOID,
        }

        return mapping.get(
            signal_status,
            NotificationType.SYSTEM_ERROR,
        )


def scheduled_test_job() -> None:
    logger.info(
        "Scheduled test job executed at %s",
        datetime.now(timezone.utc).isoformat(),
    )
    