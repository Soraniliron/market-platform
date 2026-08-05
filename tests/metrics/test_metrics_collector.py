from __future__ import annotations

import time

import pytest

from metrics.collector import MetricsCollector


def test_record_and_snapshot() -> None:
    collector = MetricsCollector()

    collector.record(
        "scanner",
        0.10,
    )

    collector.record(
        "scanner",
        0.30,
    )

    snapshot = collector.snapshot(
        "scanner",
    )

    assert snapshot is not None
    assert snapshot.name == "scanner"
    assert snapshot.count == 2
    assert snapshot.total_seconds == 0.4
    assert snapshot.average_seconds == 0.2
    assert snapshot.minimum_seconds == 0.1
    assert snapshot.maximum_seconds == 0.3


def test_measure_records_execution_time() -> None:
    collector = MetricsCollector()

    def sample() -> int:
        time.sleep(0.01)
        return 42

    result = collector.measure(
        "pipeline",
        sample,
    )

    assert result == 42

    snapshot = collector.snapshot(
        "pipeline",
    )

    assert snapshot is not None
    assert snapshot.count == 1
    assert snapshot.total_seconds > 0


def test_snapshot_all_returns_sorted_metrics() -> None:
    collector = MetricsCollector()

    collector.record(
        "risk",
        0.2,
    )

    collector.record(
        "scanner",
        0.1,
    )

    snapshots = collector.snapshot_all()

    assert len(snapshots) == 2
    assert snapshots[0].name == "risk"
    assert snapshots[1].name == "scanner"


def test_clear_removes_metrics() -> None:
    collector = MetricsCollector()

    collector.record(
        "scanner",
        0.1,
    )

    collector.clear()

    assert collector.snapshot(
        "scanner",
    ) is None


def test_negative_duration_rejected() -> None:
    collector = MetricsCollector()

    with pytest.raises(
        ValueError,
    ):
        collector.record(
            "scanner",
            -1.0,
        )
        