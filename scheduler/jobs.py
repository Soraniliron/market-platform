from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any

from config.settings import (
    MAX_DAILY_CANDIDATES,
)
from decision.decision_engine import DecisionEngine
from logs.logger import log_event
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
        notification_service: (
            NotificationService | None
        ) = None,
        signal_guard: (
            DuplicateSignalGuard | None
        ) = None,
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

        log_event(
            "AUTO_SCAN_STARTED",
            message="Automatic HOME LIST scan started",
            trading_date=today.isoformat(),
            timeframe_minutes=timeframe_minutes,
        )

        scan_results = (
            self.scanner.scan_home_list(
                timeframe_minutes=timeframe_minutes,
                start_date=today,
                end_date=today,
                contexts=contexts,
            )
        )

        log_event(
            "AUTO_SCAN_RESULTS_READY",
            message="Automatic scan results ready",
            scanned_count=len(scan_results),
            timeframe_minutes=timeframe_minutes,
        )

        decision = (
            self.decision_engine.decide(
                scan_results=scan_results,
                limit=MAX_DAILY_CANDIDATES,
            )
        )

        log_event(
            "AUTO_SCAN_DECISION_CREATED",
            message="Automatic scan decision created",
            decision_status=(
                decision.decision_status.value
            ),
            candidates_count=(
                decision.candidates_count
            ),
            top_ticker=(
                decision.top_candidate.ticker
                if decision.top_candidate
                is not None
                else None
            ),
        )

        signal = self.signal_builder.build(
            decision=decision,
            entry_context=None,
        )

        if signal is None:
            log_event(
                "AUTO_SCAN_NO_SIGNAL",
                message=(
                    "Automatic scan completed "
                    "without signal"
                ),
                reason=decision.reason,
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
            log_event(
                "DUPLICATE_SIGNAL_BLOCKED",
                message="Duplicate signal blocked",
                ticker=signal.ticker,
                status=signal.status.value,
                reason=guard_result.reason,
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

        log_event(
            "AUTO_SCAN_COMPLETED",
            message="Automatic scan completed",
            ticker=signal.ticker,
            status=signal.status.value,
            notification_status=(
                notification_result.status.value
            ),
            attempts_count=(
                notification_result.attempts_count
            ),
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
        