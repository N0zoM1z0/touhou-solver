"""Game-neutral frame-window alignment for asynchronously captured sensors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameWindow:
    """Inclusive frame-counter bounds around one sensor capture."""

    before: int
    after: int

    def __post_init__(self) -> None:
        if self.before < 0 or self.after < self.before:
            raise ValueError("invalid sensor frame window")

    @property
    def span(self) -> int:
        return self.after - self.before


@dataclass(frozen=True)
class HazardEpochAlignment:
    """Align a hazard snapshot and event snapshot to a source state."""

    source_frame: int
    hazard_window: FrameWindow
    current_frame: int
    event_window: FrameWindow | None = None

    def __post_init__(self) -> None:
        if self.source_frame < 0 or self.current_frame < 0:
            raise ValueError("frame counters cannot be negative")

    @property
    def source_to_hazard_lag(self) -> int:
        """Updates between the source state and hazard coordinates."""

        return max(0, self.hazard_window.after - self.source_frame)

    @property
    def hazard_age(self) -> int:
        """Updates between hazard coordinates and the planning epoch."""

        return max(0, self.current_frame - self.hazard_window.after)

    @property
    def event_frame_offset(self) -> int:
        """Rebase event-relative frames to the hazard coordinate epoch."""

        if self.event_window is None:
            return 0
        return max(0, self.event_window.after - self.hazard_window.after)

    @property
    def event_frame_uncertainty(self) -> int:
        """Conservative timing width contributed by both capture windows."""

        if self.event_window is None:
            return self.hazard_window.span
        return self.hazard_window.span + self.event_window.span
