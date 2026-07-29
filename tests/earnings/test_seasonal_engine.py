from datetime import date

import pytest

from earnings.models import EarningsCycle
from earnings.seasonal_engine import (
    calculate_quarter_statistics,
    get_quarter,
    group_cycles_by_quarter,
)


def build_cycle(
    report_date: date,
    day_zero_close: float = 100.0,
    cycle_low: float = 90.0,
    max_rebound_price: float = 108.0,
) -> EarningsCycle:
    return EarningsCycle(
        ticker="MSFT",
        report_date=report_date,
        next_report_date=date(
            report_date.year,
            min(report_date.month + 1, 12),
            28,
        ),
        day_zero_close=day_zero_close,
        cycle_low=cycle_low,
        cycle_low_date=report_date,
        days_to_low=5,
        max_rebound_price=max_rebound_price,
        max_rebound_date=report_date,
        days_low_to_rebound=7,
        days_report_to_rebound=12,
    )


def test_get_quarter() -> None:
    assert get_quarter(1) == 1
    assert get_quarter(4) == 2
    assert get_quarter(7) == 3
    assert get_quarter(10) == 4


def test_get_quarter_rejects_invalid_month() -> None:
    with pytest.raises(
        ValueError,
        match="report_month must be between 1 and 12",
    ):
        get_quarter(13)


def test_group_cycles_by_quarter() -> None:
    cycles = [
        build_cycle(date(2025, 1, 20)),
        build_cycle(date(2025, 4, 20)),
        build_cycle(date(2026, 1, 20)),
    ]

    grouped = group_cycles_by_quarter(cycles)

    assert len(grouped[1]) == 2
    assert len(grouped[2]) == 1


def test_group_cycles_rejects_empty_list() -> None:
    with pytest.raises(
        ValueError,
        match="At least one earnings cycle is required",
    ):
        group_cycles_by_quarter([])


def test_calculate_quarter_statistics() -> None:
    cycles = [
        build_cycle(
            report_date=date(2025, 1, 20),
            cycle_low=90.0,
            max_rebound_price=108.0,
        ),
        build_cycle(
            report_date=date(2026, 2, 20),
            cycle_low=80.0,
            max_rebound_price=96.0,
        ),
    ]

    result = calculate_quarter_statistics(cycles)

    assert result[1]["cycles_count"] == 2.0
    assert result[1]["average_drop_pct"] == pytest.approx(
        -15.0
    )
    assert result[1]["median_drop_pct"] == pytest.approx(
        -15.0
    )
    assert result[1]["average_days_to_low"] == 5.0
    assert result[1]["median_days_to_rebound"] == 7.0
