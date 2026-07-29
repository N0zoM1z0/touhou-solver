#!/usr/bin/env python3
"""Stable-slot TH08 laser execution and player contact classification."""

from __future__ import annotations

from dataclasses import dataclass

from th08_laser_model import (
    LASER_POOL_SIZE,
    LaserState,
    laser_overlaps_player,
    step_laser,
)
from th08_time_scale import canonical_time_scale_bits, validate_time_scale_bits


PLAYER_NORMAL = 0
PLAYER_SPAWNING = 1
PLAYER_DEAD = 2


@dataclass(frozen=True)
class LaserSpawnRequest:
    laser: LaserState


@dataclass(frozen=True)
class LaserSlot:
    index: int
    laser: LaserState


@dataclass(frozen=True)
class LaserPoolState:
    slots: tuple[LaserSlot, ...] = ()
    graze_count: int = 0


@dataclass(frozen=True)
class LaserContact:
    slot_index: int
    kind: str


@dataclass(frozen=True)
class LaserPoolStep:
    state: LaserPoolState
    contacts: tuple[LaserContact, ...]
    spawned_slots: tuple[int, ...]
    released_slots: tuple[int, ...]
    pool_exhausted: bool

    @property
    def hit(self) -> bool:
        return any(contact.kind == "hit" for contact in self.contacts)

    @property
    def grazes(self) -> int:
        return sum(contact.kind == "graze" for contact in self.contacts)


def _validate_slots(slots: tuple[LaserSlot, ...]) -> None:
    indices = tuple(slot.index for slot in slots)
    if indices != tuple(sorted(indices)) or len(indices) != len(set(indices)):
        raise ValueError("laser slots must be uniquely sorted")
    if any(not 0 <= index < LASER_POOL_SIZE for index in indices):
        raise ValueError("laser slot index is outside the native pool")


def _first_free_slot(occupied: set[int]) -> int | None:
    for index in range(LASER_POOL_SIZE):
        if index not in occupied:
            return index
    return None


def step_laser_pool(
    state: LaserPoolState,
    *,
    spawns_before_update: tuple[LaserSpawnRequest, ...] = (),
    player_x: float,
    player_y: float,
    player_half_width: float,
    player_half_height: float,
    player_state: int,
    time_scale: float = 1.0,
    time_scale_bits: int | None = None,
) -> LaserPoolStep:
    """Spawn and scan lasers once in ascending native slot order.

    Contact handling follows player_test_collision_and_graze (0x0044A6A0):
    an exact overlap is considered first and never falls back to graze. Only
    state 0 can be killed; states 1 and 2 cannot graze. A first hit changes the
    effective state to 2 for the rest of this same manager scan.
    """

    _validate_slots(state.slots)
    slots = {slot.index: slot.laser for slot in state.slots}
    occupied = set(slots)
    spawned: list[int] = []
    pool_exhausted = False

    for request in spawns_before_update:
        index = _first_free_slot(occupied)
        if index is None:
            pool_exhausted = True
            break
        if not request.laser.active:
            continue
        slots[index] = request.laser
        occupied.add(index)
        spawned.append(index)

    contacts: list[LaserContact] = []
    released: list[int] = []
    effective_player_state = player_state
    if time_scale_bits is None:
        time_scale_bits = canonical_time_scale_bits(time_scale)
    elif time_scale != 1.0:
        raise ValueError(
            "specify either time_scale or time_scale_bits, not both"
        )
    validate_time_scale_bits(time_scale_bits)
    for index in tuple(sorted(slots)):
        result = step_laser(
            slots[index],
            time_scale_bits=time_scale_bits,
        )
        for check in result.checks:
            direct = laser_overlaps_player(
                check.collision_box,
                player_x=player_x,
                player_y=player_y,
                player_half_width=player_half_width,
                player_half_height=player_half_height,
            )
            if direct:
                if effective_player_state == PLAYER_NORMAL:
                    contacts.append(LaserContact(index, "hit"))
                    effective_player_state = PLAYER_DEAD
                continue
            if (
                check.graze_enabled
                and effective_player_state not in (PLAYER_SPAWNING, PLAYER_DEAD)
                and laser_overlaps_player(
                    check.collision_box,
                    player_x=player_x,
                    player_y=player_y,
                    player_half_width=player_half_width,
                    player_half_height=player_half_height,
                    graze=True,
                )
            ):
                contacts.append(LaserContact(index, "graze"))

        if result.laser.active:
            slots[index] = result.laser
        else:
            del slots[index]
            released.append(index)

    return LaserPoolStep(
        LaserPoolState(
            tuple(LaserSlot(index, laser) for index, laser in sorted(slots.items())),
            state.graze_count + sum(contact.kind == "graze" for contact in contacts),
        ),
        tuple(contacts),
        tuple(spawned),
        tuple(released),
        pool_exhausted,
    )
