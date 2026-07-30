"""Root-relative generational identities for TH08 ordinary enemy slots.

The native pool reuses one of 480 fixed slots.  A slot pointer is therefore
not a body identity across time.  This module deliberately consumes ordered
allocation/retirement events rather than trying to infer lifetimes from
frame-boundary active bits.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from th08_future_body_schedule import Route2FutureBodySample


TH08_ORDINARY_ENEMY_POOL_SIZE = 480
BODY_IDENTITY_SCHEMA = "th08-ordinary-enemy-generation-identity-v1"
LIFETIME_LEDGER_SCHEMA = "th08-ordinary-enemy-lifetime-ledger-v1"
LIFECYCLE_EVENT_SCHEMA = "th08-ordinary-enemy-lifecycle-event-v1"
LIFECYCLE_STEP_SCHEMA = "th08-ordinary-enemy-lifecycle-step-v1"
GENERATION_BITS = 32
GENERATION_LIMIT = 1 << GENERATION_BITS
SLOT_MASK = GENERATION_LIMIT - 1


def _sha256_record(record: dict[str, object]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _slot(value: object) -> int:
    if (
        type(value) is not int
        or value < 0
        or value >= TH08_ORDINARY_ENEMY_POOL_SIZE
    ):
        raise ValueError("ordinary enemy slot must be an integer in [0, 480)")
    return value


def _generation(value: object) -> int:
    if type(value) is not int or not 0 <= value < GENERATION_LIMIT:
        raise ValueError("allocation generation must fit one unsigned u32")
    return value


@dataclass(frozen=True, order=True)
class Route2BodyGenerationIdentity:
    """One ordinary-pool lifetime inside an immutable producer root."""

    slot: int
    allocation_generation: int
    schema: str = BODY_IDENTITY_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != BODY_IDENTITY_SCHEMA:
            raise ValueError("unsupported body-generation identity schema")
        _slot(self.slot)
        _generation(self.allocation_generation)

    @property
    def encoded(self) -> int:
        """Injective integer used by the existing body/mode interfaces.

        Generation zero intentionally encodes to the old compact slot number.
        This preserves generation-zero retrospective fixtures without making
        a pointer or slot sufficient for producer output.
        """

        return (self.allocation_generation << GENERATION_BITS) | self.slot

    @classmethod
    def from_encoded(cls, encoded: int) -> Route2BodyGenerationIdentity:
        if type(encoded) is not int or encoded < 0:
            raise ValueError("encoded body identity must be nonnegative")
        slot = encoded & SLOT_MASK
        generation = encoded >> GENERATION_BITS
        return cls(
            slot=_slot(slot),
            allocation_generation=_generation(generation),
        )

    def record(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "slot": self.slot,
            "allocation_generation": self.allocation_generation,
            "encoded": self.encoded,
        }


@dataclass(frozen=True)
class Route2SlotLifecycleEvent:
    """One native-order allocation or retirement inside one physical update."""

    physical_update: int
    sequence: int
    kind: str
    slot: int
    source: str
    schema: str = LIFECYCLE_EVENT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != LIFECYCLE_EVENT_SCHEMA:
            raise ValueError("unsupported slot lifecycle event schema")
        if type(self.physical_update) is not int or self.physical_update < 0:
            raise ValueError("lifecycle event physical update must be nonnegative")
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("lifecycle event sequence must be nonnegative")
        if self.kind not in ("allocate", "retire"):
            raise ValueError("lifecycle event kind must be allocate or retire")
        _slot(self.slot)
        if type(self.source) is not str or not self.source:
            raise ValueError("lifecycle event source must not be empty")

    def record(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "physical_update": self.physical_update,
            "sequence": self.sequence,
            "kind": self.kind,
            "slot": self.slot,
            "source": self.source,
        }


@dataclass(frozen=True)
class Route2SlotLifetimeLedger:
    """Immutable exact slot-lifetime state relative to one producer root."""

    root_physical_update: int
    current_physical_update: int
    active: tuple[bool, ...]
    seen_lifetime: tuple[bool, ...]
    generations: tuple[int, ...]
    event_count: int = 0
    schema: str = LIFETIME_LEDGER_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != LIFETIME_LEDGER_SCHEMA:
            raise ValueError("unsupported slot-lifetime ledger schema")
        if (
            type(self.root_physical_update) is not int
            or self.root_physical_update < 0
        ):
            raise ValueError("ledger root physical update must be nonnegative")
        if (
            type(self.current_physical_update) is not int
            or self.current_physical_update < self.root_physical_update
        ):
            raise ValueError(
                "ledger current update must not precede its producer root"
            )
        for name, values in (
            ("active", self.active),
            ("seen lifetime", self.seen_lifetime),
            ("generation", self.generations),
        ):
            if type(values) is not tuple or len(values) != (
                TH08_ORDINARY_ENEMY_POOL_SIZE
            ):
                raise ValueError(f"ledger {name} vector must contain 480 slots")
        if any(type(value) is not bool for value in self.active):
            raise ValueError("ledger active vector must contain exact booleans")
        if any(type(value) is not bool for value in self.seen_lifetime):
            raise ValueError(
                "ledger seen-lifetime vector must contain exact booleans"
            )
        if any(
            type(value) is not int or not 0 <= value < GENERATION_LIMIT
            for value in self.generations
        ):
            raise ValueError("ledger generations must fit unsigned u32 words")
        if any(
            is_active and not seen
            for is_active, seen in zip(
                self.active,
                self.seen_lifetime,
                strict=True,
            )
        ):
            raise ValueError("an active slot must have a seen lifetime")
        if type(self.event_count) is not int or self.event_count < 0:
            raise ValueError("ledger event count must be nonnegative")

    @classmethod
    def from_root_active_slots(
        cls,
        *,
        root_physical_update: int,
        active_slots: tuple[int, ...],
    ) -> Route2SlotLifetimeLedger:
        if type(active_slots) is not tuple:
            raise ValueError("root active slots must be an immutable tuple")
        slots = tuple(_slot(slot) for slot in active_slots)
        if slots != tuple(sorted(slots)) or len(slots) != len(set(slots)):
            raise ValueError("root active slots must be sorted and unique")
        active_set = frozenset(slots)
        active = tuple(
            slot in active_set
            for slot in range(TH08_ORDINARY_ENEMY_POOL_SIZE)
        )
        return cls(
            root_physical_update=root_physical_update,
            current_physical_update=root_physical_update,
            active=active,
            seen_lifetime=active,
            generations=(0,) * TH08_ORDINARY_ENEMY_POOL_SIZE,
        )

    def identity_for_active_slot(
        self,
        slot: int,
    ) -> Route2BodyGenerationIdentity:
        checked = _slot(slot)
        if not self.active[checked]:
            raise ValueError("inactive slot has no current body identity")
        return Route2BodyGenerationIdentity(
            slot=checked,
            allocation_generation=self.generations[checked],
        )

    @property
    def active_identities(self) -> tuple[Route2BodyGenerationIdentity, ...]:
        return tuple(
            self.identity_for_active_slot(slot)
            for slot, is_active in enumerate(self.active)
            if is_active
        )

    def payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "root_physical_update": self.root_physical_update,
            "current_physical_update": self.current_physical_update,
            "active_identities": [
                identity.record() for identity in self.active_identities
            ],
            "seen_lifetime_slots": [
                slot
                for slot, seen in enumerate(self.seen_lifetime)
                if seen
            ],
            "nonzero_generations": [
                [slot, generation]
                for slot, generation in enumerate(self.generations)
                if generation
            ],
            "event_count": self.event_count,
        }

    @property
    def digest(self) -> str:
        return _sha256_record(self.payload())

    def record(self) -> dict[str, object]:
        return {**self.payload(), "sha256": self.digest}


@dataclass(frozen=True)
class Route2SlotLifecycleStep:
    """One exact native-order event batch and its successor ledger."""

    events: tuple[Route2SlotLifecycleEvent, ...]
    allocated_identities: tuple[Route2BodyGenerationIdentity, ...]
    retired_identities: tuple[Route2BodyGenerationIdentity, ...]
    successor: Route2SlotLifetimeLedger
    schema: str = LIFECYCLE_STEP_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != LIFECYCLE_STEP_SCHEMA:
            raise ValueError("unsupported slot lifecycle step schema")
        if type(self.events) is not tuple or any(
            type(event) is not Route2SlotLifecycleEvent
            for event in self.events
        ):
            raise ValueError("lifecycle step events must be an immutable tuple")
        for identities, name in (
            (self.allocated_identities, "allocated"),
            (self.retired_identities, "retired"),
        ):
            if type(identities) is not tuple or any(
                type(identity) is not Route2BodyGenerationIdentity
                for identity in identities
            ):
                raise ValueError(
                    f"lifecycle step {name} identities must be immutable"
                )
        if type(self.successor) is not Route2SlotLifetimeLedger:
            raise ValueError("lifecycle step successor must be a ledger")

    def record(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "events": [event.record() for event in self.events],
            "allocated_identities": [
                identity.record() for identity in self.allocated_identities
            ],
            "retired_identities": [
                identity.record() for identity in self.retired_identities
            ],
            "successor": self.successor.record(),
        }


def advance_route2_slot_lifetimes(
    ledger: Route2SlotLifetimeLedger,
    *,
    next_physical_update: int,
    events: tuple[Route2SlotLifecycleEvent, ...],
    observed_active_slots: tuple[int, ...] | None = None,
) -> Route2SlotLifecycleStep:
    """Apply a complete ordered native lifecycle event batch.

    `observed_active_slots` is only an endpoint reconciliation.  It never
    supplies or infers missing events.  A same-update allocate/retire pair can
    leave the endpoint unchanged while still consuming a generation.
    """

    if type(ledger) is not Route2SlotLifetimeLedger:
        raise ValueError("slot-lifetime predecessor must be an exact ledger")
    if (
        type(next_physical_update) is not int
        or next_physical_update != ledger.current_physical_update + 1
    ):
        raise ValueError("slot-lifetime updates must be contiguous")
    if type(events) is not tuple or any(
        type(event) is not Route2SlotLifecycleEvent for event in events
    ):
        raise ValueError("lifecycle events must be an immutable exact tuple")
    if tuple(event.sequence for event in events) != tuple(range(len(events))):
        raise ValueError("lifecycle event sequences must be contiguous from zero")
    if any(event.physical_update != next_physical_update for event in events):
        raise ValueError("lifecycle event update does not match the step")

    active = list(ledger.active)
    seen = list(ledger.seen_lifetime)
    generations = list(ledger.generations)
    allocated: list[Route2BodyGenerationIdentity] = []
    retired: list[Route2BodyGenerationIdentity] = []

    for event in events:
        slot = event.slot
        if event.kind == "allocate":
            if active[slot]:
                raise ValueError("native allocation cannot target an active slot")
            if seen[slot]:
                if generations[slot] == GENERATION_LIMIT - 1:
                    raise ValueError("allocation generation overflow")
                generations[slot] += 1
            else:
                seen[slot] = True
            active[slot] = True
            allocated.append(
                Route2BodyGenerationIdentity(
                    slot=slot,
                    allocation_generation=generations[slot],
                )
            )
            continue

        if not active[slot]:
            raise ValueError("native retirement cannot target an inactive slot")
        identity = Route2BodyGenerationIdentity(
            slot=slot,
            allocation_generation=generations[slot],
        )
        retired.append(identity)
        active[slot] = False

    if observed_active_slots is not None:
        if type(observed_active_slots) is not tuple:
            raise ValueError("observed active slots must be an immutable tuple")
        checked = tuple(_slot(slot) for slot in observed_active_slots)
        if checked != tuple(sorted(checked)) or len(checked) != len(set(checked)):
            raise ValueError("observed active slots must be sorted and unique")
        expected = tuple(
            slot
            for slot, is_active in enumerate(active)
            if is_active
        )
        if checked != expected:
            raise ValueError(
                "endpoint active slots disagree; ordered lifecycle events are "
                "incomplete"
            )

    successor = Route2SlotLifetimeLedger(
        root_physical_update=ledger.root_physical_update,
        current_physical_update=next_physical_update,
        active=tuple(active),
        seen_lifetime=tuple(seen),
        generations=tuple(generations),
        event_count=ledger.event_count + len(events),
    )
    return Route2SlotLifecycleStep(
        events=events,
        allocated_identities=tuple(allocated),
        retired_identities=tuple(retired),
        successor=successor,
    )


def lower_route2_generation_identity_to_future_body_sample(
    *,
    identity: Route2BodyGenerationIdentity,
    base_flags: int,
    x: float,
    y: float,
    half_width: float,
    half_height: float,
    uncertainty: float = 0.0,
) -> Route2FutureBodySample:
    """Lower an exact producer identity to the existing schedule interface."""

    from th08_future_body_schedule import Route2FutureBodySample

    if type(identity) is not Route2BodyGenerationIdentity:
        raise ValueError("future producer body requires a generational identity")
    return Route2FutureBodySample(
        identity=identity.encoded,
        base_flags=base_flags,
        x=x,
        y=y,
        half_width=half_width,
        half_height=half_height,
        uncertainty=uncertainty,
    )


__all__ = [
    "BODY_IDENTITY_SCHEMA",
    "GENERATION_BITS",
    "LIFECYCLE_EVENT_SCHEMA",
    "LIFECYCLE_STEP_SCHEMA",
    "LIFETIME_LEDGER_SCHEMA",
    "Route2BodyGenerationIdentity",
    "Route2SlotLifecycleEvent",
    "Route2SlotLifecycleStep",
    "Route2SlotLifetimeLedger",
    "TH08_ORDINARY_ENEMY_POOL_SIZE",
    "advance_route2_slot_lifetimes",
    "lower_route2_generation_identity_to_future_body_sample",
]
