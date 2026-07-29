import pytest

from earnings.overshoot_engine import (
    analyze_overshoot_cycle,
    analyze_overshoot_history,
    calculate_overshoot_pct,
)


def test_calculate_overshoot_pct() -> None:
    result = calculate_overshoot_pct(
        entry_price=100.0,
        minimum_close_after_entry=92.0,
    )

    assert result == pytest.approx(-8.0)


def test_analyze_overshoot_cycle_triggered() -> None:
    result = analyze_overshoot_cycle(
        cycle_index=0,
        entry_price=100.0,
        closes_after_entry=[
            99.0,
            96.0,
            93.0,
            95.0,
            97.0,
        ],
        threshold_pct=-6.0,
        window_days=5,
    )

    assert result.triggered is True
    assert result.minimum_close_after_entry == 93.0
    assert result.overshoot_pct == pytest.approx(-7.0)


def test_analyze_overshoot_cycle_uses_window_only() -> None:
    result = analyze_overshoot_cycle(
        cycle_index=0,
        entry_price=100.0,
        closes_after_entry=[
            99.0,
            98.0,
            97.0,
            96.0,
            95.0,
            85.0,
        ],
        threshold_pct=-6.0,
        window_days=5,
    )

    assert result.triggered is False
    assert result.minimum_close_after_entry == 95.0


def test_analyze_overshoot_history() -> None:
    result = analyze_overshoot_history(
        entry_prices=[
            100.0,
            100.0,
            100.0,
        ],
        closes_after_entries=[
            [99.0, 93.0, 95.0],
            [99.0, 98.0, 97.0],
            [96.0, 90.0, 92.0],
        ],
        threshold_pct=-6.0,
        window_days=5,
    )

    assert result.cycles_count == 3
    assert result.triggered_cycles == 2
    assert result.trigger_probability == pytest.approx(
        66.666666,
        rel=1e-5,
    )
    assert result.average_overshoot_pct == pytest.approx(
        -8.5
    )
    assert result.median_overshoot_pct == pytest.approx(
        -8.5
    )
    assert result.maximum_overshoot_pct == pytest.approx(
        -10.0
    )


def test_analyze_overshoot_history_rejects_length_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "entry_prices and closes_after_entries "
            "must have the same length"
        ),
    ):
        analyze_overshoot_history(
            entry_prices=[100.0],
            closes_after_entries=[
                [95.0],
                [90.0],
            ],
        )


def test_rejects_positive_threshold() -> None:
    with pytest.raises(
        ValueError,
        match="threshold_pct must be negative",
    ):
        analyze_overshoot_cycle(
            cycle_index=0,
            entry_price=100.0,
            closes_after_entry=[95.0],
            threshold_pct=6.0,
        )
