from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from tracking.models import PerformanceRecord
from tracking.performance_engine import (
    DailyPerformanceSummary,
)


@dataclass(frozen=True)
class MonthlyPerformanceSummary:
    month: str

    trading_days_count: int
    records_count: int
    buy_signals_count: int
    entries_count: int

    tp1_count: int
    tp2_count: int
    stop_count: int
    no_entry_count: int

    wins_count: int
    losses_count: int
    win_rate: float

    total_return_percent: float
    average_return_percent: float

    false_signals_count: int
    missed_opportunities_count: int


class ReportGenerator:
    def build_daily_report(
        self,
        trading_date: date,
        summary: DailyPerformanceSummary,
        selected_ticker: str | None = None,
        selected_reason: str = "",
        records: Iterable[
            PerformanceRecord
        ] = (),
    ) -> str:
        record_lines = self._build_record_lines(
            records
        )

        selected_text = (
            selected_ticker.upper()
            if selected_ticker
            else "NO TRADE"
        )

        reason_text = (
            selected_reason
            if selected_reason
            else "No reason recorded"
        )

        lines = [
            "IDB PRIME - DAILY REPORT",
            "",
            f"Date: {trading_date.isoformat()}",
            f"Selected: {selected_text}",
            f"Reason: {reason_text}",
            "",
            "SUMMARY",
            f"Records: {summary.records_count}",
            (
                "Buy signals: "
                f"{summary.buy_signals_count}"
            ),
            f"Entries: {summary.entries_count}",
            f"TP1: {summary.tp1_count}",
            f"TP2: {summary.tp2_count}",
            f"Stops: {summary.stop_count}",
            (
                "No entry: "
                f"{summary.no_entry_count}"
            ),
            f"Wins: {summary.wins_count}",
            f"Losses: {summary.losses_count}",
            f"Win rate: {summary.win_rate:.2f}%",
            (
                "Total return: "
                f"{summary.total_return_percent:.4f}%"
            ),
            (
                "Average return: "
                f"{summary.average_return_percent:.4f}%"
            ),
            (
                "False signals: "
                f"{summary.false_signals_count}"
            ),
            (
                "Missed opportunities: "
                f"{summary.missed_opportunities_count}"
            ),
        ]

        if record_lines:
            lines.extend(
                [
                    "",
                    "RECORDS",
                    *record_lines,
                ]
            )

        return "\n".join(lines)

    def build_monthly_report(
        self,
        summary: MonthlyPerformanceSummary,
    ) -> str:
        lines = [
            "IDB PRIME - MONTHLY REPORT",
            "",
            f"Month: {summary.month}",
            (
                "Trading days: "
                f"{summary.trading_days_count}"
            ),
            f"Records: {summary.records_count}",
            (
                "Buy signals: "
                f"{summary.buy_signals_count}"
            ),
            f"Entries: {summary.entries_count}",
            f"TP1: {summary.tp1_count}",
            f"TP2: {summary.tp2_count}",
            f"Stops: {summary.stop_count}",
            (
                "No entry: "
                f"{summary.no_entry_count}"
            ),
            f"Wins: {summary.wins_count}",
            f"Losses: {summary.losses_count}",
            f"Win rate: {summary.win_rate:.2f}%",
            (
                "Total return: "
                f"{summary.total_return_percent:.4f}%"
            ),
            (
                "Average return: "
                f"{summary.average_return_percent:.4f}%"
            ),
            (
                "False signals: "
                f"{summary.false_signals_count}"
            ),
            (
                "Missed opportunities: "
                f"{summary.missed_opportunities_count}"
            ),
        ]

        return "\n".join(lines)

    def summarize_month(
        self,
        month: str,
        daily_summaries: list[
            DailyPerformanceSummary
        ],
    ) -> MonthlyPerformanceSummary:
        if not month:
            raise ValueError(
                "month must not be empty"
            )

        trading_days_count = len(
            daily_summaries
        )

        records_count = sum(
            item.records_count
            for item in daily_summaries
        )

        buy_signals_count = sum(
            item.buy_signals_count
            for item in daily_summaries
        )

        entries_count = sum(
            item.entries_count
            for item in daily_summaries
        )

        tp1_count = sum(
            item.tp1_count
            for item in daily_summaries
        )

        tp2_count = sum(
            item.tp2_count
            for item in daily_summaries
        )

        stop_count = sum(
            item.stop_count
            for item in daily_summaries
        )

        no_entry_count = sum(
            item.no_entry_count
            for item in daily_summaries
        )

        wins_count = sum(
            item.wins_count
            for item in daily_summaries
        )

        losses_count = sum(
            item.losses_count
            for item in daily_summaries
        )

        completed_trades = (
            wins_count + losses_count
        )

        win_rate = (
            round(
                wins_count
                / completed_trades
                * 100,
                2,
            )
            if completed_trades > 0
            else 0.0
        )

        total_return_percent = round(
            sum(
                item.total_return_percent
                for item in daily_summaries
            ),
            4,
        )

        total_return_records = sum(
            1
            for item in daily_summaries
            if (
                item.entries_count > 0
                and (
                    item.wins_count
                    + item.losses_count
                ) > 0
            )
        )

        average_return_percent = (
            round(
                total_return_percent
                / total_return_records,
                4,
            )
            if total_return_records > 0
            else 0.0
        )

        false_signals_count = sum(
            item.false_signals_count
            for item in daily_summaries
        )

        missed_opportunities_count = sum(
            item.missed_opportunities_count
            for item in daily_summaries
        )

        return MonthlyPerformanceSummary(
            month=month,
            trading_days_count=(
                trading_days_count
            ),
            records_count=records_count,
            buy_signals_count=(
                buy_signals_count
            ),
            entries_count=entries_count,
            tp1_count=tp1_count,
            tp2_count=tp2_count,
            stop_count=stop_count,
            no_entry_count=no_entry_count,
            wins_count=wins_count,
            losses_count=losses_count,
            win_rate=win_rate,
            total_return_percent=(
                total_return_percent
            ),
            average_return_percent=(
                average_return_percent
            ),
            false_signals_count=(
                false_signals_count
            ),
            missed_opportunities_count=(
                missed_opportunities_count
            ),
        )

    @staticmethod
    def _build_record_lines(
        records: Iterable[
            PerformanceRecord
        ],
    ) -> list[str]:
        lines: list[str] = []

        for record in records:
            return_text = (
                f"{record.return_percent:.4f}%"
                if record.return_percent
                is not None
                else "N/A"
            )

            lines.append(
                (
                    f"{record.ticker} | "
                    f"{record.decision.value.upper()} | "
                    f"{record.result.value.upper()} | "
                    f"score={record.decision_score:.2f} | "
                    f"return={return_text}"
                )
            )

        return lines
        