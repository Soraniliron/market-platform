import os
from datetime import date
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


class PolygonClient:
    BASE_URL = "https://api.polygon.io"

    def __init__(self) -> None:
        self.api_key = os.getenv("POLYGON_API_KEY")

        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in .env")

    def get_daily_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        adjusted: bool = True,
    ) -> list[dict[str, Any]]:
        url = (
            f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/"
            f"{start_date.isoformat()}/{end_date.isoformat()}"
        )

        params = {
            "adjusted": str(adjusted).lower(),
            "sort": "asc",
            "limit": 50000,
            "apiKey": self.api_key,
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get("status") not in ("OK", "DELAYED"):
            raise RuntimeError(f"Polygon error: {data}")

        return data.get("results", [])
        