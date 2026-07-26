"""Authority-free semantic input-clock episode tracking.

This module deliberately knows nothing about TH08 addresses, input masks, or
planner epochs.  It groups a tri-state native semantic observation into
episodes for shadow telemetry only; it never returns an actuation directive.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Hashable, Literal


@dataclass(frozen=True)
class SemanticClockObservation:
    """One normalized native observation at a monotonic instant."""

    monotonic_ns: int
    physical_frame: int
    semantic_active: bool | None
    context: Hashable
    position: tuple[float, float] | None = None
    active_input: int | None = None


@dataclass(frozen=True)
class SemanticClockEvent:
    """A begin, completed end, or right-censored episode boundary."""

    kind: Literal["begin", "end", "censored"]
    episode_id: int
    start: SemanticClockObservation
    observation: SemanticClockObservation
    pulse_count: int
    reason: str

    @property
    def duration_ns(self) -> int:
        return max(0, self.observation.monotonic_ns - self.start.monotonic_ns)

    @property
    def displacement(self) -> float | None:
        if self.start.position is None or self.observation.position is None:
            return None
        return math.hypot(
            self.observation.position[0] - self.start.position[0],
            self.observation.position[1] - self.start.position[1],
        )


@dataclass
class _ActiveEpisode:
    episode_id: int
    start: SemanticClockObservation
    last_known: SemanticClockObservation
    pulse_count: int = 0


class SemanticInputClockTracker:
    """Group semantic-active spans without granting them control authority."""

    def __init__(self) -> None:
        self._next_episode_id = 1
        self._active: _ActiveEpisode | None = None

    @property
    def active_episode_id(self) -> int | None:
        return self._active.episode_id if self._active is not None else None

    @property
    def active_pulse_count(self) -> int:
        return self._active.pulse_count if self._active is not None else 0

    def observe(
        self,
        observation: SemanticClockObservation,
    ) -> tuple[SemanticClockEvent, ...]:
        events: list[SemanticClockEvent] = []
        active = self._active
        boundary_reason = None
        if active is not None:
            if observation.context != active.start.context:
                boundary_reason = "context_changed"
            elif observation.physical_frame != active.start.physical_frame:
                # The native gate forbids manager-frame progress while this
                # frozen-frame episode is active.  A changed frame therefore
                # proves the old episode ended, but does not prove that an
                # inactive semantic sample was observed between two active
                # states.  Preserve that distinction as right-censoring.
                boundary_reason = "physical_frame_changed"
        if active is not None and boundary_reason is not None:
            # The current observation belongs to the new frame/context.  The
            # old episode is right-censored after its last semantically known
            # sample; using the boundary sample here would incorrectly charge
            # next-episode time and displacement to both episodes.
            events.append(
                self._finish(
                    active.last_known,
                    kind="censored",
                    reason=boundary_reason,
                )
            )
            active = None

        if observation.semantic_active is True:
            if active is None:
                active = _ActiveEpisode(
                    episode_id=self._next_episode_id,
                    start=observation,
                    last_known=observation,
                )
                self._next_episode_id += 1
                self._active = active
                events.append(
                    SemanticClockEvent(
                        kind="begin",
                        episode_id=active.episode_id,
                        start=observation,
                        observation=observation,
                        pulse_count=0,
                        reason="semantic_active",
                    )
                )
            else:
                active.last_known = observation
        elif observation.semantic_active is False and active is not None:
            events.append(
                self._finish(
                    observation,
                    kind="end",
                    reason="semantic_inactive",
                )
            )
        elif observation.semantic_active is None and active is not None:
            # Unknown is not evidence of an inactive edge, but retaining its
            # timestamp/position would also make the completed boundary look
            # observed.  Keep the last semantically known sample unchanged.
            pass
        return tuple(events)

    def mark_pulse(self) -> int | None:
        """Attach a wall-pulse label to the open episode, if one exists."""

        if self._active is None:
            return None
        self._active.pulse_count += 1
        return self._active.episode_id

    def censor(
        self,
        observation: SemanticClockObservation,
        *,
        reason: str,
    ) -> SemanticClockEvent | None:
        if self._active is None:
            return None
        return self._finish(observation, kind="censored", reason=reason)

    def _finish(
        self,
        observation: SemanticClockObservation,
        *,
        kind: Literal["end", "censored"],
        reason: str,
    ) -> SemanticClockEvent:
        active = self._active
        assert active is not None
        event = SemanticClockEvent(
            kind=kind,
            episode_id=active.episode_id,
            start=active.start,
            observation=observation,
            pulse_count=active.pulse_count,
            reason=reason,
        )
        self._active = None
        return event
