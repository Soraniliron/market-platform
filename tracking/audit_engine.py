from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from tracking.models import (
    AuditEvent,
    AuditRecord,
    DecisionType,
)


class AuditEngine:
    def create_record(
        self,
        ticker: str,
        event: AuditEvent,
        decision: DecisionType,
        score: float,
        reason: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        entry_price: float | None = None,
        stop_price: float | None = None,
        tp1_price: float | None = None,
        tp2_price: float | None = None,
    ) -> AuditRecord:
        if not ticker:
            raise ValueError(
                "ticker must not be empty"
            )

        if not 0.0 <= score <= 100.0:
            raise ValueError(
                "score must be between 0 and 100"
            )

        if not reason:
            raise ValueError(
                "reason must not be empty"
            )

        return AuditRecord(
            audit_id=str(uuid4()),
            created_at=datetime.now(
                timezone.utc
            ),
            ticker=ticker.upper(),
            event=event,
            decision=decision,
            score=score,
            entry_price=entry_price,
            stop_price=stop_price,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            reason=reason,
            input_data=input_data,
            output_data=output_data,
        )

    def save_record(
        self,
        record: AuditRecord,
        file_path: str | Path,
    ) -> None:
        path = Path(file_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = asdict(record)

        data["created_at"] = (
            record.created_at.isoformat()
        )
        data["event"] = record.event.value
        data["decision"] = (
            record.decision.value
        )

        with path.open(
            "a",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                sort_keys=True,
            )
            file.write("\n")

    def load_records(
        self,
        file_path: str | Path,
    ) -> list[AuditRecord]:
        path = Path(file_path)

        if not path.exists():
            return []

        records: list[AuditRecord] = []

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line_number, line in enumerate(
                file,
                start=1,
            ):
                stripped = line.strip()

                if not stripped:
                    continue

                try:
                    data = json.loads(stripped)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Invalid audit JSON at line "
                        f"{line_number}"
                    ) from error

                records.append(
                    self._record_from_dict(
                        data=data,
                        line_number=line_number,
                    )
                )

        return records

    @staticmethod
    def _record_from_dict(
        data: dict[str, Any],
        line_number: int,
    ) -> AuditRecord:
        required_fields = {
            "audit_id",
            "created_at",
            "ticker",
            "event",
            "decision",
            "score",
            "reason",
            "input_data",
            "output_data",
        }

        missing_fields = (
            required_fields - data.keys()
        )

        if missing_fields:
            missing_text = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                f"Invalid audit record at line "
                f"{line_number}: missing fields: "
                f"{missing_text}"
            )

        return AuditRecord(
            audit_id=str(data["audit_id"]),
            created_at=datetime.fromisoformat(
                data["created_at"]
            ),
            ticker=str(
                data["ticker"]
            ).upper(),
            event=AuditEvent(
                data["event"]
            ),
            decision=DecisionType(
                data["decision"]
            ),
            score=float(data["score"]),
            entry_price=(
                float(data["entry_price"])
                if data.get("entry_price")
                is not None
                else None
            ),
            stop_price=(
                float(data["stop_price"])
                if data.get("stop_price")
                is not None
                else None
            ),
            tp1_price=(
                float(data["tp1_price"])
                if data.get("tp1_price")
                is not None
                else None
            ),
            tp2_price=(
                float(data["tp2_price"])
                if data.get("tp2_price")
                is not None
                else None
            ),
            reason=str(data["reason"]),
            input_data=dict(
                data["input_data"]
            ),
            output_data=dict(
                data["output_data"]
            ),
        )
        