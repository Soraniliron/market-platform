from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class EarningsEvent:
    ticker: str
    report_date: date
    report_time: Optional[str] = None


@dataclass(frozen=True)
class EarningsCycle:
    ticker: str
    report_date: date
    next_report_date: date
    day_zero_close: float
    cycle_low: float
    cycle_low_date: date
    days_to_low: int
    max_rebound_price: float
    max_rebound_date: date
    days_low_to_rebound: int
    days_report_to_rebound: int


@dataclass(frozen=True)
class EarningsCycleResult:
    ticker: str
    cycles_count: int
    average_drop_pct: float
    median_drop_pct: float
    average_days_to_low: float
    median_days_to_low: float
    average_rebound_pct: float
    median_rebound_pct: float
    average_days_to_rebound: float
    median_days_to_rebound: float


@dataclass(frozen=True)
class EarningsAnalysisResult:
    ticker: str
    cycles_count: int

    entry_drop_pct: float
    entry_price: float

    target_return_pct: float
    exit_price: float

    entry_hits: int
    target_hits_after_entry: int
    full_cycle_hits: int

    entry_probability: float
    target_probability_after_entry: float
    full_cycle_probability: float

    average_days_to_entry: float
    median_days_to_entry: float

    average_days_entry_to_exit: float
    median_days_entry_to_exit: float

    average_days_report_to_exit: float
    median_days_report_to_exit: float


@dataclass(frozen=True)
class EntryPercentileLevel:
    percentile: float
    entry_drop_pct: float
    entry_price: float
    entry_hits: int
    entry_probability: float


@dataclass(frozen=True)
class EntryPercentileResult:
    ticker: str
    cycles_count: int
    reference_price: float

    minimum_cycles_required: int
    production_ready: bool
    sample_status: str

    p50: EntryPercentileLevel
    p55: EntryPercentileLevel
    p60: EntryPercentileLevel
    p65: EntryPercentileLevel
    p70: EntryPercentileLevel
    p80: EntryPercentileLevel
    p90: EntryPercentileLevel


@dataclass(frozen=True)
class ExitPercentileLevel:
    percentile: float

    target_return_pct: float
    exit_price: float

    entry_hits: int
    target_hits_after_entry: int

    target_probability_after_entry: float
    full_cycle_probability: float

    average_days_entry_to_exit: float
    median_days_entry_to_exit: float

    average_days_report_to_exit: float
    median_days_report_to_exit: float


@dataclass(frozen=True)
class ExitPercentileResult:
    ticker: str
    cycles_count: int

    entry_drop_pct: float
    reference_price: float
    entry_price: float

    minimum_cycles_required: int
    production_ready: bool
    sample_status: str

    p50: ExitPercentileLevel
    p55: ExitPercentileLevel
    p60: ExitPercentileLevel
    p65: ExitPercentileLevel
    p70: ExitPercentileLevel
    p80: ExitPercentileLevel
    p90: ExitPercentileLevel
