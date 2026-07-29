from datetime import date, timedelta

import pytest

from earnings.earnings_engine import analyze_earnings_cycles
from earnings.models import EarningsCycle
from earnings.report_engine import (
    build_report,
    format_report_text,
    report_to_dict,
)


def build_cycles(
    ticker: str,
    count: int = 12,
) -> list[EarningsCycle]:
    cycles: list[EarningsCycle] = []
    base_date = date(2023, 1, 1)

    for index in range(count):
        report_date = (
            base_date
            + timedelta(days=index * 90)
        )

        next_report_date = (
            report_date
            + timedelta(days=90)
        )

        day_zero_close = 100.0 + index
        cycle_low = day_zero_close * 0.90

        cycle_low_date = (
            report_date
            + timedelta(days=10)
        )

        max_rebound_price = (
            cycle_low * 1.15
        )

        max_rebound_date = (
            cycle_low_date
            + timedelta(days=20)
        )

        cycles.append(
            EarningsCycle(
                ticker=ticker,
                report_date=report_date,
                next_report_date=next_report_date,
                day_zero_close=day_zero_close,
                cycle_low=cycle_low,
                cycle_low_date=cycle_low_date,
                days_to_low=10,
                max_rebound_price=max_rebound_price,
                max_rebound_date=max_rebound_date,
                days_low_to_rebound=20,
                days_report_to_rebound=30,
            )
        )

    return cycles


def build_mock_price_history(
    ticker: str,
    start_date: date,
    end_date: date,
) -> list[dict]:
    prices: list[dict] = []

    current_date = start_date
    day_index = 0

    while current_date <= end_date:
        if day_index < 10:
            close_price = 100.0 - day_index
        else:
            close_price = 90.0 + (
                (day_index - 10) * 1.5
            )

        prices.append(
            {
                "ticker": ticker,
                "date": current_date,
                "open": close_price,
                "high": close_price + 2.0,
                "low": close_price - 2.0,
                "close": close_price,
                "volume": 1_000_000,
            }
        )

        current_date += timedelta(days=1)
        day_index += 1

    return prices


@pytest.fixture
def mock_price_history(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "earnings.exit_engine.get_price_history",
        build_mock_price_history,
    )


def test_full_analysis_to_report_flow(
    mock_price_history,
) -> None:
    cycles = build_cycles(
        ticker="MSFT",
        count=12,
    )

    result = analyze_earnings_cycles(
        ticker="MSFT",
        cycles=cycles,
        reference_price=120.0,
        entry_percentile=0.60,
        exit_percentile=0.60,
        minimum_cycles_required=12,
    )

    report = build_report(result)
    report_dict = report_to_dict(report)
    report_text = format_report_text(report)

    assert result.ticker == "MSFT"
    assert result.cycles_count == 12
    assert result.production_ready is True

    assert report.ticker == "MSFT"
    assert report.production_ready is True
    assert report.entry_price > 0
    assert report.exit_price > report.entry_price

    assert report_dict["ticker"] == "MSFT"
    assert report_dict["production_ready"] is True
    assert report_dict["entry_price"] == (
        report.entry_price
    )
    assert report_dict["exit_price"] == (
        report.exit_price
    )

    assert "MSFT" in report_text
    assert "Entry:" in report_text
    assert "Exit:" in report_text
    assert "Production: READY" in report_text


def test_end_to_end_not_ready_with_small_sample(
    mock_price_history,
) -> None:
    cycles = build_cycles(
        ticker="JPM",
        count=5,
    )

    result = analyze_earnings_cycles(
        ticker="JPM",
        cycles=cycles,
        reference_price=200.0,
        entry_percentile=0.60,
        exit_percentile=0.60,
        minimum_cycles_required=12,
    )

    report = build_report(result)
    report_text = format_report_text(report)

    assert result.production_ready is False
    assert report.production_ready is False
    assert "Production: NOT READY" in report_text


def test_end_to_end_rejects_ticker_mismatch() -> None:
    cycles = build_cycles(
        ticker="MSFT",
        count=12,
    )

    with pytest.raises(
        ValueError,
        match="does not match JPM",
    ):
        analyze_earnings_cycles(
            ticker="JPM",
            cycles=cycles,
        )
