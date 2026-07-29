from dataclasses import dataclass
from typing import Any, Callable

from earnings.audit_engine import AuditRecord


ReplayHandler = Callable[
    [dict[str, Any]],
    dict[str, Any],
]


@dataclass(frozen=True)
class ReplayResult:
    audit_id: str
    ticker: str
    event_type: str
    original_status: str
    replay_status: str
    original_output: dict[str, Any]
    replay_output: dict[str, Any]
    matched: bool


def replay_audit_record(
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
            event_type=record.event_type,
            original_status=record.status,
            replay_status="FAILED",
            original_output=record.output_data,
            replay_output={
                "error": str(error),
            },
            matched=False,
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
        event_type=record.event_type,
        original_status=record.status,
        replay_status="SUCCESS",
        original_output=record.output_data,
        replay_output=replay_output,
        matched=matched,
    )


def replay_audit_records(
    records: list[AuditRecord],
    handlers: dict[str, ReplayHandler],
) -> list[ReplayResult]:
    results: list[ReplayResult] = []

    for record in records:
        handler = handlers.get(
            record.event_type
        )

        if handler is None:
            results.append(
                ReplayResult(
                    audit_id=record.audit_id,
                    ticker=record.ticker,
                    event_type=record.event_type,
                    original_status=record.status,
                    replay_status="SKIPPED",
                    original_output=(
                        record.output_data
                    ),
                    replay_output={
                        "reason": (
                            "NO_HANDLER"
                        ),
                    },
                    matched=False,
                )
            )

            continue

        results.append(
            replay_audit_record(
                record,
                handler,
            )
        )

    return results
