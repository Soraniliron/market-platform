from __future__ import annotations

from dataclasses import dataclass

from execution.models import EntryContext


@dataclass(frozen=True)
class InvalidationResult:
    valid: bool
    reason: str


class InvalidationEngine:
    def evaluate(
        self,
        context: EntryContext,
    ) -> InvalidationResult:
        if context.current_price <= 0:
            return InvalidationResult(
                valid=False,
                reason="Invalid current price",
            )

        if context.breakout_level <= 0:
            return InvalidationResult(
                valid=False,
                reason="Invalid breakout level",
            )

        if context.current_price < (
            context.breakout_level * 0.99
        ):
            return InvalidationResult(
                valid=False,
                reason="Breakout failed",
            )

        if (
            context.vwap is not None
            and context.current_price < context.vwap
        ):
            return InvalidationResult(
                valid=False,
                reason="Price below VWAP",
            )

        return InvalidationResult(
            valid=True,
            reason="Entry remains valid",
        )
        