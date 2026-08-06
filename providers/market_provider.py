from __future__ import annotations

from datetime import date, datetime
from typing import Any

from config.settings import APP_MODE
from importer.polygon_client import PolygonClient


class MarketProvider:
    def __init__(self) -> None:
        self.client = (
            PolygonClient()
            if APP_MODE != "mock"
            else None
        )

    def get_bars(
        self,
        ticker: str,
        timeframe_minutes: int,
        start_date: date | datetime,
        end_date: date | datetime,
    ) -> list[dict[str, Any]]:
        if APP_MODE == "mock":
            return self._get_mock_bars(
                ticker=ticker,
                timeframe_minutes=timeframe_minutes,
            )

        if self.client is None:
            raise RuntimeError(
                "Market client is not initialized"
            )

        return self.client.get_minute_history(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe_minutes=timeframe_minutes,
        )

    def get_previous_close(
        self,
        ticker: str,
    ) -> list[dict[str, Any]]:
        if APP_MODE == "mock":
            return [
                {
                    "T": ticker.upper(),
                    "c": 100.0,
                    "h": 101.0,
                    "l": 99.0,
                    "o": 99.5,
                    "v": 1_000_000,
                }
            ]

        if self.client is None:
            raise RuntimeError(
                "Market client is not initialized"
            )

        return self.client.get_previous_close(
            ticker=ticker
        )

    @staticmethod
    def _get_mock_bars(
        ticker: str,
        timeframe_minutes: int,
    ) -> list[dict[str, Any]]:
        return [
            {
                "ticker": ticker.upper(),
                "timeframe_minutes": (
                    timeframe_minutes
                ),
                "o": 100.0,
                "h": 101.0,
                "l": 99.5,
                "c": 100.5,
                "v": 250_000,
                "vw": 100.4,
                "t": 0,
                "n": 1_000,
            }
        ]
        