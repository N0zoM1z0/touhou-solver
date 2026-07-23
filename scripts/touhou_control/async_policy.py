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


__all__ = ["AsyncPolicyLead"]
