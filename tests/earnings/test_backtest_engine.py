import pytest

from earnings.backtest_engine import (
    PriceObservation,
    backtest_cycle,
    calculate_probability,
    run_backtest,
    summarize_backtest,
)


def test_backtest_cycle_completes_full_route() -> None:
    observations = [
        PriceObservation(
            day=1,
            low=105,
            high=110,
            close=108,
        ),
        PriceObservation(
            day=2,
            low=99,
            high=104,
            close=101,
        ),
        PriceObservation(
            day=3,
            low=101,
            high=112,
            close=110,
        ),
    ]

    result = backtest_cycle(
        cycle_id="cycle-1",
        observations=observations,
        entry_price=100,
        exit_price=110,
    )

    assert result.entry_reached is True
    assert result.entry_day == 2
    assert result.exit_reached_after_entry is True
    assert result.exit_day == 3
    assert result.full_route_completed is True
    assert result.days_entry_to_exit == 1


def test_backtest_cycle_requires_entry_before_exit() -> None:
    observations = [
        PriceObservation(
            day=1,
            low=105,
            high=115,
            close=110,
        ),
        PriceObservation(
            day=2,
            low=99,
            high=105,
            close=101,
        ),
    ]

    result = backtest_cycle(
        cycle_id="cycle-2",
        observations=observations,
        entry_price=100,
        exit_price=110,
    )

    assert result.entry_reached is True
    assert result.entry_day == 2
    assert result.exit_reached_after_entry is False
    assert result.exit_day is None
    assert result.full_route_completed is False


def test_backtest_cycle_without_entry() -> None:
    observations = [
        PriceObservation(
            day=1,
            low=101,
            high=108,
            close=104,
        ),
        PriceObservation(
            day=2,
            low=102,
            high=109,
            close=106,
        ),
    ]

    result = backtest_cycle(
        cycle_id="cycle-3",
        observations=observations,
        entry_price=100,
        exit_price=110,
    )

    assert result.entry_reached is False
    assert result.entry_day is None
    assert result.exit_reached_after_entry is False
    assert result.exit_day is None


def test_summarize_backtest_probabilities() -> None:
    first = backtest_cycle(
        cycle_id="cycle-1",
        observations=[
            PriceObservation(
                day=1,
                low=99,
                high=101,
                close=100,
            ),
            PriceObservation(
                day=2,
                low=101,
                high=111,
                close=109,
            ),
        ],
        entry_price=100,
        exit_price=110,
    )

    second = backtest_cycle(
        cycle_id="cycle-2",
        observations=[
            PriceObservation(
                day=1,
                low=99,
                high=105,
                close=102,
            ),
        ],
        entry_price=100,
        exit_price=110,
    )

    third = backtest_cycle(
        cycle_id="cycle-3",
        observations=[
            PriceObservation(
                day=1,
                low=101,
                high=109,
                close=105,
            ),
        ],
        entry_price=100,
        exit_price=110,
    )

    summary = summarize_backtest(
        [first, second, third]
    )

    assert summary.total_cycles == 3
    assert summary.entry_reached_cycles == 2
    assert summary.exit_after_entry_cycles == 1
    assert summary.full_route_cycles == 1
    assert summary.entry_probability == 0.6667
    assert summary.exit_probability_after_entry == 0.5
    assert summary.full_route_probability == 0.3333


def test_calculate_probability_with_zero_total() -> None:
    assert calculate_probability(0, 0) == 0.0


def test_run_backtest() -> None:
    cycles = [
        {
            "cycle_id": "cycle-1",
            "observations": [
                {
                    "day": 1,
                    "low": 99,
                    "high": 102,
                    "close": 100,
                },
                {
                    "day": 2,
                    "low": 102,
                    "high": 111,
                    "close": 109,
                },
            ],
        }
    ]

    summary = run_backtest(
        cycles=cycles,
        entry_price=100,
        exit_price=110,
    )

    assert summary.total_cycles == 1
    assert summary.full_route_cycles == 1


def test_rejects_invalid_price_relation() -> None:
    observations = [
        PriceObservation(
            day=1,
            low=99,
            high=101,
            close=100,
        )
    ]

    with pytest.raises(
        ValueError,
        match=(
            "exit_price must be greater "
            "than entry_price"
        ),
    ):
        backtest_cycle(
            cycle_id="cycle-1",
            observations=observations,
            entry_price=100,
            exit_price=90,
        )


def test_rejects_unsorted_observations() -> None:
    observations = [
        PriceObservation(
            day=2,
            low=99,
            high=101,
            close=100,
        ),
        PriceObservation(
            day=1,
            low=99,
            high=101,
            close=100,
        ),
    ]

    with pytest.raises(
        ValueError,
        match=(
            "observation days must be "
            "strictly increasing"
        ),
    ):
        backtest_cycle(
            cycle_id="cycle-1",
            observations=observations,
            entry_price=100,
            exit_price=110,
        )


def test_rejects_close_outside_range() -> None:
    observations = [
        PriceObservation(
            day=1,
            low=99,
            high=101,
            close=105,
        )
    ]

    with pytest.raises(
        ValueError,
        match=(
            "observation close must be "
            "between low and high"
        ),
    ):
        backtest_cycle(
            cycle_id="cycle-1",
            observations=observations,
            entry_price=100,
            exit_price=110,
        )
