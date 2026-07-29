from statistics import mean, median

from earnings.models import (
    EarningsCycle,
    EarningsCycleResult,
)


def calculate_drop_pct(
    cycle: EarningsCycle,
) -> float:
    return (
        (cycle.cycle_low - cycle.day_zero_close)
        / cycle.day_zero_close
    ) * 100


def calculate_rebound_pct(
    cycle: EarningsCycle,
) -> float:
    return (
        (
            cycle.max_rebound_price
            - cycle.cycle_low
        )
        / cycle.cycle_low
    ) * 100


def calculate_cycle_statistics(
    ticker: str,
    cycles: list[EarningsCycle],
) -> EarningsCycleResult:
    if not cycles:
        raise ValueError(
            "At least one earnings cycle is required"
        )

    for cycle in cycles:
        if cycle.ticker != ticker:
            raise ValueError(
                f"Cycle ticker {cycle.ticker} "
                f"does not match {ticker}"
            )

    drop_percentages = [
        calculate_drop_pct(cycle)
        for cycle in cycles
    ]

    rebound_percentages = [
        calculate_rebound_pct(cycle)
        for cycle in cycles
    ]

    days_to_low = [
        cycle.days_to_low
        for cycle in cycles
    ]

    days_to_rebound = [
        cycle.days_low_to_rebound
        for cycle in cycles
    ]

    return EarningsCycleResult(
        ticker=ticker,
        cycles_count=len(cycles),
        average_drop_pct=mean(
            drop_percentages
        ),
        median_drop_pct=median(
            drop_percentages
        ),
        average_days_to_low=mean(
            days_to_low
        ),
        median_days_to_low=median(
            days_to_low
        ),
        average_rebound_pct=mean(
            rebound_percentages
        ),
        median_rebound_pct=median(
            rebound_percentages
        ),
        average_days_to_rebound=mean(
            days_to_rebound
        ),
        median_days_to_rebound=median(
            days_to_rebound
        ),
    )
