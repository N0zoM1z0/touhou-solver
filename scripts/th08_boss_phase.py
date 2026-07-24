"""Read-only TH08 adapter for native boss health and phase progress."""

from __future__ import annotations

import math
import struct
from dataclasses import asdict, dataclass
from typing import Protocol

from touhou_control.phase_progress import PhaseProgressState


ADDR_ENEMY_MANAGER_FRAME = 0x0164D30C
BOSS_REGISTRY_ADDRESS = 0x00F54CC0
BOSS_REGISTRY_SLOTS = 4

ENEMY_CURRENT_HEALTH_OFFSET = 0x2DFC
ENEMY_MAXIMUM_HEALTH_OFFSET = 0x2E00
ENEMY_PHASE_HEALTH_OFFSET = 0x2E04
ENEMY_PHASE_TIMER_FRACTION_OFFSET = 0x2E18
ENEMY_PHASE_TIMER_ELAPSED_OFFSET = 0x2E1C
ENEMY_HEALTH_WINDOW_SIZE = 0x24

ENEMY_FLAGS_OFFSET = 0x3324
ENEMY_FLAGS2_OFFSET = 0x3328
ENEMY_FRAME_DAMAGE_OFFSET = 0x3354
ENEMY_HEALTH_THRESHOLDS_OFFSET = 0x3358
ENEMY_TIMEOUT_FRAME_OFFSET = 0x3378
ENEMY_CONTROL_WINDOW_SIZE = 0x58

ENEMY_ACTIVE_FLAG = 0x00000001
# ECL opcode 0x53 writes bit index 2: the concrete mask is 1 << 2.
ENEMY_BOSS_FLAG2 = 0x00000004
ENEMY_PLAYER_SHOT_DAMAGE_FLAG = 0x00000040
ENEMY_DAMAGE_BLOCKING_FLAGS = 0x00000830
ENEMY_FLAGS2_UPDATE_BLOCKED = 0x00000080


class MemoryReader(Protocol):
    def read(self, address: int, size: int) -> bytes: ...

    def u32(self, address: int) -> int: ...


@dataclass(frozen=True)
class BossPhaseSnapshot:
    frame_before: int
    frame_after: int
    pointer: int
    registry_slot: int | None
    current_health: int
    maximum_health: int
    phase_start_health: int
    health_thresholds: tuple[int, int, int, int]
    phase_end_health: int
    timer_elapsed: int
    timer_fraction: float
    timeout_frame: int | None
    frame_damage: int
    flags: int
    flags2: int
    native_damage_gate_open: bool
    stable: bool
    attempts: int

    @property
    def elapsed_frames(self) -> float:
        return self.timer_elapsed + self.timer_fraction

    @property
    def health_remaining(self) -> int:
        return max(0, self.current_health - self.phase_end_health)

    @property
    def health_span(self) -> int:
        return max(0, self.phase_start_health - self.phase_end_health)

    @property
    def health_progress(self) -> float | None:
        if self.health_span <= 0:
            return None
        completed = self.phase_start_health - self.current_health
        return min(1.0, max(0.0, completed / self.health_span))

    def as_progress_state(
        self,
        *,
        context: object | None = None,
        bomb_active: bool = False,
    ) -> PhaseProgressState:
        return PhaseProgressState(
            key=(
                context,
                self.pointer,
                self.phase_start_health,
                self.phase_end_health,
                self.timeout_frame,
            ),
            frame=self.frame_after,
            current_health=self.current_health,
            phase_start_health=self.phase_start_health,
            phase_end_health=self.phase_end_health,
            elapsed_frames=self.elapsed_frames,
            timeout_frames=self.timeout_frame,
            damageable=(
                self.native_damage_gate_open
                and not bomb_active
                and self.stable
            ),
            stable=self.stable,
        )


def _decode_snapshot(
    *,
    frame_before: int,
    frame_after: int,
    pointer: int,
    registry_slot: int | None,
    health: bytes,
    control: bytes,
    attempts: int,
) -> BossPhaseSnapshot | None:
    current_health, maximum_health, phase_start_health = struct.unpack_from(
        "<iii", health, 0
    )
    timer_fraction = struct.unpack_from(
        "<f",
        health,
        ENEMY_PHASE_TIMER_FRACTION_OFFSET - ENEMY_CURRENT_HEALTH_OFFSET,
    )[0]
    timer_elapsed = struct.unpack_from(
        "<i",
        health,
        ENEMY_PHASE_TIMER_ELAPSED_OFFSET - ENEMY_CURRENT_HEALTH_OFFSET,
    )[0]
    flags, flags2 = struct.unpack_from("<II", control, 0)
    if not flags & ENEMY_ACTIVE_FLAG or not flags2 & ENEMY_BOSS_FLAG2:
        return None
    frame_damage = struct.unpack_from(
        "<i",
        control,
        ENEMY_FRAME_DAMAGE_OFFSET - ENEMY_FLAGS_OFFSET,
    )[0]
    thresholds = struct.unpack_from(
        "<iiii",
        control,
        ENEMY_HEALTH_THRESHOLDS_OFFSET - ENEMY_FLAGS_OFFSET,
    )
    timeout = struct.unpack_from(
        "<i",
        control,
        ENEMY_TIMEOUT_FRAME_OFFSET - ENEMY_FLAGS_OFFSET,
    )[0]
    if (
        current_health < 0
        or maximum_health < 0
        or phase_start_health < 0
        or not math.isfinite(timer_fraction)
    ):
        return None
    active_thresholds = tuple(
        threshold
        for threshold in thresholds
        if 0 <= threshold <= current_health
    )
    phase_end_health = max(active_thresholds, default=0)
    return BossPhaseSnapshot(
        frame_before=frame_before,
        frame_after=frame_after,
        pointer=pointer,
        registry_slot=registry_slot,
        current_health=current_health,
        maximum_health=maximum_health,
        phase_start_health=phase_start_health,
        health_thresholds=thresholds,
        phase_end_health=phase_end_health,
        timer_elapsed=timer_elapsed,
        timer_fraction=timer_fraction,
        timeout_frame=timeout if timeout >= 0 else None,
        frame_damage=frame_damage,
        flags=flags,
        flags2=flags2,
        native_damage_gate_open=bool(
            flags & ENEMY_PLAYER_SHOT_DAMAGE_FLAG
            and not flags & ENEMY_DAMAGE_BLOCKING_FLAGS
            and not flags2 & ENEMY_FLAGS2_UPDATE_BLOCKED
        ),
        stable=frame_before == frame_after,
        attempts=attempts,
    )


def capture_boss_phase_snapshot(
    reader: MemoryReader,
    *,
    preferred_pointer: int = 0,
    maximum_attempts: int = 3,
) -> BossPhaseSnapshot | None:
    """Capture the active boss with a manager-frame consistency bracket."""

    if maximum_attempts <= 0:
        raise ValueError("maximum attempts must be positive")
    last_snapshot: BossPhaseSnapshot | None = None
    for attempt in range(1, maximum_attempts + 1):
        frame_before = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
        registry_blob = reader.read(
            BOSS_REGISTRY_ADDRESS,
            BOSS_REGISTRY_SLOTS * 4,
        )
        registry = struct.unpack("<IIII", registry_blob)
        pointers: list[tuple[int, int | None]] = []
        if preferred_pointer:
            preferred_slot = next(
                (
                    index
                    for index, pointer in enumerate(registry)
                    if pointer == preferred_pointer
                ),
                None,
            )
            pointers.append((preferred_pointer, preferred_slot))
        pointers.extend(
            (pointer, index)
            for index, pointer in enumerate(registry)
            if pointer and pointer != preferred_pointer
        )
        for pointer, registry_slot in pointers:
            health = reader.read(
                pointer + ENEMY_CURRENT_HEALTH_OFFSET,
                ENEMY_HEALTH_WINDOW_SIZE,
            )
            control = reader.read(
                pointer + ENEMY_FLAGS_OFFSET,
                ENEMY_CONTROL_WINDOW_SIZE,
            )
            frame_after = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
            snapshot = _decode_snapshot(
                frame_before=frame_before,
                frame_after=frame_after,
                pointer=pointer,
                registry_slot=registry_slot,
                health=health,
                control=control,
                attempts=attempt,
            )
            if snapshot is None:
                continue
            last_snapshot = snapshot
            if snapshot.stable:
                return snapshot
        if not pointers:
            return None
    return last_snapshot


def serialize_boss_phase_snapshot(
    snapshot: BossPhaseSnapshot | None,
) -> dict[str, object] | None:
    if snapshot is None:
        return None
    result = asdict(snapshot)
    result.update(
        {
            "elapsed_frames": snapshot.elapsed_frames,
            "health_remaining": snapshot.health_remaining,
            "health_span": snapshot.health_span,
            "health_progress": snapshot.health_progress,
        }
    )
    return result
