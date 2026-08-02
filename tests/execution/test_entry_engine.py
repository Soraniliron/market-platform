from __future__ import annotations

import pytest

from execution.entry_engine import EntryEngine
from execution.models import (
    EntryContext,
    EntryStatus,
)


def build_valid_context(
    **overrides,
) -> EntryContext:
    values = {
        "current_price": 102.0,
        "breakout_level": 101.5,
        "vwap": 101.0,
        "current_volume": 300_000.0,
        "average_volume_same_window": 200_000.0,
        "atr": 1.0,
        "recent_swing_low": 100.5,
        "spy_aligned": True,
        "qqq_aligned": True,
        "chart_quality_score": 80.0,
        "decision_score": 85.0,
        "minutes_from_market_open": 30,
        "maximum_entry_delay_minutes": 60,
    }

    values.update(overrides)

    return EntryContext(**values)


def test_build_trade_plan_returns_buy_now() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="META",
        context=build_valid_context(),
    )

    assert plan.ticker == "META"
    assert plan.status == EntryStatus.BUY_NOW

    assert plan.entry_price == 102.0
    assert plan.stop_price == 100.5

    assert plan.risk_per_share == 1.5
    assert plan.tp1_price == 104.25
    assert plan.tp2_price == 105.0

    assert plan.reward_tp1 == 2.25
    assert plan.reward_tp2 == 3.0

    assert plan.risk_reward_tp1 == 1.5
    assert plan.risk_reward_tp2 == 2.0

    assert plan.invalidation_price == 100.5
    assert plan.decision_score == 85.0


def test_rejects_expired_entry_window() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="AAPL",
        context=build_valid_context(
            minutes_from_market_open=61,
        ),
    )

    assert plan.status == EntryStatus.REJECT
    assert plan.entry_price is None
    assert plan.reason == "Entry window expired"


def test_waits_for_minimum_decision_score() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="MSFT",
        context=build_valid_context(
            decision_score=79.0,
        ),
    )

    assert plan.status == EntryStatus.WAIT
    assert plan.entry_price is None
    assert (
        plan.reason
        == "Decision score below minimum threshold"
    )


def test_watches_low_chart_quality() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="NVDA",
        context=build_valid_context(
            chart_quality_score=60.0,
        ),
    )

    assert plan.status == EntryStatus.WATCH
    assert plan.entry_price is None
    assert (
        plan.reason
        == "Chart quality below minimum threshold"
    )


def test_watches_when_indexes_are_not_aligned() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="PLTR",
        context=build_valid_context(
            qqq_aligned=False,
        ),
    )

    assert plan.status == EntryStatus.WATCH
    assert plan.entry_price is None
    assert (
        plan.reason
        == "SPY and QQQ are not both aligned"
    )


def test_watches_when_rvol_is_too_low() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="JPM",
        context=build_valid_context(
            current_volume=210_000.0,
            average_volume_same_window=200_000.0,
        ),
    )

    assert plan.status == EntryStatus.WATCH
    assert plan.entry_price is None
    assert "RVOL 1.05" in plan.reason


def test_waits_until_breakout_is_reached() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="AVGO",
        context=build_valid_context(
            current_price=101.0,
            breakout_level=101.5,
        ),
    )

    assert plan.status == EntryStatus.WAIT
    assert plan.entry_price is None
    assert plan.reason == "Breakout level not reached"


def test_waits_when_price_is_below_vwap() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="AMD",
        context=build_valid_context(
            current_price=102.0,
            breakout_level=101.5,
            vwap=102.5,
        ),
    )

    assert plan.status == EntryStatus.WAIT
    assert plan.entry_price is None
    assert plan.reason == "Price is below VWAP"


def test_rejects_invalid_stop_price() -> None:
    engine = EntryEngine()

    plan = engine.build_trade_plan(
        ticker="META",
        context=build_valid_context(
            current_price=1.0,
            breakout_level=1.0,
            vwap=0.9,
            atr=2.0,
            recent_swing_low=0.5,
        ),
    )

    assert plan.status == EntryStatus.REJECT
    assert plan.entry_price is None
    assert plan.reason == "Invalid stop price"


@pytest.mark.parametrize(
    (
        "field_name",
        "invalid_value",
    ),
    [
        ("current_price", 0.0),
        ("breakout_level", 0.0),
        ("current_volume", 0.0),
        ("average_volume_same_window", 0.0),
        ("atr", 0.0),
        ("recent_swing_low", 0.0),
    ],
)
def test_rejects_non_positive_required_values(
    field_name: str,
    invalid_value: float,
) -> None:
    engine = EntryEngine()

    with pytest.raises(
        ValueError,
        match=(
            f"{field_name} must be "
            "greater than zero"
        ),
    ):
        engine.build_trade_plan(
            ticker="META",
            context=build_valid_context(
                **{
                    field_name: invalid_value,
                }
            ),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "invalid_value",
        "error_message",
    ),
    [
        (
            "decision_score",
            101.0,
            (
                "decision_score must be "
                "between 0 and 100"
            ),
        ),
        (
            "chart_quality_score",
            -1.0,
            (
                "chart_quality_score must be "
                "between 0 and 100"
            ),
        ),
        (
            "minutes_from_market_open",
            -1,
            (
                "minutes_from_market_open must be "
                "zero or greater"
            ),
        ),
        (
            "maximum_entry_delay_minutes",
            0,
            (
                "maximum_entry_delay_minutes must "
                "be at least one"
            ),
        ),
    ],
)
def test_rejects_invalid_context_ranges(
    field_name: str,
    invalid_value: float,
    error_message: str,
) -> None:
    engine = EntryEngine()

    with pytest.raises(
        ValueError,
        match=error_message,
    ):
        engine.build_trade_plan(
            ticker="META",
            context=build_valid_context(
                **{
                    field_name: invalid_value,
                }
            ),
        )
        