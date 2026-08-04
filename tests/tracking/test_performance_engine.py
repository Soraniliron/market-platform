from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tracking.models import (
    DecisionType,
    TradeResult,
)
from tracking.performance_engine import (
    PerformanceEngine,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def test_evaluate_trade_hits_tp1() -> None:
    engine = PerformanceEngine()

    record = engine.evaluate_trade(
        ticker="META",
        created_at=now(),
        decision=DecisionType.BUY,
        decision_score=90.0,
        engine_scores={
            "gap": 85.0,
            "volume": 90.0,
            "index": 80.0,
            "vwap": 88.0,
            "chart_quality": 92.0,
        },
        selected_rank=1,
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        observed_prices=[
            99.5,
            100.0,
            100.8,
            102.1,
        ],
    )

    assert record.result == TradeResult.TP1
    assert record.exit_price == 102.0
    assert record.return_percent == 2.0


def test_evaluate_trade_hits_tp2_before_tp1_recording() -> None:
    engine = PerformanceEngine()

    record = engine.evaluate_trade(
        ticker="JPM",
        created_at=now(),
        decision=DecisionType.BUY,
        decision_score=93.0,
        engine_scores={"volume": 95.0},
        selected_rank=1,
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        observed_prices=[
            100.0,
            104.2,
        ],
    )

    assert record.result == TradeResult.TP2
    assert record.exit_price == 104.0
    assert record.return_percent == 4.0


def test_evaluate_trade_hits_stop() -> None:
    engine = PerformanceEngine()

    record = engine.evaluate_trade(
        ticker="PLTR",
        created_at=now(),
        decision=DecisionType.BUY,
        decision_score=84.0,
        engine_scores={"gap": 80.0},
        selected_rank=1,
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        observed_prices=[
            100.0,
            99.0,
            97.8,
        ],
    )

    assert record.result == TradeResult.STOP
    assert record.exit_price == 98.0
    assert record.return_percent == -2.0


def test_no_entry_when_entry_not_touched() -> None:
    engine = PerformanceEngine()

    record = engine.evaluate_trade(
        ticker="MSFT",
        created_at=now(),
        decision=DecisionType.BUY,
        decision_score=82.0,
        engine_scores={"index": 75.0},
        selected_rank=1,
        entry_price=105.0,
        stop_price=102.0,
        tp1_price=107.0,
        tp2_price=109.0,
        observed_prices=[
            100.0,
            101.0,
            102.0,
        ],
    )

    assert record.result == TradeResult.NO_ENTRY
    assert record.exit_price is None
    assert record.return_percent is None


def test_non_buy_decision_returns_no_entry() -> None:
    engine = PerformanceEngine()

    record = engine.evaluate_trade(
        ticker="CRM",
        created_at=now(),
        decision=DecisionType.WATCH,
        decision_score=70.0,
        engine_scores={"vwap": 65.0},
        selected_rank=2,
        entry_price=None,
        stop_price=None,
        tp1_price=None,
        tp2_price=None,
        observed_prices=[100.0, 101.0],
    )

    assert record.result == TradeResult.NO_ENTRY
    assert record.return_percent is None


def test_open_trade_when_no_level_hit() -> None:
    engine = PerformanceEngine()

    record = engine.evaluate_trade(
        ticker="AAPL",
        created_at=now(),
        decision=DecisionType.BUY,
        decision_score=88.0,
        engine_scores={"chart_quality": 90.0},
        selected_rank=1,
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        observed_prices=[
            100.0,
            100.5,
            101.0,
        ],
    )

    assert record.result == TradeResult.OPEN
    assert record.exit_price is None
    assert record.return_percent is None


def test_summary() -> None:
    engine = PerformanceEngine()

    records = [
        engine.evaluate_trade(
            ticker="META",
            created_at=now(),
            decision=DecisionType.BUY,
            decision_score=90.0,
            engine_scores={"gap": 90.0},
            selected_rank=1,
            entry_price=100.0,
            stop_price=98.0,
            tp1_price=102.0,
            tp2_price=104.0,
            observed_prices=[100.0, 102.0],
        ),
        engine.evaluate_trade(
            ticker="JPM",
            created_at=now(),
            decision=DecisionType.BUY,
            decision_score=92.0,
            engine_scores={"volume": 95.0},
            selected_rank=1,
            entry_price=100.0,
            stop_price=98.0,
            tp1_price=102.0,
            tp2_price=104.0,
            observed_prices=[100.0, 104.0],
        ),
        engine.evaluate_trade(
            ticker="PLTR",
            created_at=now(),
            decision=DecisionType.BUY,
            decision_score=81.0,
            engine_scores={"index": 70.0},
            selected_rank=1,
            entry_price=100.0,
            stop_price=98.0,
            tp1_price=102.0,
            tp2_price=104.0,
            observed_prices=[100.0, 98.0],
        ),
        engine.evaluate_trade(
            ticker="CRM",
            created_at=now(),
            decision=DecisionType.WATCH,
            decision_score=68.0,
            engine_scores={"vwap": 60.0},
            selected_rank=2,
            entry_price=None,
            stop_price=None,
            tp1_price=None,
            tp2_price=None,
            observed_prices=[100.0],
        ),
    ]

    summary = engine.summarize(
        records=records,
        missed_opportunities_count=2,
    )

    assert summary.records_count == 4
    assert summary.buy_signals_count == 3
    assert summary.entries_count == 3
    assert summary.tp1_count == 1
    assert summary.tp2_count == 1
    assert summary.stop_count == 1
    assert summary.no_entry_count == 1
    assert summary.wins_count == 2
    assert summary.losses_count == 1
    assert summary.win_rate == 66.67
    assert summary.total_return_percent == 4.0
    assert summary.average_return_percent == 1.3333
    assert summary.false_signals_count == 1
    assert summary.missed_opportunities_count == 2


def test_detects_missed_opportunity() -> None:
    result = PerformanceEngine.is_missed_opportunity(
        selected=False,
        reference_price=100.0,
        highest_price=102.5,
        minimum_move_percent=2.0,
    )

    assert result is True


def test_selected_stock_is_not_missed_opportunity() -> None:
    result = PerformanceEngine.is_missed_opportunity(
        selected=True,
        reference_price=100.0,
        highest_price=103.0,
        minimum_move_percent=2.0,
    )

    assert result is False


@pytest.mark.parametrize(
    "price",
    [0.0, -1.0],
)
def test_rejects_invalid_observed_prices(
    price: float,
) -> None:
    engine = PerformanceEngine()

    with pytest.raises(
        ValueError,
        match=(
            "observed prices must be "
            "greater than zero"
        ),
    ):
        engine.evaluate_trade(
            ticker="META",
            created_at=now(),
            decision=DecisionType.BUY,
            decision_score=90.0,
            engine_scores={"gap": 90.0},
            selected_rank=1,
            entry_price=100.0,
            stop_price=98.0,
            tp1_price=102.0,
            tp2_price=104.0,
            observed_prices=[price],
        )
        