"""Ordered TH08 timeline allocation and initial-VM lifecycle lowering.

The native producer at ``enemy_spawn_from_timeline`` (0x0042A4E0) selects
the first inactive ordinary-enemy slot, copies the template, starts the main
ECL VM, and executes it once immediately.  A return value of ``-1`` retires
that allocation before the timeline scheduler continues.

This module owns only that observed allocation boundary.  The supplied
initial-VM executor remains an explicit dependency until the complete enemy
ECL interpreter and its native root are connected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from th08_future_body_identity import (
    GENERATION_LIMIT,
    Route2BodyGenerationIdentity,
    Route2SlotLifecycleEvent,
    Route2SlotLifecycleStep,
    Route2SlotLifetimeLedger,
    TH08_ORDINARY_ENEMY_POOL_SIZE,
    advance_route2_slot_lifetimes,
)
from th08_timeline_model import TimelineSpawnRequest


TIMELINE_SPAWN_LIFECYCLE_SCHEMA = (
    "th08-timeline-spawn-lifecycle-step-v1"
)
TIMELINE_SPAWN_OUTCOME_SCHEMA = "th08-timeline-spawn-outcome-v1"


class InitialEnemyVmExecutor(Protocol):
    """Execute the freshly initialized main VM exactly once."""

    def __call__(
        self,
        request: TimelineSpawnRequest,
        identity: Route2BodyGenerationIdentity,
    ) -> int:
        ...


@dataclass(frozen=True)
class Route2TimelineSpawnOutcome:
    request: TimelineSpawnRequest
    identity: Route2BodyGenerationIdentity | None
    initial_vm_return: int | None
    survived_initial_vm: bool
    pool_full: bool
    schema: str = TIMELINE_SPAWN_OUTCOME_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != TIMELINE_SPAWN_OUTCOME_SCHEMA:
            raise ValueError("unsupported timeline-spawn outcome schema")
        if type(self.request) is not TimelineSpawnRequest:
            raise ValueError("timeline-spawn outcome requires an exact request")
        if self.pool_full:
            if (
                self.identity is not None
                or self.initial_vm_return is not None
                or self.survived_initial_vm
            ):
                raise ValueError("pool-full spawn cannot own an allocation")
            return
        if type(self.identity) is not Route2BodyGenerationIdentity:
            raise ValueError("allocated spawn requires a generation identity")
        if type(self.initial_vm_return) is not int:
            raise ValueError("allocated spawn requires an exact VM result")
        if self.survived_initial_vm != (self.initial_vm_return != -1):
            raise ValueError("initial-VM survival disagrees with its return")


@dataclass(frozen=True)
class Route2TimelineSpawnLifecycleStep:
    physical_update: int
    outcomes: tuple[Route2TimelineSpawnOutcome, ...]
    lifecycle: Route2SlotLifecycleStep
    schema: str = TIMELINE_SPAWN_LIFECYCLE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != TIMELINE_SPAWN_LIFECYCLE_SCHEMA:
            raise ValueError("unsupported timeline-spawn lifecycle schema")
        if (
            type(self.physical_update) is not int
            or self.physical_update < 0
        ):
            raise ValueError("timeline-spawn physical update must be nonnegative")
        if type(self.outcomes) is not tuple or any(
            type(outcome) is not Route2TimelineSpawnOutcome
            for outcome in self.outcomes
        ):
            raise ValueError("timeline-spawn outcomes must be an exact tuple")
        if self.lifecycle.successor.current_physical_update != (
            self.physical_update
        ):
            raise ValueError("timeline-spawn lifecycle update disagrees")


def _next_identity(
    *,
    slot: int,
    seen: list[bool],
    generations: list[int],
) -> Route2BodyGenerationIdentity:
    generation = generations[slot]
    if seen[slot]:
        if generation == GENERATION_LIMIT - 1:
            raise ValueError("allocation generation overflow")
        generation += 1
        generations[slot] = generation
    else:
        seen[slot] = True
    return Route2BodyGenerationIdentity(
        slot=slot,
        allocation_generation=generation,
    )


def execute_route2_timeline_spawn_lifecycles(
    ledger: Route2SlotLifetimeLedger,
    *,
    next_physical_update: int,
    spawns: tuple[TimelineSpawnRequest, ...],
    initial_vm_executor: InitialEnemyVmExecutor,
    observed_active_slots: tuple[int, ...] | None = None,
) -> Route2TimelineSpawnLifecycleStep:
    """Lower one native-order timeline spawn batch into ledger events.

    Pool search is repeated after every initial-VM result.  Consequently an
    allocate/initial-VM-``-1`` pair exposes that same slot to a later spawn in
    this update, exactly as the native scheduler does.
    """

    if type(ledger) is not Route2SlotLifetimeLedger:
        raise ValueError("timeline-spawn predecessor must be an exact ledger")
    if (
        type(next_physical_update) is not int
        or next_physical_update != ledger.current_physical_update + 1
    ):
        raise ValueError("timeline-spawn updates must be contiguous")
    if type(spawns) is not tuple or any(
        type(spawn) is not TimelineSpawnRequest for spawn in spawns
    ):
        raise ValueError("timeline spawns must be an immutable exact tuple")
    if not callable(initial_vm_executor):
        raise ValueError("initial VM executor must be callable")

    active = list(ledger.active)
    seen = list(ledger.seen_lifetime)
    generations = list(ledger.generations)
    events: list[Route2SlotLifecycleEvent] = []
    outcomes: list[Route2TimelineSpawnOutcome] = []

    for request in spawns:
        slot = next(
            (
                candidate
                for candidate in range(TH08_ORDINARY_ENEMY_POOL_SIZE)
                if not active[candidate]
            ),
            None,
        )
        if slot is None:
            outcomes.append(
                Route2TimelineSpawnOutcome(
                    request=request,
                    identity=None,
                    initial_vm_return=None,
                    survived_initial_vm=False,
                    pool_full=True,
                )
            )
            continue

        identity = _next_identity(
            slot=slot,
            seen=seen,
            generations=generations,
        )
        events.append(
            Route2SlotLifecycleEvent(
                physical_update=next_physical_update,
                sequence=len(events),
                kind="allocate",
                slot=slot,
                source=(
                    "enemy_spawn_from_timeline:"
                    f"timeline={request.timeline_index}:"
                    f"offset=0x{request.instruction_offset:x}"
                ),
            )
        )
        active[slot] = True
        initial_vm_return = initial_vm_executor(request, identity)
        if type(initial_vm_return) is not int:
            raise ValueError("initial VM executor must return an exact integer")
        survived = initial_vm_return != -1
        if not survived:
            events.append(
                Route2SlotLifecycleEvent(
                    physical_update=next_physical_update,
                    sequence=len(events),
                    kind="retire",
                    slot=slot,
                    source=(
                        "enemy_spawn_from_timeline:"
                        "initial_enemy_ecl_vm_return_minus_one"
                    ),
                )
            )
            active[slot] = False
        outcomes.append(
            Route2TimelineSpawnOutcome(
                request=request,
                identity=identity,
                initial_vm_return=initial_vm_return,
                survived_initial_vm=survived,
                pool_full=False,
            )
        )

    lifecycle = advance_route2_slot_lifetimes(
        ledger,
        next_physical_update=next_physical_update,
        events=tuple(events),
        observed_active_slots=observed_active_slots,
    )
    return Route2TimelineSpawnLifecycleStep(
        physical_update=next_physical_update,
        outcomes=tuple(outcomes),
        lifecycle=lifecycle,
    )


__all__ = [
    "InitialEnemyVmExecutor",
    "Route2TimelineSpawnLifecycleStep",
    "Route2TimelineSpawnOutcome",
    "TIMELINE_SPAWN_LIFECYCLE_SCHEMA",
    "TIMELINE_SPAWN_OUTCOME_SCHEMA",
    "execute_route2_timeline_spawn_lifecycles",
]
