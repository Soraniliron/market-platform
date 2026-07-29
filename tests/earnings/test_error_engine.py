import pytest

from earnings.error_engine import (
    execute_safely,
    error_response,
    success_response,
)


def test_success_response():
    result = success_response(
        {"value": 10}
    )

    assert result.success is True
    assert result.data == {"value": 10}
    assert result.error is None


def test_error_response():
    result = error_response(
        "TEST_ERROR",
        "Something failed",
    )

    assert result.success is False
    assert result.data is None
    assert result.error.code == "TEST_ERROR"
    assert result.error.message == "Something failed"


def test_execute_safely_success():
    def handler():
        return {"answer": 42}

    result = execute_safely(handler)

    assert result.success is True
    assert result.data == {"answer": 42}


def test_execute_safely_validation_error():
    def handler():
        raise ValueError("invalid input")

    result = execute_safely(handler)

    assert result.success is False
    assert result.error.code == "VALIDATION_ERROR"


def test_execute_safely_engine_error():
    def handler():
        raise RuntimeError("boom")

    result = execute_safely(handler)

    assert result.success is False
    assert result.error.code == "ENGINE_ERROR"


def test_execute_safely_invalid_handler():
    result = execute_safely(None)

    assert result.success is False
    assert result.error.code == "INVALID_HANDLER"


def test_execute_safely_invalid_output():
    def handler():
        return 123

    result = execute_safely(handler)

    assert result.success is False
    assert result.error.code == "INVALID_ENGINE_OUTPUT"


def test_success_response_rejects_non_dict():
    with pytest.raises(ValueError):
        success_response(123)


def test_error_response_requires_code():
    with pytest.raises(ValueError):
        error_response("", "message")


def test_error_response_requires_message():
    with pytest.raises(ValueError):
        error_response("ERR", "")
