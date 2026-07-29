from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FilterDecision:
    ticker: str
    filter_name: str
    triggered: bool
    action: str
    reason: str


def evaluate_lly_overshoot(
    ticker: str,
    entry_price: float,
    closes_after_entry: list[float],
) -> FilterDecision:
    if ticker.upper() != "LLY":
        return FilterDecision(
            ticker=ticker,
            filter_name="LLY_OVERSHOOT_CONFIRMED",
            triggered=False,
            action="NOT_APPLICABLE",
            reason="Filter applies only to LLY",
        )

    if entry_price <= 0:
        raise ValueError(
            "entry_price must be greater than zero"
        )

    if not closes_after_entry:
        raise ValueError(
            "At least one close price is required"
        )

    first_five_closes = closes_after_entry[:5]

    overshoot_threshold = entry_price * 0.94

    triggered = any(
        close_price <= overshoot_threshold
        for close_price in first_five_closes
    )

    if triggered:
        return FilterDecision(
            ticker=ticker,
            filter_name="LLY_OVERSHOOT_CONFIRMED",
            triggered=True,
            action="WAIT_FOR_STABILIZATION",
            reason=(
                "Close reached at least 6% below Entry "
                "within five trading days"
            ),
        )

    return FilterDecision(
        ticker=ticker,
        filter_name="LLY_OVERSHOOT_CONFIRMED",
        triggered=False,
        action="NORMAL_PATH",
        reason=(
            "No close reached 6% below Entry "
            "within five trading days"
        ),
    )


def evaluate_late_entry_volume_filter(
    ticker: str,
    entry_day: int,
    entry_volume: float,
    average_volume_5d: float,
    day_zero_close: float,
    entry_close: float,
    minimum_day: int,
    minimum_rvol: float,
    require_close_below_day_zero: bool,
    filter_name: str,
) -> FilterDecision:
    if entry_day < 0:
        raise ValueError(
            "entry_day must be zero or greater"
        )

    if entry_volume < 0:
        raise ValueError(
            "entry_volume must be zero or greater"
        )

    if average_volume_5d <= 0:
        raise ValueError(
            "average_volume_5d must be greater than zero"
        )

    if day_zero_close <= 0 or entry_close <= 0:
        raise ValueError(
            "prices must be greater than zero"
        )

    relative_volume = (
        entry_volume / average_volume_5d
    )

    late_entry = entry_day > minimum_day
    high_volume = relative_volume >= minimum_rvol

    close_condition = (
        entry_close < day_zero_close
        if require_close_below_day_zero
        else True
    )

    triggered = (
        late_entry
        and high_volume
        and close_condition
    )

    if triggered:
        return FilterDecision(
            ticker=ticker,
            filter_name=filter_name,
            triggered=True,
            action="SKIP_CYCLE",
            reason=(
                f"Late Entry after Day {minimum_day}, "
                f"RVOL {relative_volume:.2f}, "
                "and required price condition confirmed"
            ),
        )

    return FilterDecision(
        ticker=ticker,
        filter_name=filter_name,
        triggered=False,
        action="NORMAL_PATH",
        reason=(
            f"Filter conditions not fully met; "
            f"RVOL {relative_volume:.2f}"
        ),
    )


def evaluate_bac_late_entry(
    entry_day: int,
    entry_volume: float,
    average_volume_5d: float,
    day_zero_close: float,
    entry_close: float,
) -> FilterDecision:
    return evaluate_late_entry_volume_filter(
        ticker="BAC",
        entry_day=entry_day,
        entry_volume=entry_volume,
        average_volume_5d=average_volume_5d,
        day_zero_close=day_zero_close,
        entry_close=entry_close,
        minimum_day=15,
        minimum_rvol=1.25,
        require_close_below_day_zero=True,
        filter_name="BAC_LATE_ENTRY",
    )


def evaluate_cof_late_entry(
    entry_day: int,
    entry_volume: float,
    average_volume_5d: float,
    day_zero_close: float,
    entry_close: float,
) -> FilterDecision:
    return evaluate_late_entry_volume_filter(
        ticker="COF",
        entry_day=entry_day,
        entry_volume=entry_volume,
        average_volume_5d=average_volume_5d,
        day_zero_close=day_zero_close,
        entry_close=entry_close,
        minimum_day=15,
        minimum_rvol=1.30,
        require_close_below_day_zero=False,
        filter_name="COF_LATE_ENTRY",
    )
