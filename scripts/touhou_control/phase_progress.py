"""Game-neutral phase-progress observations and safe objective selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable


@dataclass(frozen=True)
class PhaseProgressState:
    """One stable observation of a finite-health or finite-time phase."""

    key: Hashable
    frame: int
    current_health: int
    phase_start_health: int
    phase_end_health: int
    elapsed_frames: float
    timeout_frames: int | None
    damageable: bool
    stable: bool = True

    @property
    def health_span(self) -> int:
        return max(0, self.phase_start_health - self.phase_end_health)

    @property
    def health_remaining(self) -> int:
        return max(0, self.current_health - self.phase_end_health)

    @property
    def health_progress(self) -> float | None:
        if self.health_span <= 0:
            return None
        completed = self.phase_start_health - self.current_health
        return min(1.0, max(0.0, completed / self.health_span))

    @property
    def time_remaining(self) -> float | None:
        if self.timeout_frames is None or self.timeout_frames < 0:
            return None
        return max(0.0, self.timeout_frames - self.elapsed_frames)


@dataclass(frozen=True)
class PhaseProgressObservation:
    """A differential observation that never calls a reset "damage"."""

    state: PhaseProgressState
    status: str
    frame_delta: int | None = None
    health_delta: int | None = None
    damage_per_frame: float | None = None


class PhaseProgressTracker:
    """Compare consecutive stable samples from the same phase."""

    def __init__(self) -> None:
        self._previous: PhaseProgressState | None = None

    def reset(self) -> None:
        self._previous = None

    def observe(
        self,
        state: PhaseProgressState | None,
    ) -> PhaseProgressObservation | None:
        if state is None:
            self._previous = None
            return None
        previous = self._previous
        self._previous = state if state.stable else None
        if not state.stable:
            return PhaseProgressObservation(state, "unstable")
        if previous is None:
            return PhaseProgressObservation(state, "initial")
        if previous.key != state.key:
            return PhaseProgressObservation(state, "phase_changed")
        frame_delta = state.frame - previous.frame
        if (
            frame_delta <= 0
            or state.elapsed_frames < previous.elapsed_frames
            or state.current_health > previous.current_health
        ):
            return PhaseProgressObservation(state, "phase_reset")
        health_delta = previous.current_health - state.current_health
        return PhaseProgressObservation(
            state=state,
            status="comparable",
            frame_delta=frame_delta,
            health_delta=health_delta,
            damage_per_frame=health_delta / frame_delta,
        )


@dataclass(frozen=True)
class ProgressCandidate:
    """A soft progress objective guarded by hard survival certificates."""

    action: str
    progress_cost: float
    viable: bool
    issue_collisions: int
    issue_min_clearance: float
    baseline_rank: tuple[object, ...]


def select_progress_action(
    candidates: tuple[ProgressCandidate, ...],
) -> ProgressCandidate | None:
    """Select progress only inside the already viable, issue-safe set."""

    eligible = tuple(
        candidate
        for candidate in candidates
        if (
            candidate.viable
            and candidate.issue_collisions == 0
            and candidate.issue_min_clearance >= 0.0
        )
    )
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda candidate: (
            candidate.progress_cost,
            candidate.baseline_rank,
            candidate.action,
        ),
    )
