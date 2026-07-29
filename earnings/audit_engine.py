import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


REQUIRED_AUDIT_FIELDS = {
    "audit_id",
    "created_at",
    "ticker",
    "event_type",
    "status",
    "input_data",
    "output_data",
}


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    created_at: str
    ticker: str
    event_type: str
    status: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    metadata: dict[str, Any]


def create_audit_record(
    ticker: str,
    event_type: str,
    status: str,
    input_data: dict[str, Any],
    output_data: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> AuditRecord:
    if not ticker:
        raise ValueError(
            "ticker must not be empty"
        )

    if not event_type:
        raise ValueError(
            "event_type must not be empty"
        )

    if not status:
        raise ValueError(
            "status must not be empty"
        )

    return AuditRecord(
        audit_id=str(uuid4()),
        created_at=datetime.now(
            timezone.utc
        ).isoformat(),
        ticker=ticker,
        event_type=event_type,
        status=status,
        input_data=input_data,
        output_data=output_data,
        metadata=metadata or {},
    )


def audit_record_to_dict(
    record: AuditRecord,
) -> dict[str, Any]:
    return asdict(record)


def save_audit_record(
    record: AuditRecord,
    file_path: str | Path,
) -> None:
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as file:
        json.dump(
            audit_record_to_dict(record),
            file,
            ensure_ascii=False,
            sort_keys=True,
        )

        file.write("\n")


def validate_audit_data(
    data: Any,
    line_number: int,
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid audit record at line "
            f"{line_number}: expected JSON object"
        )

    missing_fields = (
        REQUIRED_AUDIT_FIELDS - data.keys()
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

    if not isinstance(
        data["input_data"],
        dict,
    ):
        raise ValueError(
            f"Invalid audit record at line "
            f"{line_number}: input_data must "
            f"be an object"
        )

    if not isinstance(
        data["output_data"],
        dict,
    ):
        raise ValueError(
            f"Invalid audit record at line "
            f"{line_number}: output_data must "
            f"be an object"
        )

    metadata = data.get(
        "metadata",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        raise ValueError(
            f"Invalid audit record at line "
            f"{line_number}: metadata must "
            f"be an object"
        )

    return data


def load_audit_records(
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
            stripped_line = line.strip()

            if not stripped_line:
                continue

            try:
                parsed_data = json.loads(
                    stripped_line
                )
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid audit JSON "
                    f"at line {line_number}"
                ) from error

            data = validate_audit_data(
                parsed_data,
                line_number,
            )

            records.append(
                AuditRecord(
                    audit_id=data["audit_id"],
                    created_at=data["created_at"],
                    ticker=data["ticker"],
                    event_type=data["event_type"],
                    status=data["status"],
                    input_data=data["input_data"],
                    output_data=data["output_data"],
                    metadata=data.get(
                        "metadata",
                        {},
                    ),
                )
            )

    return records
