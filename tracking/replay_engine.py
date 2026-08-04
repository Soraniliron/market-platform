from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from tracking.models import AuditRecord


ReplayHandler = Callable[
    [dict[str, Any]],
    dict[str, Any],
]


@dataclass(frozen=True)
class ReplayResult:
    audit_id: str
    ticker: str

    original_output: dict[str, Any]
    replay_output: dict[str, Any]

    matched: bool
    status: str
    reason: str


class ReplayEngine:
    def replay_record(
        self,
        record: AuditRecord,
        handler: ReplayHandler,
    ) -> ReplayResult:
        if not callable(handler):
            raise ValueError(
                "handler must be callable"
            )

        try:
            replay_output = handler(
                record.input_data
            )
        except Exception as error:
            return ReplayResult(
                audit_id=record.audit_id,
                ticker=record.ticker,
                original_output=(
                    record.output_data
                ),
                replay_output={
                    "error": str(error),
                },
                matched=False,
                status="failed",
                reason="Replay handler failed",
            )

        if not isinstance(
            replay_output,
            dict,
        ):
            raise ValueError(
                "handler must return a dictionary"
            )

        matched = (
            replay_output
            == record.output_data
        )

        return ReplayResult(
            audit_id=record.audit_id,
            ticker=record.ticker,
            original_output=(
                record.output_data
            ),
            replay_output=replay_output,
            matched=matched,
            status=(
                "matched"
                if matched
                else "mismatched"
            ),
            reason=(
                "Replay output matched original"
                if matched
                else (
                    "Replay output differs "
                    "from original"
                )
            ),
        )

    def replay_records(
        self,
        records: list[AuditRecord],
        handlers: dict[
            str,
            ReplayHandler,
        ],
    ) -> list[ReplayResult]:
        results: list[ReplayResult] = []

        for record in records:
            handler = handlers.get(
                record.event.value
            )

            if handler is None:
                results.append(
                    ReplayResult(
                        audit_id=record.audit_id,
                        ticker=record.ticker,
                        original_output=(
                            record.output_data
                        ),
                        replay_output={},
                        matched=False,
                        status="skipped",
                        reason=(
                            "No replay handler "
                            "for event"
                        ),
                    )
                )
                continue

            results.append(
                self.replay_record(
                    record=record,
                    handler=handler,
                )
            )

        return results
        