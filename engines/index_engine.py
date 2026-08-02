from __future__ import annotations

from engines.base_engine import (
    BaseEngine,
    EngineResult,
)
from scanner.context import MarketContext
from scanner.models import MarketSnapshot


class IndexEngine(BaseEngine):
    name = "index"

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        context: MarketContext | None = None,
    ) -> EngineResult:
        if (
            context is None
            or context.index is None
        ):
            return EngineResult(
                engine=self.name,
                score=50.0,
                passed=False,
                reason="Index context unavailable",
            )

        index = context.index

        score = 50.0
        passed = False
        reasons: list[str] = []

        if index.market_trend >= 2:
            score += 25
            passed = True
            reasons.append("Strong market trend")
        elif index.market_trend == 1:
            score += 10
            reasons.append("Positive market trend")
        elif index.market_trend == -1:
            score -= 10
            reasons.append("Weak market trend")
        elif index.market_trend <= -2:
            score -= 25
            reasons.append("Strong market weakness")

        if index.spy_above_vwap:
            score += 10
            reasons.append("SPY above VWAP")
        else:
            score -= 10
            reasons.append("SPY below VWAP")

        if index.qqq_above_vwap:
            score += 10
            reasons.append("QQQ above VWAP")
        else:
            score -= 10
            reasons.append("QQQ below VWAP")

        score = max(
            0.0,
            min(score, 100.0),
        )

        return EngineResult(
            engine=self.name,
            score=score,
            passed=passed,
            reason="; ".join(reasons),
        )
        