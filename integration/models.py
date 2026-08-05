from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from decision.models import DecisionResult, TradingSignal
from execution.risk_engine import PositionSizeResult
from notifications.models import NotificationResult
from tracking.models import AuditRecord


@dataclass(frozen=True)
class PipelineResult:
    success: bool

    decision: DecisionResult | None
    signal: TradingSignal | None

    position_size: PositionSizeResult | None

    notification: NotificationResult | None

    audit_record: AuditRecord | None

    execution_time_seconds: float

    metadata: dict[str, Any]


class PipelineTimer:
    def __init__(self) -> None:
        self._started = perf_counter()

    def elapsed(self) -> float:
        return round(
            perf_counter() - self._started,
            6,
        )
        