from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScanStatus(str, Enum):
    STRONG = "strong"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    WEAK = "weak"
    REJECTED = "rejected"


@dataclass(frozen=True)
class MarketSnapshot:
    ticker: str
    price: float
    previous_close: float
    change_percent: float
    volume: float
    vwap: float | None
    high: float
    low: float
    timeframe_minutes: int


@dataclass(frozen=True)
class ScanResult:
    ticker: str
    status: ScanStatus
    score: float
    price: float
    change_percent: float
    volume: float
    vwap: float | None
    above_vwap: bool | None
    reason: str
    