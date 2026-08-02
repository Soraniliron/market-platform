from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from scanner.context import MarketContext
from scanner.models import MarketSnapshot


@dataclass(frozen=True)
class EngineResult:
    engine: str
    score: float
    passed: bool
    reason: str


class BaseEngine(ABC):
    name: str

    @abstractmethod
    def evaluate(
        self,
        snapshot: MarketSnapshot,
        context: MarketContext | None = None,
    ) -> EngineResult:
        """Evaluate one market snapshot."""
        raise NotImplementedError
        