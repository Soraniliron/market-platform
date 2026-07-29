from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import requests

from config.settings import (
    MASSIVE_API_KEY,
    MASSIVE_BASE_URL,
    REQUEST_TIMEOUT_SECONDS,
    validate_market_data_settings,
)


class PolygonClient:
    def __init__(self) -> None:
        validate_market_data_settings()

        self.api_key = MASSIVE_API_KEY
        self.base_url = MASSIVE_BASE_URL

        self.session = requests.Session()
        self.session.params.update({"apiKey": self.api_key})

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"

        response = self.session.get(
            url,
            params=params or {},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        data = response.json()
        status = data.get("status")

        if status not in {"OK", "DELAYED"}:
            raise RuntimeError(f"Massive API error: {data}")

        return data

    def get_aggregates(
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        start_date: date | datetime,
        end_date: date | datetime,
        adjusted: bool = True,
        sort: str = "asc",
        limit: int = 50000,
    ) -> list[dict[str, Any]]:
        if multiplier <= 0:
            raise ValueError("multiplier must be greater than 0")

        allowed_timespans = {
            "second",
            "minute",
            "hour",
            "day",
            "week",
            "month",
            "quarter",
            "year",
        }

        if timespan not in allowed_timespans:
            raise ValueError(
                f"Unsupported timespan: {timespan}. "
                f"Allowed values: {sorted(allowed_timespans)}"
            )

        start_value = self._format_range_value(start_date)
        end_value = self._format_range_value(end_date)

        path = (
            f"/v2/aggs/ticker/{ticker.upper()}/range/"
            f"{multiplier}/{timespan}/{start_value}/{end_value}"
        )

        params = {
            "adjusted": str(adjusted).lower(),
            "sort": sort,
            "limit": limit,
        }

        data = self._get(path, params=params)
        return data.get("results", [])

    def get_daily_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        adjusted: bool = True,
    ) -> list[dict[str, Any]]:
        return self.get_aggregates(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            start_date=start_date,
            end_date=end_date,
            adjusted=adjusted,
        )

    def get_minute_history(
        self,
        ticker: str,
        start_date: date | datetime,
        end_date: date | datetime,
        timeframe_minutes: int = 1,
        adjusted: bool = True,
    ) -> list[dict[str, Any]]:
        if timeframe_minutes not in {1, 5, 15}:
            raise ValueError(
                "timeframe_minutes must be one of: 1, 5, 15"
            )

        return self.get_aggregates(
            ticker=ticker,
            multiplier=timeframe_minutes,
            timespan="minute",
            start_date=start_date,
            end_date=end_date,
            adjusted=adjusted,
        )

    def get_previous_close(
        self,
        ticker: str,
        adjusted: bool = True,
    ) -> list[dict[str, Any]]:
        path = f"/v2/aggs/ticker/{ticker.upper()}/prev"

        params = {
            "adjusted": str(adjusted).lower(),
        }

        data = self._get(path, params=params)
        return data.get("results", [])

    @staticmethod
    def _format_range_value(value: date | datetime) -> str:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)

            return str(int(value.timestamp() * 1000))

        return value.isoformat()
