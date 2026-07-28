"""Lookup-only background-future endpoints around birth observation."""

from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any


FUTURE_ABSENT = "absent"
FUTURE_DONE = "done"
FUTURE_INFLIGHT = "inflight"
FUTURE_STATES = frozenset((FUTURE_ABSENT, FUTURE_DONE, FUTURE_INFLIGHT))

BIRTH_CONTENTION_OMITTED_SOURCES = (
    "game_process",
    "os_scheduler_and_other_processes",
    "native_internal_workers_after_endpoint_ambiguity",
    "candidate_supplemental_and_prewarm_services",
    "allocator_and_page_faults",
)


def future_state(future: Future[Any] | None) -> str:
    """Inspect one future without waiting, cancellation, or result lookup."""

    if future is None:
        return FUTURE_ABSENT
    return FUTURE_DONE if future.done() else FUTURE_INFLIGHT


@dataclass(frozen=True)
class BirthObserverFutureStates:
    corridor: str
    survival: str
    enemy: str

    def __post_init__(self) -> None:
        for value in (self.corridor, self.survival, self.enemy):
            if value not in FUTURE_STATES:
                raise ValueError("invalid birth-observer future state")


@dataclass(frozen=True)
class BirthObserverContention:
    before: BirthObserverFutureStates
    after: BirthObserverFutureStates

    def record(self) -> dict[str, object]:
        return {
            "corridor_future": {
                "before": self.before.corridor,
                "after": self.after.corridor,
            },
            "survival_future": {
                "before": self.before.survival,
                "after": self.after.survival,
            },
            "enemy_future": {
                "before": self.before.enemy,
                "after": self.after.enemy,
            },
            "omitted_sources": list(BIRTH_CONTENTION_OMITTED_SOURCES),
        }


def capture_birth_observer_future_states(
    *,
    corridor_future: Future[Any] | None,
    survival_future: Future[Any] | None,
    enemy_future: Future[Any] | None,
) -> BirthObserverFutureStates:
    """Capture three nonblocking states at one observer endpoint."""

    return BirthObserverFutureStates(
        corridor=future_state(corridor_future),
        survival=future_state(survival_future),
        enemy=future_state(enemy_future),
    )


__all__ = [
    "BIRTH_CONTENTION_OMITTED_SOURCES",
    "FUTURE_ABSENT",
    "FUTURE_DONE",
    "FUTURE_INFLIGHT",
    "FUTURE_STATES",
    "BirthObserverContention",
    "BirthObserverFutureStates",
    "capture_birth_observer_future_states",
    "future_state",
]
