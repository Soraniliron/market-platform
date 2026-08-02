from __future__ import annotations

import pytest

from execution.models import (
    EntryStatus,
    TradePlan,
)
from execution.risk_engine import (
    PositionSizeResult,
    RiskContext,
    RiskEngine,
    RiskStatus,
)


def build_trade_plan(
    **overrides,
) -> TradePlan:
    values = {
        "ticker": "META",
        "status": EntryStatus.BUY_NOW,
        "entry_price": 100.0,
        "stop_price": 98.0,
        "tp1_price": 103.0,
        "tp2_price": 104.0,
        "risk_per_share": 2.0,
        "reward_tp1": 3.0,
        "reward_tp2": 4.0,
        "risk_reward_tp1": 1.5,
        "risk_reward_tp2": 2.0,
        "invalidation_price": 98.0,
        "decision_score": 85.0,
        "reason": "Valid trade plan",
    }

    values.update(overrides)

    return TradePlan(**values)


def build_risk_context(
    **overrides,
) -> RiskContext:
    values = {
        "account_equity": 100_000.0,
        "available_cash": 50_000.0,
        "maximum_risk_percent": 1.0,
        "maximum_position_percent": 20.0,
        "daily_realized_pnl": 0.0,
        "maximum_daily_loss_percent": 3.0,
        "maximum_liquidity_value": None,
        "existing_position_value": 0.0,
    }

    values.update(overrides)

    return RiskContext(**values)


def test_calculates_position_size_by_risk() -> None:
    engine = RiskEngine()

    result = engine.calculate_position_size(
        trade_plan=build_trade_plan(),
        context=build_risk_context(),
    )

    assert isinstance(
        result,
        PositionSizeResult,
    )

    assert result.status == RiskStatus.APPROVED
    assert result.quantity == 200
    assert result.position_value == 20_000.0
    assert result.total_position_value == 20_000.0
    assert result.total_risk == 400.0
    assert result.maximum_risk_value == 1_000.0
    assert result.maximum_position_value == 20_000.0
    assert result.maximum_allowed_value == 20_000.0
    assert "exposure" in result.reason


def test_reduces_position_by_liquidity() -> None:
    engine = RiskEngine()

    result = engine.calculate_position_size(
        trade_plan=build_trade_plan(),
        context=build_risk_context(
            maximum_liquidity_value=5_000.0,
        ),
    )

    assert result.status == RiskStatus.REDUCED
    assert result.quantity == 50
    assert result.position_value == 5_000.0
    assert result.total_position_value == 5_000.0
    assert result.total_risk == 100.0
    assert (
        result.maximum_allowed_value
        == 5_000.0
    )
    assert "liquidity" in result.reason


def test_rejects_non_buy_trade_plan() -> None:
    engine = RiskEngine()

    result = engine.calculate_position_size(
        trade_plan=build_trade_plan(
            status=EntryStatus.WATCH,
        ),
        context=build_risk_context(),
    )

    assert result.status == RiskStatus.REJECTED
    assert result.quantity == 0
    assert (
        result.reason
        == (
            "Trade plan is not approved "
            "for immediate entry"
        )
    )


def test_rejects_when_daily_loss_limit_reached() -> None:
    engine = RiskEngine()

    result = engine.calculate_position_size(
        trade_plan=build_trade_plan(),
        context=build_risk_context(
            daily_realized_pnl=-3_000.0,
        ),
    )

    assert result.status == RiskStatus.REJECTED
    assert result.quantity == 0
    assert result.reason == (
        "Daily loss limit reached"
    )


def test_rejects_when_no_position_capacity() -> None:
    engine = RiskEngine()

    result = engine.calculate_position_size(
        trade_plan=build_trade_plan(),
        context=build_risk_context(
            existing_position_value=20_000.0,
        ),
    )

    assert result.status == RiskStatus.REJECTED
    assert result.quantity == 0
    assert result.reason == (
        "No remaining position capacity"
    )


def test_rejects_missing_entry_information() -> None:
    engine = RiskEngine()

    result = engine.calculate_position_size(
        trade_plan=build_trade_plan(
            entry_price=None,
        ),
        context=build_risk_context(),
    )

    assert result.status == RiskStatus.REJECTED
    assert result.quantity == 0
    assert (
        result.reason
        == (
            "Trade plan is missing entry "
            "or risk information"
        )
    )


def test_rejects_invalid_risk_per_share() -> None:
    engine = RiskEngine()

    result = engine.calculate_position_size(
        trade_plan=build_trade_plan(
            risk_per_share=0.0,
        ),
        context=build_risk_context(),
    )

    assert result.status == RiskStatus.REJECTED
    assert result.quantity == 0
    assert result.reason == (
        "Risk per share must be positive"
    )


@pytest.mark.parametrize(
    (
        "field_name",
        "invalid_value",
    ),
    [
        ("account_equity", 0.0),
        ("available_cash", 0.0),
    ],
)
def test_rejects_non_positive_account_values(
    field_name: str,
    invalid_value: float,
) -> None:
    engine = RiskEngine()

    with pytest.raises(
        ValueError,
        match=(
            f"{field_name} must be "
            "greater than zero"
        ),
    ):
        engine.calculate_position_size(
            trade_plan=build_trade_plan(),
            context=build_risk_context(
                **{
                    field_name: invalid_value,
                }
            ),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "invalid_value",
    ),
    [
        ("maximum_risk_percent", 0.0),
        ("maximum_position_percent", 0.0),
        ("maximum_daily_loss_percent", 0.0),
        ("maximum_risk_percent", 101.0),
        ("maximum_position_percent", 101.0),
        ("maximum_daily_loss_percent", 101.0),
    ],
)
def test_rejects_invalid_percentages(
    field_name: str,
    invalid_value: float,
) -> None:
    engine = RiskEngine()

    with pytest.raises(
        ValueError,
        match=(
            f"{field_name} must be "
            "greater than zero and "
            "no more than 100"
        ),
    ):
        engine.calculate_position_size(
            trade_plan=build_trade_plan(),
            context=build_risk_context(
                **{
                    field_name: invalid_value,
                }
            ),
        )


def test_rejects_invalid_liquidity_value() -> None:
    engine = RiskEngine()

    with pytest.raises(
        ValueError,
        match=(
            "maximum_liquidity_value must "
            "be greater than zero"
        ),
    ):
        engine.calculate_position_size(
            trade_plan=build_trade_plan(),
            context=build_risk_context(
                maximum_liquidity_value=0.0,
            ),
        )


def test_rejects_negative_existing_position() -> None:
    engine = RiskEngine()

    with pytest.raises(
        ValueError,
        match=(
            "existing_position_value must "
            "be zero or greater"
        ),
    ):
        engine.calculate_position_size(
            trade_plan=build_trade_plan(),
            context=build_risk_context(
                existing_position_value=-1.0,
            ),
        )
        