from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from config.home_list import HOME_LIST
from providers.market_provider import MarketProvider
from scanner.models import MarketSnapshot, ScanResult, ScanStatus


class MarketScanner:
    def __init__(
        self,
        provider: MarketProvider | None = None,
        home_list: Iterable[str] | None = None,
    ) -> None:
        self.provider = provider or MarketProvider()
        self.home_list = list(home_list or HOME_LIST)

    def scan_ticker(
        self,
        ticker: str,
        timeframe_minutes: int,
        start_date: date | datetime,
        end_date: date | datetime,
    ) -> ScanResult:
        bars = self.provider.get_bars(
            ticker=ticker,
            timeframe_minutes=timeframe_minutes,
            start_date=start_date,
            end_date=end_date,
        )
        previous_close_data = self.provider.get_previous_close(ticker=ticker)

        snapshot = self._build_snapshot(
            ticker=ticker,
            timeframe_minutes=timeframe_minutes,
            bars=bars,
            previous_close_data=previous_close_data,
        )

        return self._classify(snapshot)

    def scan_home_list(
        self,
        timeframe_minutes: int,
        start_date: date | datetime,
        end_date: date | datetime,
    ) -> list[ScanResult]:
        results: list[ScanResult] = []

        for ticker in self.home_list:
            try:
                result = self.scan_ticker(
                    ticker=ticker,
                    timeframe_minutes=timeframe_minutes,
                    start_date=start_date,
                    end_date=end_date,
                )
            except (ValueError, RuntimeError, KeyError, TypeError):
                result = ScanResult(
                    ticker=ticker,
                    status=ScanStatus.REJECTED,
                    score=0.0,
                    price=0.0,
                    change_percent=0.0,
                    volume=0.0,
                    vwap=None,
                    above_vwap=None,
                    reason="Market data unavailable or invalid",
                )

            results.append(result)

        return sorted(
            results,
            key=lambda item: item.score,
            reverse=True,
        )

    @staticmethod
    def _build_snapshot(
        ticker: str,
        timeframe_minutes: int,
        bars: list[dict],
        previous_close_data: list[dict],
    ) -> MarketSnapshot:
        if not bars:
            raise ValueError(f"No bars returned for {ticker}")

        if not previous_close_data:
            raise ValueError(f"No previous close returned for {ticker}")

        latest_bar = bars[-1]
        previous_close_row = previous_close_data[0]

        price = float(latest_bar["c"])
        previous_close = float(previous_close_row["c"])

        if previous_close <= 0:
            raise ValueError(f"Invalid previous close for {ticker}")

        change_percent = ((price - previous_close) / previous_close) * 100

        raw_vwap = latest_bar.get("vw")
        vwap = float(raw_vwap) if raw_vwap is not None else None

        return MarketSnapshot(
            ticker=ticker.upper(),
            price=price,
            previous_close=previous_close,
            change_percent=change_percent,
            volume=float(latest_bar.get("v", 0.0)),
            vwap=vwap,
            high=float(latest_bar["h"]),
            low=float(latest_bar["l"]),
            timeframe_minutes=timeframe_minutes,
        )

    @staticmethod
    def _classify(snapshot: MarketSnapshot) -> ScanResult:
        above_vwap = (
            snapshot.price >= snapshot.vwap
            if snapshot.vwap is not None
            else None
        )

        score = 50.0

        if snapshot.change_percent >= 2.0:
            score += 30.0
        elif snapshot.change_percent >= 1.0:
            score += 20.0
        elif snapshot.change_percent >= 0.25:
            score += 10.0
        elif snapshot.change_percent <= -2.0:
            score -= 30.0
        elif snapshot.change_percent <= -1.0:
            score -= 20.0
        elif snapshot.change_percent <= -0.25:
            score -= 10.0

        if above_vwap is True:
            score += 10.0
        elif above_vwap is False:
            score -= 10.0

        score = max(0.0, min(score, 100.0))

        if score >= 80.0:
            status = ScanStatus.STRONG
            reason = "Strong price change with VWAP support"
        elif score >= 65.0:
            status = ScanStatus.POSITIVE
            reason = "Positive momentum"
        elif score >= 40.0:
            status = ScanStatus.NEUTRAL
            reason = "No decisive momentum"
        else:
            status = ScanStatus.WEAK
            reason = "Weak price action"

        return ScanResult(
            ticker=snapshot.ticker,
            status=status,
            score=score,
            price=snapshot.price,
            change_percent=round(snapshot.change_percent, 4),
            volume=snapshot.volume,
            vwap=snapshot.vwap,
            above_vwap=above_vwap,
            reason=reason,
        )
        