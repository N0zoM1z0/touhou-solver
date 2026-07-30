"""Read-only TH08 adapter for native boss health and phase progress."""

from __future__ import annotations

import math
import struct
from dataclasses import asdict, dataclass
from typing import Protocol

from th08_enemy_damage_model import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_DAMAGE_BLOCKING_FLAGS,
    ENEMY_FLAGS2_UPDATE_BLOCKED,
    ENEMY_HP_SUBTRACTION_FLAG,
    ENEMY_PLAYER_SHOT_DAMAGE_FLAG,
    EnemyPlayerShotDamageContext,
    EnemyPlayerShotDamageGate,
    evaluate_enemy_player_shot_damage_gate,
)
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

# ECL opcode 0x53 writes bit index 2: the concrete mask is 1 << 2.
ENEMY_BOSS_FLAG2 = 0x00000004
BOSS_PHASE_SUCCESSOR_SPECIAL_MODE_FLAG = 0x00004000
BOSS_PHASE_SUCCESSOR_MODE_BITS_MASK = 0x00000180


class MemoryReader(Protocol):
    def read(self, address: int, size: int) -> bytes: ...

    def u32(self, address: int) -> int: ...


def boss_phase_successor_write_enabled(engine_flags: int) -> bool:
    """Return whether ECL 0x85/0x86 overwrite their successor register."""

    if not 0 <= engine_flags <= 0xFFFFFFFF:
        raise ValueError("engine_flags must be a uint32")
    special_mode = bool(
        engine_flags & BOSS_PHASE_SUCCESSOR_SPECIAL_MODE_FLAG
        and engine_flags & BOSS_PHASE_SUCCESSOR_MODE_BITS_MASK
    )
    return not special_mode


@dataclass(frozen=True)
class BossPhaseTransitionStep:
    """One native-ordered phase-boundary mutation."""

    kind: str
    health_threshold_index: int | None
    health_threshold: int | None
    current_health_before: int
    current_health_after: int
    phase_start_health_before: int
    phase_start_health_after: int
    timer_elapsed_before: int
    timer_elapsed_after: int
    timeout_frame_before: int | None
    timeout_frame_after: int | None


@dataclass(frozen=True)
class BossPhaseTransitionProjection:
    """Known field effects of the manager's pre-damage transition loop."""

    steps: tuple[BossPhaseTransitionStep, ...]
    current_health: int
    phase_start_health: int
    health_thresholds: tuple[int, int, int, int]
    timer_elapsed: int
    timer_fraction: float
    timeout_frame: int | None

    @property
    def completion_pending(self) -> str | None:
        if not self.steps:
            return None
        return self.steps[0].kind


def project_boss_phase_transition_prefix(
    *,
    current_health: int,
    phase_start_health: int,
    health_thresholds: tuple[int, int, int, int],
    timer_elapsed: int,
    timer_fraction: float,
    timeout_frame: int | None,
) -> BossPhaseTransitionProjection:
    """Project the native transition loop before player-shot damage.

    Health thresholds are tested in slot order with a strict ``health <
    threshold`` predicate. A health transition clears the timeout. Only when
    no health transition fires can an elapsed integer timer trigger timeout;
    timeout restores the greatest positive retained threshold.

    Starting the selected ECL subroutine has effects outside this bounded
    field projection, so callers must not treat the returned state as a full
    phase or hazard successor.
    """

    thresholds = list(health_thresholds)
    projected_health = current_health
    projected_phase_start = phase_start_health
    projected_timer_elapsed = timer_elapsed
    projected_timer_fraction = timer_fraction
    projected_timeout = timeout_frame
    steps: list[BossPhaseTransitionStep] = []

    while True:
        crossed_index = next(
            (
                index
                for index, threshold in enumerate(thresholds)
                if threshold >= 0 and projected_health < threshold
            ),
            None,
        )
        if crossed_index is not None:
            threshold = thresholds[crossed_index]
            step = BossPhaseTransitionStep(
                kind="health",
                health_threshold_index=crossed_index,
                health_threshold=threshold,
                current_health_before=projected_health,
                current_health_after=threshold,
                phase_start_health_before=projected_phase_start,
                phase_start_health_after=threshold,
                timer_elapsed_before=projected_timer_elapsed,
                timer_elapsed_after=projected_timer_elapsed,
                timeout_frame_before=projected_timeout,
                timeout_frame_after=None,
            )
            steps.append(step)
            projected_health = threshold
            projected_phase_start = threshold
            thresholds[crossed_index] = -1
            projected_timeout = None
            continue

        if (
            projected_timeout is not None
            and projected_timer_elapsed >= projected_timeout
        ):
            restore_index: int | None = None
            restore_threshold = 0
            for index, threshold in enumerate(thresholds):
                if restore_threshold < threshold:
                    restore_index = index
                    restore_threshold = threshold
            health_after = projected_health
            phase_start_after = projected_phase_start
            if restore_index is not None and restore_threshold > 0:
                health_after = restore_threshold
                phase_start_after = restore_threshold
                thresholds[restore_index] = -1
            steps.append(
                BossPhaseTransitionStep(
                    kind="timeout",
                    health_threshold_index=restore_index,
                    health_threshold=(
                        restore_threshold
                        if restore_index is not None and restore_threshold > 0
                        else None
                    ),
                    current_health_before=projected_health,
                    current_health_after=health_after,
                    phase_start_health_before=projected_phase_start,
                    phase_start_health_after=phase_start_after,
                    timer_elapsed_before=projected_timer_elapsed,
                    timer_elapsed_after=0,
                    timeout_frame_before=projected_timeout,
                    timeout_frame_after=None,
                )
            )
            projected_health = health_after
            projected_phase_start = phase_start_after
            projected_timer_elapsed = 0
            projected_timer_fraction = 0.0
            projected_timeout = None
            continue
        break

    return BossPhaseTransitionProjection(
        steps=tuple(steps),
        current_health=projected_health,
        phase_start_health=projected_phase_start,
        health_thresholds=tuple(thresholds),
        timer_elapsed=projected_timer_elapsed,
        timer_fraction=projected_timer_fraction,
        timeout_frame=projected_timeout,
    )


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
    def active_health_thresholds(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            (index, threshold)
            for index, threshold in enumerate(self.health_thresholds)
            if threshold >= 0
        )

    @property
    def transition_projection(self) -> BossPhaseTransitionProjection:
        return project_boss_phase_transition_prefix(
            current_health=self.current_health,
            phase_start_health=self.phase_start_health,
            health_thresholds=self.health_thresholds,
            timer_elapsed=self.timer_elapsed,
            timer_fraction=self.timer_fraction,
            timeout_frame=self.timeout_frame,
        )

    @property
    def completion_pending(self) -> str | None:
        return self.transition_projection.completion_pending

    @property
    def timeout_condition_met(self) -> bool:
        return (
            self.timeout_frame is not None
            and self.timer_elapsed >= self.timeout_frame
        )

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
        continuity_context: object | None = None,
        bomb_active: bool = False,
        player_transition_state: int = 0,
        spell_active: bool = False,
        active_spell_owner: bool = False,
    ) -> PhaseProgressState:
        damage_gate = self.player_shot_damage_gate(
            bomb_active=bomb_active,
            player_transition_state=player_transition_state,
            spell_active=spell_active,
            active_spell_owner=active_spell_owner,
        )
        return PhaseProgressState(
            key=(
                context,
                self.pointer,
                self.phase_start_health,
                self.health_thresholds,
                self.timeout_frame,
            ),
            frame=self.frame_after,
            current_health=self.current_health,
            phase_start_health=self.phase_start_health,
            phase_end_health=self.phase_end_health,
            elapsed_frames=self.elapsed_frames,
            timeout_frames=self.timeout_frame,
            damageable=damage_gate.hp_subtraction_open and self.stable,
            stable=self.stable,
            completion_pending=self.completion_pending,
            continuity_key=(continuity_context, self.pointer),
        )

    def player_shot_damage_gate(
        self,
        *,
        bomb_active: bool,
        player_transition_state: int,
        spell_active: bool = False,
        active_spell_owner: bool = False,
        damage_tick_due: bool = True,
    ) -> EnemyPlayerShotDamageGate:
        """Evaluate native manager gates for this captured boss state."""

        return evaluate_enemy_player_shot_damage_gate(
            EnemyPlayerShotDamageContext(
                flags=self.flags,
                flags2=self.flags2,
                bomb_active=bomb_active,
                player_transition_state=player_transition_state,
                damage_tick_due=damage_tick_due,
                spell_active=spell_active,
                active_spell_owner=active_spell_owner,
            )
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
    if maximum_health < 0 or phase_start_health < 0 or not math.isfinite(
        timer_fraction
    ):
        return None
    active_thresholds = tuple(
        threshold
        for threshold in thresholds
        if threshold >= 0
    )
    crossed_threshold = next(
        (
            threshold
            for threshold in thresholds
            if threshold >= 0 and current_health < threshold
        ),
        None,
    )
    phase_end_health = (
        crossed_threshold
        if crossed_threshold is not None
        else max(active_thresholds, default=0)
    )
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
            flags & ENEMY_ACTIVE_FLAG
            and flags & ENEMY_HP_SUBTRACTION_FLAG
            and flags & ENEMY_PLAYER_SHOT_DAMAGE_FLAG
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
    transition_projection = snapshot.transition_projection
    result.update(
        {
            "elapsed_frames": snapshot.elapsed_frames,
            "active_health_thresholds": [
                {"index": index, "health": health}
                for index, health in snapshot.active_health_thresholds
            ],
            "health_remaining": snapshot.health_remaining,
            "health_span": snapshot.health_span,
            "health_progress": snapshot.health_progress,
            "timeout_condition_met": snapshot.timeout_condition_met,
            "completion_pending": snapshot.completion_pending,
            "transition_projection": asdict(transition_projection),
        }
    )
    return result
