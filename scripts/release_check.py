from __future__ import annotations

import compileall
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


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

    project_root_text = str(PROJECT_ROOT)

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
        print(f"{title}: FAILED")
        return False

    print(f"{title}: PASSED")
    return True


def check_compilation() -> bool:
    print("\n=== Python Compilation Check ===")

    directories = [
        PROJECT_ROOT / "api",
        PROJECT_ROOT / "config",
        PROJECT_ROOT / "database",
        PROJECT_ROOT / "earnings",
        PROJECT_ROOT / "engines",
        PROJECT_ROOT / "importer",
        PROJECT_ROOT / "providers",
        PROJECT_ROOT / "scanner",
        PROJECT_ROOT / "scheduler",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "tests",
    ]

    success = True

    for directory in directories:
        if not directory.exists():
            print(
                f"Missing directory: {directory}"
            )
            success = False
            continue

        compiled = compileall.compile_dir(
            str(directory),
            quiet=1,
        )

        if not compiled:
            print(
                f"Compilation failed: {directory}"
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
    print("\n=== Core Import Check ===")

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(
            0,
            str(PROJECT_ROOT),
        )

    try:
        from earnings.audit_engine import (
            create_audit_record,
        )
        from earnings.backtest_engine import (
            run_backtest,
        )
        from earnings.earnings_engine import (
            analyze_earnings_cycles,
        )
        from earnings.error_engine import (
            execute_safely,
        )
        from earnings.replay_engine import (
            replay_audit_record,
        )
        from earnings.report_engine import (
            build_report,
        )
        from earnings.validation_engine import (
            validate_analysis_input,
        )
        from engines.base_engine import (
            BaseEngine,
            EngineResult,
        )
        from engines.gap_engine import (
            GapEngine,
        )
        from engines.volume_engine import (
            VolumeEngine,
        )
        from providers.market_provider import (
            MarketProvider,
        )
        from scanner.context import (
            MarketContext,
            VolumeContext,
        )
        from scanner.scanner_engine import (
            MarketScanner,
        )

        required_objects = [
            create_audit_record,
            run_backtest,
            analyze_earnings_cycles,
            execute_safely,
            replay_audit_record,
            build_report,
            validate_analysis_input,
            BaseEngine,
            EngineResult,
            GapEngine,
            VolumeEngine,
            MarketProvider,
            MarketContext,
            VolumeContext,
            MarketScanner,
        ]

        if any(
            item is None
            for item in required_objects
        ):
            raise ImportError(
                "A required object is unavailable"
            )

    except ImportError as error:
        print(
            f"Core Import Check: FAILED: {error}"
        )
        return False

    print("Core Import Check: PASSED")
    return True


def main() -> int:
    print("IDB PRIME - RELEASE CHECK")

    checks = [
        check_compilation(),
        check_core_imports(),
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
    raise SystemExit(main())
    