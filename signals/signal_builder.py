from __future__ import annotations

from decision.models import (
    DecisionResult,
    DecisionStatus,
    TradingSignal,
)
from execution.entry_engine import EntryEngine
from execution.models import (
    EntryContext,
    EntryStatus,
    TradePlan,
)


class SignalBuilder:
    def __init__(
        self,
        entry_engine: EntryEngine | None = None,
    ) -> None:
        self.entry_engine = (
            entry_engine
            or EntryEngine()
        )

    def build(
        self,
        decision: DecisionResult,
        entry_context: EntryContext | None = None,
    ) -> TradingSignal | None:
        top = decision.top_candidate

        if top is None:
            return None

        if (
            decision.decision_status
            not in (
                DecisionStatus.BUY,
                DecisionStatus.WATCH,
            )
        ):
            return TradingSignal(
                ticker=top.ticker,
                status=(
                    decision.decision_status
                ),
                score=top.score,
                entry_price=None,
                stop_price=None,
                tp1_price=None,
                tp2_price=None,
                reason=decision.reason,
            )

        if entry_context is None:
            return TradingSignal(
                ticker=top.ticker,
                status=DecisionStatus.WATCH,
                score=top.score,
                entry_price=None,
                stop_price=None,
                tp1_price=None,
                tp2_price=None,
                reason=(
                    "Entry context unavailable"
                ),
            )

        trade_plan = (
            self.entry_engine.build_trade_plan(
                ticker=top.ticker,
                context=entry_context,
            )
        )

        return self._build_signal_from_plan(
            decision=decision,
            trade_plan=trade_plan,
        )

    @staticmethod
    def _build_signal_from_plan(
        decision: DecisionResult,
        trade_plan: TradePlan,
    ) -> TradingSignal:
        status_mapping = {
            EntryStatus.BUY_NOW: (
                DecisionStatus.BUY
            ),
            EntryStatus.WATCH: (
                DecisionStatus.WATCH
            ),
            EntryStatus.WAIT: (
                DecisionStatus.WAIT
            ),
            EntryStatus.REJECT: (
                DecisionStatus.AVOID
            ),
        }

        signal_status = status_mapping[
            trade_plan.status
        ]

        return TradingSignal(
            ticker=trade_plan.ticker,
            status=signal_status,
            score=trade_plan.decision_score,
            entry_price=(
                trade_plan.entry_price
            ),
            stop_price=(
                trade_plan.stop_price
            ),
            tp1_price=(
                trade_plan.tp1_price
            ),
            tp2_price=(
                trade_plan.tp2_price
            ),
            reason=(
                f"{decision.reason} | "
                f"{trade_plan.reason}"
            ),
        )
        