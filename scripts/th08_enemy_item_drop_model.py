#!/usr/bin/env python3
"""Executable TH08 enemy item-source and defeat-drop recurrence."""

from __future__ import annotations

from dataclasses import dataclass, replace

from th08_item_model import (
    FREE,
    HOMING,
    ITEM_BOMB,
    ITEM_LIFE_OR_BOMB,
    ITEM_POINT,
    ITEM_POWER_LARGE,
    ITEM_POWER_SMALL,
)
from th08_item_pool import ItemSpawnRequest
from th08_rng import Th08Rng


ENEMY_PRIMARY_DROP_TYPE_OFFSET = 0x3304
ENEMY_POINT_DROP_COUNT_OFFSET = 0x3308
ENEMY_POWER_DROP_COUNT_OFFSET = 0x330C

ENEMY_DEFEAT_DROP_MODES = frozenset({0, 1, 2})
ENEMY_NO_DROP_MODE = 3

# byte_4C70D8, consumed by the primary-type -1 global every-third schedule.
DEFAULT_DROP_SEQUENCE_TYPES = (
    0,
    0,
    1,
    0,
    1,
    0,
    0,
    0,
    1,
    1,
    0,
    0,
    1,
    1,
    1,
    0,
    1,
    0,
    1,
    0,
    1,
    0,
    1,
    0,
    1,
    0,
    0,
    1,
    1,
    1,
    0,
    0,
)


@dataclass(frozen=True)
class EnemyDropConfiguration:
    """Enemy fields consumed after HP defeat in native modes 0, 1, and 2."""

    primary_item_type: int = ITEM_POWER_SMALL
    point_item_count: int = 0
    power_item_count: int = 0
    defeat_mode: int = 0

    def __post_init__(self) -> None:
        if self.defeat_mode not in {*ENEMY_DEFEAT_DROP_MODES, ENEMY_NO_DROP_MODE}:
            raise ValueError("enemy defeat mode must be in 0..3")


@dataclass(frozen=True)
class DefaultDropSequenceState:
    """Global uint16 state used only when primary item type is -1."""

    call_counter: int = 0
    item_index: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.call_counter <= 0xFFFF:
            raise ValueError("default-drop call counter must be a uint16")
        if not 0 <= self.item_index < len(DEFAULT_DROP_SEQUENCE_TYPES):
            raise ValueError("default-drop item index is outside the table")


@dataclass(frozen=True)
class EnemyDefeatDropBatch:
    """Ordered pre-item-manager requests produced by one HP-defeat helper."""

    helper_invoked: bool
    requests: tuple[ItemSpawnRequest, ...]
    post_configuration: EnemyDropConfiguration
    post_sequence_state: DefaultDropSequenceState
    randomized_position_count: int


def _random_square_position(
    *,
    enemy_x: float,
    enemy_y: float,
    rng: Th08Rng,
) -> tuple[float, float]:
    return (
        enemy_x + rng.next_unit() * 128.0 - 64.0,
        enemy_y + rng.next_unit() * 128.0 - 64.0,
    )


def _randomized_requests(
    *,
    enemy_x: float,
    enemy_y: float,
    item_types: tuple[int, ...],
    rng: Th08Rng,
) -> tuple[ItemSpawnRequest, ...]:
    requests = []
    for item_type in item_types:
        x, y = _random_square_position(
            enemy_x=enemy_x,
            enemy_y=enemy_y,
            rng=rng,
        )
        requests.append(
            ItemSpawnRequest(
                x=x,
                y=y,
                item_type=item_type,
                motion_state=FREE,
            )
        )
    return tuple(requests)


def direct_item_request(
    *,
    enemy_x: float,
    enemy_y: float,
    item_type: int,
) -> ItemSpawnRequest:
    """Materialize ECL 0x8D before item-pool allocation."""

    return ItemSpawnRequest(
        x=enemy_x,
        y=enemy_y,
        item_type=item_type,
        motion_state=FREE,
    )


def materialize_power_bundle_requests(
    *,
    enemy_x: float,
    enemy_y: float,
    count: int,
    power: int,
    rng: Th08Rng,
) -> tuple[ItemSpawnRequest, ...]:
    """Materialize ECL 0x8E in native loop and RNG order."""

    if power < 0:
        raise ValueError("Power cannot be negative")
    count = max(0, count)
    if power >= 128:
        item_types = (ITEM_POINT,) * count
    elif count:
        item_types = (ITEM_POWER_LARGE,) + (ITEM_POWER_SMALL,) * (count - 1)
    else:
        item_types = ()
    return _randomized_requests(
        enemy_x=enemy_x,
        enemy_y=enemy_y,
        item_types=item_types,
        rng=rng,
    )


def materialize_point_item_requests(
    *,
    enemy_x: float,
    enemy_y: float,
    count: int,
    rng: Th08Rng,
) -> tuple[ItemSpawnRequest, ...]:
    """Materialize ECL 0xA8 in native loop and RNG order."""

    return _randomized_requests(
        enemy_x=enemy_x,
        enemy_y=enemy_y,
        item_types=(ITEM_POINT,) * max(0, count),
        rng=rng,
    )


def route_item_callback_request(
    *,
    enemy_x: float,
    enemy_y: float,
    bomb_active: bool,
) -> ItemSpawnRequest:
    """Materialize built-in enemy callback 31."""

    return direct_item_request(
        enemy_x=enemy_x,
        enemy_y=enemy_y,
        item_type=ITEM_BOMB if bomb_active else ITEM_LIFE_OR_BOMB,
    )


def materialize_enemy_defeat_drop_batch(
    configuration: EnemyDropConfiguration,
    *,
    enemy_x: float,
    enemy_y: float,
    power: int,
    bomb_related_damage: bool,
    rng: Th08Rng,
    sequence_state: DefaultDropSequenceState = DefaultDropSequenceState(),
) -> EnemyDefeatDropBatch:
    """Apply the native configured-drop helper before item-manager update.

    The result contains requests, not successful allocations. Playfield
    rejection and item-pool exhaustion remain the responsibility of
    ``step_item_pool``.
    """

    if power < 0:
        raise ValueError("Power cannot be negative")
    if configuration.defeat_mode == ENEMY_NO_DROP_MODE:
        return EnemyDefeatDropBatch(
            helper_invoked=False,
            requests=(),
            post_configuration=configuration,
            post_sequence_state=sequence_state,
            randomized_position_count=0,
        )

    requests: list[ItemSpawnRequest] = []
    next_sequence = sequence_state
    primary_type: int | None = None
    if configuration.primary_item_type >= 0:
        primary_type = configuration.primary_item_type
    elif configuration.primary_item_type == -1:
        if sequence_state.call_counter % 3 == 0:
            primary_type = DEFAULT_DROP_SEQUENCE_TYPES[
                sequence_state.item_index
            ]
            next_index = sequence_state.item_index + 1
            if next_index == len(DEFAULT_DROP_SEQUENCE_TYPES):
                next_index = 0
        else:
            next_index = sequence_state.item_index
        next_sequence = DefaultDropSequenceState(
            call_counter=(sequence_state.call_counter + 1) & 0xFFFF,
            item_index=next_index,
        )

    if primary_type is not None:
        requests.append(
            ItemSpawnRequest(
                x=enemy_x,
                y=enemy_y,
                item_type=primary_type,
                motion_state=HOMING if bomb_related_damage else FREE,
            )
        )

    power_type = ITEM_POINT if power >= 128 else ITEM_POWER_SMALL
    power_count = max(0, configuration.power_item_count)
    point_count = max(0, configuration.point_item_count)
    requests.extend(
        _randomized_requests(
            enemy_x=enemy_x,
            enemy_y=enemy_y,
            item_types=(power_type,) * power_count,
            rng=rng,
        )
    )
    requests.extend(
        _randomized_requests(
            enemy_x=enemy_x,
            enemy_y=enemy_y,
            item_types=(ITEM_POINT,) * point_count,
            rng=rng,
        )
    )
    return EnemyDefeatDropBatch(
        helper_invoked=True,
        requests=tuple(requests),
        post_configuration=replace(
            configuration,
            point_item_count=0,
            power_item_count=0,
        ),
        post_sequence_state=next_sequence,
        randomized_position_count=power_count + point_count,
    )
