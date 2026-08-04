from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tracking.models import (
    DecisionType,
    PerformanceRecord,
    TradeResult,
)


@dataclass(frozen=True)
class DailyPerformanceSummary:
    records_count: int
    buy_signals_count: int
    entries_count: int

    tp1_count: int
    tp2_count: int
    stop_count: int
    no_entry_count: int

    wins_count: int
    losses_count: int
    win_rate: float

    total_return_percent: float
    average_return_percent: float

    false_signals_count: int
    missed_opportunities_count: int


class PerformanceEngine:
    def evaluate_trade(
        self,
        ticker: str,
        created_at: datetime,
        decision: DecisionType,
        decision_score: float,
        engine_scores: dict[str, float],
        selected_rank: int | None,
        entry_price: float | None,
        stop_price: float | None,
        tp1_price: float | None,
        tp2_price: float | None,
        observed_prices: list[float],
        notes: str = "",
    ) -> PerformanceRecord:
        self._validate_inputs(
            ticker=ticker,
            decision_score=decision_score,
            engine_scores=engine_scores,
            observed_prices=observed_prices,
        )

        if (
            decision != DecisionType.BUY
            or entry_price is None
        ):
            return PerformanceRecord(
                ticker=ticker.upper(),
                created_at=created_at,
                decision=decision,
                result=TradeResult.NO_ENTRY,
                entry_price=entry_price,
                exit_price=None,
                stop_price=stop_price,
                tp1_price=tp1_price,
                tp2_price=tp2_price,
                return_percent=None,
                decision_score=decision_score,
                engine_scores=engine_scores,
                selected_rank=selected_rank,
                notes=notes,
            )

        self._validate_trade_levels(
            entry_price=entry_price,
            stop_price=stop_price,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
        )

        entry_index = self._find_first_touch(
            prices=observed_prices,
            level=entry_price,
            condition="at_or_above",
        )

        if entry_index is None:
            return PerformanceRecord(
                ticker=ticker.upper(),
                created_at=created_at,
                decision=decision,
                result=TradeResult.NO_ENTRY,
                entry_price=entry_price,
                exit_price=None,
                stop_price=stop_price,
                tp1_price=tp1_price,
                tp2_price=tp2_price,
                return_percent=None,
                decision_score=decision_score,
                engine_scores=engine_scores,
                selected_rank=selected_rank,
                notes=notes,
            )

        prices_after_entry = observed_prices[
            entry_index:
        ]

        result, exit_price = (
            self._resolve_trade_result(
                prices=prices_after_entry,
                stop_price=stop_price,
                tp1_price=tp1_price,
                tp2_price=tp2_price,
            )
        )

        return_percent = (
            self._calculate_return_percent(
                entry_price=entry_price,
                exit_price=exit_price,
            )
            if exit_price is not None
            else None
        )

        return PerformanceRecord(
            ticker=ticker.upper(),
            created_at=created_at,
            decision=decision,
            result=result,
            entry_price=entry_price,
            exit_price=exit_price,
            stop_price=stop_price,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            return_percent=return_percent,
            decision_score=decision_score,
            engine_scores=engine_scores,
            selected_rank=selected_rank,
            notes=notes,
        )

    def summarize(
        self,
        records: list[PerformanceRecord],
        missed_opportunities_count: int = 0,
    ) -> DailyPerformanceSummary:
        if missed_opportunities_count < 0:
            raise ValueError(
                "missed_opportunities_count must "
                "be zero or greater"
            )

        buy_records = [
            record
            for record in records
            if record.decision == DecisionType.BUY
        ]

        entries = [
            record
            for record in buy_records
            if record.result
            != TradeResult.NO_ENTRY
        ]

        tp1_count = sum(
            record.result == TradeResult.TP1
            for record in entries
        )

        tp2_count = sum(
            record.result == TradeResult.TP2
            for record in entries
        )

        stop_count = sum(
            record.result == TradeResult.STOP
            for record in entries
        )

        no_entry_count = sum(
            record.result == TradeResult.NO_ENTRY
            for record in records
        )

        wins_count = tp1_count + tp2_count
        losses_count = stop_count

        completed_trades = (
            wins_count + losses_count
        )

        win_rate = (
            round(
                wins_count
                / completed_trades
                * 100,
                2,
            )
            if completed_trades > 0
            else 0.0
        )

        returns = [
            record.return_percent
            for record in records
            if record.return_percent is not None
        ]

        total_return_percent = round(
            sum(returns),
            4,
        )

        average_return_percent = (
            round(
                total_return_percent
                / len(returns),
                4,
            )
            if returns
            else 0.0
        )

        false_signals_count = stop_count

        return DailyPerformanceSummary(
            records_count=len(records),
            buy_signals_count=len(buy_records),
            entries_count=len(entries),
            tp1_count=tp1_count,
            tp2_count=tp2_count,
            stop_count=stop_count,
            no_entry_count=no_entry_count,
            wins_count=wins_count,
            losses_count=losses_count,
            win_rate=win_rate,
            total_return_percent=(
                total_return_percent
            ),
            average_return_percent=(
                average_return_percent
            ),
            false_signals_count=(
                false_signals_count
            ),
            missed_opportunities_count=(
                missed_opportunities_count
            ),
        )

    @staticmethod
    def is_missed_opportunity(
        selected: bool,
        reference_price: float,
        highest_price: float,
        minimum_move_percent: float = 2.0,
    ) -> bool:
        if reference_price <= 0:
            raise ValueError(
                "reference_price must be "
                "greater than zero"
            )

        if highest_price <= 0:
            raise ValueError(
                "highest_price must be "
                "greater than zero"
            )

        if minimum_move_percent <= 0:
            raise ValueError(
                "minimum_move_percent must be "
                "greater than zero"
            )

        move_percent = (
            (
                highest_price
                - reference_price
            )
            / reference_price
        ) * 100

        return (
            not selected
            and move_percent
            >= minimum_move_percent
        )

    @staticmethod
    def _resolve_trade_result(
        prices: list[float],
        stop_price: float | None,
        tp1_price: float | None,
        tp2_price: float | None,
    ) -> tuple[
        TradeResult,
        float | None,
    ]:
        for price in prices:
            if (
                stop_price is not None
                and price <= stop_price
            ):
                return (
                    TradeResult.STOP,
                    stop_price,
                )

            if (
                tp2_price is not None
                and price >= tp2_price
            ):
                return (
                    TradeResult.TP2,
                    tp2_price,
                )

            if (
                tp1_price is not None
                and price >= tp1_price
            ):
                return (
                    TradeResult.TP1,
                    tp1_price,
                )

        return (
            TradeResult.OPEN,
            None,
        )

    @staticmethod
    def _find_first_touch(
        prices: list[float],
        level: float,
        condition: str,
    ) -> int | None:
        for index, price in enumerate(prices):
            if (
                condition == "at_or_above"
                and price >= level
            ):
                return index

        return None

    @staticmethod
    def _calculate_return_percent(
        entry_price: float,
        exit_price: float,
    ) -> float:
        return round(
            (
                (
                    exit_price
                    - entry_price
                )
                / entry_price
            )
            * 100,
            4,
        )

    @staticmethod
    def _validate_inputs(
        ticker: str,
        decision_score: float,
        engine_scores: dict[str, float],
        observed_prices: list[float],
    ) -> None:
        if not ticker:
            raise ValueError(
                "ticker must not be empty"
            )

        if not (
            0.0
            <= decision_score
            <= 100.0
        ):
            raise ValueError(
                "decision_score must be "
                "between 0 and 100"
            )

        for engine, score in (
            engine_scores.items()
        ):
            if not (
                0.0
                <= score
                <= 100.0
            ):
                raise ValueError(
                    f"engine score for {engine} "
                    "must be between 0 and 100"
                )

        if any(
            price <= 0
            for price in observed_prices
        ):
            raise ValueError(
                "observed prices must be "
                "greater than zero"
            )

    @staticmethod
    def _validate_trade_levels(
        entry_price: float,
        stop_price: float | None,
        tp1_price: float | None,
        tp2_price: float | None,
    ) -> None:
        if entry_price <= 0:
            raise ValueError(
                "entry_price must be "
                "greater than zero"
            )

        if (
            stop_price is not None
            and stop_price >= entry_price
        ):
            raise ValueError(
                "stop_price must be below "
                "entry_price"
            )

        if (
            tp1_price is not None
            and tp1_price <= entry_price
        ):
            raise ValueError(
                "tp1_price must be above "
                "entry_price"
            )

        if (
            tp2_price is not None
            and (
                tp1_price is None
                or tp2_price <= tp1_price
            )
        ):
            raise ValueError(
                "tp2_price must be above "
                "tp1_price"
            )
            