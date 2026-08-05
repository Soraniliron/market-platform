from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from decision.decision_engine import DecisionEngine
from decision.models import (
    DecisionStatus,
    TradingSignal,
)
from execution.models import EntryContext
from execution.risk_engine import (
    PositionSizeResult,
    RiskContext,
    RiskEngine,
    RiskStatus,
)
from integration.models import (
    PipelineResult,
    PipelineTimer,
)
from logs.logger import log_event
from metrics.collector import (
    MetricsCollector,
    metrics,
)
from notifications.models import (
    NotificationResult,
    NotificationType,
)
from notifications.notification_service import (
    NotificationService,
)
from scanner.context import MarketContext
from scanner.scanner_engine import MarketScanner
from signals.signal_builder import SignalBuilder
from tracking.audit_engine import AuditEngine
from tracking.models import (
    AuditEvent,
    AuditRecord,
    DecisionType,
)


class ManualTradingPipeline:
    def __init__(
        self,
        scanner: MarketScanner | None = None,
        decision_engine: DecisionEngine | None = None,
        signal_builder: SignalBuilder | None = None,
        risk_engine: RiskEngine | None = None,
        notification_service: (
            NotificationService | None
        ) = None,
        audit_engine: AuditEngine | None = None,
        metrics_collector: (
            MetricsCollector | None
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

        self.risk_engine = (
            risk_engine
            or RiskEngine()
        )

        self.notification_service = (
            notification_service
            or NotificationService()
        )

        self.audit_engine = (
            audit_engine
            or AuditEngine()
        )

        self.metrics = (
            metrics_collector
            or metrics
        )

    def run(
        self,
        timeframe_minutes: int,
        start_date: date,
        end_date: date,
        market_contexts: (
            dict[str, MarketContext]
            | None
        ) = None,
        entry_context: EntryContext | None = None,
        risk_context: RiskContext | None = None,
        recipients: tuple[str, ...] | None = None,
        audit_file_path: (
            str | Path | None
        ) = None,
    ) -> PipelineResult:
        timer = PipelineTimer()

        decision = None
        signal = None
        position_size = None
        notification = None
        audit_record = None

        metadata: dict[str, Any] = {
            "timeframe_minutes": (
                timeframe_minutes
            ),
            "start_date": (
                start_date.isoformat()
            ),
            "end_date": (
                end_date.isoformat()
            ),
        }

        log_event(
            "PIPELINE_STARTED",
            message="Manual trading pipeline started",
            timeframe_minutes=timeframe_minutes,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        try:
            log_event(
                "SCAN_STARTED",
                message="HOME LIST scan started",
                timeframe_minutes=timeframe_minutes,
            )

            scan_results = self.metrics.measure(
                "pipeline.scanner",
                self.scanner.scan_home_list,
                timeframe_minutes=timeframe_minutes,
                start_date=start_date,
                end_date=end_date,
                contexts=market_contexts,
            )

            metadata["scanned_count"] = len(
                scan_results
            )

            log_event(
                "SCAN_COMPLETED",
                message="HOME LIST scan completed",
                scanned_count=len(scan_results),
                timeframe_minutes=timeframe_minutes,
            )

            decision = self.metrics.measure(
                "pipeline.decision",
                self.decision_engine.decide,
                scan_results=scan_results,
                limit=3,
            )

            log_event(
                "DECISION_CREATED",
                message="Trading decision created",
                status=(
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
                top_score=(
                    decision.top_candidate.score
                    if decision.top_candidate
                    is not None
                    else None
                ),
            )

            signal = self.metrics.measure(
                "pipeline.signal_builder",
                self.signal_builder.build,
                decision=decision,
                entry_context=entry_context,
            )

            if signal is None:
                log_event(
                    "NO_SIGNAL",
                    message="Pipeline completed without signal",
                    decision_status=(
                        decision.decision_status.value
                    ),
                    reason=decision.reason,
                )

                audit_record = (
                    self._create_audit_record(
                        ticker="MARKET",
                        signal=None,
                        decision_status=(
                            decision.decision_status
                        ),
                        score=0.0,
                        reason=decision.reason,
                        input_data={
                            "scan_results": [
                                asdict(item)
                                for item
                                in scan_results
                            ],
                        },
                        output_data={
                            "decision": asdict(
                                decision
                            ),
                            "signal": None,
                        },
                    )
                )

                self._save_audit_if_requested(
                    record=audit_record,
                    audit_file_path=(
                        audit_file_path
                    ),
                )

                return self._result(
                    timer=timer,
                    success=True,
                    decision=decision,
                    signal=None,
                    position_size=None,
                    notification=None,
                    audit_record=audit_record,
                    metadata=metadata,
                )

            log_event(
                "SIGNAL_CREATED",
                message="Trading signal created",
                ticker=signal.ticker,
                status=signal.status.value,
                score=signal.score,
                entry_price=signal.entry_price,
                stop_price=signal.stop_price,
                tp1_price=signal.tp1_price,
                tp2_price=signal.tp2_price,
            )

            if (
                signal.status
                == DecisionStatus.BUY
            ):
                if entry_context is None:
                    raise ValueError(
                        "entry_context is required "
                        "for a BUY signal"
                    )

                if risk_context is None:
                    raise ValueError(
                        "risk_context is required "
                        "for a BUY signal"
                    )

                trade_plan = self.metrics.measure(
                    "pipeline.entry",
                    (
                        self.signal_builder
                        .entry_engine
                        .build_trade_plan
                    ),
                    ticker=signal.ticker,
                    context=entry_context,
                )

                position_size = self.metrics.measure(
                    "pipeline.risk",
                    (
                        self.risk_engine
                        .calculate_position_size
                    ),
                    trade_plan=trade_plan,
                    context=risk_context,
                )

                log_event(
                    "RISK_EVALUATED",
                    message="Risk evaluation completed",
                    ticker=signal.ticker,
                    status=position_size.status.value,
                    quantity=position_size.quantity,
                    position_value=(
                        position_size.position_value
                    ),
                    total_risk=(
                        position_size.total_risk
                    ),
                    reason=position_size.reason,
                )

                if (
                    position_size.status
                    == RiskStatus.REJECTED
                ):
                    signal = TradingSignal(
                        ticker=signal.ticker,
                        status=DecisionStatus.AVOID,
                        score=signal.score,
                        entry_price=None,
                        stop_price=None,
                        tp1_price=None,
                        tp2_price=None,
                        reason=(
                            f"{signal.reason} | "
                            f"Risk rejected: "
                            f"{position_size.reason}"
                        ),
                    )

                    log_event(
                        "RISK_REJECTED",
                        message="Signal rejected by risk engine",
                        ticker=signal.ticker,
                        reason=position_size.reason,
                    )

            notification = self.metrics.measure(
                "pipeline.notification",
                self._send_notification,
                signal=signal,
                recipients=recipients,
            )

            log_event(
                "NOTIFICATION_COMPLETED",
                message="Notification processing completed",
                ticker=signal.ticker,
                notification_type=(
                    notification
                    .notification_type
                    .value
                ),
                delivery_status=(
                    notification.status.value
                ),
                attempts_count=(
                    notification.attempts_count
                ),
            )

            audit_record = (
                self._create_audit_record(
                    ticker=signal.ticker,
                    signal=signal,
                    decision_status=(
                        signal.status
                    ),
                    score=signal.score,
                    reason=signal.reason,
                    input_data={
                        "entry_context": (
                            asdict(entry_context)
                            if entry_context
                            is not None
                            else None
                        ),
                        "risk_context": (
                            asdict(risk_context)
                            if risk_context
                            is not None
                            else None
                        ),
                    },
                    output_data={
                        "decision": asdict(
                            decision
                        ),
                        "signal": asdict(
                            signal
                        ),
                        "position_size": (
                            asdict(position_size)
                            if position_size
                            is not None
                            else None
                        ),
                        "notification": (
                            asdict(notification)
                            if notification
                            is not None
                            else None
                        ),
                    },
                )
            )

            self._save_audit_if_requested(
                record=audit_record,
                audit_file_path=(
                    audit_file_path
                ),
            )

            return self._result(
                timer=timer,
                success=True,
                decision=decision,
                signal=signal,
                position_size=position_size,
                notification=notification,
                audit_record=audit_record,
                metadata=metadata,
            )

        except Exception as error:
            metadata["error"] = str(error)

            log_event(
                "PIPELINE_FAILED",
                level=40,
                message="Manual trading pipeline failed",
                error=str(error),
                timeframe_minutes=timeframe_minutes,
            )

            return self._result(
                timer=timer,
                success=False,
                decision=decision,
                signal=signal,
                position_size=position_size,
                notification=notification,
                audit_record=audit_record,
                metadata=metadata,
            )

    def _result(
        self,
        timer: PipelineTimer,
        success: bool,
        decision,
        signal,
        position_size,
        notification,
        audit_record,
        metadata: dict[str, Any],
    ) -> PipelineResult:
        elapsed = timer.elapsed()

        self.metrics.record(
            "pipeline.total",
            elapsed,
        )

        metadata["execution_time_seconds"] = (
            elapsed
        )

        log_event(
            "PIPELINE_COMPLETED",
            message="Manual trading pipeline completed",
            success=success,
            execution_time_seconds=elapsed,
            scanned_count=metadata.get(
                "scanned_count",
                0,
            ),
            signal_ticker=(
                signal.ticker
                if signal is not None
                else None
            ),
            signal_status=(
                signal.status.value
                if signal is not None
                else None
            ),
        )

        return PipelineResult(
            success=success,
            decision=decision,
            signal=signal,
            position_size=position_size,
            notification=notification,
            audit_record=audit_record,
            execution_time_seconds=elapsed,
            metadata=metadata,
        )

    def _send_notification(
        self,
        signal: TradingSignal,
        recipients: tuple[str, ...] | None,
    ) -> NotificationResult:
        notification_type = (
            self._notification_type(
                signal.status
            )
        )

        return (
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

    def _create_audit_record(
        self,
        ticker: str,
        signal: TradingSignal | None,
        decision_status: DecisionStatus,
        score: float,
        reason: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
    ) -> AuditRecord:
        return self.audit_engine.create_record(
            ticker=ticker,
            event=AuditEvent.SIGNAL,
            decision=(
                self._decision_type(
                    decision_status
                )
            ),
            score=score,
            reason=reason,
            input_data=input_data,
            output_data=output_data,
            entry_price=(
                signal.entry_price
                if signal is not None
                else None
            ),
            stop_price=(
                signal.stop_price
                if signal is not None
                else None
            ),
            tp1_price=(
                signal.tp1_price
                if signal is not None
                else None
            ),
            tp2_price=(
                signal.tp2_price
                if signal is not None
                else None
            ),
        )

    def _save_audit_if_requested(
        self,
        record: AuditRecord,
        audit_file_path: str | Path | None,
    ) -> None:
        if audit_file_path is None:
            return

        self.audit_engine.save_record(
            record=record,
            file_path=audit_file_path,
        )

    @staticmethod
    def _notification_type(
        status: DecisionStatus,
    ) -> NotificationType:
        mapping = {
            DecisionStatus.BUY: (
                NotificationType.BUY
            ),
            DecisionStatus.WATCH: (
                NotificationType.WATCH
            ),
            DecisionStatus.WAIT: (
                NotificationType.WAIT
            ),
            DecisionStatus.AVOID: (
                NotificationType.AVOID
            ),
        }

        return mapping[status]

    @staticmethod
    def _decision_type(
        status: DecisionStatus,
    ) -> DecisionType:
        mapping = {
            DecisionStatus.BUY: (
                DecisionType.BUY
            ),
            DecisionStatus.WATCH: (
                DecisionType.WATCH
            ),
            DecisionStatus.WAIT: (
                DecisionType.WAIT
            ),
            DecisionStatus.AVOID: (
                DecisionType.AVOID
            ),
        }

        return mapping[status]
        