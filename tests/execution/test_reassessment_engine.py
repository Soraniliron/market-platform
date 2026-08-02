from __future__ import annotations

from execution.models import EntryContext
from execution.reassessment_engine import (
    ReassessmentEngine,
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


def test_original_entry_remains_valid() -> None:
    result = ReassessmentEngine().evaluate(
        build_context()
    )

    assert result.should_reassess is False
    assert (
        result.reason
        == "Original entry remains valid"
    )


def test_reassesses_expired_entry_window() -> None:
    result = ReassessmentEngine().evaluate(
        build_context(
            minutes_from_market_open=61,
        )
    )

    assert result.should_reassess is True
    assert result.reason == "Entry window expired"


def test_reassesses_price_too_far_above_breakout() -> None:
    result = ReassessmentEngine().evaluate(
        build_context(
            current_price=102.6,
            breakout_level=101.0,
        )
    )

    assert result.should_reassess is True
    assert (
        result.reason
        == "Price moved too far above breakout"
    )


def test_reassesses_lost_vwap_support() -> None:
    result = ReassessmentEngine().evaluate(
        build_context(
            current_price=100.5,
            vwap=101.0,
        )
    )

    assert result.should_reassess is True
    assert result.reason == "Price lost VWAP support"


def test_reassesses_weakened_index_alignment() -> None:
    result = ReassessmentEngine().evaluate(
        build_context(
            qqq_aligned=False,
        )
    )

    assert result.should_reassess is True
    assert result.reason == "Index alignment weakened"


def test_reassesses_invalid_market_time() -> None:
    result = ReassessmentEngine().evaluate(
        build_context(
            minutes_from_market_open=-1,
        )
    )

    assert result.should_reassess is True
    assert result.reason == "Invalid market time"
    