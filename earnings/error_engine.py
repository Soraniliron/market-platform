from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EngineError:
    code: str
    message: str
    details: dict[str, Any]


@dataclass(frozen=True)
class EngineResponse:
    success: bool
    data: dict[str, Any] | None
    error: EngineError | None


def success_response(
    data: dict[str, Any],
) -> EngineResponse:
    if not isinstance(data, dict):
        raise ValueError(
            "data must be a dictionary"
        )

    return EngineResponse(
        success=True,
        data=data,
        error=None,
    )


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> EngineResponse:
    if not code:
        raise ValueError(
            "code must not be empty"
        )

    if not message:
        raise ValueError(
            "message must not be empty"
        )

    return EngineResponse(
        success=False,
        data=None,
        error=EngineError(
            code=code,
            message=message,
            details=details or {},
        ),
    )


def execute_safely(
    handler,
    *args,
    **kwargs,
) -> EngineResponse:
    if not callable(handler):
        return error_response(
            code="INVALID_HANDLER",
            message="handler must be callable",
        )

    try:
        result = handler(
            *args,
            **kwargs,
        )
    except ValueError as error:
        return error_response(
            code="VALIDATION_ERROR",
            message=str(error),
            details={
                "exception_type": (
                    type(error).__name__
                ),
            },
        )
    except Exception as error:
        return error_response(
            code="ENGINE_ERROR",
            message=str(error),
            details={
                "exception_type": (
                    type(error).__name__
                ),
            },
        )

    if not isinstance(result, dict):
        return error_response(
            code="INVALID_ENGINE_OUTPUT",
            message=(
                "handler must return "
                "a dictionary"
            ),
            details={
                "output_type": (
                    type(result).__name__
                ),
            },
        )

    return success_response(result)
