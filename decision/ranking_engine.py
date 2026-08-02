from __future__ import annotations

from decision.models import (
    DecisionStatus,
    RankedCandidate,
)
from scanner.models import (
    ScanResult,
    ScanStatus,
)


class RankingEngine:
    def rank(
        self,
        scan_results: list[ScanResult],
        limit: int = 3,
    ) -> tuple[RankedCandidate, ...]:
        if limit < 1:
            raise ValueError(
                "limit must be at least one"
            )

        eligible_results = [
            result
            for result in scan_results
            if result.status
            != ScanStatus.REJECTED
        ]

        sorted_results = sorted(
            eligible_results,
            key=lambda result: (
                result.score,
                result.change_percent,
                result.volume,
            ),
            reverse=True,
        )

        ranked_candidates: list[
            RankedCandidate
        ] = []

        for index, result in enumerate(
            sorted_results[:limit],
            start=1,
        ):
            decision_status = (
                self._map_status(result)
            )

            ranked_candidates.append(
                RankedCandidate(
                    rank=index,
                    ticker=result.ticker,
                    score=result.score,
                    status=decision_status,
                    scan_result=result,
                    reason=(
                        self._build_reason(
                            result=result,
                            status=(
                                decision_status
                            ),
                        )
                    ),
                )
            )

        return tuple(
            ranked_candidates
        )

    @staticmethod
    def _map_status(
        result: ScanResult,
    ) -> DecisionStatus:
        if result.score >= 80.0:
            return DecisionStatus.BUY

        if result.score >= 65.0:
            return DecisionStatus.WATCH

        if result.score >= 40.0:
            return DecisionStatus.WAIT

        return DecisionStatus.AVOID

    @staticmethod
    def _build_reason(
        result: ScanResult,
        status: DecisionStatus,
    ) -> str:
        return (
            f"{status.value.upper()} | "
            f"score={result.score:.2f} | "
            f"change={result.change_percent:.2f}% | "
            f"{result.reason}"
        )
        