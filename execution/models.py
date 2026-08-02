from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EntryStatus(str, Enum):
    BUY_NOW = "buy_now"
    WATCH = "watch"
    WAIT = "wait"
    REJECT = "reject"


@dataclass(frozen=True)
class EntryContext:
    current_price: float
    breakout_level: float
    vwap: float | None

    current_volume: float
    average_volume_same_window: float

    atr: float
    recent_swing_low: float

    spy_aligned: bool
    qqq_aligned: bool

    chart_quality_score: float
    decision_score: float

    minutes_from_market_open: int
    maximum_entry_delay_minutes: int = 60


@dataclass(frozen=True)
class TradePlan:
    ticker: str
    status: EntryStatus

    entry_price: float | None
    stop_price: float | None
    tp1_price: float | None
    tp2_price: float | None

    risk_per_share: float | None
    reward_tp1: float | None
    reward_tp2: float | None

    risk_reward_tp1: float | None
    risk_reward_tp2: float | None

    invalidation_price: float | None

    decision_score: float
    reason: str
    