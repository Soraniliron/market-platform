import pytest

from earnings.validation_engine import (
    ValidationError,
    raise_for_validation,
    validate_analysis_input,
    validate_cycles,
    validate_entry_exit_prices,
    validate_percentage,
    validate_positive_number,
    validate_ticker,
)


def test_validate_ticker_accepts_valid_value():
    assert validate_ticker("MSFT") == []


def test_validate_ticker_rejects_empty():
    issues = validate_ticker("")
    assert issues[0].code == "EMPTY_VALUE"


def test_validate_positive_number():
    assert validate_positive_number(10, "price") == []
    assert validate_positive_number(-1, "price")[0].code == "NON_POSITIVE_VALUE"


def test_validate_percentage():
    assert validate_percentage(55, "entry") == []
    assert validate_percentage(120, "entry")[0].code == "OUT_OF_RANGE"


def test_validate_cycles():
    assert validate_cycles([{}], 1) == []
    assert validate_cycles([], 1)[0].code == "INSUFFICIENT_SAMPLE"


def test_validate_entry_exit_prices():
    assert validate_entry_exit_prices(100, 110) == []

    issues = validate_entry_exit_prices(100, 90)
    assert issues[0].code == "INVALID_PRICE_RELATION"


def test_validate_analysis_input_success():
    result = validate_analysis_input(
        ticker="MSFT",
        cycles=[{}],
        entry_percentile=55,
    )

    assert result.is_valid
    assert result.issues == ()


def test_validate_analysis_input_failure():
    result = validate_analysis_input(
        ticker="",
        cycles=[],
        entry_percentile=150,
    )

    assert not result.is_valid
    assert len(result.issues) == 3


def test_raise_for_validation():
    result = validate_analysis_input(
        ticker="",
        cycles=[],
        entry_percentile=150,
    )

    with pytest.raises(ValidationError):
        raise_for_validation(result)
