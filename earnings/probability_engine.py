from statistics import mean, median
from typing import Optional

from earnings.models import (
    EarningsAnalysisResult,
    EarningsCycle,
)
from earnings.statistics_engine import calculate_drop_pct
from engines.price_analysis import get_price_history


def calculate_percentile(
    values: list[float],
    percentile: float,
) -> float:
    if not values:
        raise ValueError(
            "At least one value is required"
        )

    if percentile < 0 or percentile > 1:
        raise ValueError(
            "percentile must be between 0 and 1"
        )

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = percentile * (
        len(sorted_values) - 1
    )

    lower_index = int(position)

    upper_index = min(
        lower_index + 1,
        len(sorted_values) - 1,
    )

    weight = position - lower_index

    return (
        sorted_values[lower_index] * (1 - weight)
        + sorted_values[upper_index] * weight
    )


def validate_cycles(
    ticker: str,
    cycles: list[EarningsCycle],
) -> None:
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


def calculate_entry_exit_analysis(
    ticker: str,
    cycles: list[EarningsCycle],
    entry_percentile: float = 0.60,
    target_return_pct: float = 10.0,
    reference_price: Optional[float] = None,
) -> EarningsAnalysisResult:
    validate_cycles(
        ticker=ticker,
        cycles=cycles,
    )

    if entry_percentile < 0 or entry_percentile > 1:
        raise ValueError(
            "entry_percentile must be between 0 and 1"
        )

    if target_return_pct <= 0:
        raise ValueError(
            "target_return_pct must be greater than zero"
        )

    drop_depths = [
        abs(calculate_drop_pct(cycle))
        for cycle in cycles
    ]

    entry_drop_depth = calculate_percentile(
        values=drop_depths,
        percentile=entry_percentile,
    )

    entry_drop_pct = -entry_drop_depth

    if reference_price is None:
        reference_price = (
            cycles[-1].day_zero_close
        )

    if reference_price <= 0:
        raise ValueError(
            "reference_price must be greater than zero"
        )

    entry_price = reference_price * (
        1 + entry_drop_pct / 100
    )

    exit_price = entry_price * (
        1 + target_return_pct / 100
    )

    entry_hits = 0
    target_hits_after_entry = 0

    days_to_entry_values: list[int] = []
    days_entry_to_exit_values: list[int] = []
    days_report_to_exit_values: list[int] = []

    for cycle in cycles:
        prices = get_price_history(
            ticker=ticker,
            start_date=cycle.report_date,
            end_date=cycle.next_report_date,
        )

        if not prices:
            continue

        cycle_entry_price = (
            cycle.day_zero_close
            * (1 + entry_drop_pct / 100)
        )

        cycle_exit_price = (
            cycle_entry_price
            * (1 + target_return_pct / 100)
        )

        entry_index: Optional[int] = None

        for index, row in enumerate(prices):
            close_price = float(
                row["close"]
            )

            if close_price <= cycle_entry_price:
                entry_index = index
                break

        if entry_index is None:
            continue

        entry_hits += 1
        days_to_entry_values.append(
            entry_index
        )

        exit_index: Optional[int] = None

        for index in range(
            entry_index,
            len(prices),
        ):
            high_price = float(
                prices[index]["high"]
            )

            if high_price >= cycle_exit_price:
                exit_index = index
                break

        if exit_index is None:
            continue

        target_hits_after_entry += 1

        days_entry_to_exit_values.append(
            exit_index - entry_index
        )

        days_report_to_exit_values.append(
            exit_index
        )

    cycles_count = len(cycles)
    full_cycle_hits = target_hits_after_entry

    entry_probability = (
        entry_hits / cycles_count
    ) * 100

    target_probability_after_entry = (
        target_hits_after_entry
        / entry_hits
        * 100
        if entry_hits > 0
        else 0.0
    )

    full_cycle_probability = (
        full_cycle_hits / cycles_count
    ) * 100

    return EarningsAnalysisResult(
        ticker=ticker,
        cycles_count=cycles_count,
        entry_drop_pct=entry_drop_pct,
        entry_price=entry_price,
        target_return_pct=target_return_pct,
        exit_price=exit_price,
        entry_hits=entry_hits,
        target_hits_after_entry=(
            target_hits_after_entry
        ),
        full_cycle_hits=full_cycle_hits,
        entry_probability=entry_probability,
        target_probability_after_entry=(
            target_probability_after_entry
        ),
        full_cycle_probability=(
            full_cycle_probability
        ),
        average_days_to_entry=(
            mean(days_to_entry_values)
            if days_to_entry_values
            else 0.0
        ),
        median_days_to_entry=(
            median(days_to_entry_values)
            if days_to_entry_values
            else 0.0
        ),
        average_days_entry_to_exit=(
            mean(days_entry_to_exit_values)
            if days_entry_to_exit_values
            else 0.0
        ),
        median_days_entry_to_exit=(
            median(days_entry_to_exit_values)
            if days_entry_to_exit_values
            else 0.0
        ),
        average_days_report_to_exit=(
            mean(days_report_to_exit_values)
            if days_report_to_exit_values
            else 0.0
        ),
        median_days_report_to_exit=(
            median(days_report_to_exit_values)
            if days_report_to_exit_values
            else 0.0
        ),
    )
