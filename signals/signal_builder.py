from __future__ import annotations

from decision.models import (
    DecisionResult,
    DecisionStatus,
    TradingSignal,
)


class SignalBuilder:
    def build(
        self,
        decision: DecisionResult,
    ) -> TradingSignal | None:
        top = decision.top_candidate

        if top is None:
            return None

        if decision.decision_status not in (
            DecisionStatus.BUY,
            DecisionStatus.WATCH,
        ):
            return TradingSignal(
                ticker=top.ticker,
                status=decision.decision_status,
                score=top.score,
                entry_price=None,
                stop_price=None,
                tp1_price=None,
                tp2_price=None,
                reason=decision.reason,
            )

        price = top.scan_result.price

        entry = round(price, 2)
        stop = round(price * 0.985, 2)
        tp1 = round(price * 1.02, 2)
        tp2 = round(price * 1.04, 2)

        return TradingSignal(
            ticker=top.ticker,
            status=decision.decision_status,
            score=top.score,
            entry_price=entry,
            stop_price=stop,
            tp1_price=tp1,
            tp2_price=tp2,
            reason=decision.reason,
        )
        