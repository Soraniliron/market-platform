from __future__ import annotations

from engines.base_engine import (
    BaseEngine,
    EngineResult,
)
from scanner.context import MarketContext
from scanner.models import MarketSnapshot


class VolumeEngine(BaseEngine):
    name = "volume"

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        context: MarketContext | None = None,
    ) -> EngineResult:
        if (
            context is None
            or context.volume is None
        ):
            return EngineResult(
                engine=self.name,
                score=50.0,
                passed=False,
                reason="Volume context unavailable",
            )

        volume = context.volume

        if volume.average_volume_same_window <= 0:
            raise ValueError(
                "average_volume_same_window must be greater than zero"
            )

        rvol = (
            volume.current_volume
            / volume.average_volume_same_window
        )

        score = 50.0
        passed = False
        reasons: list[str] = []

        if rvol >= 2.0:
            score += 35.0
            passed = True
            reasons.append(
                f"Very high RVOL ({rvol:.2f})"
            )
        elif rvol >= 1.5:
            score += 25.0
            passed = True
            reasons.append(
                f"High RVOL ({rvol:.2f})"
            )
        elif rvol >= 1.2:
            score += 15.0
            passed = True
            reasons.append(
                f"Positive RVOL ({rvol:.2f})"
            )
        elif rvol < 0.8:
            score -= 15.0
            reasons.append(
                f"Weak RVOL ({rvol:.2f})"
            )
        else:
            reasons.append(
                f"Normal RVOL ({rvol:.2f})"
            )

        if (
            volume.previous_window_volume is not None
            and volume.previous_window_volume > 0
        ):
            acceleration = (
                volume.current_volume
                / volume.previous_window_volume
            )

            if acceleration >= 1.5:
                score += 15.0
                passed = True
                reasons.append(
                    "Strong volume acceleration"
                )
            elif acceleration <= 0.7:
                score -= 15.0
                reasons.append(
                    "Volume deceleration"
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
        