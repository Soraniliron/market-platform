from __future__ import annotations

from engines.base_engine import (
    BaseEngine,
    EngineResult,
)
from scanner.context import MarketContext
from scanner.models import MarketSnapshot


class VWAPEngine(BaseEngine):
    name = "vwap"

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        context: MarketContext | None = None,
    ) -> EngineResult:
        if snapshot.vwap is None:
            return EngineResult(
                engine=self.name,
                score=50.0,
                passed=False,
                reason="VWAP unavailable",
            )

        if snapshot.vwap <= 0:
            raise ValueError(
                "vwap must be greater than zero"
            )

        distance_percent = (
            (snapshot.price - snapshot.vwap)
            / snapshot.vwap
        ) * 100

        score = 50.0
        passed = False
        reasons: list[str] = []

        if distance_percent >= 1.0:
            score += 30.0
            passed = True
            reasons.append(
                f"Price strongly above VWAP "
                f"({distance_percent:.2f}%)"
            )
        elif distance_percent >= 0.25:
            score += 20.0
            passed = True
            reasons.append(
                f"Price above VWAP "
                f"({distance_percent:.2f}%)"
            )
        elif distance_percent >= 0.0:
            score += 10.0
            passed = True
            reasons.append(
                "Price holding above VWAP"
            )
        elif distance_percent <= -1.0:
            score -= 30.0
            reasons.append(
                f"Price strongly below VWAP "
                f"({distance_percent:.2f}%)"
            )
        elif distance_percent <= -0.25:
            score -= 20.0
            reasons.append(
                f"Price below VWAP "
                f"({distance_percent:.2f}%)"
            )
        else:
            score -= 10.0
            reasons.append(
                "Price slightly below VWAP"
            )

        if (
            snapshot.low <= snapshot.vwap
            <= snapshot.high
        ):
            if snapshot.price >= snapshot.vwap:
                score += 10.0
                passed = True
                reasons.append(
                    "VWAP retest held"
                )
            else:
                score -= 10.0
                reasons.append(
                    "VWAP retest rejected"
                )

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
        