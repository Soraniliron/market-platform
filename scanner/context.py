from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeContext:
    current_volume: float
    average_volume_same_window: float
    previous_window_volume: float | None = None


@dataclass(frozen=True)
class MarketContext:
    volume: VolumeContext | None = None
    