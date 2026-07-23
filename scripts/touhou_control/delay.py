"""Online identification of frame-quantized input actuation delay."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass


def _nearest_rank(values: tuple[int, ...], quantile: float) -> int:
    if not values:
        raise ValueError("quantile requires at least one value")
    ordered = sorted(values)
    rank = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[rank]


@dataclass(frozen=True)
class DelayEstimate:
    nominal: int
    support: tuple[int, ...]
    computation_samples: int
    pickup_samples: int
    end_to_end_samples: int
    guard_active: bool
    overruns: int
    censored: int


@dataclass(frozen=True)
class _PendingActuation:
    snapshot_frame: int
    issue_frame: int
    expected_mask: int
    support_high: int


class AdaptiveControlDelay:
    """Learn snapshot-to-visible-input delay from censored live observations."""

    def __init__(
        self,
        *,
        supported_mask: int,
        minimum: int = 1,
        maximum: int = 4,
        window: int = 120,
        guard_frames: int = 600,
        default_pickup_frames: int = 1,
    ) -> None:
        if minimum < 0 or maximum < minimum:
            raise ValueError("invalid delay bounds")
        if window <= 0 or guard_frames <= 0:
            raise ValueError("window and guard duration must be positive")
        self.supported_mask = supported_mask
        self.minimum = minimum
        self.maximum = maximum
        self.guard_frames = guard_frames
        self.default_pickup_frames = default_pickup_frames
        self.computation_lags: deque[int] = deque(maxlen=window)
        self.pickup_lags: deque[int] = deque(maxlen=window)
        self.end_to_end_lags: deque[int] = deque(maxlen=window)
        self.pending: _PendingActuation | None = None
        self.guard_until = -1
        self.overruns = 0
        self.censored = 0

    def reset(self) -> None:
        self.computation_lags.clear()
        self.pickup_lags.clear()
        self.end_to_end_lags.clear()
        self.pending = None
        self.guard_until = -1
        self.overruns = 0
        self.censored = 0

    def observe(self, *, frame: int, input_mask: int) -> None:
        pending = self.pending
        if pending is None:
            return
        if input_mask & self.supported_mask == pending.expected_mask:
            pickup_lag = frame - pending.issue_frame
            end_to_end_lag = frame - pending.snapshot_frame
            if 0 <= pickup_lag < 120 and 0 < end_to_end_lag < 120:
                self.pickup_lags.append(pickup_lag)
                self.end_to_end_lags.append(end_to_end_lag)
                if end_to_end_lag > pending.support_high:
                    self.overruns += 1
                    self.guard_until = max(
                        self.guard_until,
                        frame + self.guard_frames,
                    )
            self.pending = None
        elif frame - pending.issue_frame >= 12:
            self.censored += 1
            self.pending = None

    def issued(
        self,
        *,
        snapshot_frame: int,
        issue_frame: int,
        expected_mask: int,
        support_high: int,
    ) -> None:
        if self.pending is not None:
            self.censored += 1
        self.pending = _PendingActuation(
            snapshot_frame=snapshot_frame,
            issue_frame=issue_frame,
            expected_mask=expected_mask & self.supported_mask,
            support_high=support_high,
        )

    def record_computation_lag(self, lag: int) -> None:
        if 0 <= lag < 120:
            self.computation_lags.append(lag)

    def register_hit(self, frame: int) -> None:
        self.guard_until = max(
            self.guard_until,
            frame + self.guard_frames,
        )

    def estimate(self, *, frame: int, default: int = 2) -> DelayEstimate:
        guard_active = frame <= self.guard_until
        if self.end_to_end_lags:
            values = tuple(self.end_to_end_lags)
            low = _nearest_rank(values, 0.10)
            nominal = _nearest_rank(values, 0.75)
            high = _nearest_rank(values, 0.95)
            if len(values) < 12:
                high += 1
            high = max(high, max(values[-8:]))
        elif self.computation_lags:
            computation = tuple(self.computation_lags)
            pickup = tuple(self.pickup_lags) or (self.default_pickup_frames,)
            low = _nearest_rank(computation, 0.10) + _nearest_rank(pickup, 0.10)
            nominal = _nearest_rank(computation, 0.75) + _nearest_rank(
                pickup, 0.50
            )
            high = _nearest_rank(computation, 0.95) + _nearest_rank(
                pickup, 0.95
            )
            high = max(high, nominal + 1)
        else:
            low = default
            nominal = default + 1
            high = default + 1
        if guard_active:
            high += 1
        low = max(self.minimum, min(self.maximum, low))
        high = max(low, min(self.maximum, high))
        nominal = max(low, min(high, nominal))
        return DelayEstimate(
            nominal=nominal,
            support=tuple(range(low, high + 1)),
            computation_samples=len(self.computation_lags),
            pickup_samples=len(self.pickup_lags),
            end_to_end_samples=len(self.end_to_end_lags),
            guard_active=guard_active,
            overruns=self.overruns,
            censored=self.censored,
        )
