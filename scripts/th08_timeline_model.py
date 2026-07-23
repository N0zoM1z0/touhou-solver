#!/usr/bin/env python3
"""Executable TH08 stage-timeline scheduler and enemy-spawn boundary.

The record loop is observed in ``stage_timeline_step`` (0x0042A8A0).
Enemy allocation and the initial ECL call are a separate boundary owned by
``enemy_spawn_from_timeline`` (0x0042A4E0); this module emits exact spawn
requests instead of pretending that the full enemy VM is already integrated.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, replace

from th08_ecl import EclFile, Timeline, TimelineInstruction
from th08_rng import Th08Rng


TIMELINE_MARKER_SLOTS = 4
INDEXED_ENEMY_SLOTS = 8


def _signed(word: int) -> int:
    return word if word < 0x80000000 else word - 0x100000000


def _float(word: int) -> float:
    return struct.unpack("<f", struct.pack("<I", word))[0]


@dataclass(frozen=True)
class TimelineClock:
    instruction_index: int = 0
    elapsed: int = 0
    stopped: bool = False
    blocked_reason: str | None = None


@dataclass(frozen=True)
class IndexedEnemyView:
    """Fields exposed by the ECL-owned indexed-enemy registry.

    Opcode 0x7F in the enemy VM owns the registry. The timeline scheduler only
    reads active/presence for opcode 0x0A and writes enemy+0x2D30 for opcode
    0x08, so the partial simulator keeps this as an explicit boundary view.
    """

    active: bool = True
    field_2d30: int = 0


@dataclass(frozen=True)
class TimelineExternalState:
    stage_transition_busy: bool = False
    spawn_suppressed: bool = False
    conditional_gate_blocked: bool = False
    indexed_enemies: tuple[IndexedEnemyView | None, ...] = (None,) * INDEXED_ENEMY_SLOTS

    def __post_init__(self) -> None:
        if len(self.indexed_enemies) != INDEXED_ENEMY_SLOTS:
            raise ValueError(
                f"indexed enemy view must contain {INDEXED_ENEMY_SLOTS} slots"
            )


@dataclass(frozen=True)
class TimelineSpawnRequest:
    timeline_index: int
    instruction_offset: int
    instruction_time: int
    opcode: int
    subroutine: int
    x: float
    y: float
    z: float
    field_2dfc: int
    byte_3304: int
    field_2e08: int
    variant: bool
    field_3308: int | None = None
    field_330c: int | None = None


@dataclass(frozen=True)
class TimelineEngineEvent:
    timeline_index: int
    instruction_offset: int
    opcode: int
    value: int


@dataclass(frozen=True)
class TimelineFieldWrite:
    timeline_index: int
    instruction_offset: int
    indexed_enemy: int
    field_2d30: int


@dataclass(frozen=True)
class StageTimelineState:
    clocks: tuple[TimelineClock, ...]
    markers: tuple[int, ...] = (-1,) * TIMELINE_MARKER_SLOTS
    rng_state: int = 0
    rng_calls: int = 0
    stage_flag_10: bool = False

    def __post_init__(self) -> None:
        if len(self.markers) != TIMELINE_MARKER_SLOTS:
            raise ValueError(
                f"timeline marker state must contain {TIMELINE_MARKER_SLOTS} slots"
            )


@dataclass(frozen=True)
class StageTimelineStep:
    state: StageTimelineState
    external: TimelineExternalState
    spawns: tuple[TimelineSpawnRequest, ...]
    engine_events: tuple[TimelineEngineEvent, ...]
    field_writes: tuple[TimelineFieldWrite, ...]


def initial_stage_timeline_state(
    ecl: EclFile, *, rng_seed: int, rng_calls: int = 0
) -> StageTimelineState:
    return StageTimelineState(
        clocks=tuple(TimelineClock() for _ in ecl.timelines),
        rng_state=rng_seed,
        rng_calls=rng_calls,
    )


def _require_arguments(insn: TimelineInstruction, count: int) -> tuple[int, ...]:
    if len(insn.arguments) != count:
        raise ValueError(
            f"timeline opcode {insn.opcode:#x} at {insn.offset:#x} has "
            f"{len(insn.arguments)} arguments; expected {count}"
        )
    return insn.arguments


def _spawn_request(
    timeline_index: int,
    insn: TimelineInstruction,
    rng: Th08Rng,
) -> TimelineSpawnRequest:
    opcode = insn.opcode
    words = insn.arguments
    variant = opcode in (0x01, 0x04, 0x05, 0x0C)
    extended_3308 = None
    extended_330c = None

    if opcode in (0x00, 0x01, 0x0F):
        words = _require_arguments(insn, 6)
        subroutine = _signed(words[0])
        x, y = _float(words[1]), _float(words[2])
        field_2dfc, byte_3304, field_2e08 = map(_signed, words[3:6])
    elif opcode in (0x02, 0x04):
        words = _require_arguments(insn, 7)
        subroutine = _signed(words[0])
        minimum_x, maximum_x = _float(words[1]), _float(words[2])
        x = rng.next_scaled(maximum_x - minimum_x) + minimum_x
        y = _float(words[3])
        field_2dfc, byte_3304, field_2e08 = map(_signed, words[4:7])
    elif opcode in (0x03, 0x05):
        words = _require_arguments(insn, 5)
        subroutine = _signed(words[0])
        x, y = rng.next_scaled(384.0), _float(words[1])
        field_2dfc, byte_3304, field_2e08 = map(_signed, words[2:5])
    elif opcode in (0x0B, 0x0C):
        words = _require_arguments(insn, 7)
        subroutine = _signed(words[0])
        x, y = _float(words[1]), _float(words[2])
        field_2dfc = _signed(words[3])
        byte_3304 = -1
        extended_3308, extended_330c = map(_signed, words[4:6])
        field_2e08 = _signed(words[6])
    else:
        raise ValueError(f"opcode {opcode:#x} is not a timeline spawn")

    values = (x, y)
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"timeline spawn at {insn.offset:#x} has non-finite position")
    return TimelineSpawnRequest(
        timeline_index=timeline_index,
        instruction_offset=insn.offset,
        instruction_time=insn.time,
        opcode=opcode,
        subroutine=subroutine,
        x=x,
        y=y,
        z=0.0,
        field_2dfc=field_2dfc,
        byte_3304=byte_3304 & 0xFF,
        field_2e08=field_2e08,
        variant=variant,
        field_3308=extended_3308,
        field_330c=extended_330c,
    )


def _step_one_timeline(
    timeline_index: int,
    timeline: Timeline,
    clock: TimelineClock,
    *,
    active_difficulty_mask: int,
    markers: tuple[int, ...],
    external: TimelineExternalState,
    rng: Th08Rng,
    stage_flag_10: bool,
) -> tuple[
    TimelineClock,
    tuple[int, ...],
    TimelineExternalState,
    bool,
    list[TimelineSpawnRequest],
    list[TimelineEngineEvent],
    list[TimelineFieldWrite],
]:
    if clock.stopped:
        return clock, markers, external, stage_flag_10, [], [], []

    index = clock.instruction_index
    blocked_reason = None
    spawns: list[TimelineSpawnRequest] = []
    events: list[TimelineEngineEvent] = []
    writes: list[TimelineFieldWrite] = []

    while index < len(timeline.instructions):
        insn = timeline.instructions[index]
        if clock.elapsed < insn.time:
            break
        if clock.elapsed > insn.time:
            index += 1
            continue
        if not (insn.difficulty_mask & active_difficulty_mask):
            index += 1
            continue

        opcode = insn.opcode
        if opcode in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0C):
            if not external.stage_transition_busy and not external.spawn_suppressed:
                spawns.append(_spawn_request(timeline_index, insn, rng))
        elif opcode == 0x0F:
            spawns.append(_spawn_request(timeline_index, insn, rng))
        elif opcode in (0x06, 0x09):
            (value,) = _require_arguments(insn, 1)
            events.append(
                TimelineEngineEvent(
                    timeline_index, insn.offset, opcode, _signed(value)
                )
            )
        elif opcode == 0x07:
            _require_arguments(insn, 0)
            if external.conditional_gate_blocked:
                blocked_reason = "conditional_gate"
                break
        elif opcode == 0x08:
            enemy_index, value = map(_signed, _require_arguments(insn, 2))
            if not 0 <= enemy_index < len(external.indexed_enemies):
                raise IndexError(f"timeline indexed enemy {enemy_index} is out of range")
            enemy = external.indexed_enemies[enemy_index]
            if enemy is None:
                raise RuntimeError(
                    f"timeline opcode 0x08 dereferences empty indexed enemy {enemy_index}"
                )
            indexed = list(external.indexed_enemies)
            indexed[enemy_index] = replace(enemy, field_2d30=value & 0xFFFF)
            external = replace(external, indexed_enemies=tuple(indexed))
            writes.append(
                TimelineFieldWrite(
                    timeline_index, insn.offset, enemy_index, value & 0xFFFF
                )
            )
        elif opcode == 0x0A:
            (enemy_index,) = map(_signed, _require_arguments(insn, 1))
            if not 0 <= enemy_index < len(external.indexed_enemies):
                raise IndexError(f"timeline indexed enemy {enemy_index} is out of range")
            enemy = external.indexed_enemies[enemy_index]
            if enemy is not None and enemy.active:
                blocked_reason = f"indexed_enemy_{enemy_index}_active"
                break
        elif opcode == 0x0D:
            (marker,) = map(_signed, _require_arguments(insn, 1))
            mutable = list(markers)
            consumed = False
            for marker_index, current in enumerate(mutable):
                if current == marker:
                    mutable[marker_index] = -1
                    consumed = True
            markers = tuple(mutable)
            if not consumed:
                blocked_reason = f"marker_{marker}"
                break
        elif opcode == 0x0E:
            (marker,) = map(_signed, _require_arguments(insn, 1))
            markers = tuple(marker if current < 0 else current for current in markers)
        elif opcode == 0x10:
            _require_arguments(insn, 0)
            stage_flag_10 = True
        else:
            raise ValueError(
                f"unsupported timeline opcode {opcode:#x} at {insn.offset:#x}"
            )
        index += 1

    stopped = index >= len(timeline.instructions)
    elapsed = clock.elapsed if blocked_reason else clock.elapsed + 1
    return (
        TimelineClock(index, elapsed, stopped, blocked_reason),
        markers,
        external,
        stage_flag_10,
        spawns,
        events,
        writes,
    )


def step_stage_timelines(
    ecl: EclFile,
    state: StageTimelineState,
    *,
    active_difficulty_mask: int,
    external: TimelineExternalState = TimelineExternalState(),
) -> StageTimelineStep:
    """Advance every timeline once in native index order.

    Marker writes from an earlier timeline are immediately visible to later
    timelines in the same manager update. Indexed-enemy state is an explicit
    input/output boundary until opcode 0x7F and the full enemy VM are executed
    by the integrated simulator.
    """

    if len(state.clocks) != len(ecl.timelines):
        raise ValueError("timeline state/program count mismatch")
    if not 0 <= active_difficulty_mask <= 0xFF:
        raise ValueError("active timeline difficulty mask must fit in one byte")

    rng = Th08Rng(state.rng_state, state.rng_calls)
    markers = state.markers
    stage_flag = state.stage_flag_10
    clocks: list[TimelineClock] = []
    spawns: list[TimelineSpawnRequest] = []
    events: list[TimelineEngineEvent] = []
    writes: list[TimelineFieldWrite] = []

    for timeline_index, (timeline, clock) in enumerate(
        zip(ecl.timelines, state.clocks, strict=True)
    ):
        (
            clock,
            markers,
            external,
            stage_flag,
            local_spawns,
            local_events,
            local_writes,
        ) = _step_one_timeline(
            timeline_index,
            timeline,
            clock,
            active_difficulty_mask=active_difficulty_mask,
            markers=markers,
            external=external,
            rng=rng,
            stage_flag_10=stage_flag,
        )
        clocks.append(clock)
        spawns.extend(local_spawns)
        events.extend(local_events)
        writes.extend(local_writes)

    return StageTimelineStep(
        StageTimelineState(
            clocks=tuple(clocks),
            markers=markers,
            rng_state=rng.state,
            rng_calls=rng.calls,
            stage_flag_10=stage_flag,
        ),
        external,
        tuple(spawns),
        tuple(events),
        tuple(writes),
    )
