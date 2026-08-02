from __future__ import annotations

from decision.models import (
    DecisionResult,
    DecisionStatus,
    RankedCandidate,
)
from decision.ranking_engine import (
    RankingEngine,
)
from scanner.models import ScanResult


class DecisionEngine:
    def __init__(
        self,
        ranking_engine: RankingEngine | None = None,
        minimum_buy_score: float = 80.0,
        minimum_watch_score: float = 65.0,
    ) -> None:
        if not (
            0.0
            <= minimum_watch_score
            <= 100.0
        ):
            raise ValueError(
                "minimum_watch_score must be "
                "between 0 and 100"
            )

        if not (
            0.0
            <= minimum_buy_score
            <= 100.0
        ):
            raise ValueError(
                "minimum_buy_score must be "
                "between 0 and 100"
            )

        if (
            minimum_buy_score
            < minimum_watch_score
        ):
            raise ValueError(
                "minimum_buy_score must be "
                "greater than or equal to "
                "minimum_watch_score"
            )

        self.ranking_engine = (
            ranking_engine
            or RankingEngine()
        )

        self.minimum_buy_score = (
            minimum_buy_score
        )

        self.minimum_watch_score = (
            minimum_watch_score
        )

    def decide(
        self,
        scan_results: list[ScanResult],
        limit: int = 3,
    ) -> DecisionResult:
        ranked_candidates = (
            self.ranking_engine.rank(
                scan_results=scan_results,
                limit=limit,
            )
        )

        if not ranked_candidates:
            return DecisionResult(
                candidates_count=0,
                ranked_candidates=(),
                top_candidate=None,
                decision_status=(
                    DecisionStatus.AVOID
                ),
                reason=(
                    "No eligible candidates "
                    "were found"
                ),
            )

        top_candidate = ranked_candidates[0]

        decision_status = (
            self._resolve_status(
                top_candidate
            )
        )

        reason = self._build_reason(
            top_candidate=top_candidate,
            decision_status=decision_status,
            candidates_count=len(
                ranked_candidates
            ),
        )

        return DecisionResult(
            candidates_count=len(
                ranked_candidates
            ),
            ranked_candidates=(
                ranked_candidates
            ),
            top_candidate=top_candidate,
            decision_status=(
                decision_status
            ),
            reason=reason,
        )

    def _resolve_status(
        self,
        top_candidate: RankedCandidate,
    ) -> DecisionStatus:
        if (
            top_candidate.score
            >= self.minimum_buy_score
        ):
            return DecisionStatus.BUY

        if (
            top_candidate.score
            >= self.minimum_watch_score
        ):
            return DecisionStatus.WATCH

        if top_candidate.score >= 40.0:
            return DecisionStatus.WAIT

        return DecisionStatus.AVOID

    @staticmethod
    def _build_reason(
        top_candidate: RankedCandidate,
        decision_status: DecisionStatus,
        candidates_count: int,
    ) -> str:
        return (
            f"{decision_status.value.upper()} | "
            f"top={top_candidate.ticker} | "
            f"score={top_candidate.score:.2f} | "
            f"candidates={candidates_count} | "
            f"{top_candidate.reason}"
        )
        