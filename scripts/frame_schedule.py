#!/usr/bin/env python3
"""Game-independent ordered frame-schedule primitives.

This module deliberately contains no TH08 addresses or subsystem names.  A
game adapter supplies registered phases and their ordered internal events;
simulation and search code can then query one canonical same-frame order.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameEvent:
    key: str
    source_address: int | None = None
    confidence: str = "observed"
    solver_relevant: bool = True
    detail: str = ""


@dataclass(frozen=True)
class FramePhase:
    key: str
    priority: int
    registration_order: int
    events: tuple[FrameEvent, ...]
    source_address: int | None = None
    confidence: str = "observed"
    modes: frozenset[str] = frozenset()

    def enabled_for(self, mode: str) -> bool:
        return not self.modes or mode in self.modes


@dataclass(frozen=True)
class OrderedEvent:
    phase_key: str
    phase_priority: int
    phase_registration_order: int
    event_index: int
    event: FrameEvent

    @property
    def key(self) -> str:
        return self.event.key


@dataclass(frozen=True)
class FrameSchedule:
    """A stable ordered schedule suitable for one fixed simulation tick.

    Lower priorities execute first.  Equal priorities preserve explicit
    registration order, matching engines that keep stable callback lists.
    Empty ``modes`` means a phase is common to every adapter-defined mode.
    """

    phases: tuple[FramePhase, ...]

    def __post_init__(self) -> None:
        phase_keys = [phase.key for phase in self.phases]
        if len(set(phase_keys)) != len(phase_keys):
            raise ValueError("phase keys must be unique")
        for phase in self.phases:
            if not phase.key:
                raise ValueError("phase key cannot be empty")
            event_keys = [event.key for event in phase.events]
            if len(set(event_keys)) != len(event_keys):
                raise ValueError(f"event keys in {phase.key!r} must be unique")

    def phases_for(self, mode: str) -> tuple[FramePhase, ...]:
        enabled = (phase for phase in self.phases if phase.enabled_for(mode))
        return tuple(
            sorted(
                enabled,
                key=lambda phase: (phase.priority, phase.registration_order),
            )
        )

    def events_for(
        self, mode: str, *, solver_only: bool = False
    ) -> tuple[OrderedEvent, ...]:
        result: list[OrderedEvent] = []
        for phase in self.phases_for(mode):
            for event_index, event in enumerate(phase.events):
                if solver_only and not event.solver_relevant:
                    continue
                result.append(
                    OrderedEvent(
                        phase_key=phase.key,
                        phase_priority=phase.priority,
                        phase_registration_order=phase.registration_order,
                        event_index=event_index,
                        event=event,
                    )
                )
        return tuple(result)

    def event_position(self, mode: str, event_key: str) -> int:
        matches = [
            index
            for index, event in enumerate(self.events_for(mode))
            if event.key == event_key
        ]
        if not matches:
            raise KeyError(event_key)
        if len(matches) != 1:
            raise ValueError(f"event key {event_key!r} is ambiguous")
        return matches[0]

    def happens_before(self, mode: str, first: str, second: str) -> bool:
        return self.event_position(mode, first) < self.event_position(mode, second)


def stable_priority_order(phases: tuple[FramePhase, ...]) -> tuple[str, ...]:
    """Return phase keys in engine order without requiring a full schedule."""

    return tuple(
        phase.key
        for phase in sorted(
            phases,
            key=lambda phase: (phase.priority, phase.registration_order),
        )
    )
