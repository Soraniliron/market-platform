from dataclasses import dataclass
from typing import Any

from earnings.models import EarningsCycle


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    issues: tuple[ValidationIssue, ...]


class ValidationError(ValueError):
    def __init__(
        self,
        issues: list[ValidationIssue],
    ) -> None:
        self.issues = tuple(issues)

        message = "; ".join(
            f"{issue.field}: {issue.message}"
            for issue in issues
        )

        super().__init__(message)


def validate_ticker(
    ticker: Any,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not isinstance(ticker, str):
        issues.append(
            ValidationIssue(
                field="ticker",
                code="INVALID_TYPE",
                message="ticker must be a string",
            )
        )

        return issues

    normalized_ticker = ticker.strip()

    if not normalized_ticker:
        issues.append(
            ValidationIssue(
                field="ticker",
                code="EMPTY_VALUE",
                message="ticker must not be empty",
            )
        )

        return issues

    if len(normalized_ticker) > 10:
        issues.append(
            ValidationIssue(
                field="ticker",
                code="VALUE_TOO_LONG",
                message=(
                    "ticker must contain at most "
                    "10 characters"
                ),
            )
        )

    allowed_characters = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789.-"
    )

    if any(
        character not in allowed_characters
        for character in normalized_ticker.upper()
    ):
        issues.append(
            ValidationIssue(
                field="ticker",
                code="INVALID_FORMAT",
                message=(
                    "ticker contains unsupported "
                    "characters"
                ),
            )
        )

    return issues


def validate_positive_number(
    value: Any,
    field: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        issues.append(
            ValidationIssue(
                field=field,
                code="INVALID_TYPE",
                message=f"{field} must be a number",
            )
        )

        return issues

    if value <= 0:
        issues.append(
            ValidationIssue(
                field=field,
                code="NON_POSITIVE_VALUE",
                message=(
                    f"{field} must be greater "
                    f"than zero"
                ),
            )
        )

    return issues


def validate_percentage(
    value: Any,
    field: str,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        issues.append(
            ValidationIssue(
                field=field,
                code="INVALID_TYPE",
                message=(
                    f"{field} must be a number"
                ),
            )
        )

        return issues

    if value < minimum or value > maximum:
        issues.append(
            ValidationIssue(
                field=field,
                code="OUT_OF_RANGE",
                message=(
                    f"{field} must be between "
                    f"{minimum} and {maximum}"
                ),
            )
        )

    return issues


def validate_cycles(
    cycles: Any,
    minimum_cycles: int = 1,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not isinstance(cycles, list):
        issues.append(
            ValidationIssue(
                field="cycles",
                code="INVALID_TYPE",
                message="cycles must be a list",
            )
        )

        return issues

    if len(cycles) < minimum_cycles:
        issues.append(
            ValidationIssue(
                field="cycles",
                code="INSUFFICIENT_SAMPLE",
                message=(
                    "cycles must contain at least "
                    f"{minimum_cycles} items"
                ),
            )
        )

    for index, cycle in enumerate(cycles):
        if not isinstance(
            cycle,
            (dict, EarningsCycle),
        ):
            issues.append(
                ValidationIssue(
                    field=f"cycles[{index}]",
                    code="INVALID_TYPE",
                    message=(
                        "each cycle must be a "
                        "dictionary or EarningsCycle"
                    ),
                )
            )

    return issues


def validate_entry_exit_prices(
    entry_price: Any,
    exit_price: Any,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    issues.extend(
        validate_positive_number(
            entry_price,
            "entry_price",
        )
    )

    issues.extend(
        validate_positive_number(
            exit_price,
            "exit_price",
        )
    )

    if issues:
        return issues

    if exit_price <= entry_price:
        issues.append(
            ValidationIssue(
                field="exit_price",
                code="INVALID_PRICE_RELATION",
                message=(
                    "exit_price must be greater "
                    "than entry_price"
                ),
            )
        )

    return issues


def validate_analysis_input(
    ticker: Any,
    cycles: Any,
    entry_percentile: Any,
    minimum_cycles: int = 1,
) -> ValidationResult:
    issues: list[ValidationIssue] = []

    issues.extend(
        validate_ticker(ticker)
    )

    issues.extend(
        validate_cycles(
            cycles,
            minimum_cycles=minimum_cycles,
        )
    )

    issues.extend(
        validate_percentage(
            entry_percentile,
            "entry_percentile",
        )
    )

    return ValidationResult(
        is_valid=not issues,
        issues=tuple(issues),
    )


def raise_for_validation(
    result: ValidationResult,
) -> None:
    if not result.is_valid:
        raise ValidationError(
            list(result.issues)
        )
