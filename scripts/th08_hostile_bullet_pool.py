#!/usr/bin/env python3
"""Executable base-state TH08 hostile bullet pool and contact geometry.

This module intentionally rejects transform-bearing bullets. It establishes
the native allocation/scan order and the straight active-state runtime that
the recovered transform VM can extend without changing pool semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


BULLET_POOL_SIZE = 1536
BULLET_GRAZE_MARGIN = 20.0
PLAYER_NORMAL = 0
PLAYER_SPAWNING = 1
PLAYER_DEAD = 2


@dataclass(frozen=True)
class HostileBulletState:
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    hitbox_width: float
    hitbox_height: float
    age: int = 0
    grazed: bool = False
    collision_suppressed: bool = False
    transform_flags: int = 0
    active: bool = True


@dataclass(frozen=True)
class HostileBulletSpawnRequest:
    bullet: HostileBulletState


@dataclass(frozen=True)
class HostileBulletSlot:
    index: int
    bullet: HostileBulletState


@dataclass(frozen=True)
class HostileBulletPoolState:
    slots: tuple[HostileBulletSlot, ...] = ()
    allocation_cursor: int = 0
    graze_count: int = 0


@dataclass(frozen=True)
class HostileBulletContact:
    slot_index: int
    kind: str


@dataclass(frozen=True)
class HostileBulletPoolStep:
    state: HostileBulletPoolState
    contacts: tuple[HostileBulletContact, ...]
    spawned_slots: tuple[int, ...]
    released_slots: tuple[int, ...]
    pool_exhausted: bool

    @property
    def hit(self) -> bool:
        return any(contact.kind == "hit" for contact in self.contacts)

    @property
    def grazes(self) -> int:
        return sum(contact.kind == "graze" for contact in self.contacts)


def _validate_state(state: HostileBulletPoolState) -> None:
    indices = tuple(slot.index for slot in state.slots)
    if indices != tuple(sorted(indices)) or len(indices) != len(set(indices)):
        raise ValueError("hostile bullet slots must be uniquely sorted")
    if any(not 0 <= index < BULLET_POOL_SIZE for index in indices):
        raise ValueError("hostile bullet slot index is outside the native pool")
    if not 0 <= state.allocation_cursor < BULLET_POOL_SIZE:
        raise ValueError("hostile bullet allocation cursor is outside the pool")
    for slot in state.slots:
        bullet = slot.bullet
        if bullet.hitbox_width < 0.0 or bullet.hitbox_height < 0.0:
            raise ValueError("hostile bullet hitbox dimensions cannot be negative")
        if bullet.transform_flags:
            raise NotImplementedError(
                "transform-bearing hostile bullets require the transform VM"
            )


def _allocate_slot(occupied: set[int], cursor: int) -> tuple[int | None, int]:
    for offset in range(BULLET_POOL_SIZE):
        index = (cursor + offset) % BULLET_POOL_SIZE
        if index not in occupied:
            return index, (index + 1) % BULLET_POOL_SIZE
    return None, cursor


def native_bullet_scan_order() -> tuple[int, ...]:
    """Return the physical order observed in bullet_manager_update."""

    return (0, *range(BULLET_POOL_SIZE - 1, 0, -1))


def _fully_outside_playfield(
    bullet: HostileBulletState, *, width: float, height: float
) -> bool:
    return (
        bullet.x + bullet.hitbox_width / 2.0 < 0.0
        or bullet.x - bullet.hitbox_width / 2.0 > width
        or bullet.y + bullet.hitbox_height / 2.0 < 0.0
        or bullet.y - bullet.hitbox_height / 2.0 > height
    )


def _overlap(
    bullet: HostileBulletState,
    *,
    player_x: float,
    player_y: float,
    player_half_width: float,
    player_half_height: float,
    margin: float = 0.0,
) -> bool:
    return (
        abs(player_x - bullet.x)
        <= player_half_width + bullet.hitbox_width / 2.0 + margin
        and abs(player_y - bullet.y)
        <= player_half_height + bullet.hitbox_height / 2.0 + margin
    )


def step_hostile_bullet_pool(
    state: HostileBulletPoolState,
    *,
    spawns_before_update: tuple[HostileBulletSpawnRequest, ...] = (),
    player_x: float,
    player_y: float,
    player_hitbox_half_width: float,
    player_hitbox_half_height: float,
    player_aux_half_width: float,
    player_aux_half_height: float,
    player_state: int,
    playfield_width: float = 384.0,
    playfield_height: float = 448.0,
) -> HostileBulletPoolStep:
    """Run the transform-free active bullet subset once.

    New enemy bullets participate in the same later priority-14 scan. Graze is
    tested only after age 16 and latches per bullet. Exact collision is tested
    every active frame; it removes the bullet even if the player is currently
    non-normal, but only state 0 enters the hit transition.
    """

    _validate_state(state)
    if min(
        player_hitbox_half_width,
        player_hitbox_half_height,
        player_aux_half_width,
        player_aux_half_height,
        playfield_width,
        playfield_height,
    ) < 0.0:
        raise ValueError("player and playfield dimensions cannot be negative")

    slots = {slot.index: slot.bullet for slot in state.slots}
    occupied = set(slots)
    cursor = state.allocation_cursor
    spawned: list[int] = []
    pool_exhausted = False
    for request in spawns_before_update:
        if not request.bullet.active:
            continue
        if request.bullet.transform_flags:
            raise NotImplementedError(
                "transform-bearing hostile bullets require the transform VM"
            )
        index, cursor = _allocate_slot(occupied, cursor)
        if index is None:
            pool_exhausted = True
            break
        slots[index] = request.bullet
        occupied.add(index)
        spawned.append(index)

    contacts: list[HostileBulletContact] = []
    released: list[int] = []
    effective_player_state = player_state
    for index in native_bullet_scan_order():
        bullet = slots.get(index)
        if bullet is None:
            continue
        moved = replace(
            bullet,
            x=bullet.x + bullet.velocity_x,
            y=bullet.y + bullet.velocity_y,
        )
        if _fully_outside_playfield(
            moved, width=playfield_width, height=playfield_height
        ):
            del slots[index]
            released.append(index)
            continue

        remove = False
        if not moved.collision_suppressed:
            if (
                not moved.grazed
                and moved.age >= 16
                and effective_player_state not in (PLAYER_SPAWNING, PLAYER_DEAD)
                and _overlap(
                    moved,
                    player_x=player_x,
                    player_y=player_y,
                    player_half_width=player_aux_half_width,
                    player_half_height=player_aux_half_height,
                    margin=BULLET_GRAZE_MARGIN,
                )
            ):
                contacts.append(HostileBulletContact(index, "graze"))
                moved = replace(moved, grazed=True)

            if _overlap(
                moved,
                player_x=player_x,
                player_y=player_y,
                player_half_width=player_hitbox_half_width,
                player_half_height=player_hitbox_half_height,
            ):
                remove = True
                if effective_player_state == PLAYER_NORMAL:
                    contacts.append(HostileBulletContact(index, "hit"))
                    effective_player_state = PLAYER_DEAD
                else:
                    contacts.append(HostileBulletContact(index, "absorbed"))

        if remove:
            del slots[index]
            released.append(index)
        else:
            slots[index] = replace(moved, age=moved.age + 1)

    return HostileBulletPoolStep(
        HostileBulletPoolState(
            tuple(
                HostileBulletSlot(index, bullet)
                for index, bullet in sorted(slots.items())
            ),
            cursor,
            state.graze_count
            + sum(contact.kind == "graze" for contact in contacts),
        ),
        tuple(contacts),
        tuple(spawned),
        tuple(released),
        pool_exhausted,
    )
