#!/usr/bin/env python3
"""Timing primitives for rolling asynchronous control policies."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field


@dataclass
class AsyncPolicyLead:
    """Estimate how far a policy epoch must lead its observation snapshot."""

    frames_per_second: float = 60.0
    initial_frames: int = 80
    overlap_frames: int = 8
    minimum_frames: int = 48
    maximum_frames: int = 180
    window: int = 16
    _solve_frames: deque[int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.frames_per_second <= 0.0:
            raise ValueError("frames per second must be positive")
        if self.overlap_frames < 0 or self.minimum_frames < 0:
            raise ValueError("policy lead bounds cannot be negative")
        if not self.minimum_frames <= self.initial_frames <= self.maximum_frames:
            raise ValueError("initial policy lead is outside its bounds")
        if self.window < 1:
            raise ValueError("policy lead window must be positive")
        self._solve_frames = deque(maxlen=self.window)

    @property
    def frames(self) -> int:
        if not self._solve_frames:
            return self.initial_frames
        ordered = sorted(self._solve_frames)
        rank = max(0, math.ceil(0.90 * len(ordered)) - 1)
        estimate = ordered[rank] - self.overlap_frames
        if len(ordered) < 4:
            estimate = max(estimate, self.initial_frames)
        return min(
            self.maximum_frames,
            max(self.minimum_frames, estimate),
        )

    def observe(self, solve_ms: float) -> None:
        if not math.isfinite(solve_ms) or solve_ms < 0.0:
            raise ValueError("solve duration must be finite and nonnegative")
        self._solve_frames.append(
            math.ceil(solve_ms * self.frames_per_second / 1000.0)
        )

    @property
    def sample_count(self) -> int:
        return len(self._solve_frames)

    @property
    def p90_solve_frames(self) -> int | None:
        if not self._solve_frames:
            return None
        ordered = sorted(self._solve_frames)
        rank = max(0, math.ceil(0.90 * len(ordered)) - 1)
        return ordered[rank]

    def serial_coverage_margin(self, horizon_frames: int) -> int:
        """Return policy frames left after the slower submit interval."""

        if horizon_frames <= 0:
            raise ValueError("policy horizon must be positive")
        solve_frames = self.p90_solve_frames or self.initial_frames
        return horizon_frames - max(self.frames, solve_frames)

    def serial_worker_serviceable(self, horizon_frames: int) -> bool:
        return self.serial_coverage_margin(horizon_frames) > 0


def delay_support_envelope(
    support: tuple[int, ...],
    *,
    minimum: int,
    maximum: int,
    padding: int = 1,
) -> tuple[int, ...]:
    """Pad a contiguous delay estimate for one async solve interval."""

    if (
        minimum < 0
        or maximum < minimum
        or padding < 0
        or not support
        or tuple(range(support[0], support[-1] + 1)) != support
        or support[0] < minimum
        or support[-1] > maximum
    ):
        raise ValueError("invalid delay support envelope")
    low = max(minimum, support[0] - padding)
    high = min(maximum, support[-1] + padding)
    return tuple(range(low, high + 1))


__all__ = ["AsyncPolicyLead", "delay_support_envelope"]
