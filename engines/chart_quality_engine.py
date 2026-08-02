from __future__ import annotations

from engines.base_engine import (
    BaseEngine,
    EngineResult,
)
from scanner.context import MarketContext
from scanner.models import MarketSnapshot


class ChartQualityEngine(BaseEngine):
    name = "chart_quality"

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        context: MarketContext | None = None,
    ) -> EngineResult:
        if snapshot.high <= 0:
            raise ValueError(
                "high must be greater than zero"
            )

        if snapshot.low <= 0:
            raise ValueError(
                "low must be greater than zero"
            )

        if snapshot.low > snapshot.high:
            raise ValueError(
                "low must not exceed high"
            )

        candle_range = (
            snapshot.high - snapshot.low
        )

        if candle_range == 0:
            return EngineResult(
                engine=self.name,
                score=50.0,
                passed=False,
                reason="No candle range",
            )

        close_location = (
            snapshot.price - snapshot.low
        ) / candle_range

        open_location = (
            snapshot.open_price - snapshot.low
        ) / candle_range

        body_size = abs(
            snapshot.price
            - snapshot.open_price
        )

        body_ratio = (
            body_size / candle_range
        )

        score = 50.0
        passed = False
        reasons: list[str] = []

        if close_location >= 0.80:
            score += 25.0
            passed = True
            reasons.append(
                "Close near candle high"
            )
        elif close_location >= 0.60:
            score += 15.0
            passed = True
            reasons.append(
                "Close in upper candle range"
            )
        elif close_location <= 0.20:
            score -= 25.0
            reasons.append(
                "Close near candle low"
            )
        elif close_location <= 0.40:
            score -= 15.0
            reasons.append(
                "Close in lower candle range"
            )
        else:
            reasons.append(
                "Close in middle candle range"
            )

        if snapshot.price > snapshot.open_price:
            if body_ratio >= 0.60:
                score += 20.0
                passed = True
                reasons.append(
                    "Strong bullish candle body"
                )
            elif body_ratio >= 0.35:
                score += 10.0
                reasons.append(
                    "Positive candle body"
                )
            else:
                reasons.append(
                    "Small bullish candle body"
                )
        elif snapshot.price < snapshot.open_price:
            if body_ratio >= 0.60:
                score -= 20.0
                reasons.append(
                    "Strong bearish candle body"
                )
            elif body_ratio >= 0.35:
                score -= 10.0
                reasons.append(
                    "Negative candle body"
                )
            else:
                reasons.append(
                    "Small bearish candle body"
                )
        else:
            reasons.append(
                "Doji candle"
            )

        if (
            snapshot.price > snapshot.open_price
            and open_location <= 0.35
            and close_location >= 0.75
        ):
            score += 10.0
            passed = True
            reasons.append(
                "Clean bullish expansion"
            )

        if (
            snapshot.price < snapshot.open_price
            and open_location >= 0.65
            and close_location <= 0.25
        ):
            score -= 10.0
            reasons.append(
                "Clean bearish expansion"
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
        