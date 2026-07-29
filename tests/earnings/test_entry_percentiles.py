from datetime import date

from earnings.earnings_engine import (
    calculate_entry_percentiles,
    get_sample_status,
)
from earnings.models import EarningsCycle


def build_cycle(
    ticker: str,
    day_zero_close: float,
    cycle_low: float,
) -> EarningsCycle:
    return EarningsCycle(
        ticker=ticker,
        report_date=date(2025, 1, 1),
        next_report_date=date(2025, 4, 1),
        day_zero_close=day_zero_close,
        cycle_low=cycle_low,
        cycle_low_date=date(2025, 2, 1),
        days_to_low=20,
        max_rebound_price=day_zero_close,
        max_rebound_date=date(2025, 3, 1),
        days_low_to_rebound=20,
        days_report_to_rebound=40,
    )


def test_three_cycles_are_insufficient_for_production() -> None:
    cycles = [
        build_cycle("MSFT", 100.0, 80.0),
        build_cycle("MSFT", 100.0, 85.0),
        build_cycle("MSFT", 100.0, 95.0),
    ]

    result = calculate_entry_percentiles(
        ticker="MSFT",
        cycles=cycles,
        reference_price=100.0,
    )

    assert result.cycles_count == 3
    assert result.minimum_cycles_required == 12
    assert result.production_ready is False
    assert result.sample_status == "INSUFFICIENT_SAMPLE"


def test_p60_requires_two_hits_out_of_three() -> None:
    cycles = [
        build_cycle("MSFT", 100.0, 80.0),
        build_cycle("MSFT", 100.0, 85.0),
        build_cycle("MSFT", 100.0, 95.0),
    ]

    result = calculate_entry_percentiles(
        ticker="MSFT",
        cycles=cycles,
        reference_price=100.0,
    )

    assert result.p60.entry_hits == 2
    assert round(result.p60.entry_probability, 2) == 66.67
    assert result.p60.entry_drop_pct == -15.0
    assert result.p60.entry_price == 85.0


def test_p90_requires_all_three_cycles() -> None:
    cycles = [
        build_cycle("MSFT", 100.0, 80.0),
        build_cycle("MSFT", 100.0, 85.0),
        build_cycle("MSFT", 100.0, 95.0),
    ]

    result = calculate_entry_percentiles(
        ticker="MSFT",
        cycles=cycles,
        reference_price=100.0,
    )

    assert result.p90.entry_hits == 3
    assert result.p90.entry_probability == 100.0
    assert result.p90.entry_drop_pct == -5.0
    assert result.p90.entry_price == 95.0


def test_sample_status_levels() -> None:
    assert get_sample_status(3, 12) == "INSUFFICIENT_SAMPLE"
    assert get_sample_status(4, 12) == "RESEARCH_ONLY"
    assert get_sample_status(12, 12) == "PRODUCTION_READY"
    assert get_sample_status(20, 12) == "STABILITY_READY"
