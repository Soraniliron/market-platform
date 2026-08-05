from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock


@dataclass(frozen=True)
class SignalFingerprint:
    ticker: str
    status: str
    entry_price: float | None
    stop_price: float | None
    tp1_price: float | None
    tp2_price: float | None


@dataclass(frozen=True)
class SignalGuardResult:
    allowed: bool
    reason: str
    fingerprint: SignalFingerprint


class DuplicateSignalGuard:
    def __init__(
        self,
        cooldown_minutes: int = 30,
    ) -> None:
        if cooldown_minutes < 1:
            raise ValueError(
                "cooldown_minutes must be at least one"
            )

        self.cooldown = timedelta(
            minutes=cooldown_minutes
        )

        self._last_sent: dict[
            SignalFingerprint,
            datetime,
        ] = {}

        self._lock = Lock()

    def check(
        self,
        ticker: str,
        status: str,
        entry_price: float | None,
        stop_price: float | None,
        tp1_price: float | None,
        tp2_price: float | None,
        now: datetime | None = None,
    ) -> SignalGuardResult:
        if not ticker:
            raise ValueError(
                "ticker must not be empty"
            )

        if not status:
            raise ValueError(
                "status must not be empty"
            )

        current_time = (
            now
            if now is not None
            else datetime.now(timezone.utc)
        )

        if current_time.tzinfo is None:
            current_time = current_time.replace(
                tzinfo=timezone.utc
            )

        fingerprint = SignalFingerprint(
            ticker=ticker.upper(),
            status=status.lower(),
            entry_price=entry_price,
            stop_price=stop_price,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
        )

        with self._lock:
            previous_time = self._last_sent.get(
                fingerprint
            )

            if previous_time is not None:
                elapsed = (
                    current_time
                    - previous_time
                )

                if elapsed < self.cooldown:
                    return SignalGuardResult(
                        allowed=False,
                        reason=(
                            "Duplicate signal blocked "
                            "during cooldown"
                        ),
                        fingerprint=fingerprint,
                    )

            self._last_sent[
                fingerprint
            ] = current_time

        return SignalGuardResult(
            allowed=True,
            reason="Signal allowed",
            fingerprint=fingerprint,
        )

    def reset(
        self,
        ticker: str | None = None,
    ) -> None:
        with self._lock:
            if ticker is None:
                self._last_sent.clear()
                return

            normalized_ticker = (
                ticker.upper()
            )

            keys_to_remove = [
                fingerprint
                for fingerprint
                in self._last_sent
                if fingerprint.ticker
                == normalized_ticker
            ]

            for fingerprint in keys_to_remove:
                del self._last_sent[
                    fingerprint
                ]

    def purge_expired(
        self,
        now: datetime | None = None,
    ) -> int:
        current_time = (
            now
            if now is not None
            else datetime.now(timezone.utc)
        )

        if current_time.tzinfo is None:
            current_time = current_time.replace(
                tzinfo=timezone.utc
            )

        with self._lock:
            expired = [
                fingerprint
                for fingerprint, sent_at
                in self._last_sent.items()
                if (
                    current_time - sent_at
                    >= self.cooldown
                )
            ]

            for fingerprint in expired:
                del self._last_sent[
                    fingerprint
                ]

        return len(expired)
        