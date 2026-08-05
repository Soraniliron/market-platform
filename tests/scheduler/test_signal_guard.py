from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from scheduler.signal_guard import (
    DuplicateSignalGuard,
)


def build_time(
    minute: int = 0,
) -> datetime:
    return datetime(
        2026,
        8,
        5,
        13,
        minute,
        tzinfo=timezone.utc,
    )


def test_first_signal_is_allowed() -> None:
    guard = DuplicateSignalGuard(
        cooldown_minutes=30,
    )

    result = guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=build_time(),
    )

    assert result.allowed is True
    assert result.reason == "Signal allowed"
    assert result.fingerprint.ticker == "META"
    assert result.fingerprint.status == "buy"


def test_duplicate_signal_is_blocked() -> None:
    guard = DuplicateSignalGuard(
        cooldown_minutes=30,
    )

    first_time = build_time()

    guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=first_time,
    )

    result = guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=(
            first_time
            + timedelta(minutes=10)
        ),
    )

    assert result.allowed is False
    assert (
        result.reason
        == (
            "Duplicate signal blocked "
            "during cooldown"
        )
    )


def test_same_signal_allowed_after_cooldown() -> None:
    guard = DuplicateSignalGuard(
        cooldown_minutes=30,
    )

    first_time = build_time()

    guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=first_time,
    )

    result = guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=(
            first_time
            + timedelta(minutes=30)
        ),
    )

    assert result.allowed is True


def test_changed_signal_is_allowed() -> None:
    guard = DuplicateSignalGuard(
        cooldown_minutes=30,
    )

    current_time = build_time()

    guard.check(
        ticker="META",
        status="WATCH",
        entry_price=None,
        stop_price=None,
        tp1_price=None,
        tp2_price=None,
        now=current_time,
    )

    result = guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=current_time,
    )

    assert result.allowed is True


def test_changed_price_is_allowed() -> None:
    guard = DuplicateSignalGuard(
        cooldown_minutes=30,
    )

    current_time = build_time()

    guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=current_time,
    )

    result = guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.5,
        stop_price=98.5,
        tp1_price=102.5,
        tp2_price=104.5,
        now=current_time,
    )

    assert result.allowed is True


def test_reset_one_ticker() -> None:
    guard = DuplicateSignalGuard(
        cooldown_minutes=30,
    )

    current_time = build_time()

    guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=current_time,
    )

    guard.reset(
        ticker="META",
    )

    result = guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=current_time,
    )

    assert result.allowed is True


def test_reset_all_signals() -> None:
    guard = DuplicateSignalGuard(
        cooldown_minutes=30,
    )

    current_time = build_time()

    guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=current_time,
    )

    guard.check(
        ticker="AAPL",
        status="WATCH",
        entry_price=None,
        stop_price=None,
        tp1_price=None,
        tp2_price=None,
        now=current_time,
    )

    guard.reset()

    meta_result = guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=current_time,
    )

    aapl_result = guard.check(
        ticker="AAPL",
        status="WATCH",
        entry_price=None,
        stop_price=None,
        tp1_price=None,
        tp2_price=None,
        now=current_time,
    )

    assert meta_result.allowed is True
    assert aapl_result.allowed is True


def test_purge_expired_signals() -> None:
    guard = DuplicateSignalGuard(
        cooldown_minutes=30,
    )

    first_time = build_time()

    guard.check(
        ticker="META",
        status="BUY",
        entry_price=100.0,
        stop_price=98.0,
        tp1_price=102.0,
        tp2_price=104.0,
        now=first_time,
    )

    purged_count = guard.purge_expired(
        now=(
            first_time
            + timedelta(minutes=31)
        )
    )

    assert purged_count == 1


def test_rejects_invalid_cooldown() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "cooldown_minutes must be "
            "at least one"
        ),
    ):
        DuplicateSignalGuard(
            cooldown_minutes=0,
        )


def test_rejects_empty_ticker() -> None:
    guard = DuplicateSignalGuard()

    with pytest.raises(
        ValueError,
        match="ticker must not be empty",
    ):
        guard.check(
            ticker="",
            status="BUY",
            entry_price=100.0,
            stop_price=98.0,
            tp1_price=102.0,
            tp2_price=104.0,
        )


def test_rejects_empty_status() -> None:
    guard = DuplicateSignalGuard()

    with pytest.raises(
        ValueError,
        match="status must not be empty",
    ):
        guard.check(
            ticker="META",
            status="",
            entry_price=100.0,
            stop_price=98.0,
            tp1_price=102.0,
            tp2_price=104.0,
        )
        