from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AuditEvent(str, Enum):
    SCAN = "scan"
    RANKING = "ranking"
    DECISION = "decision"
    ENTRY = "entry"
    RISK = "risk"
    SIGNAL = "signal"
    EXIT = "exit"


class DecisionType(str, Enum):
    BUY = "buy"
    WATCH = "watch"
    WAIT = "wait"
    AVOID = "avoid"
    NO_TRADE = "no_trade"


class TradeResult(str, Enum):
    OPEN = "open"
    TP1 = "tp1"
    TP2 = "tp2"
    STOP = "stop"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    NO_ENTRY = "no_entry"


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    created_at: datetime

    ticker: str
    event: AuditEvent

    decision: DecisionType

    score: float

    entry_price: float | None
    stop_price: float | None
    tp1_price: float | None
    tp2_price: float | None

    reason: str

    input_data: dict
    output_data: dict


@dataclass(frozen=True)
class PerformanceRecord:
    ticker: str

    created_at: datetime

    decision: DecisionType

    result: TradeResult

    entry_price: float | None
    exit_price: float | None

    stop_price: float | None
    tp1_price: float | None
    tp2_price: float | None

    return_percent: float | None

    decision_score: float

    engine_scores: dict[str, float]

    selected_rank: int | None

    notes: str
    