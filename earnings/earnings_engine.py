from dataclasses import dataclass
from typing import Optional

from earnings.entry_engine import (
    calculate_entry_percentile_level,
)
from earnings.exit_engine import calculate_exit_percentiles
from earnings.models import (
    EarningsCycle,
    EntryPercentileLevel,
    EntryPercentileResult,
    ExitPercentileLevel,
    ExitPercentileResult,
    EarningsCycleResult,
)
from earnings.sample_engine import (
    get_sample_status,
    is_production_ready,
)
from earnings.statistics_engine import (
    calculate_cycle_statistics,
)


ENTRY_PROBABILITIES = (
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.80,
    0.90,
)

SUPPORTED_PERCENTILES = {
    0.50: "p50",
    0.55: "p55",
    0.60: "p60",
    0.65: "p65",
    0.70: "p70",
    0.80: "p80",
    0.90: "p90",
}


@dataclass(frozen=True)
class EarningsEngineResult:
    ticker: str
    cycles_count: int

    statistics: EarningsCycleResult

    entry_percentiles: EntryPercentileResult
    exit_percentiles: ExitPercentileResult

    selected_entry_percentile: float
    selected_exit_percentile: float

    selected_entry: EntryPercentileLevel
    selected_exit: ExitPercentileLevel

    production_ready: bool
    sample_status: str


def validate_cycles(
    ticker: str,
    cycles: list[EarningsCycle],
) -> None:
    if not ticker:
        raise ValueError(
            "ticker must not be empty"
        )

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


def validate_supported_percentile(
    percentile: float,
    field_name: str,
) -> None:
    if percentile not in SUPPORTED_PERCENTILES:
        raise ValueError(
            f"{field_name} must be one of: "
            "0.50, 0.55, 0.60, 0.65, "
            "0.70, 0.80, 0.90"
        )


def calculate_entry_percentiles(
    ticker: str,
    cycles: list[EarningsCycle],
    reference_price: Optional[float] = None,
    minimum_cycles_required: int = 12,
) -> EntryPercentileResult:
    validate_cycles(
        ticker=ticker,
        cycles=cycles,
    )

    if minimum_cycles_required < 1:
        raise ValueError(
            "minimum_cycles_required must be at least one"
        )

    if reference_price is None:
        reference_price = cycles[-1].day_zero_close

    if reference_price <= 0:
        raise ValueError(
            "reference_price must be greater than zero"
        )

    levels = {
        probability: calculate_entry_percentile_level(
            cycles=cycles,
            reach_probability=probability,
            reference_price=reference_price,
        )
        for probability in ENTRY_PROBABILITIES
    }

    cycles_count = len(cycles)

    return EntryPercentileResult(
        ticker=ticker,
        cycles_count=cycles_count,
        reference_price=reference_price,
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


def analyze_earnings_cycles(
    ticker: str,
    cycles: list[EarningsCycle],
    reference_price: Optional[float] = None,
    entry_percentile: float = 0.60,
    exit_percentile: float = 0.60,
    minimum_cycles_required: int = 12,
) -> EarningsEngineResult:
    validate_cycles(
        ticker=ticker,
        cycles=cycles,
    )

    validate_supported_percentile(
        percentile=entry_percentile,
        field_name="entry_percentile",
    )

    validate_supported_percentile(
        percentile=exit_percentile,
        field_name="exit_percentile",
    )

    entry_percentiles = calculate_entry_percentiles(
        ticker=ticker,
        cycles=cycles,
        reference_price=reference_price,
        minimum_cycles_required=(
            minimum_cycles_required
        ),
    )

    entry_attribute = SUPPORTED_PERCENTILES[
        entry_percentile
    ]

    selected_entry = getattr(
        entry_percentiles,
        entry_attribute,
    )

    exit_percentiles = calculate_exit_percentiles(
        ticker=ticker,
        cycles=cycles,
        entry_drop_pct=(
            selected_entry.entry_drop_pct
        ),
        reference_price=(
            entry_percentiles.reference_price
        ),
        minimum_cycles_required=(
            minimum_cycles_required
        ),
    )

    exit_attribute = SUPPORTED_PERCENTILES[
        exit_percentile
    ]

    selected_exit = getattr(
        exit_percentiles,
        exit_attribute,
    )

    statistics = calculate_cycle_statistics(
        ticker=ticker,
        cycles=cycles,
    )

    return EarningsEngineResult(
        ticker=ticker,
        cycles_count=len(cycles),
        statistics=statistics,
        entry_percentiles=entry_percentiles,
        exit_percentiles=exit_percentiles,
        selected_entry_percentile=(
            entry_percentile
        ),
        selected_exit_percentile=(
            exit_percentile
        ),
        selected_entry=selected_entry,
        selected_exit=selected_exit,
        production_ready=(
            entry_percentiles.production_ready
            and exit_percentiles.production_ready
        ),
        sample_status=(
            entry_percentiles.sample_status
        ),
    )
