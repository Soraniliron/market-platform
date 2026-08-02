from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from execution.models import (
    EntryStatus,
    TradePlan,
)


class RiskStatus(str, Enum):
    APPROVED = "approved"
    REDUCED = "reduced"
    REJECTED = "rejected"


@dataclass(frozen=True)
class RiskContext:
    account_equity: float
    available_cash: float

    maximum_risk_percent: float
    maximum_position_percent: float

    daily_realized_pnl: float
    maximum_daily_loss_percent: float

    maximum_liquidity_value: float | None = None
    existing_position_value: float = 0.0


@dataclass(frozen=True)
class PositionSizeResult:
    ticker: str
    status: RiskStatus

    quantity: int
    position_value: float
    total_position_value: float

    risk_per_share: float
    total_risk: float

    maximum_risk_value: float
    maximum_position_value: float
    maximum_allowed_value: float

    reason: str


class RiskEngine:
    def calculate_position_size(
        self,
        trade_plan: TradePlan,
        context: RiskContext,
    ) -> PositionSizeResult:
        self._validate_context(context)

        if trade_plan.status != EntryStatus.BUY_NOW:
            return self._rejected_result(
                trade_plan=trade_plan,
                reason=(
                    "Trade plan is not approved "
                    "for immediate entry"
                ),
            )

        if (
            trade_plan.entry_price is None
            or trade_plan.risk_per_share is None
        ):
            return self._rejected_result(
                trade_plan=trade_plan,
                reason=(
                    "Trade plan is missing entry "
                    "or risk information"
                ),
            )

        if trade_plan.entry_price <= 0:
            return self._rejected_result(
                trade_plan=trade_plan,
                reason="Entry price must be positive",
            )

        if trade_plan.risk_per_share <= 0:
            return self._rejected_result(
                trade_plan=trade_plan,
                reason=(
                    "Risk per share must be positive"
                ),
            )

        maximum_daily_loss_value = (
            context.account_equity
            * context.maximum_daily_loss_percent
            / 100
        )

        if (
            context.daily_realized_pnl
            <= -maximum_daily_loss_value
        ):
            return self._rejected_result(
                trade_plan=trade_plan,
                reason=(
                    "Daily loss limit reached"
                ),
            )

        maximum_risk_value = (
            context.account_equity
            * context.maximum_risk_percent
            / 100
        )

        maximum_position_value = (
            context.account_equity
            * context.maximum_position_percent
            / 100
        )

        maximum_allowed_value = min(
            maximum_position_value,
            context.available_cash,
        )

        if (
            context.maximum_liquidity_value
            is not None
        ):
            maximum_allowed_value = min(
                maximum_allowed_value,
                context.maximum_liquidity_value,
            )

        remaining_position_capacity = (
            maximum_allowed_value
            - context.existing_position_value
        )

        if remaining_position_capacity <= 0:
            return self._rejected_result(
                trade_plan=trade_plan,
                reason=(
                    "No remaining position capacity"
                ),
            )

        quantity_by_risk = int(
            maximum_risk_value
            / trade_plan.risk_per_share
        )

        quantity_by_value = int(
            remaining_position_capacity
            / trade_plan.entry_price
        )

        quantity = min(
            quantity_by_risk,
            quantity_by_value,
        )

        if quantity < 1:
            return self._rejected_result(
                trade_plan=trade_plan,
                reason=(
                    "Calculated position size "
                    "is below one share"
                ),
            )

        position_value = round(
            quantity
            * trade_plan.entry_price,
            2,
        )

        total_position_value = round(
            context.existing_position_value
            + position_value,
            2,
        )

        total_risk = round(
            quantity
            * trade_plan.risk_per_share,
            2,
        )

        status = RiskStatus.APPROVED

        limiting_reasons: list[str] = []

        if quantity == quantity_by_risk:
            limiting_reasons.append(
                "position limited by risk"
            )

        if quantity == quantity_by_value:
            limiting_reasons.append(
                "position limited by exposure"
            )

        if (
            context.maximum_liquidity_value
            is not None
            and maximum_allowed_value
            == context.maximum_liquidity_value
        ):
            status = RiskStatus.REDUCED
            limiting_reasons.append(
                "position limited by liquidity"
            )

        reason = (
            "; ".join(limiting_reasons)
            if limiting_reasons
            else "Position size approved"
        )

        return PositionSizeResult(
            ticker=trade_plan.ticker,
            status=status,
            quantity=quantity,
            position_value=position_value,
            total_position_value=(
                total_position_value
            ),
            risk_per_share=(
                trade_plan.risk_per_share
            ),
            total_risk=total_risk,
            maximum_risk_value=round(
                maximum_risk_value,
                2,
            ),
            maximum_position_value=round(
                maximum_position_value,
                2,
            ),
            maximum_allowed_value=round(
                maximum_allowed_value,
                2,
            ),
            reason=reason,
        )

    @staticmethod
    def _validate_context(
        context: RiskContext,
    ) -> None:
        positive_fields = {
            "account_equity": (
                context.account_equity
            ),
            "available_cash": (
                context.available_cash
            ),
        }

        for field_name, value in (
            positive_fields.items()
        ):
            if value <= 0:
                raise ValueError(
                    f"{field_name} must be "
                    "greater than zero"
                )

        percentage_fields = {
            "maximum_risk_percent": (
                context.maximum_risk_percent
            ),
            "maximum_position_percent": (
                context.maximum_position_percent
            ),
            "maximum_daily_loss_percent": (
                context.maximum_daily_loss_percent
            ),
        }

        for field_name, value in (
            percentage_fields.items()
        ):
            if not 0 < value <= 100:
                raise ValueError(
                    f"{field_name} must be "
                    "greater than zero and "
                    "no more than 100"
                )

        if (
            context.maximum_liquidity_value
            is not None
            and context.maximum_liquidity_value
            <= 0
        ):
            raise ValueError(
                "maximum_liquidity_value must "
                "be greater than zero"
            )

        if context.existing_position_value < 0:
            raise ValueError(
                "existing_position_value must "
                "be zero or greater"
            )

    @staticmethod
    def _rejected_result(
        trade_plan: TradePlan,
        reason: str,
    ) -> PositionSizeResult:
        return PositionSizeResult(
            ticker=trade_plan.ticker,
            status=RiskStatus.REJECTED,
            quantity=0,
            position_value=0.0,
            total_position_value=0.0,
            risk_per_share=(
                trade_plan.risk_per_share
                or 0.0
            ),
            total_risk=0.0,
            maximum_risk_value=0.0,
            maximum_position_value=0.0,
            maximum_allowed_value=0.0,
            reason=reason,
        )
        