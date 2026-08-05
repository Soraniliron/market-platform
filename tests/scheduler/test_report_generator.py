from __future__ import annotations

from datetime import date, datetime, timezone

from scheduler.report_generator import (
    MonthlyPerformanceSummary,
    ReportGenerator,
)
from tracking.models import (
    DecisionType,
    PerformanceRecord,
    TradeResult,
)
from tracking.performance_engine import (
    DailyPerformanceSummary,
)


def build_record() -> PerformanceRecord:
    return PerformanceRecord(
        ticker="META",
        created_at=datetime.now(timezone.utc),
        decision=DecisionType.BUY,
        result=TradeResult.TP1,
        entry_price=100.0,
        exit_price=102.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        return_percent=2.0,
        decision_score=91.0,
        engine_scores={"gap": 90.0},
        selected_rank=1,
        notes="OK",
    )


def build_summary() -> DailyPerformanceSummary:
    return DailyPerformanceSummary(
        records_count=5,
        buy_signals_count=3,
        entries_count=3,
        tp1_count=1,
        tp2_count=1,
        stop_count=1,
        no_entry_count=2,
        wins_count=2,
        losses_count=1,
        win_rate=66.67,
        total_return_percent=4.0,
        average_return_percent=1.3333,
        false_signals_count=1,
        missed_opportunities_count=2,
    )


def test_build_daily_report() -> None:
    generator = ReportGenerator()

    report = generator.build_daily_report(
        trading_date=date(2026, 8, 5),
        summary=build_summary(),
        selected_ticker="META",
        selected_reason="Highest decision score",
        records=[build_record()],
    )

    assert "IDB PRIME - DAILY REPORT" in report
    assert "META" in report
    assert "Highest decision score" in report
    assert "Win rate: 66.67%" in report


def test_build_monthly_report() -> None:
    generator = ReportGenerator()

    summary = MonthlyPerformanceSummary(
        month="2026-08",
        trading_days_count=20,
        records_count=100,
        buy_signals_count=40,
        entries_count=30,
        tp1_count=15,
        tp2_count=10,
        stop_count=5,
        no_entry_count=70,
        wins_count=25,
        losses_count=5,
        win_rate=83.33,
        total_return_percent=35.0,
        average_return_percent=1.75,
        false_signals_count=5,
        missed_opportunities_count=8,
    )

    report = generator.build_monthly_report(summary)

    assert "MONTHLY REPORT" in report
    assert "2026-08" in report
    assert "83.33%" in report


def test_summarize_month() -> None:
    generator = ReportGenerator()

    summary = generator.summarize_month(
        month="2026-08",
        daily_summaries=[
            build_summary(),
            build_summary(),
        ],
    )

    assert summary.trading_days_count == 2
    assert summary.records_count == 10
    assert summary.buy_signals_count == 6
    assert summary.entries_count == 6
    assert summary.wins_count == 4
    assert summary.losses_count == 2
    assert summary.false_signals_count == 2
    assert summary.missed_opportunities_count == 4
    