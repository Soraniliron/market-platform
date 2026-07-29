from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PriceObservation:
    day: int
    low: float
    high: float
    close: float


@dataclass(frozen=True)
class BacktestCycleResult:
    cycle_id: str
    entry_price: float
    exit_price: float
    entry_reached: bool
    entry_day: int | None
    exit_reached_after_entry: bool
    exit_day: int | None
    full_route_completed: bool
    days_entry_to_exit: int | None


@dataclass(frozen=True)
class BacktestSummary:
    total_cycles: int
    entry_reached_cycles: int
    exit_after_entry_cycles: int
    full_route_cycles: int
    entry_probability: float
    exit_probability_after_entry: float
    full_route_probability: float
    results: tuple[BacktestCycleResult, ...]


def validate_observations(
    observations: list[PriceObservation],
) -> None:
    if not isinstance(observations, list):
        raise ValueError(
            "observations must be a list"
        )

    if not observations:
        raise ValueError(
            "observations must not be empty"
        )

    previous_day: int | None = None

    for observation in observations:
        if not isinstance(
            observation,
            PriceObservation,
        ):
            raise ValueError(
                "each observation must be "
                "a PriceObservation"
            )

        if observation.day < 0:
            raise ValueError(
                "observation day must not "
                "be negative"
            )

        if previous_day is not None:
            if observation.day <= previous_day:
                raise ValueError(
                    "observation days must be "
                    "strictly increasing"
                )

        if observation.low <= 0:
            raise ValueError(
                "observation low must be "
                "greater than zero"
            )

        if observation.high <= 0:
            raise ValueError(
                "observation high must be "
                "greater than zero"
            )

        if observation.close <= 0:
            raise ValueError(
                "observation close must be "
                "greater than zero"
            )

        if observation.low > observation.high:
            raise ValueError(
                "observation low must not "
                "exceed high"
            )

        if not (
            observation.low
            <= observation.close
            <= observation.high
        ):
            raise ValueError(
                "observation close must be "
                "between low and high"
            )

        previous_day = observation.day


def backtest_cycle(
    cycle_id: str,
    observations: list[PriceObservation],
    entry_price: float,
    exit_price: float,
) -> BacktestCycleResult:
    if not cycle_id:
        raise ValueError(
            "cycle_id must not be empty"
        )

    if entry_price <= 0:
        raise ValueError(
            "entry_price must be greater "
            "than zero"
        )

    if exit_price <= entry_price:
        raise ValueError(
            "exit_price must be greater "
            "than entry_price"
        )

    validate_observations(observations)

    entry_day: int | None = None
    exit_day: int | None = None

    for observation in observations:
        if (
            entry_day is None
            and observation.low <= entry_price
        ):
            entry_day = observation.day
            continue

        if (
            entry_day is not None
            and observation.day >= entry_day
            and observation.high >= exit_price
        ):
            exit_day = observation.day
            break

    entry_reached = entry_day is not None
    exit_reached_after_entry = (
        entry_day is not None
        and exit_day is not None
    )

    days_entry_to_exit: int | None = None

    if exit_reached_after_entry:
        days_entry_to_exit = (
            exit_day - entry_day
        )

    return BacktestCycleResult(
        cycle_id=cycle_id,
        entry_price=entry_price,
        exit_price=exit_price,
        entry_reached=entry_reached,
        entry_day=entry_day,
        exit_reached_after_entry=(
            exit_reached_after_entry
        ),
        exit_day=exit_day,
        full_route_completed=(
            exit_reached_after_entry
        ),
        days_entry_to_exit=(
            days_entry_to_exit
        ),
    )


def calculate_probability(
    successes: int,
    total: int,
) -> float:
    if total <= 0:
        return 0.0

    return round(
        successes / total,
        4,
    )


def summarize_backtest(
    results: list[BacktestCycleResult],
) -> BacktestSummary:
    if not isinstance(results, list):
        raise ValueError(
            "results must be a list"
        )

    total_cycles = len(results)

    entry_reached_cycles = sum(
        result.entry_reached
        for result in results
    )

    exit_after_entry_cycles = sum(
        result.exit_reached_after_entry
        for result in results
    )

    full_route_cycles = sum(
        result.full_route_completed
        for result in results
    )

    return BacktestSummary(
        total_cycles=total_cycles,
        entry_reached_cycles=(
            entry_reached_cycles
        ),
        exit_after_entry_cycles=(
            exit_after_entry_cycles
        ),
        full_route_cycles=(
            full_route_cycles
        ),
        entry_probability=calculate_probability(
            entry_reached_cycles,
            total_cycles,
        ),
        exit_probability_after_entry=(
            calculate_probability(
                exit_after_entry_cycles,
                entry_reached_cycles,
            )
        ),
        full_route_probability=(
            calculate_probability(
                full_route_cycles,
                total_cycles,
            )
        ),
        results=tuple(results),
    )


def run_backtest(
    cycles: list[dict[str, Any]],
    entry_price: float,
    exit_price: float,
) -> BacktestSummary:
    if not isinstance(cycles, list):
        raise ValueError(
            "cycles must be a list"
        )

    results: list[BacktestCycleResult] = []

    for cycle in cycles:
        if not isinstance(cycle, dict):
            raise ValueError(
                "each cycle must be a dictionary"
            )

        cycle_id = cycle.get("cycle_id")
        raw_observations = cycle.get(
            "observations"
        )

        if not isinstance(
            raw_observations,
            list,
        ):
            raise ValueError(
                "cycle observations must be "
                "a list"
            )

        observations = [
            PriceObservation(
                day=observation["day"],
                low=observation["low"],
                high=observation["high"],
                close=observation["close"],
            )
            for observation in raw_observations
        ]

        results.append(
            backtest_cycle(
                cycle_id=cycle_id,
                observations=observations,
                entry_price=entry_price,
                exit_price=exit_price,
            )
        )

    return summarize_backtest(results)
