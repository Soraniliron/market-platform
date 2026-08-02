from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from config.home_list import HOME_LIST
from engines.base_engine import (
    BaseEngine,
    EngineResult,
)
from engines.gap_engine import GapEngine
from engines.volume_engine import VolumeEngine
from providers.market_provider import MarketProvider
from scanner.context import MarketContext
from scanner.models import (
    MarketSnapshot,
    ScanResult,
    ScanStatus,
)


class MarketScanner:
    def __init__(
        self,
        provider: MarketProvider | None = None,
        home_list: Iterable[str] | None = None,
        engines: list[BaseEngine] | None = None,
    ) -> None:
        self.provider = provider or MarketProvider()
        self.home_list = list(home_list or HOME_LIST)

        self.engines = (
            engines
            if engines is not None
            else [
                GapEngine(),
                VolumeEngine(),
            ]
        )

    def scan_ticker(
        self,
        ticker: str,
        timeframe_minutes: int,
        start_date: date | datetime,
        end_date: date | datetime,
        context: MarketContext | None = None,
    ) -> ScanResult:
        bars = self.provider.get_bars(
            ticker=ticker,
            timeframe_minutes=timeframe_minutes,
            start_date=start_date,
            end_date=end_date,
        )

        previous_close_data = (
            self.provider.get_previous_close(
                ticker=ticker,
            )
        )

        snapshot = self._build_snapshot(
            ticker=ticker,
            timeframe_minutes=timeframe_minutes,
            bars=bars,
            previous_close_data=previous_close_data,
        )

        return self._classify(
            snapshot=snapshot,
            context=context,
        )

    def scan_home_list(
        self,
        timeframe_minutes: int,
        start_date: date | datetime,
        end_date: date | datetime,
        contexts: dict[str, MarketContext] | None = None,
    ) -> list[ScanResult]:
        results: list[ScanResult] = []

        normalized_contexts = {
            ticker.upper(): context
            for ticker, context in (
                contexts or {}
            ).items()
        }

        for ticker in self.home_list:
            normalized_ticker = ticker.upper()

            try:
                result = self.scan_ticker(
                    ticker=normalized_ticker,
                    timeframe_minutes=timeframe_minutes,
                    start_date=start_date,
                    end_date=end_date,
                    context=normalized_contexts.get(
                        normalized_ticker
                    ),
                )
            except (
                ValueError,
                RuntimeError,
                KeyError,
                TypeError,
            ):
                result = ScanResult(
                    ticker=normalized_ticker,
                    status=ScanStatus.REJECTED,
                    score=0.0,
                    price=0.0,
                    change_percent=0.0,
                    volume=0.0,
                    vwap=None,
                    above_vwap=None,
                    reason=(
                        "Market data unavailable "
                        "or invalid"
                    ),
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
            raise ValueError(
                f"No bars returned for {ticker}"
            )

        if not previous_close_data:
            raise ValueError(
                f"No previous close returned "
                f"for {ticker}"
            )

        latest_bar = bars[-1]
        previous_close_row = (
            previous_close_data[0]
        )

        price = float(latest_bar["c"])
        open_price = float(latest_bar["o"])
        previous_close = float(
            previous_close_row["c"]
        )

        if price <= 0:
            raise ValueError(
                f"Invalid price for {ticker}"
            )

        if open_price <= 0:
            raise ValueError(
                f"Invalid open price for {ticker}"
            )

        if previous_close <= 0:
            raise ValueError(
                f"Invalid previous close "
                f"for {ticker}"
            )

        high = float(latest_bar["h"])
        low = float(latest_bar["l"])

        if high <= 0 or low <= 0:
            raise ValueError(
                f"Invalid price range for {ticker}"
            )

        if low > high:
            raise ValueError(
                f"Low exceeds high for {ticker}"
            )

        change_percent = (
            (price - previous_close)
            / previous_close
        ) * 100

        raw_vwap = latest_bar.get("vw")

        vwap = (
            float(raw_vwap)
            if raw_vwap is not None
            else None
        )

        return MarketSnapshot(
            ticker=ticker.upper(),
            price=price,
            open_price=open_price,
            previous_close=previous_close,
            change_percent=change_percent,
            volume=float(
                latest_bar.get("v", 0.0)
            ),
            vwap=vwap,
            high=high,
            low=low,
            timeframe_minutes=timeframe_minutes,
        )

    def _evaluate_engines(
        self,
        snapshot: MarketSnapshot,
        context: MarketContext | None,
    ) -> list[EngineResult]:
        results: list[EngineResult] = []

        for engine in self.engines:
            result = engine.evaluate(
                snapshot=snapshot,
                context=context,
            )

            results.append(result)

        return results

    def _classify(
        self,
        snapshot: MarketSnapshot,
        context: MarketContext | None = None,
    ) -> ScanResult:
        engine_results = self._evaluate_engines(
            snapshot=snapshot,
            context=context,
        )

        score = (
            sum(
                result.score
                for result in engine_results
            )
            / len(engine_results)
            if engine_results
            else 50.0
        )

        score = max(
            0.0,
            min(score, 100.0),
        )

        above_vwap = (
            snapshot.price >= snapshot.vwap
            if snapshot.vwap is not None
            else None
        )

        if score >= 80.0:
            status = ScanStatus.STRONG
        elif score >= 65.0:
            status = ScanStatus.POSITIVE
        elif score >= 40.0:
            status = ScanStatus.NEUTRAL
        else:
            status = ScanStatus.WEAK

        reason = "; ".join(
            (
                f"{result.engine}: "
                f"{result.reason}"
            )
            for result in engine_results
        )

        if not reason:
            reason = "No engine result"

        return ScanResult(
            ticker=snapshot.ticker,
            status=status,
            score=round(score, 2),
            price=snapshot.price,
            change_percent=round(
                snapshot.change_percent,
                4,
            ),
            volume=snapshot.volume,
            vwap=snapshot.vwap,
            above_vwap=above_vwap,
            reason=reason,
        )
        