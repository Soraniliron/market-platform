from dataclasses import asdict
from pathlib import Path
from typing import Optional

from earnings.audit_engine import (
    audit_record_to_dict,
    create_audit_record,
    save_audit_record,
)
from earnings.earnings_engine import (
    analyze_earnings_cycles,
)
from earnings.error_engine import (
    EngineResponse,
    execute_safely,
)
from earnings.models import EarningsCycle
from earnings.report_engine import (
    build_report,
    format_report_text,
    report_to_dict,
)
from earnings.validation_engine import (
    raise_for_validation,
    validate_analysis_input,
)


DEFAULT_AUDIT_PATH = Path(
    "data/audit/earnings_analysis.jsonl"
)


def _analyze_stock_handler(
    ticker: str,
    cycles: list[EarningsCycle],
    reference_price: Optional[float] = None,
    entry_percentile: float = 0.60,
    exit_percentile: float = 0.60,
    minimum_cycles_required: int = 12,
    audit_path: str | Path | None = (
        DEFAULT_AUDIT_PATH
    ),
) -> dict:
    normalized_ticker = ticker.strip().upper()

    validation_result = validate_analysis_input(
        ticker=normalized_ticker,
        cycles=cycles,
        entry_percentile=(
            entry_percentile * 100
        ),
        minimum_cycles=1,
    )

    raise_for_validation(
        validation_result
    )

    result = analyze_earnings_cycles(
        ticker=normalized_ticker,
        cycles=cycles,
        reference_price=reference_price,
        entry_percentile=entry_percentile,
        exit_percentile=exit_percentile,
        minimum_cycles_required=(
            minimum_cycles_required
        ),
    )

    report = build_report(result)

    output_data = {
        "ticker": normalized_ticker,
        "cycles_count": result.cycles_count,
        "production_ready": (
            result.production_ready
        ),
        "sample_status": result.sample_status,
        "report": report_to_dict(report),
        "report_text": format_report_text(
            report
        ),
        "selected_entry": asdict(
            result.selected_entry
        ),
        "selected_exit": asdict(
            result.selected_exit
        ),
        "statistics": asdict(
            result.statistics
        ),
    }

    audit_record = create_audit_record(
        ticker=normalized_ticker,
        event_type="EARNINGS_ANALYSIS",
        status="SUCCESS",
        input_data={
            "ticker": normalized_ticker,
            "cycles_count": len(cycles),
            "reference_price": (
                reference_price
            ),
            "entry_percentile": (
                entry_percentile
            ),
            "exit_percentile": (
                exit_percentile
            ),
            "minimum_cycles_required": (
                minimum_cycles_required
            ),
        },
        output_data=output_data,
        metadata={
            "engine": "IDB_PRIME_LONG",
            "api": "core_api",
        },
    )

    if audit_path is not None:
        save_audit_record(
            record=audit_record,
            file_path=audit_path,
        )

    output_data["audit"] = (
        audit_record_to_dict(
            audit_record
        )
    )

    return output_data


def analyze_stock(
    ticker: str,
    cycles: list[EarningsCycle],
    reference_price: Optional[float] = None,
    entry_percentile: float = 0.60,
    exit_percentile: float = 0.60,
    minimum_cycles_required: int = 12,
    audit_path: str | Path | None = (
        DEFAULT_AUDIT_PATH
    ),
) -> EngineResponse:
    return execute_safely(
        _analyze_stock_handler,
        ticker=ticker,
        cycles=cycles,
        reference_price=reference_price,
        entry_percentile=entry_percentile,
        exit_percentile=exit_percentile,
        minimum_cycles_required=(
            minimum_cycles_required
        ),
        audit_path=audit_path,
    )
