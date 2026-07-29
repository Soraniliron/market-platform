from dataclasses import dataclass
from statistics import mean, median


@dataclass(frozen=True)
class OvershootCycleResult:
    cycle_index: int
    entry_price: float
    minimum_close_after_entry: float
    overshoot_pct: float
    triggered: bool


@dataclass(frozen=True)
class OvershootAnalysisResult:
    cycles_count: int
    triggered_cycles: int
    trigger_probability: float
    average_overshoot_pct: float
    median_overshoot_pct: float
    maximum_overshoot_pct: float
    threshold_pct: float
    window_days: int
    results: list[OvershootCycleResult]


def calculate_overshoot_pct(
    entry_price: float,
    minimum_close_after_entry: float,
) -> float:
    if entry_price <= 0:
        raise ValueError(
            "entry_price must be greater than zero"
        )

    if minimum_close_after_entry <= 0:
        raise ValueError(
            "minimum_close_after_entry must be greater than zero"
        )

    return (
        (minimum_close_after_entry - entry_price)
        / entry_price
    ) * 100


def analyze_overshoot_cycle(
    cycle_index: int,
    entry_price: float,
    closes_after_entry: list[float],
    threshold_pct: float = -6.0,
    window_days: int = 5,
) -> OvershootCycleResult:
    if cycle_index < 0:
        raise ValueError(
            "cycle_index must be zero or greater"
        )

    if entry_price <= 0:
        raise ValueError(
            "entry_price must be greater than zero"
        )

    if not closes_after_entry:
        raise ValueError(
            "At least one close price is required"
        )

    if threshold_pct >= 0:
        raise ValueError(
            "threshold_pct must be negative"
        )

    if window_days < 1:
        raise ValueError(
            "window_days must be at least one"
        )

    window_closes = closes_after_entry[:window_days]

    for close_price in window_closes:
        if close_price <= 0:
            raise ValueError(
                "close prices must be greater than zero"
            )

    minimum_close = min(window_closes)

    overshoot_pct = calculate_overshoot_pct(
        entry_price=entry_price,
        minimum_close_after_entry=minimum_close,
    )

    return OvershootCycleResult(
        cycle_index=cycle_index,
        entry_price=entry_price,
        minimum_close_after_entry=minimum_close,
        overshoot_pct=overshoot_pct,
        triggered=overshoot_pct <= threshold_pct,
    )


def analyze_overshoot_history(
    entry_prices: list[float],
    closes_after_entries: list[list[float]],
    threshold_pct: float = -6.0,
    window_days: int = 5,
) -> OvershootAnalysisResult:
    if not entry_prices:
        raise ValueError(
            "At least one entry price is required"
        )

    if len(entry_prices) != len(closes_after_entries):
        raise ValueError(
            "entry_prices and closes_after_entries "
            "must have the same length"
        )

    results = [
        analyze_overshoot_cycle(
            cycle_index=index,
            entry_price=entry_price,
            closes_after_entry=closes_after_entries[index],
            threshold_pct=threshold_pct,
            window_days=window_days,
        )
        for index, entry_price in enumerate(entry_prices)
    ]

    triggered_results = [
        result
        for result in results
        if result.triggered
    ]

    triggered_cycles = len(triggered_results)

    triggered_overshoots = [
        result.overshoot_pct
        for result in triggered_results
    ]

    return OvershootAnalysisResult(
        cycles_count=len(results),
        triggered_cycles=triggered_cycles,
        trigger_probability=(
            triggered_cycles / len(results)
        ) * 100,
        average_overshoot_pct=(
            mean(triggered_overshoots)
            if triggered_overshoots
            else 0.0
        ),
        median_overshoot_pct=(
            median(triggered_overshoots)
            if triggered_overshoots
            else 0.0
        ),
        maximum_overshoot_pct=(
            min(triggered_overshoots)
            if triggered_overshoots
            else 0.0
        ),
        threshold_pct=threshold_pct,
        window_days=window_days,
        results=results,
    )
