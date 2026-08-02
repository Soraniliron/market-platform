from __future__ import annotations

from engines.base_engine import (
    BaseEngine,
    EngineResult,
)
from scanner.context import MarketContext
from scanner.models import MarketSnapshot


class GapEngine(BaseEngine):
    name = "gap"

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        context: MarketContext | None = None,
    ) -> EngineResult:
        if snapshot.previous_close <= 0:
            raise ValueError(
                "previous_close must be greater than zero"
            )

        gap_percent = (
            (
                snapshot.open_price
                - snapshot.previous_close
            )
            / snapshot.previous_close
        ) * 100

        if gap_percent >= 2.0:
            score = 90.0
            passed = True
            reason = (
                f"Strong gap up of {gap_percent:.2f}%"
            )
        elif gap_percent >= 1.0:
            score = 75.0
            passed = True
            reason = (
                f"Positive gap up of {gap_percent:.2f}%"
            )
        elif gap_percent >= 0.25:
            score = 60.0
            passed = True
            reason = (
                f"Small positive gap of {gap_percent:.2f}%"
            )
        elif gap_percent <= -2.0:
            score = 10.0
            passed = False
            reason = (
                f"Strong gap down of {gap_percent:.2f}%"
            )
        elif gap_percent <= -1.0:
            score = 25.0
            passed = False
            reason = (
                f"Negative gap down of {gap_percent:.2f}%"
            )
        elif gap_percent <= -0.25:
            score = 40.0
            passed = False
            reason = (
                f"Small negative gap of {gap_percent:.2f}%"
            )
        else:
            score = 50.0
            passed = False
            reason = "No meaningful gap"

        return EngineResult(
            engine=self.name,
            score=score,
            passed=passed,
            reason=reason,
        )
        