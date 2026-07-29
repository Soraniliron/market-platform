from dataclasses import asdict, dataclass

from earnings.earnings_engine import EarningsEngineResult


@dataclass(frozen=True)
class EarningsReport:
    ticker: str

    entry_price: float
    exit_price: float

    entry_probability: float
    exit_probability: float

    production_ready: bool
    sample_status: str

    entry_percentile: float
    exit_percentile: float

    average_drop_pct: float
    median_drop_pct: float

    average_rebound_pct: float
    median_rebound_pct: float


def build_report(
    result: EarningsEngineResult,
) -> EarningsReport:
    return EarningsReport(
        ticker=result.ticker,
        entry_price=result.selected_entry.entry_price,
        exit_price=result.selected_exit.exit_price,
        entry_probability=(
            result.selected_entry.entry_probability
        ),
        exit_probability=(
            result.selected_exit.target_probability_after_entry
        ),
        production_ready=result.production_ready,
        sample_status=result.sample_status,
        entry_percentile=(
            result.selected_entry_percentile * 100
        ),
        exit_percentile=(
            result.selected_exit_percentile * 100
        ),
        average_drop_pct=(
            result.statistics.average_drop_pct
        ),
        median_drop_pct=(
            result.statistics.median_drop_pct
        ),
        average_rebound_pct=(
            result.statistics.average_rebound_pct
        ),
        median_rebound_pct=(
            result.statistics.median_rebound_pct
        ),
    )


def report_to_dict(
    report: EarningsReport,
) -> dict:
    return asdict(report)


def format_report_text(
    report: EarningsReport,
) -> str:
    readiness = (
        "READY"
        if report.production_ready
        else "NOT READY"
    )

    return (
        f"IDB PRIME LONG - {report.ticker}\n"
        f"Entry: {report.entry_price:.2f}\n"
        f"Exit: {report.exit_price:.2f}\n"
        f"Entry probability: "
        f"{report.entry_probability:.2f}%\n"
        f"Exit probability after entry: "
        f"{report.exit_probability:.2f}%\n"
        f"Entry percentile: "
        f"{report.entry_percentile:.0f}%\n"
        f"Exit percentile: "
        f"{report.exit_percentile:.0f}%\n"
        f"Sample status: {report.sample_status}\n"
        f"Production: {readiness}"
    )
