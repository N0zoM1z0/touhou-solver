#!/usr/bin/env python3
"""Game-neutral deterministic execution over an observed frame schedule."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from frame_schedule import FrameSchedule, OrderedEvent


StateT = TypeVar("StateT")
ControlT = TypeVar("ControlT")


@dataclass(frozen=True)
class EventContext:
    frame_index: int
    mode: str
    ordered_event: OrderedEvent

    @property
    def event_key(self) -> str:
        return self.ordered_event.key


class EventHandler(Protocol[StateT, ControlT]):
    def __call__(
        self,
        state: StateT,
        control: ControlT,
        context: EventContext,
    ) -> StateT: ...


StateObserver = Callable[[EventContext, StateT], None]


@dataclass(frozen=True)
class FrameExecution(Generic[StateT]):
    state: StateT
    executed_events: tuple[str, ...]


class DeterministicFrameExecutor(Generic[StateT, ControlT]):
    """Execute selected schedule events in their native stable order.

    ``event_keys`` supports incremental reconstruction: a game adapter can
    integrate one verified subsystem at a time while still inheriting the
    full engine's same-frame ordering. Every selected event must have a
    handler; absent gameplay behavior is never silently skipped.
    """

    def __init__(
        self,
        *,
        schedule: FrameSchedule,
        mode: str,
        handlers: Mapping[str, EventHandler[StateT, ControlT]],
        event_keys: tuple[str, ...] | None = None,
        solver_only: bool = True,
    ) -> None:
        scheduled = schedule.events_for(mode, solver_only=solver_only)
        available = {event.key for event in scheduled}
        selected = available if event_keys is None else set(event_keys)
        missing_from_schedule = selected - available
        if missing_from_schedule:
            raise ValueError(
                "selected events are absent from the enabled schedule: "
                f"{sorted(missing_from_schedule)}"
            )
        missing_handlers = selected - handlers.keys()
        if missing_handlers:
            raise ValueError(
                f"selected events have no handler: {sorted(missing_handlers)}"
            )
        self._mode = mode
        self._handlers = dict(handlers)
        self._events = tuple(event for event in scheduled if event.key in selected)

    @property
    def event_order(self) -> tuple[str, ...]:
        return tuple(event.key for event in self._events)

    def step(
        self,
        state: StateT,
        control: ControlT,
        *,
        frame_index: int,
        observer: StateObserver[StateT] | None = None,
    ) -> FrameExecution[StateT]:
        if frame_index < 0:
            raise ValueError("frame index must be non-negative")
        current = state
        executed: list[str] = []
        for event in self._events:
            context = EventContext(frame_index, self._mode, event)
            current = self._handlers[event.key](current, control, context)
            executed.append(event.key)
            if observer is not None:
                observer(context, current)
        return FrameExecution(current, tuple(executed))
