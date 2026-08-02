from __future__ import annotations

from dataclasses import dataclass

from execution.models import EntryContext


@dataclass(frozen=True)
class ReassessmentResult:
    should_reassess: bool
    reason: str


class ReassessmentEngine:
    def evaluate(
        self,
        context: EntryContext,
    ) -> ReassessmentResult:
        if context.minutes_from_market_open < 0:
            return ReassessmentResult(
                should_reassess=True,
                reason="Invalid market time",
            )

        if (
            context.minutes_from_market_open
            > context.maximum_entry_delay_minutes
        ):
            return ReassessmentResult(
                should_reassess=True,
                reason="Entry window expired",
            )

        if (
            context.current_price
            > context.breakout_level * 1.015
        ):
            return ReassessmentResult(
                should_reassess=True,
                reason="Price moved too far above breakout",
            )

        if (
            context.vwap is not None
            and context.current_price < context.vwap
        ):
            return ReassessmentResult(
                should_reassess=True,
                reason="Price lost VWAP support",
            )

        if (
            not context.spy_aligned
            or not context.qqq_aligned
        ):
            return ReassessmentResult(
                should_reassess=True,
                reason="Index alignment weakened",
            )

        return ReassessmentResult(
            should_reassess=False,
            reason="Original entry remains valid",
        )
        