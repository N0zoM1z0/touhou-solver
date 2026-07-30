"""Focused native capture for TH08 player-shot emission state."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Protocol

from th08_runtime.game_state import (
    ADDR_PLAYER,
    PLAYER_SHOT_POOL_OFFSET,
    PLAYER_SHOT_POOL_SIZE,
    PLAYER_SHOT_SLOT_STATE_OFFSET,
    PLAYER_SHOT_SLOT_STRIDE,
    PLAYER_SHOT_TIMER_OFFSET,
)


PLAYER_SHOT_EMISSION_STATE_SCHEMA = "th08-player-shot-emission-state-v1"
TH08_TIMER_CAPTURE_SIZE = 12
PLAYER_SHOT_POOL_CAPTURE_SIZE = (
    (PLAYER_SHOT_POOL_SIZE - 1) * PLAYER_SHOT_SLOT_STRIDE
    + PLAYER_SHOT_SLOT_STATE_OFFSET
    + 2
)


class PlayerShotStateReader(Protocol):
    def read(self, address: int, size: int) -> bytes:
        ...


@dataclass(frozen=True)
class PlayerShotEmissionRuntimeState:
    timer_previous: int
    timer_fraction_bits: int
    timer_current: int
    slot_state_words: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.slot_state_words) != PLAYER_SHOT_POOL_SIZE:
            raise ValueError("player-shot capture must contain 128 slot words")
        if not all(0 <= value <= 0xFFFF for value in self.slot_state_words):
            raise ValueError("player-shot slot states must be uint16")

    @property
    def timer_integer_changed(self) -> bool:
        return self.timer_previous != self.timer_current

    @property
    def occupied_slot_indices(self) -> tuple[int, ...]:
        return tuple(
            index for index, value in enumerate(self.slot_state_words) if value
        )

    @property
    def free_slot_count(self) -> int:
        return sum(value == 0 for value in self.slot_state_words)

    def record(self) -> dict[str, object]:
        return {
            "schema": PLAYER_SHOT_EMISSION_STATE_SCHEMA,
            "timer": {
                "previous": self.timer_previous,
                "fraction_bits": self.timer_fraction_bits,
                "current": self.timer_current,
                "integer_changed": self.timer_integer_changed,
            },
            "pool": {
                "slot_count": PLAYER_SHOT_POOL_SIZE,
                "free_slot_count": self.free_slot_count,
                "occupied_slot_indices": list(self.occupied_slot_indices),
                "slot_state_words": list(self.slot_state_words),
            },
        }


def capture_player_shot_emission_state(
    reader: PlayerShotStateReader,
) -> PlayerShotEmissionRuntimeState:
    """Capture cadence identity and all 128 pool state words in two reads."""

    timer = reader.read(
        ADDR_PLAYER + PLAYER_SHOT_TIMER_OFFSET,
        TH08_TIMER_CAPTURE_SIZE,
    )
    if len(timer) != TH08_TIMER_CAPTURE_SIZE:
        raise ValueError("short player-shot timer capture")
    timer_previous, timer_fraction_bits, timer_current = struct.unpack(
        "<iIi",
        timer,
    )

    pool = reader.read(
        ADDR_PLAYER + PLAYER_SHOT_POOL_OFFSET,
        PLAYER_SHOT_POOL_CAPTURE_SIZE,
    )
    if len(pool) != PLAYER_SHOT_POOL_CAPTURE_SIZE:
        raise ValueError("short player-shot pool capture")
    slot_state_words = tuple(
        struct.unpack_from(
            "<H",
            pool,
            index * PLAYER_SHOT_SLOT_STRIDE + PLAYER_SHOT_SLOT_STATE_OFFSET,
        )[0]
        for index in range(PLAYER_SHOT_POOL_SIZE)
    )
    return PlayerShotEmissionRuntimeState(
        timer_previous=timer_previous,
        timer_fraction_bits=timer_fraction_bits,
        timer_current=timer_current,
        slot_state_words=slot_state_words,
    )


__all__ = [
    "PLAYER_SHOT_EMISSION_STATE_SCHEMA",
    "PLAYER_SHOT_POOL_CAPTURE_SIZE",
    "TH08_TIMER_CAPTURE_SIZE",
    "PlayerShotEmissionRuntimeState",
    "capture_player_shot_emission_state",
]
