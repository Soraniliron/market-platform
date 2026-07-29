from datetime import date

import pytest

from earnings.exit_engine import (
    calculate_exit_percentile_level,
    calculate_exit_percentiles,
)
from earnings.models import EarningsCycle


def build_cycle(
    ticker: str,
    day_zero_close: float,
) -> EarningsCycle:
    return EarningsCycle(
        ticker=ticker,
        report_date=date(2026, 1, 1),
        next_report_date=date(2026, 2, 1),
        day_zero_close=day_zero_close,
        cycle_low=day_zero_close * 0.90,
        cycle_low_date=date(2026, 1, 10),
        days_to_low=7,
        max_rebound_price=day_zero_close * 1.05,
        max_rebound_date=date(2026, 1, 20),
        days_low_to_rebound=8,
        days_report_to_rebound=15,
    )


def test_calculate_exit_percentile_level() -> None:
    entry_cycle_data = [
        {
            "prices": [
                {"close": 90.0, "high": 90.0},
                {"close": 92.0, "high": 95.0},
                {"close": 96.0, "high": 100.0},
            ],
            "entry_index": 0,
            "entry_price": 90.0,
            "maximum_return_pct": 11.111111,
        },
        {
            "prices": [
                {"close": 90.0, "high": 90.0},
                {"close": 93.0, "high": 94.5},
            ],
            "entry_index": 0,
            "entry_price": 90.0,
            "maximum_return_pct": 5.0,
        },
    ]

    result = calculate_exit_percentile_level(
        cycles_count=4,
        entry_cycle_data=entry_cycle_data,
        reach_probability=0.50,
        current_entry_price=90.0,
    )

    assert result.percentile == 50.0
    assert result.target_return_pct == pytest.approx(
        11.111111
    )
    assert result.exit_price == pytest.approx(100.0)
    assert result.entry_hits == 2
    assert result.target_hits_after_entry == 1
    assert result.target_probability_after_entry == 50.0
    assert result.full_cycle_probability == 25.0


def test_exit_percentiles_requires_cycles() -> None:
    with pytest.raises(
        ValueError,
        match="At least one earnings cycle is required",
    ):
        calculate_exit_percentiles(
            ticker="MSFT",
            cycles=[],
            entry_drop_pct=-10.0,
        )


def test_exit_percentiles_rejects_positive_entry_drop() -> None:
    cycles = [
        build_cycle(
            ticker="MSFT",
            day_zero_close=100.0,
        )
    ]

    with pytest.raises(
        ValueError,
        match="entry_drop_pct must be zero or negative",
    ):
        calculate_exit_percentiles(
            ticker="MSFT",
            cycles=cycles,
            entry_drop_pct=5.0,
        )


def test_exit_percentiles_rejects_ticker_mismatch() -> None:
    cycles = [
        build_cycle(
            ticker="AAPL",
            day_zero_close=100.0,
        )
    ]

    with pytest.raises(
        ValueError,
        match="Cycle ticker AAPL does not match MSFT",
    ):
        calculate_exit_percentiles(
            ticker="MSFT",
            cycles=cycles,
            entry_drop_pct=-10.0,
        )
