from math import ceil
from statistics import mean, median
from typing import Optional

from earnings.models import (
    EarningsCycle,
    ExitPercentileLevel,
    ExitPercentileResult,
)
from earnings.sample_engine import (
    get_sample_status,
    is_production_ready,
)
from engines.price_analysis import get_price_history


EXIT_PROBABILITIES = (
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.80,
    0.90,
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


def find_first_entry_index(
    prices: list[dict],
    entry_price: float,
) -> Optional[int]:
    for index, row in enumerate(prices):
        close_price = float(row["close"])

        if close_price <= entry_price:
            return index

    return None


def calculate_max_return_after_entry(
    prices: list[dict],
    entry_index: int,
    entry_price: float,
) -> float:
    maximum_high = max(
        float(row["high"])
        for row in prices[entry_index:]
    )

    return (
        (maximum_high - entry_price)
        / entry_price
    ) * 100


def find_first_exit_index(
    prices: list[dict],
    entry_index: int,
    exit_price: float,
) -> Optional[int]:
    for index in range(
        entry_index,
        len(prices),
    ):
        high_price = float(
            prices[index]["high"]
        )

        if high_price >= exit_price:
            return index

    return None


def collect_entry_cycle_data(
    ticker: str,
    cycles: list[EarningsCycle],
    entry_drop_pct: float,
) -> list[dict]:
    entry_cycle_data: list[dict] = []

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

        entry_index = find_first_entry_index(
            prices=prices,
            entry_price=cycle_entry_price,
        )

        if entry_index is None:
            continue

        maximum_return_pct = (
            calculate_max_return_after_entry(
                prices=prices,
                entry_index=entry_index,
                entry_price=cycle_entry_price,
            )
        )

        entry_cycle_data.append(
            {
                "prices": prices,
                "entry_index": entry_index,
                "entry_price": cycle_entry_price,
                "maximum_return_pct": max(
                    0.0,
                    maximum_return_pct,
                ),
            }
        )

    return entry_cycle_data


def calculate_exit_percentile_level(
    cycles_count: int,
    entry_cycle_data: list[dict],
    reach_probability: float,
    current_entry_price: float,
) -> ExitPercentileLevel:
    if cycles_count < 1:
        raise ValueError(
            "cycles_count must be at least one"
        )

    if not entry_cycle_data:
        raise ValueError(
            "At least one entry hit is required"
        )

    if reach_probability <= 0 or reach_probability > 1:
        raise ValueError(
            "reach_probability must be greater "
            "than zero and no greater than one"
        )

    maximum_returns_descending = sorted(
        (
            float(item["maximum_return_pct"])
            for item in entry_cycle_data
        ),
        reverse=True,
    )

    required_hits = ceil(
        reach_probability
        * len(entry_cycle_data)
    )

    target_return_pct = (
        maximum_returns_descending[
            required_hits - 1
        ]
    )

    exit_price = current_entry_price * (
        1 + target_return_pct / 100
    )

    target_hits_after_entry = 0
    days_entry_to_exit_values: list[int] = []
    days_report_to_exit_values: list[int] = []

    for item in entry_cycle_data:
        cycle_exit_price = (
            float(item["entry_price"])
            * (1 + target_return_pct / 100)
        )

        exit_index = find_first_exit_index(
            prices=item["prices"],
            entry_index=item["entry_index"],
            exit_price=cycle_exit_price,
        )

        if exit_index is None:
            continue

        target_hits_after_entry += 1

        days_entry_to_exit_values.append(
            exit_index - item["entry_index"]
        )

        days_report_to_exit_values.append(
            exit_index
        )

    entry_hits = len(entry_cycle_data)

    target_probability_after_entry = (
        target_hits_after_entry
        / entry_hits
    ) * 100

    full_cycle_probability = (
        target_hits_after_entry
        / cycles_count
    ) * 100

    return ExitPercentileLevel(
        percentile=reach_probability * 100,
        target_return_pct=target_return_pct,
        exit_price=exit_price,
        entry_hits=entry_hits,
        target_hits_after_entry=(
            target_hits_after_entry
        ),
        target_probability_after_entry=(
            target_probability_after_entry
        ),
        full_cycle_probability=(
            full_cycle_probability
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


def calculate_exit_percentiles(
    ticker: str,
    cycles: list[EarningsCycle],
    entry_drop_pct: float,
    reference_price: Optional[float] = None,
    minimum_cycles_required: int = 12,
) -> ExitPercentileResult:
    validate_cycles(
        ticker=ticker,
        cycles=cycles,
    )

    if entry_drop_pct > 0:
        raise ValueError(
            "entry_drop_pct must be zero or negative"
        )

    if minimum_cycles_required < 1:
        raise ValueError(
            "minimum_cycles_required must be at least one"
        )

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

    entry_cycle_data = collect_entry_cycle_data(
        ticker=ticker,
        cycles=cycles,
        entry_drop_pct=entry_drop_pct,
    )

    if not entry_cycle_data:
        raise ValueError(
            "The selected entry level was not reached "
            "in any earnings cycle"
        )

    cycles_count = len(cycles)

    levels = {
        probability: calculate_exit_percentile_level(
            cycles_count=cycles_count,
            entry_cycle_data=entry_cycle_data,
            reach_probability=probability,
            current_entry_price=entry_price,
        )
        for probability in EXIT_PROBABILITIES
    }

    return ExitPercentileResult(
        ticker=ticker,
        cycles_count=cycles_count,
        entry_drop_pct=entry_drop_pct,
        reference_price=reference_price,
        entry_price=entry_price,
        minimum_cycles_required=(
            minimum_cycles_required
        ),
        production_ready=is_production_ready(
            cycles_count=cycles_count,
            minimum_cycles_required=(
                minimum_cycles_required
            ),
        ),
        sample_status=get_sample_status(
            cycles_count=cycles_count,
            minimum_cycles_required=(
                minimum_cycles_required
            ),
        ),
        p50=levels[0.50],
        p55=levels[0.55],
        p60=levels[0.60],
        p65=levels[0.65],
        p70=levels[0.70],
        p80=levels[0.80],
        p90=levels[0.90],
    )
