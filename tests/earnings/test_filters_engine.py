import pytest

from earnings.filters_engine import (
    evaluate_bac_late_entry,
    evaluate_cof_late_entry,
    evaluate_lly_overshoot,
)


def test_lly_overshoot_triggered() -> None:
    result = evaluate_lly_overshoot(
        ticker="LLY",
        entry_price=100.0,
        closes_after_entry=[
            99.0,
            97.0,
            93.5,
            95.0,
            96.0,
        ],
    )

    assert result.triggered is True
    assert result.action == "WAIT_FOR_STABILIZATION"


def test_lly_overshoot_not_triggered() -> None:
    result = evaluate_lly_overshoot(
        ticker="LLY",
        entry_price=100.0,
        closes_after_entry=[
            99.0,
            98.0,
            97.0,
            96.0,
            95.0,
        ],
    )

    assert result.triggered is False
    assert result.action == "NORMAL_PATH"


def test_lly_filter_not_applicable() -> None:
    result = evaluate_lly_overshoot(
        ticker="MSFT",
        entry_price=100.0,
        closes_after_entry=[90.0],
    )

    assert result.triggered is False
    assert result.action == "NOT_APPLICABLE"


def test_bac_late_entry_triggered() -> None:
    result = evaluate_bac_late_entry(
        entry_day=16,
        entry_volume=1_300_000,
        average_volume_5d=1_000_000,
        day_zero_close=100.0,
        entry_close=95.0,
    )

    assert result.triggered is True
    assert result.action == "SKIP_CYCLE"


def test_bac_late_entry_requires_close_below_day_zero() -> None:
    result = evaluate_bac_late_entry(
        entry_day=16,
        entry_volume=1_300_000,
        average_volume_5d=1_000_000,
        day_zero_close=100.0,
        entry_close=101.0,
    )

    assert result.triggered is False
    assert result.action == "NORMAL_PATH"


def test_cof_late_entry_triggered() -> None:
    result = evaluate_cof_late_entry(
        entry_day=17,
        entry_volume=1_400_000,
        average_volume_5d=1_000_000,
        day_zero_close=100.0,
        entry_close=102.0,
    )

    assert result.triggered is True
    assert result.action == "SKIP_CYCLE"


def test_invalid_average_volume() -> None:
    with pytest.raises(
        ValueError,
        match="average_volume_5d must be greater than zero",
    ):
        evaluate_bac_late_entry(
            entry_day=16,
            entry_volume=1_300_000,
            average_volume_5d=0,
            day_zero_close=100.0,
            entry_close=95.0,
        )
