from __future__ import annotations

from execution.invalidation_engine import (
    InvalidationEngine,
)
from execution.models import (
    EntryContext,
    EntryStatus,
    TradePlan,
)
from execution.overshoot_engine import (
    OvershootEngine,
)
from execution.reassessment_engine import (
    ReassessmentEngine,
)


class EntryEngine:
    def __init__(
        self,
        minimum_decision_score: float = 80.0,
        minimum_chart_quality_score: float = 65.0,
        minimum_rvol: float = 1.2,
        minimum_risk_reward_tp1: float = 1.5,
        minimum_risk_reward_tp2: float = 2.0,
        invalidation_engine: InvalidationEngine | None = None,
        reassessment_engine: ReassessmentEngine | None = None,
        overshoot_engine: OvershootEngine | None = None,
    ) -> None:
        self.minimum_decision_score = (
            minimum_decision_score
        )
        self.minimum_chart_quality_score = (
            minimum_chart_quality_score
        )
        self.minimum_rvol = minimum_rvol
        self.minimum_risk_reward_tp1 = (
            minimum_risk_reward_tp1
        )
        self.minimum_risk_reward_tp2 = (
            minimum_risk_reward_tp2
        )

        self.invalidation_engine = (
            invalidation_engine
            or InvalidationEngine()
        )

        self.reassessment_engine = (
            reassessment_engine
            or ReassessmentEngine()
        )

        self.overshoot_engine = (
            overshoot_engine
            or OvershootEngine()
        )

    def build_trade_plan(
        self,
        ticker: str,
        context: EntryContext,
    ) -> TradePlan:
        self._validate_context(context)

        if (
            context.minutes_from_market_open
            > context.maximum_entry_delay_minutes
        ):
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.REJECT,
                reason="Entry window expired",
            )

        if (
            context.decision_score
            < self.minimum_decision_score
        ):
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.WAIT,
                reason=(
                    "Decision score below "
                    "minimum threshold"
                ),
            )

        if (
            context.chart_quality_score
            < self.minimum_chart_quality_score
        ):
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.WATCH,
                reason=(
                    "Chart quality below "
                    "minimum threshold"
                ),
            )

        if (
            not context.spy_aligned
            or not context.qqq_aligned
        ):
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.WATCH,
                reason=(
                    "SPY and QQQ are not both aligned"
                ),
            )

        relative_volume = (
            context.current_volume
            / context.average_volume_same_window
        )

        if relative_volume < self.minimum_rvol:
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.WATCH,
                reason=(
                    f"RVOL {relative_volume:.2f} "
                    "below minimum threshold"
                ),
            )

        if (
            context.current_price
            < context.breakout_level
        ):
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.WAIT,
                reason="Breakout level not reached",
            )

        if (
            context.vwap is not None
            and context.current_price
            < context.vwap
        ):
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.WAIT,
                reason="Price is below VWAP",
            )

        invalidation_result = (
            self.invalidation_engine.evaluate(
                context
            )
        )

        if not invalidation_result.valid:
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.REJECT,
                reason=(
                    f"Invalidation: "
                    f"{invalidation_result.reason}"
                ),
            )

        overshoot_result = (
            self.overshoot_engine.evaluate(
                context
            )
        )

        if overshoot_result.overshoot:
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.WATCH,
                reason=(
                    f"Overshoot: "
                    f"{overshoot_result.reason} "
                    f"({overshoot_result.distance_percent:.2f}%)"
                ),
            )

        reassessment_result = (
            self.reassessment_engine.evaluate(
                context
            )
        )

        if (
            reassessment_result.should_reassess
        ):
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.WATCH,
                reason=(
                    f"Reassessment required: "
                    f"{reassessment_result.reason}"
                ),
            )

        entry_price = round(
            max(
                context.current_price,
                context.breakout_level,
            ),
            2,
        )

        atr_stop = (
            entry_price
            - context.atr
        )

        stop_price = round(
            min(
                atr_stop,
                context.recent_swing_low,
            ),
            2,
        )

        if stop_price <= 0:
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.REJECT,
                reason="Invalid stop price",
            )

        if stop_price >= entry_price:
            return self._empty_plan(
                ticker=ticker,
                context=context,
                status=EntryStatus.REJECT,
                reason=(
                    "Stop price must be "
                    "below entry price"
                ),
            )

        risk_per_share = round(
            entry_price - stop_price,
            4,
        )

        tp1_price = round(
            entry_price
            + (
                risk_per_share
                * self.minimum_risk_reward_tp1
            ),
            2,
        )

        tp2_price = round(
            entry_price
            + (
                risk_per_share
                * self.minimum_risk_reward_tp2
            ),
            2,
        )

        reward_tp1 = round(
            tp1_price - entry_price,
            4,
        )

        reward_tp2 = round(
            tp2_price - entry_price,
            4,
        )

        risk_reward_tp1 = round(
            reward_tp1 / risk_per_share,
            4,
        )

        risk_reward_tp2 = round(
            reward_tp2 / risk_per_share,
            4,
        )

        return TradePlan(
            ticker=ticker.upper(),
            status=EntryStatus.BUY_NOW,
            entry_price=entry_price,
            stop_price=stop_price,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            risk_per_share=risk_per_share,
            reward_tp1=reward_tp1,
            reward_tp2=reward_tp2,
            risk_reward_tp1=risk_reward_tp1,
            risk_reward_tp2=risk_reward_tp2,
            invalidation_price=stop_price,
            decision_score=(
                context.decision_score
            ),
            reason=(
                "Entry conditions confirmed: "
                f"breakout, RVOL {relative_volume:.2f}, "
                "VWAP and index alignment; "
                "no invalidation, reassessment, "
                "or overshoot detected"
            ),
        )

    @staticmethod
    def _validate_context(
        context: EntryContext,
    ) -> None:
        positive_fields = {
            "current_price": (
                context.current_price
            ),
            "breakout_level": (
                context.breakout_level
            ),
            "current_volume": (
                context.current_volume
            ),
            "average_volume_same_window": (
                context.average_volume_same_window
            ),
            "atr": context.atr,
            "recent_swing_low": (
                context.recent_swing_low
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

        if not (
            0.0
            <= context.chart_quality_score
            <= 100.0
        ):
            raise ValueError(
                "chart_quality_score must be "
                "between 0 and 100"
            )

        if not (
            0.0
            <= context.decision_score
            <= 100.0
        ):
            raise ValueError(
                "decision_score must be "
                "between 0 and 100"
            )

        if (
            context.minutes_from_market_open
            < 0
        ):
            raise ValueError(
                "minutes_from_market_open must be "
                "zero or greater"
            )

        if (
            context.maximum_entry_delay_minutes
            < 1
        ):
            raise ValueError(
                "maximum_entry_delay_minutes must "
                "be at least one"
            )

    @staticmethod
    def _empty_plan(
        ticker: str,
        context: EntryContext,
        status: EntryStatus,
        reason: str,
    ) -> TradePlan:
        return TradePlan(
            ticker=ticker.upper(),
            status=status,
            entry_price=None,
            stop_price=None,
            tp1_price=None,
            tp2_price=None,
            risk_per_share=None,
            reward_tp1=None,
            reward_tp2=None,
            risk_reward_tp1=None,
            risk_reward_tp2=None,
            invalidation_price=None,
            decision_score=(
                context.decision_score
            ),
            reason=reason,
        )
        