from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable

from config.settings import (
    APP_MODE,
    EMAIL_ENABLED,
    EMAIL_FROM,
    EMAIL_TO,
    MASSIVE_API_KEY,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_USERNAME,
)
from database.connection import get_connection


@dataclass(frozen=True)
class HealthCheckResult:
    component: str
    healthy: bool
    status: str
    details: dict


@dataclass(frozen=True)
class SystemHealthReport:
    healthy: bool
    status: str
    checked_at: str
    app_mode: str
    checks: tuple[HealthCheckResult, ...]

    def to_dict(self) -> dict:
        return asdict(self)


class HealthMonitor:
    def __init__(
        self,
        database_check: Callable[
            [],
            HealthCheckResult,
        ]
        | None = None,
        scheduler_check: Callable[
            [],
            HealthCheckResult,
        ]
        | None = None,
    ) -> None:
        self.database_check = (
            database_check
            or self._check_database
        )

        self.scheduler_check = (
            scheduler_check
            or self._default_scheduler_check
        )

    def check_all(
        self,
    ) -> SystemHealthReport:
        checks = (
            self.database_check(),
            self.scheduler_check(),
            self._check_email(),
            self._check_market_provider(),
            self._check_application(),
        )

        healthy = all(
            check.healthy
            for check in checks
        )

        return SystemHealthReport(
            healthy=healthy,
            status=(
                "healthy"
                if healthy
                else "degraded"
            ),
            checked_at=datetime.now(
                timezone.utc
            ).isoformat(),
            app_mode=APP_MODE,
            checks=checks,
        )

    @staticmethod
    def _check_database() -> HealthCheckResult:
        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT 1;")
            row = cursor.fetchone()

            if row is None or row[0] != 1:
                return HealthCheckResult(
                    component="database",
                    healthy=False,
                    status="failed",
                    details={
                        "reason": (
                            "Unexpected database response"
                        ),
                    },
                )

            return HealthCheckResult(
                component="database",
                healthy=True,
                status="ok",
                details={
                    "query_result": row[0],
                },
            )

        except Exception as error:
            return HealthCheckResult(
                component="database",
                healthy=False,
                status="failed",
                details={
                    "error": str(error),
                },
            )

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

    @staticmethod
    def _default_scheduler_check() -> HealthCheckResult:
        return HealthCheckResult(
            component="scheduler",
            healthy=True,
            status="configured",
            details={
                "runtime_state": (
                    "not supplied to monitor"
                ),
            },
        )

    @staticmethod
    def _check_email() -> HealthCheckResult:
        if not EMAIL_ENABLED:
            return HealthCheckResult(
                component="email",
                healthy=True,
                status="disabled",
                details={
                    "enabled": False,
                },
            )

        missing = []

        if not SMTP_HOST:
            missing.append("SMTP_HOST")

        if not SMTP_USERNAME:
            missing.append("SMTP_USERNAME")

        if not SMTP_PASSWORD:
            missing.append("SMTP_PASSWORD")

        if not EMAIL_FROM:
            missing.append("EMAIL_FROM")

        if not EMAIL_TO:
            missing.append("EMAIL_TO")

        if missing:
            return HealthCheckResult(
                component="email",
                healthy=False,
                status="misconfigured",
                details={
                    "missing": missing,
                },
            )

        return HealthCheckResult(
            component="email",
            healthy=True,
            status="configured",
            details={
                "enabled": True,
                "smtp_host": SMTP_HOST,
                "sender": EMAIL_FROM,
                "recipients_count": len(
                    EMAIL_TO
                ),
            },
        )

    @staticmethod
    def _check_market_provider() -> HealthCheckResult:
        if APP_MODE == "mock":
            return HealthCheckResult(
                component="market_provider",
                healthy=True,
                status="mock",
                details={
                    "live_data": False,
                },
            )

        if not MASSIVE_API_KEY:
            return HealthCheckResult(
                component="market_provider",
                healthy=False,
                status="misconfigured",
                details={
                    "reason": (
                        "Missing market data API key"
                    ),
                },
            )

        return HealthCheckResult(
            component="market_provider",
            healthy=True,
            status="configured",
            details={
                "live_data": True,
            },
        )

    @staticmethod
    def _check_application() -> HealthCheckResult:
        return HealthCheckResult(
            component="application",
            healthy=True,
            status="ok",
            details={
                "app_mode": APP_MODE,
            },
        )
        