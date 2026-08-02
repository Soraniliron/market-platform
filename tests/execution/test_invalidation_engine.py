from __future__ import annotations

from execution.invalidation_engine import (
    InvalidationEngine,
)
from execution.models import EntryContext


def build_context(**overrides) -> EntryContext:
    values = {
        "current_price": 102.0,
        "breakout_level": 101.0,
        "vwap": 100.5,
        "current_volume": 300000.0,
        "average_volume_same_window": 200000.0,
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


def test_valid_entry() -> None:
    result = InvalidationEngine().evaluate(
        build_context()
    )

    assert result.valid is True


def test_breakout_failed() -> None:
    result = InvalidationEngine().evaluate(
        build_context(
            current_price=99.5,
            breakout_level=101.0,
        )
    )

    assert result.valid is False
    assert result.reason == "Breakout failed"


def test_price_below_vwap() -> None:
    result = InvalidationEngine().evaluate(
        build_context(
            current_price=100.0,
            breakout_level=100.5,
            vwap=101.0,
        )
    )

    assert result.valid is False
    assert result.reason == "Price below VWAP"
    