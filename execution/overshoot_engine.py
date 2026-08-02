from __future__ import annotations

from dataclasses import dataclass

from execution.models import EntryContext


@dataclass(frozen=True)
class OvershootResult:
    overshoot: bool
    distance_percent: float
    reason: str


class OvershootEngine:
    def __init__(
        self,
        maximum_distance_percent: float = 1.5,
    ) -> None:
        if maximum_distance_percent <= 0:
            raise ValueError(
                "maximum_distance_percent must be greater than zero"
            )

        self.maximum_distance_percent = (
            maximum_distance_percent
        )

    def evaluate(
        self,
        context: EntryContext,
    ) -> OvershootResult:
        if context.breakout_level <= 0:
            raise ValueError(
                "breakout_level must be greater than zero"
            )

        distance_percent = (
            (
                context.current_price
                - context.breakout_level
            )
            / context.breakout_level
        ) * 100

        rounded_distance = round(
            distance_percent,
            4,
        )

        if (
            distance_percent
            > self.maximum_distance_percent
        ):
            return OvershootResult(
                overshoot=True,
                distance_percent=rounded_distance,
                reason=(
                    "Price moved too far above "
                    "the breakout level"
                ),
            )

        return OvershootResult(
            overshoot=False,
            distance_percent=rounded_distance,
            reason=(
                "Price remains within the "
                "allowed entry distance"
            ),
        )
        