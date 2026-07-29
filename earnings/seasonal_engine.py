from collections import defaultdict
from statistics import mean, median

from earnings.models import EarningsCycle
from earnings.statistics_engine import (
    calculate_drop_pct,
    calculate_rebound_pct,
)


def get_quarter(report_month: int) -> int:
    if report_month < 1 or report_month > 12:
        raise ValueError(
            "report_month must be between 1 and 12"
        )

    return ((report_month - 1) // 3) + 1


def group_cycles_by_quarter(
    cycles: list[EarningsCycle],
) -> dict[int, list[EarningsCycle]]:
    if not cycles:
        raise ValueError(
            "At least one earnings cycle is required"
        )

    grouped: dict[int, list[EarningsCycle]] = (
        defaultdict(list)
    )

    for cycle in cycles:
        quarter = get_quarter(
            cycle.report_date.month
        )

        grouped[quarter].append(cycle)

    return dict(grouped)


def calculate_quarter_statistics(
    cycles: list[EarningsCycle],
) -> dict[int, dict[str, float]]:
    grouped_cycles = group_cycles_by_quarter(
        cycles=cycles
    )

    results: dict[int, dict[str, float]] = {}

    for quarter, quarter_cycles in grouped_cycles.items():
        drop_values = [
            calculate_drop_pct(cycle)
            for cycle in quarter_cycles
        ]

        rebound_values = [
            calculate_rebound_pct(cycle)
            for cycle in quarter_cycles
        ]

        days_to_low_values = [
            cycle.days_to_low
            for cycle in quarter_cycles
        ]

        days_to_rebound_values = [
            cycle.days_low_to_rebound
            for cycle in quarter_cycles
        ]

        results[quarter] = {
            "cycles_count": float(
                len(quarter_cycles)
            ),
            "average_drop_pct": mean(
                drop_values
            ),
            "median_drop_pct": median(
                drop_values
            ),
            "average_rebound_pct": mean(
                rebound_values
            ),
            "median_rebound_pct": median(
                rebound_values
            ),
            "average_days_to_low": mean(
                days_to_low_values
            ),
            "median_days_to_low": median(
                days_to_low_values
            ),
            "average_days_to_rebound": mean(
                days_to_rebound_values
            ),
            "median_days_to_rebound": median(
                days_to_rebound_values
            ),
        }

    return results
