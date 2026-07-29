from datetime import date

import pytest

from providers.market_provider import MarketProvider


def test_mock_provider_returns_bars(monkeypatch):
    monkeypatch.setattr(
        "providers.market_provider.APP_MODE",
        "mock",
    )

    provider = MarketProvider()

    bars = provider.get_bars(
        ticker="AAPL",
        timeframe_minutes=5,
        start_date=date(2026, 7, 29),
        end_date=date(2026, 7, 29),
    )

    assert len(bars) == 1
    assert bars[0]["ticker"] == "AAPL"
    assert bars[0]["timeframe_minutes"] == 5


def test_mock_provider_returns_previous_close(monkeypatch):
    monkeypatch.setattr(
        "providers.market_provider.APP_MODE",
        "mock",
    )

    provider = MarketProvider()
    result = provider.get_previous_close("MSFT")

    assert len(result) == 1
    assert result[0]["T"] == "MSFT"
    assert result[0]["c"] == 100.0


def test_live_provider_delegates_to_client(monkeypatch):
    class FakeClient:
        def get_minute_history(
            self,
            ticker,
            start_date,
            end_date,
            timeframe_minutes,
        ):
            return [
                {
                    "ticker": ticker,
                    "timeframe_minutes": timeframe_minutes,
                }
            ]

        def get_previous_close(self, ticker):
            return [{"T": ticker, "c": 123.45}]

    monkeypatch.setattr(
        "providers.market_provider.APP_MODE",
        "live",
    )
    monkeypatch.setattr(
        "providers.market_provider.PolygonClient",
        FakeClient,
    )

    provider = MarketProvider()

    bars = provider.get_bars(
        ticker="NVDA",
        timeframe_minutes=15,
        start_date=date(2026, 7, 29),
        end_date=date(2026, 7, 29),
    )

    previous_close = provider.get_previous_close("NVDA")

    assert bars[0]["ticker"] == "NVDA"
    assert bars[0]["timeframe_minutes"] == 15
    assert previous_close[0]["c"] == 123.45


@pytest.mark.parametrize("timeframe", [1, 5, 15])
def test_supported_timeframes_in_mock_mode(
    monkeypatch,
    timeframe,
):
    monkeypatch.setattr(
        "providers.market_provider.APP_MODE",
        "mock",
    )

    provider = MarketProvider()

    bars = provider.get_bars(
        ticker="META",
        timeframe_minutes=timeframe,
        start_date=date(2026, 7, 29),
        end_date=date(2026, 7, 29),
    )

    assert bars[0]["timeframe_minutes"] == timeframe
