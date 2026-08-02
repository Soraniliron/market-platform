from __future__ import annotations

import pytest

from execution.models import EntryContext
from execution.overshoot_engine import (
    OvershootEngine,
)


def build_context(
    **overrides,
) -> EntryContext:
    values = {
        "current_price": 101.5,
        "breakout_level": 101.0,
        "vwap": 100.8,
        "current_volume": 300_000.0,
        "average_volume_same_window": 200_000.0,
        "atr": 1.0,
        "recent_swing_low": 99.5,
        "spy_aligned": True,
        "qqq_aligned": True,
        "chart_quality_score": 80.0,
        "decision_score": 85.0,
        "minutes_from_market_open": 20,
        "maximum_entry_delay_minutes": 60,
    }

    values.update(overrides)

    return EntryContext(**values)


def test_price_within_allowed_distance() -> None:
    engine = OvershootEngine(
        maximum_distance_percent=1.5,
    )

    result = engine.evaluate(
        build_context(
            current_price=101.5,
            breakout_level=101.0,
        )
    )

    assert result.overshoot is False
    assert result.distance_percent == 0.495
    assert (
        result.reason
        == (
            "Price remains within the "
            "allowed entry distance"
        )
    )


def test_detects_overshoot() -> None:
    engine = OvershootEngine(
        maximum_distance_percent=1.5,
    )

    result = engine.evaluate(
        build_context(
            current_price=103.0,
            breakout_level=101.0,
        )
    )

    assert result.overshoot is True
    assert result.distance_percent == 1.9802
    assert (
        result.reason
        == (
            "Price moved too far above "
            "the breakout level"
        )
    )


def test_exact_threshold_is_not_overshoot() -> None:
    engine = OvershootEngine(
        maximum_distance_percent=1.5,
    )

    result = engine.evaluate(
        build_context(
            current_price=101.5,
            breakout_level=100.0,
        )
    )

    assert result.overshoot is False
    assert result.distance_percent == 1.5


def test_negative_distance_is_not_overshoot() -> None:
    engine = OvershootEngine()

    result = engine.evaluate(
        build_context(
            current_price=99.0,
            breakout_level=100.0,
        )
    )

    assert result.overshoot is False
    assert result.distance_percent == -1.0


def test_rejects_invalid_breakout_level() -> None:
    engine = OvershootEngine()

    with pytest.raises(
        ValueError,
        match=(
            "breakout_level must be "
            "greater than zero"
        ),
    ):
        engine.evaluate(
            build_context(
                breakout_level=0.0,
            )
        )


def test_rejects_invalid_threshold() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "maximum_distance_percent must be "
            "greater than zero"
        ),
    ):
        OvershootEngine(
            maximum_distance_percent=0.0,
        )
        