from __future__ import annotations

from health.monitor import (
    HealthCheckResult,
    HealthMonitor,
)


def test_all_checks_healthy() -> None:
    monitor = HealthMonitor(
        database_check=lambda: HealthCheckResult(
            component="database",
            healthy=True,
            status="ok",
            details={},
        ),
        scheduler_check=lambda: HealthCheckResult(
            component="scheduler",
            healthy=True,
            status="running",
            details={},
        ),
    )

    report = monitor.check_all()

    assert report.healthy is True
    assert report.status == "healthy"
    assert len(report.checks) == 5


def test_database_failure_marks_system_unhealthy() -> None:
    monitor = HealthMonitor(
        database_check=lambda: HealthCheckResult(
            component="database",
            healthy=False,
            status="failed",
            details={
                "error": "connection failed",
            },
        ),
        scheduler_check=lambda: HealthCheckResult(
            component="scheduler",
            healthy=True,
            status="running",
            details={},
        ),
    )

    report = monitor.check_all()

    assert report.healthy is False
    assert report.status == "degraded"


def test_report_to_dict() -> None:
    monitor = HealthMonitor(
        database_check=lambda: HealthCheckResult(
            component="database",
            healthy=True,
            status="ok",
            details={},
        ),
        scheduler_check=lambda: HealthCheckResult(
            component="scheduler",
            healthy=True,
            status="running",
            details={},
        ),
    )

    report = monitor.check_all()

    payload = report.to_dict()

    assert payload["healthy"] is True
    assert payload["status"] == "healthy"
    assert "checked_at" in payload
    assert len(payload["checks"]) == 5
    