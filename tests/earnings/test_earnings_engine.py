from types import SimpleNamespace

import pytest

import earnings.earnings_engine as earnings_engine


def build_cycle(
    ticker: str = "MSFT",
) -> SimpleNamespace:
    return SimpleNamespace(
        ticker=ticker,
        day_zero_close=100.0,
    )


def test_analyze_earnings_cycles_connects_engines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected_entry = SimpleNamespace(
        entry_drop_pct=-10.0,
        entry_price=90.0,
    )

    entry_result = SimpleNamespace(
        reference_price=100.0,
        production_ready=True,
        sample_status="PRODUCTION_READY",
        p60=selected_entry,
    )

    selected_exit = SimpleNamespace(
        target_return_pct=12.0,
        exit_price=100.8,
    )

    exit_result = SimpleNamespace(
        production_ready=True,
        p60=selected_exit,
    )

    statistics = SimpleNamespace(
        ticker="MSFT",
        cycles_count=12,
    )

    monkeypatch.setattr(
        earnings_engine,
        "calculate_entry_percentiles",
        lambda **kwargs: entry_result,
    )

    monkeypatch.setattr(
        earnings_engine,
        "calculate_exit_percentiles",
        lambda **kwargs: exit_result,
    )

    monkeypatch.setattr(
        earnings_engine,
        "calculate_cycle_statistics",
        lambda **kwargs: statistics,
    )

    cycles = [
        build_cycle()
        for _ in range(12)
    ]

    result = earnings_engine.analyze_earnings_cycles(
        ticker="MSFT",
        cycles=cycles,
        reference_price=100.0,
        entry_percentile=0.60,
        exit_percentile=0.60,
    )

    assert result.ticker == "MSFT"
    assert result.cycles_count == 12
    assert result.selected_entry is selected_entry
    assert result.selected_exit is selected_exit
    assert result.statistics is statistics
    assert result.production_ready is True
    assert result.sample_status == "PRODUCTION_READY"


def test_analyze_earnings_cycles_selects_requested_levels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry_p55 = SimpleNamespace(
        entry_drop_pct=-8.0,
        entry_price=92.0,
    )

    entry_result = SimpleNamespace(
        reference_price=100.0,
        production_ready=False,
        sample_status="RESEARCH_ONLY",
        p55=entry_p55,
    )

    exit_p70 = SimpleNamespace(
        target_return_pct=10.0,
        exit_price=101.2,
    )

    exit_result = SimpleNamespace(
        production_ready=False,
        p70=exit_p70,
    )

    monkeypatch.setattr(
        earnings_engine,
        "calculate_entry_percentiles",
        lambda **kwargs: entry_result,
    )

    monkeypatch.setattr(
        earnings_engine,
        "calculate_exit_percentiles",
        lambda **kwargs: exit_result,
    )

    monkeypatch.setattr(
        earnings_engine,
        "calculate_cycle_statistics",
        lambda **kwargs: SimpleNamespace(),
    )

    result = earnings_engine.analyze_earnings_cycles(
        ticker="MSFT",
        cycles=[build_cycle()],
        entry_percentile=0.55,
        exit_percentile=0.70,
    )

    assert result.selected_entry is entry_p55
    assert result.selected_exit is exit_p70
    assert result.selected_entry_percentile == 0.55
    assert result.selected_exit_percentile == 0.70
    assert result.production_ready is False


def test_rejects_unsupported_entry_percentile() -> None:
    with pytest.raises(
        ValueError,
        match="entry_percentile must be one of",
    ):
        earnings_engine.analyze_earnings_cycles(
            ticker="MSFT",
            cycles=[build_cycle()],
            entry_percentile=0.75,
        )


def test_rejects_empty_cycles() -> None:
    with pytest.raises(
        ValueError,
        match="At least one earnings cycle is required",
    ):
        earnings_engine.analyze_earnings_cycles(
            ticker="MSFT",
            cycles=[],
        )


def test_rejects_mismatched_ticker() -> None:
    with pytest.raises(
        ValueError,
        match="does not match MSFT",
    ):
        earnings_engine.analyze_earnings_cycles(
            ticker="MSFT",
            cycles=[
                build_cycle(ticker="AAPL"),
            ],
        )
