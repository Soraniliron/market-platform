from datetime import date

import pytest

from earnings.models import EarningsCycle
from earnings.probability_engine import (
    calculate_entry_exit_analysis,
    calculate_percentile,
)


def build_cycle(
    ticker: str = "MSFT",
    day_zero_close: float = 100.0,
) -> EarningsCycle:
    return EarningsCycle(
        ticker=ticker,
        report_date=date(2026, 1, 1),
        next_report_date=date(2026, 2, 1),
        day_zero_close=day_zero_close,
        cycle_low=90.0,
        cycle_low_date=date(2026, 1, 10),
        days_to_low=7,
        max_rebound_price=105.0,
        max_rebound_date=date(2026, 1, 20),
        days_low_to_rebound=8,
        days_report_to_rebound=15,
    )


def test_calculate_percentile_interpolates() -> None:
    result = calculate_percentile(
        values=[10.0, 20.0, 30.0],
        percentile=0.25,
    )

    assert result == pytest.approx(15.0)


def test_calculate_percentile_rejects_empty_values() -> None:
    with pytest.raises(
        ValueError,
        match="At least one value is required",
    ):
        calculate_percentile(
            values=[],
            percentile=0.50,
        )


def test_calculate_percentile_rejects_invalid_probability() -> None:
    with pytest.raises(
        ValueError,
        match="percentile must be between 0 and 1",
    ):
        calculate_percentile(
            values=[10.0],
            percentile=1.10,
        )


def test_entry_exit_analysis_rejects_ticker_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="Cycle ticker AAPL does not match MSFT",
    ):
        calculate_entry_exit_analysis(
            ticker="MSFT",
            cycles=[
                build_cycle(
                    ticker="AAPL",
                )
            ],
        )


def test_entry_exit_analysis_rejects_invalid_target() -> None:
    with pytest.raises(
        ValueError,
        match="target_return_pct must be greater than zero",
    ):
        calculate_entry_exit_analysis(
            ticker="MSFT",
            cycles=[build_cycle()],
            target_return_pct=0.0,
        )
