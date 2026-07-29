from datetime import date, timedelta
from pathlib import Path

import pytest

from earnings.core_api import analyze_stock
from earnings.models import EarningsCycle


def build_cycles(
    ticker: str,
    count: int = 12,
) -> list[EarningsCycle]:
    cycles: list[EarningsCycle] = []
    base_date = date(2023, 1, 1)

    for index in range(count):
        report_date = (
            base_date
            + timedelta(days=index * 90)
        )

        next_report_date = (
            report_date
            + timedelta(days=90)
        )

        day_zero_close = 100.0 + index
        cycle_low = day_zero_close * 0.90

        cycle_low_date = (
            report_date
            + timedelta(days=10)
        )

        max_rebound_price = (
            cycle_low * 1.15
        )

        max_rebound_date = (
            cycle_low_date
            + timedelta(days=20)
        )

        cycles.append(
            EarningsCycle(
                ticker=ticker,
                report_date=report_date,
                next_report_date=next_report_date,
                day_zero_close=day_zero_close,
                cycle_low=cycle_low,
                cycle_low_date=cycle_low_date,
                days_to_low=10,
                max_rebound_price=max_rebound_price,
                max_rebound_date=max_rebound_date,
                days_low_to_rebound=20,
                days_report_to_rebound=30,
            )
        )

    return cycles


def build_mock_price_history(
    ticker: str,
    start_date: date,
    end_date: date,
) -> list[dict]:
    prices: list[dict] = []
    current_date = start_date
    day_index = 0

    while current_date <= end_date:
        if day_index < 10:
            close_price = 100.0 - day_index
        else:
            close_price = 90.0 + (
                (day_index - 10) * 1.5
            )

        prices.append(
            {
                "ticker": ticker,
                "date": current_date,
                "open": close_price,
                "high": close_price + 2.0,
                "low": close_price - 2.0,
                "close": close_price,
                "volume": 1_000_000,
            }
        )

        current_date += timedelta(days=1)
        day_index += 1

    return prices


@pytest.fixture
def mock_price_history(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "earnings.exit_engine.get_price_history",
        build_mock_price_history,
    )


def test_analyze_stock_success(
    mock_price_history,
    tmp_path: Path,
) -> None:
    audit_path = (
        tmp_path
        / "audit"
        / "earnings.jsonl"
    )

    response = analyze_stock(
        ticker="msft",
        cycles=build_cycles(
            ticker="MSFT",
            count=12,
        ),
        reference_price=120.0,
        audit_path=audit_path,
    )

    assert response.success is True
    assert response.error is None
    assert response.data is not None

    assert response.data["ticker"] == "MSFT"
    assert response.data["cycles_count"] == 12
    assert (
        response.data["production_ready"]
        is True
    )

    assert response.data["report"]["ticker"] == (
        "MSFT"
    )

    assert (
        response.data["report"]["entry_price"]
        > 0
    )

    assert (
        response.data["report"]["exit_price"]
        > response.data["report"]["entry_price"]
    )

    assert (
        response.data["audit"]["status"]
        == "SUCCESS"
    )

    assert audit_path.exists()
    assert audit_path.read_text(
        encoding="utf-8"
    ).strip()


def test_analyze_stock_without_audit_file(
    mock_price_history,
) -> None:
    response = analyze_stock(
        ticker="JPM",
        cycles=build_cycles(
            ticker="JPM",
            count=12,
        ),
        reference_price=200.0,
        audit_path=None,
    )

    assert response.success is True
    assert response.data is not None
    assert response.data["ticker"] == "JPM"
    assert "audit" in response.data


def test_analyze_stock_rejects_empty_ticker() -> None:
    response = analyze_stock(
        ticker="",
        cycles=[],
        audit_path=None,
    )

    assert response.success is False
    assert response.data is None
    assert response.error is not None
    assert (
        response.error.code
        == "VALIDATION_ERROR"
    )


def test_analyze_stock_rejects_ticker_mismatch(
    mock_price_history,
) -> None:
    response = analyze_stock(
        ticker="JPM",
        cycles=build_cycles(
            ticker="MSFT",
            count=12,
        ),
        audit_path=None,
    )

    assert response.success is False
    assert response.data is None
    assert response.error is not None
    assert (
        response.error.code
        == "VALIDATION_ERROR"
    )
    assert "does not match JPM" in (
        response.error.message
    )


def test_analyze_stock_not_production_ready(
    mock_price_history,
) -> None:
    response = analyze_stock(
        ticker="BAC",
        cycles=build_cycles(
            ticker="BAC",
            count=5,
        ),
        reference_price=70.0,
        minimum_cycles_required=12,
        audit_path=None,
    )

    assert response.success is True
    assert response.data is not None
    assert (
        response.data["production_ready"]
        is False
    )
