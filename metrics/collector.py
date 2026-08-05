from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from threading import Lock
from time import perf_counter
from typing import Callable


@dataclass(frozen=True)
class MetricSnapshot:
    name: str
    count: int
    total_seconds: float
    average_seconds: float
    minimum_seconds: float
    maximum_seconds: float


class MetricsCollector:
    def __init__(self) -> None:
        self._lock = Lock()
        self._metrics: dict[str, list[float]] = {}

    def record(
        self,
        metric_name: str,
        duration_seconds: float,
    ) -> None:
        if duration_seconds < 0:
            raise ValueError(
                "duration_seconds must be >= 0"
            )

        with self._lock:
            self._metrics.setdefault(
                metric_name,
                [],
            ).append(duration_seconds)

    def measure(
        self,
        metric_name: str,
        func: Callable,
        *args,
        **kwargs,
    ):
        started = perf_counter()

        try:
            return func(
                *args,
                **kwargs,
            )

        finally:
            self.record(
                metric_name,
                perf_counter() - started,
            )

    def snapshot(
        self,
        metric_name: str,
    ) -> MetricSnapshot | None:
        values = self._metrics.get(
            metric_name,
        )

        if not values:
            return None

        return MetricSnapshot(
            name=metric_name,
            count=len(values),
            total_seconds=round(
                sum(values),
                6,
            ),
            average_seconds=round(
                mean(values),
                6,
            ),
            minimum_seconds=round(
                min(values),
                6,
            ),
            maximum_seconds=round(
                max(values),
                6,
            ),
        )

    def snapshot_all(
        self,
    ) -> tuple[MetricSnapshot, ...]:
        snapshots = []

        for metric_name in sorted(
            self._metrics,
        ):
            snapshot = self.snapshot(
                metric_name,
            )

            if snapshot is not None:
                snapshots.append(
                    snapshot
                )

        return tuple(snapshots)

    def clear(self) -> None:
        with self._lock:
            self._metrics.clear()


metrics = MetricsCollector()
