import compileall
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_command(
    command: list[str],
    title: str,
) -> bool:
    print(f"\n=== {title} ===")

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
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
        PROJECT_ROOT / "earnings",
        PROJECT_ROOT / "engines",
        PROJECT_ROOT / "database",
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

        required_objects = [
            create_audit_record,
            run_backtest,
            analyze_earnings_cycles,
            execute_safely,
            replay_audit_record,
            build_report,
            validate_analysis_input,
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
