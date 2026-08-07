from __future__ import annotations

import compileall
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


PRODUCTION_DIRECTORIES = (
    "api",
    "config",
    "database",
    "decision",
    "earnings",
    "engines",
    "execution",
    "health",
    "importer",
    "integration",
    "logs",
    "metrics",
    "notifications",
    "providers",
    "scanner",
    "scheduler",
    "scripts",
    "signals",
    "tracking",
    "tests",
)


def run_command(
    command: list[str],
    title: str,
) -> bool:
    print(f"\n=== {title} ===")

    environment = os.environ.copy()

    existing_pythonpath = environment.get(
        "PYTHONPATH",
        "",
    )

    project_root_text = str(
        PROJECT_ROOT
    )

    environment["PYTHONPATH"] = (
        project_root_text
        if not existing_pythonpath
        else (
            f"{project_root_text}"
            f"{os.pathsep}"
            f"{existing_pythonpath}"
        )
    )

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
    )

    if result.returncode != 0:
        print(
            f"{title}: FAILED"
        )
        return False

    print(
        f"{title}: PASSED"
    )
    return True


def check_project_structure() -> bool:
    print(
        "\n=== Project Structure Check ==="
    )

    missing = []

    for directory_name in (
        PRODUCTION_DIRECTORIES
    ):
        directory = (
            PROJECT_ROOT
            / directory_name
        )

        if not directory.exists():
            missing.append(
                directory_name
            )

    if missing:
        for directory_name in missing:
            print(
                "Missing directory: "
                f"{directory_name}"
            )

        print(
            "Project Structure Check: FAILED"
        )
        return False

    print(
        "Project Structure Check: PASSED"
    )
    return True


def check_compilation() -> bool:
    print(
        "\n=== Python Compilation Check ==="
    )

    success = True

    for directory_name in (
        PRODUCTION_DIRECTORIES
    ):
        directory = (
            PROJECT_ROOT
            / directory_name
        )

        if not directory.exists():
            print(
                f"Missing directory: "
                f"{directory}"
            )
            success = False
            continue

        compiled = (
            compileall.compile_dir(
                str(directory),
                quiet=1,
            )
        )

        if not compiled:
            print(
                "Compilation failed: "
                f"{directory}"
            )
            success = False

    if success:
        print(
            "Python Compilation Check: PASSED"
        )
    else:
        print(
            "Python Compilation Check: FAILED"
        )

    return success


def check_core_imports() -> bool:
    print(
        "\n=== Core Import Check ==="
    )

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(
            0,
            str(PROJECT_ROOT),
        )

    try:
        from decision.decision_engine import (
            DecisionEngine,
        )
        from decision.ranking_engine import (
            RankingEngine,
        )
        from engines.chart_quality_engine import (
            ChartQualityEngine,
        )
        from engines.gap_engine import (
            GapEngine,
        )
        from engines.index_engine import (
            IndexEngine,
        )
        from engines.volume_engine import (
            VolumeEngine,
        )
        from engines.vwap_engine import (
            VWAPEngine,
        )
        from execution.entry_engine import (
            EntryEngine,
        )
        from execution.invalidation_engine import (
            InvalidationEngine,
        )
        from execution.overshoot_engine import (
            OvershootEngine,
        )
        from execution.reassessment_engine import (
            ReassessmentEngine,
        )
        from execution.risk_engine import (
            RiskEngine,
        )
        from health.monitor import (
            HealthMonitor,
        )
        from integration.pipeline import (
            ManualTradingPipeline,
        )
        from metrics.collector import (
            MetricsCollector,
        )
        from notifications.notification_service import (
            NotificationService,
        )
        from providers.market_provider import (
            MarketProvider,
        )
        from scanner.scanner_engine import (
            MarketScanner,
        )
        from scheduler.jobs import (
            AutoScanJob,
        )
        from scheduler.report_generator import (
            ReportGenerator,
        )
        from scheduler.signal_guard import (
            DuplicateSignalGuard,
        )
        from signals.signal_builder import (
            SignalBuilder,
        )
        from tracking.audit_engine import (
            AuditEngine,
        )
        from tracking.performance_engine import (
            PerformanceEngine,
        )
        from tracking.replay_engine import (
            ReplayEngine,
        )

        required_objects = [
            DecisionEngine,
            RankingEngine,
            ChartQualityEngine,
            GapEngine,
            IndexEngine,
            VolumeEngine,
            VWAPEngine,
            EntryEngine,
            InvalidationEngine,
            OvershootEngine,
            ReassessmentEngine,
            RiskEngine,
            HealthMonitor,
            ManualTradingPipeline,
            MetricsCollector,
            NotificationService,
            MarketProvider,
            MarketScanner,
            AutoScanJob,
            ReportGenerator,
            DuplicateSignalGuard,
            SignalBuilder,
            AuditEngine,
            PerformanceEngine,
            ReplayEngine,
        ]

        if any(
            item is None
            for item in required_objects
        ):
            raise ImportError(
                "A required core object "
                "is unavailable"
            )

    except (
        ImportError,
        AttributeError,
    ) as error:
        print(
            "Core Import Check: FAILED: "
            f"{error}"
        )
        return False

    print(
        "Core Import Check: PASSED"
    )
    return True


def check_configuration() -> bool:
    print(
        "\n=== Configuration Check ==="
    )

    try:
        from config.settings import (
            APP_MODE,
            LOG_LEVEL,
            MAX_DAILY_CANDIDATES,
            REQUEST_TIMEOUT_SECONDS,
            SCHEDULER_INTERVAL_SECONDS,
        )

        if APP_MODE not in {
            "mock",
            "live",
        }:
            raise ValueError(
                "APP_MODE must be "
                "'mock' or 'live'"
            )

        if not LOG_LEVEL:
            raise ValueError(
                "LOG_LEVEL must not be empty"
            )

        if (
            REQUEST_TIMEOUT_SECONDS
            < 1
        ):
            raise ValueError(
                "REQUEST_TIMEOUT_SECONDS "
                "must be at least one"
            )

        if (
            SCHEDULER_INTERVAL_SECONDS
            < 1
        ):
            raise ValueError(
                "SCHEDULER_INTERVAL_SECONDS "
                "must be at least one"
            )

        if (
            MAX_DAILY_CANDIDATES
            < 1
        ):
            raise ValueError(
                "MAX_DAILY_CANDIDATES "
                "must be at least one"
            )

    except Exception as error:
        print(
            "Configuration Check: FAILED: "
            f"{error}"
        )
        return False

    print(
        "Configuration Check: PASSED"
    )
    return True


def main() -> int:
    print(
        "IDB PRIME - RELEASE CHECK"
    )

    checks = [
        check_project_structure(),
        check_compilation(),
        check_core_imports(),
        check_configuration(),
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
            ],
            "Full Test Suite",
        ),
    ]

    if all(checks):
        print(
            "\nRELEASE CHECK: PASSED"
        )
        return 0

    print(
        "\nRELEASE CHECK: FAILED"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
    