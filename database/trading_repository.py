from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg2.extras import Json, execute_values

from database.connection import get_connection
from decision.models import DecisionResult
from execution.models import TradePlan
from execution.risk_engine import PositionSizeResult
from notifications.models import NotificationResult
from scanner.models import ScanResult
from tracking.models import (
    AuditRecord,
    PerformanceRecord,
)


class TradingRepository:
    def save_scan_run(
        self,
        scan_run_id: UUID,
        started_at: datetime,
        timeframe_minutes: int,
        trading_date,
        status: str,
        scanned_count: int = 0,
        completed_at: datetime | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO scan_runs (
                id,
                started_at,
                completed_at,
                timeframe_minutes,
                trading_date,
                status,
                scanned_count,
                error_message,
                metadata
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            ON CONFLICT (id)
            DO UPDATE SET
                completed_at = EXCLUDED.completed_at,
                status = EXCLUDED.status,
                scanned_count = EXCLUDED.scanned_count,
                error_message = EXCLUDED.error_message,
                metadata = EXCLUDED.metadata;
            """,
            (
                str(scan_run_id),
                started_at,
                completed_at,
                timeframe_minutes,
                trading_date,
                status,
                scanned_count,
                error_message,
                Json(metadata or {}),
            ),
        )

        connection.commit()
        cursor.close()
        connection.close()

    def save_scan_results(
        self,
        scan_run_id: UUID,
        results: list[ScanResult],
    ) -> int:
        if not results:
            return 0

        values = [
            (
                str(scan_run_id),
                result.ticker,
                index,
                result.status.value,
                result.score,
                result.price,
                result.change_percent,
                result.volume,
                result.vwap,
                result.above_vwap,
                result.reason,
                Json({}),
            )
            for index, result in enumerate(
                results,
                start=1,
            )
        ]

        connection = get_connection()
        cursor = connection.cursor()

        execute_values(
            cursor,
            """
            INSERT INTO scan_results (
                scan_run_id,
                ticker,
                rank,
                scan_status,
                score,
                price,
                change_percent,
                volume,
                vwap,
                above_vwap,
                reason,
                engine_scores
            )
            VALUES %s;
            """,
            values,
        )

        connection.commit()
        cursor.close()
        connection.close()

        return len(values)

    def save_decision(
        self,
        decision_id: UUID,
        scan_run_id: UUID | None,
        decision: DecisionResult,
    ) -> None:
        top = decision.top_candidate

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO decisions (
                id,
                scan_run_id,
                ticker,
                decision_status,
                score,
                selected_rank,
                candidates_count,
                reason,
                metadata
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                str(decision_id),
                (
                    str(scan_run_id)
                    if scan_run_id
                    is not None
                    else None
                ),
                (
                    top.ticker
                    if top is not None
                    else None
                ),
                decision.decision_status.value,
                (
                    top.score
                    if top is not None
                    else 0.0
                ),
                (
                    top.rank
                    if top is not None
                    else None
                ),
                decision.candidates_count,
                decision.reason,
                Json({}),
            ),
        )

        connection.commit()
        cursor.close()
        connection.close()

    def save_trade_plan(
        self,
        trade_plan_id: UUID,
        decision_id: UUID,
        trade_plan: TradePlan,
    ) -> None:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO trade_plans (
                id,
                decision_id,
                ticker,
                entry_status,
                entry_price,
                stop_price,
                tp1_price,
                tp2_price,
                risk_per_share,
                risk_reward_tp1,
                risk_reward_tp2,
                invalidation_price,
                reason,
                metadata
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                str(trade_plan_id),
                str(decision_id),
                trade_plan.ticker,
                trade_plan.status.value,
                trade_plan.entry_price,
                trade_plan.stop_price,
                trade_plan.tp1_price,
                trade_plan.tp2_price,
                trade_plan.risk_per_share,
                trade_plan.risk_reward_tp1,
                trade_plan.risk_reward_tp2,
                trade_plan.invalidation_price,
                trade_plan.reason,
                Json({}),
            ),
        )

        connection.commit()
        cursor.close()
        connection.close()

    def save_risk_result(
        self,
        risk_result_id: UUID,
        trade_plan_id: UUID,
        result: PositionSizeResult,
    ) -> None:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO risk_results (
                id,
                trade_plan_id,
                ticker,
                risk_status,
                quantity,
                position_value,
                total_position_value,
                risk_per_share,
                total_risk,
                maximum_risk_value,
                maximum_position_value,
                maximum_allowed_value,
                reason
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                str(risk_result_id),
                str(trade_plan_id),
                result.ticker,
                result.status.value,
                result.quantity,
                result.position_value,
                result.total_position_value,
                result.risk_per_share,
                result.total_risk,
                result.maximum_risk_value,
                result.maximum_position_value,
                result.maximum_allowed_value,
                result.reason,
            ),
        )

        connection.commit()
        cursor.close()
        connection.close()

    def save_notification(
        self,
        notification_id: UUID,
        ticker: str | None,
        result: NotificationResult,
    ) -> None:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO notification_logs (
                id,
                ticker,
                notification_type,
                delivery_status,
                subject,
                recipients,
                attempts_count,
                sent_at,
                error_message
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                str(notification_id),
                (
                    ticker.upper()
                    if ticker
                    else None
                ),
                result.notification_type.value,
                result.status.value,
                result.subject,
                Json(list(result.recipients)),
                result.attempts_count,
                result.sent_at,
                result.error_message,
            ),
        )

        connection.commit()
        cursor.close()
        connection.close()

    def save_audit_record(
        self,
        record: AuditRecord,
    ) -> None:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO audit_records (
                audit_id,
                created_at,
                ticker,
                event,
                decision,
                score,
                entry_price,
                stop_price,
                tp1_price,
                tp2_price,
                reason,
                input_data,
                output_data
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            ON CONFLICT (audit_id)
            DO NOTHING;
            """,
            (
                record.audit_id,
                record.created_at,
                record.ticker,
                record.event.value,
                record.decision.value,
                record.score,
                record.entry_price,
                record.stop_price,
                record.tp1_price,
                record.tp2_price,
                record.reason,
                Json(record.input_data),
                Json(record.output_data),
            ),
        )

        connection.commit()
        cursor.close()
        connection.close()

    def save_performance_record(
        self,
        record: PerformanceRecord,
    ) -> None:
        data = asdict(record)

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO performance_records (
                ticker,
                created_at,
                decision,
                result,
                entry_price,
                exit_price,
                stop_price,
                tp1_price,
                tp2_price,
                return_percent,
                decision_score,
                engine_scores,
                selected_rank,
                notes
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                record.ticker,
                record.created_at,
                record.decision.value,
                record.result.value,
                record.entry_price,
                record.exit_price,
                record.stop_price,
                record.tp1_price,
                record.tp2_price,
                record.return_percent,
                record.decision_score,
                Json(data["engine_scores"]),
                record.selected_rank,
                record.notes,
            ),
        )

        connection.commit()
        cursor.close()
        connection.close()
        