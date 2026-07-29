from math import ceil

from earnings.models import (
    EarningsCycle,
    EntryPercentileLevel,
)


def calculate_drop_pct(
    cycle: EarningsCycle,
) -> float:
    return (
        (cycle.cycle_low - cycle.day_zero_close)
        / cycle.day_zero_close
    ) * 100


def calculate_entry_percentile_level(
    cycles: list[EarningsCycle],
    reach_probability: float,
    reference_price: float,
) -> EntryPercentileLevel:
    if not cycles:
        raise ValueError(
            "At least one earnings cycle is required"
        )

    if reach_probability <= 0 or reach_probability > 1:
        raise ValueError(
            "reach_probability must be greater than zero and no greater than one"
        )

    drop_depths_descending = sorted(
        (
            max(
                0.0,
                abs(calculate_drop_pct(cycle)),
            )
            for cycle in cycles
        ),
        reverse=True,
    )

    required_hits = ceil(
        reach_probability * len(cycles)
    )

    entry_drop_depth = drop_depths_descending[
        required_hits - 1
    ]

    entry_drop_pct = -entry_drop_depth

    entry_price = reference_price * (
        1 + entry_drop_pct / 100
    )

    entry_hits = sum(
        1
        for drop_depth in drop_depths_descending
        if drop_depth >= entry_drop_depth
    )

    entry_probability = (
        entry_hits / len(cycles)
    ) * 100

    return EntryPercentileLevel(
        percentile=reach_probability * 100,
        entry_drop_pct=entry_drop_pct,
        entry_price=entry_price,
        entry_hits=entry_hits,
        entry_probability=entry_probability,
    )
