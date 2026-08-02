from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from scanner.models import ScanResult


class DecisionStatus(str, Enum):
    BUY = "buy"
    WATCH = "watch"
    WAIT = "wait"
    AVOID = "avoid"


@dataclass(frozen=True)
class RankedCandidate:
    rank: int
    ticker: str
    score: float
    status: DecisionStatus
    scan_result: ScanResult
    reason: str


@dataclass(frozen=True)
class DecisionResult:
    candidates_count: int
    ranked_candidates: tuple[RankedCandidate, ...]
    top_candidate: RankedCandidate | None
    decision_status: DecisionStatus
    reason: str


@dataclass(frozen=True)
class TradingSignal:
    ticker: str
    status: DecisionStatus
    score: float
    entry_price: float | None
    stop_price: float | None
    tp1_price: float | None
    tp2_price: float | None
    reason: str
    