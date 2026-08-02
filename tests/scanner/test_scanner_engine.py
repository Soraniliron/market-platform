from __future__ import annotations

from datetime import date

import pytest

from scanner.context import (
    MarketContext,
    VolumeContext,
)
from scanner.models import ScanStatus
from scanner.scanner_engine import MarketScanner


class FakeProvider:
    def __init__(
        self,
        bars_by_ticker: dict[str, list[dict]],
        previous_close_by_ticker: dict[str, list[dict]],
    ) -> None:
        self.bars_by_ticker = bars_by_ticker
        self.previous_close_by_ticker = (
            previous_close_by_ticker
        )

    def get_bars(
        self,
        ticker: str,
        timeframe_minutes: int,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        return self.bars_by_ticker[ticker]

    def get_previous_close(
        self,
        ticker: str,
    ) -> list[dict]:
        return self.previous_close_by_ticker[
            ticker
        ]


def build_strong_context() -> MarketContext:
    return MarketContext(
        volume=VolumeContext(
            current_volume=500_000,
            average_volume_same_window=250_000,
            previous_window_volume=300_000,
        )
    )


def build_weak_context() -> MarketContext:
    return MarketContext(
        volume=VolumeContext(
            current_volume=200_000,
            average_volume_same_window=500_000,
            previous_window_volume=400_000,
        )
    )


def test_scan_ticker_returns_strong_result() -> None:
    provider = FakeProvider(
        bars_by_ticker={
            "META": [
                {
                    "o": 103.0,
                    "c": 103.0,
                    "h": 104.0,
                    "l": 101.0,
                    "v": 500_000,
                    "vw": 102.0,
                }
            ]
        },
        previous_close_by_ticker={
            "META": [
                {
                    "c": 100.0,
                }
            ]
        },
    )

    scanner = MarketScanner(
        provider=provider,
        home_list=["META"],
    )

    result = scanner.scan_ticker(
        ticker="META",
        timeframe_minutes=15,
        start_date=date(2026, 7, 30),
        end_date=date(2026, 7, 30),
        context=build_strong_context(),
    )

    assert result.ticker == "META"
    assert result.status == ScanStatus.STRONG
    assert result.score == 95.0
    assert result.change_percent == 3.0
    assert result.above_vwap is True
    assert "gap:" in result.reason
    assert "volume:" in result.reason


def test_scan_ticker_returns_weak_result() -> None:
    provider = FakeProvider(
        bars_by_ticker={
            "PLTR": [
                {
                    "o": 97.0,
                    "c": 97.0,
                    "h": 99.0,
                    "l": 96.0,
                    "v": 200_000,
                    "vw": 98.0,
                }
            ]
        },
        previous_close_by_ticker={
            "PLTR": [
                {
                    "c": 100.0,
                }
            ]
        },
    )

    scanner = MarketScanner(
        provider=provider,
        home_list=["PLTR"],
    )

    result = scanner.scan_ticker(
        ticker="PLTR",
        timeframe_minutes=15,
        start_date=date(2026, 7, 30),
        end_date=date(2026, 7, 30),
        context=build_weak_context(),
    )

    assert result.status == ScanStatus.WEAK
    assert result.score == 15.0
    assert result.change_percent == -3.0
    assert result.above_vwap is False


def test_scan_home_list_sorts_by_score_descending() -> None:
    provider = FakeProvider(
        bars_by_ticker={
            "META": [
                {
                    "o": 103.0,
                    "c": 103.0,
                    "h": 104.0,
                    "l": 101.0,
                    "v": 500_000,
                    "vw": 102.0,
                }
            ],
            "MSFT": [
                {
                    "o": 100.5,
                    "c": 100.5,
                    "h": 101.0,
                    "l": 99.5,
                    "v": 250_000,
                    "vw": 100.0,
                }
            ],
        },
        previous_close_by_ticker={
            "META": [
                {
                    "c": 100.0,
                }
            ],
            "MSFT": [
                {
                    "c": 100.0,
                }
            ],
        },
    )

    scanner = MarketScanner(
        provider=provider,
        home_list=["MSFT", "META"],
    )

    contexts = {
        "META": build_strong_context(),
        "MSFT": MarketContext(
            volume=VolumeContext(
                current_volume=250_000,
                average_volume_same_window=250_000,
                previous_window_volume=250_000,
            )
        ),
    }

    results = scanner.scan_home_list(
        timeframe_minutes=15,
        start_date=date(2026, 7, 30),
        end_date=date(2026, 7, 30),
        contexts=contexts,
    )

    assert [
        result.ticker
        for result in results
    ] == [
        "META",
        "MSFT",
    ]

    assert results[0].score > results[1].score


def test_scan_home_list_rejects_invalid_market_data() -> None:
    provider = FakeProvider(
        bars_by_ticker={
            "META": [],
        },
        previous_close_by_ticker={
            "META": [
                {
                    "c": 100.0,
                }
            ],
        },
    )

    scanner = MarketScanner(
        provider=provider,
        home_list=["META"],
    )

    results = scanner.scan_home_list(
        timeframe_minutes=15,
        start_date=date(2026, 7, 30),
        end_date=date(2026, 7, 30),
    )

    assert len(results) == 1
    assert (
        results[0].status
        == ScanStatus.REJECTED
    )
    assert results[0].score == 0.0


@pytest.mark.parametrize(
    (
        "timeframe_minutes",
        "expected_timeframe",
    ),
    [
        (1, 1),
        (5, 5),
        (15, 15),
    ],
)
def test_build_snapshot_supports_expected_timeframes(
    timeframe_minutes: int,
    expected_timeframe: int,
) -> None:
    snapshot = MarketScanner._build_snapshot(
        ticker="AAPL",
        timeframe_minutes=timeframe_minutes,
        bars=[
            {
                "o": 100.25,
                "c": 101.0,
                "h": 102.0,
                "l": 99.0,
                "v": 200_000,
                "vw": 100.5,
            }
        ],
        previous_close_data=[
            {
                "c": 100.0,
            }
        ],
    )

    assert (
        snapshot.timeframe_minutes
        == expected_timeframe
    )
    assert snapshot.open_price == 100.25


def test_scan_ticker_without_volume_context() -> None:
    provider = FakeProvider(
        bars_by_ticker={
            "AAPL": [
                {
                    "o": 101.0,
                    "c": 101.5,
                    "h": 102.0,
                    "l": 100.5,
                    "v": 200_000,
                    "vw": 101.0,
                }
            ]
        },
        previous_close_by_ticker={
            "AAPL": [
                {
                    "c": 100.0,
                }
            ]
        },
    )

    scanner = MarketScanner(
        provider=provider,
        home_list=["AAPL"],
    )

    result = scanner.scan_ticker(
        ticker="AAPL",
        timeframe_minutes=5,
        start_date=date(2026, 7, 30),
        end_date=date(2026, 7, 30),
    )

    assert result.score == 62.5
    assert result.status == ScanStatus.NEUTRAL
    assert (
        "Volume context unavailable"
        in result.reason
    )
    
