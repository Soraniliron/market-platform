from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import LOG_LEVEL


LOG_DIR = Path("logs")
LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


class JsonFormatter(logging.Formatter):
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        event_name = getattr(
            record,
            "event_name",
            None,
        )

        if event_name is not None:
            payload["event"] = event_name

        event_data = getattr(
            record,
            "event_data",
            None,
        )

        if isinstance(
            event_data,
            dict,
        ):
            payload.update(event_data)

        if record.exc_info:
            payload["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )


def _resolve_log_level() -> int:
    return getattr(
        logging,
        LOG_LEVEL,
        logging.INFO,
    )


def _configure_logger() -> logging.Logger:
    configured_logger = logging.getLogger(
        "market-platform"
    )

    configured_logger.setLevel(
        _resolve_log_level()
    )

    configured_logger.propagate = False

    if configured_logger.handlers:
        return configured_logger

    formatter = JsonFormatter()

    console_handler = (
        logging.StreamHandler()
    )

    console_handler.setFormatter(
        formatter
    )

    configured_logger.addHandler(
        console_handler
    )

    try:
        file_handler = logging.FileHandler(
            LOG_DIR / "market-platform.log",
            encoding="utf-8",
        )

        file_handler.setFormatter(
            formatter
        )

        configured_logger.addHandler(
            file_handler
        )

    except (
        PermissionError,
        OSError,
    ):
        configured_logger.warning(
            "File logging unavailable",
            extra={
                "event_name": (
                    "FILE_LOGGING_UNAVAILABLE"
                ),
                "event_data": {
                    "log_path": str(
                        LOG_DIR
                        / "market-platform.log"
                    ),
                },
            },
        )

    return configured_logger


logger = _configure_logger()


def log_event(
    event_name: str,
    *,
    level: int = logging.INFO,
    message: str | None = None,
    **event_data: Any,
) -> None:
    if not event_name:
        raise ValueError(
            "event_name must not be empty"
        )

    logger.log(
        level,
        message or event_name,
        extra={
            "event_name": event_name,
            "event_data": event_data,
        },
    )
    