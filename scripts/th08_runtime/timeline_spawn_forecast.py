"""Bounded live forecast of fixed-position TH08 timeline enemy spawns."""

from __future__ import annotations

from dataclasses import dataclass
import struct
from pathlib import Path
from typing import Any, Sequence

from th08_ecl import EclFile, TimelineInstruction, parse_ecl
from th08_native_future_body_root import TH08_TIMELINE_RUNTIME_BASE
from th08_runtime_agent import ADDR_ENEMY_MANAGER_FRAME


ECL_FILE_CONTEXT_ADDRESS = 0x004ECCB8
ECL_FILE_HEADER_SIZE = 0x48
ECL_FILE_MAGIC = 0x800
ECL_MAXIMUM_TIMELINE_COUNT = 15
TIMELINE_RUNTIME_SLOT_COUNT = 16
TIMELINE_RUNTIME_SLOT_SIZE = 0x10
TIMELINE_SPAWN_SUPPRESSED_ADDRESS = 0x00F54E2C
FRSCREEN_STATE_ADDRESS = 0x0160F428
FRSCREEN_TIMELINE_SPAWN_GATE_OFFSET = 0x2C
ECL_DIFFICULTY_MASK_ADDRESS = 0x0160F53C

FIXED_POSITION_SPAWN_OPCODES = frozenset(
    {0x00, 0x01, 0x0B, 0x0C, 0x0F}
)
ALL_SPAWN_OPCODES = frozenset(
    {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0C, 0x0F}
)
FORECAST_BARRIER_OPCODES = frozenset(
    {0x06, 0x07, 0x08, 0x09, 0x0A, 0x0D, 0x0E, 0x10}
)
DEFAULT_SPAWN_FORECAST_HORIZON = 240
PLAYFIELD_LEFT = 8.0
PLAYFIELD_RIGHT = 376.0


def _signed(word: int) -> int:
    return word if word < 0x80000000 else word - 0x100000000


def _float32(word: int) -> float:
    return struct.unpack("<f", struct.pack("<I", word))[0]


@dataclass(frozen=True, slots=True)
class TimelineClockObservation:
    """One runtime clock mapped back to an immutable static instruction."""

    timeline_index: int
    elapsed: int
    instruction_offset: int


@dataclass(frozen=True, slots=True)
class UpcomingFixedSpawn:
    """One fixed-position spawn reachable without crossing a timeline gate."""

    timeline_index: int
    instruction_offset: int
    instruction_time: int
    lead_frames: int
    subroutine: int
    x: float
    y: float

    def record(self) -> dict[str, int | float]:
        return {
            "timeline_index": self.timeline_index,
            "instruction_offset": self.instruction_offset,
            "instruction_time": self.instruction_time,
            "lead_frames": self.lead_frames,
            "subroutine": self.subroutine,
            "x": self.x,
            "y": self.y,
        }


@dataclass(frozen=True, slots=True)
class UpcomingSpawnObservation:
    """Fail-closed result from one frame-bracketed runtime observation."""

    target: UpcomingFixedSpawn | None
    reason: str
    frame_before: int
    frame_after: int
    horizon_frames: int
    ecl_sha256: str

    def record(self) -> dict[str, object]:
        return {
            "target": (
                self.target.record()
                if self.target is not None
                else None
            ),
            "reason": self.reason,
            "frame_before": self.frame_before,
            "frame_after": self.frame_after,
            "horizon_frames": self.horizon_frames,
            "ecl_sha256": self.ecl_sha256,
        }


def _fixed_spawn(
    timeline_index: int,
    instruction: TimelineInstruction,
    *,
    elapsed: int,
) -> UpcomingFixedSpawn:
    if instruction.opcode not in FIXED_POSITION_SPAWN_OPCODES:
        raise ValueError("instruction is not a fixed-position spawn")
    arguments = instruction.arguments
    if instruction.opcode in {0x00, 0x01, 0x0F}:
        if len(arguments) != 6:
            raise ValueError("ordinary fixed spawn has invalid arguments")
    else:
        if len(arguments) != 7:
            raise ValueError("extended fixed spawn has invalid arguments")
    return UpcomingFixedSpawn(
        timeline_index=timeline_index,
        instruction_offset=instruction.offset,
        instruction_time=instruction.time,
        lead_frames=instruction.time - elapsed,
        subroutine=_signed(arguments[0]),
        x=_float32(arguments[1]),
        y=_float32(arguments[2]),
    )


def forecast_upcoming_fixed_spawn(
    ecl: EclFile,
    clocks: Sequence[TimelineClockObservation],
    *,
    active_difficulty_mask: int,
    horizon_frames: int = DEFAULT_SPAWN_FORECAST_HORIZON,
) -> UpcomingFixedSpawn | None:
    """Find the next in-playfield fixed spawn without crossing a gate."""

    if horizon_frames <= 0:
        raise ValueError("spawn forecast horizon must be positive")
    if not 0 <= active_difficulty_mask <= 0xFF:
        raise ValueError("difficulty mask must fit in one byte")

    candidates: list[UpcomingFixedSpawn] = []
    for clock in clocks:
        if not 0 <= clock.timeline_index < len(ecl.timelines):
            continue
        timeline = ecl.timelines[clock.timeline_index]
        instruction_index = next(
            (
                index
                for index, instruction in enumerate(
                    timeline.instructions
                )
                if instruction.offset == clock.instruction_offset
            ),
            None,
        )
        if instruction_index is None:
            continue
        for instruction in timeline.instructions[instruction_index:]:
            if instruction.time < clock.elapsed:
                continue
            lead_frames = instruction.time - clock.elapsed
            if lead_frames > horizon_frames:
                break
            if not instruction.difficulty_mask & active_difficulty_mask:
                continue
            if instruction.opcode in FORECAST_BARRIER_OPCODES:
                break
            if instruction.opcode not in ALL_SPAWN_OPCODES:
                continue
            if instruction.opcode not in FIXED_POSITION_SPAWN_OPCODES:
                continue
            spawn = _fixed_spawn(
                clock.timeline_index,
                instruction,
                elapsed=clock.elapsed,
            )
            if PLAYFIELD_LEFT <= spawn.x <= PLAYFIELD_RIGHT:
                candidates.append(spawn)
                break
    return (
        min(
            candidates,
            key=lambda spawn: (
                spawn.lead_frames,
                spawn.timeline_index,
                spawn.instruction_offset,
            ),
        )
        if candidates
        else None
    )


class StageTimelineSpawnForecaster:
    """Validate a live relocated timeline before exposing one spawn target."""

    def __init__(
        self,
        ecl_path: Path,
        *,
        expected_difficulty_mask: int,
        horizon_frames: int = DEFAULT_SPAWN_FORECAST_HORIZON,
    ) -> None:
        self.ecl = parse_ecl(ecl_path)
        self._static_bytes = ecl_path.read_bytes()
        self.expected_difficulty_mask = expected_difficulty_mask
        self.horizon_frames = horizon_frames

    def _result(
        self,
        target: UpcomingFixedSpawn | None,
        reason: str,
        *,
        frame_before: int,
        frame_after: int,
    ) -> UpcomingSpawnObservation:
        return UpcomingSpawnObservation(
            target=target,
            reason=reason,
            frame_before=frame_before,
            frame_after=frame_after,
            horizon_frames=self.horizon_frames,
            ecl_sha256=self.ecl.sha256,
        )

    def observe(self, reader: Any) -> UpcomingSpawnObservation:
        """Capture clocks/gates and verify the selected runtime byte range."""

        frame_before = int(reader.u32(ADDR_ENEMY_MANAGER_FRAME))
        try:
            context = reader.read(ECL_FILE_CONTEXT_ADDRESS, 8)
            if len(context) != 8:
                raise ValueError("short runtime ECL context")
            ecl_base, subroutine_table = struct.unpack("<II", context)
            if ecl_base == 0:
                raise ValueError("runtime ECL base is null")
            header = reader.read(ecl_base, ECL_FILE_HEADER_SIZE)
            if len(header) != ECL_FILE_HEADER_SIZE:
                raise ValueError("short relocated ECL header")
            magic, subroutine_count, timeline_count = struct.unpack_from(
                "<IHH",
                header,
            )
            if (
                magic != ECL_FILE_MAGIC
                or subroutine_count != self.ecl.header.subroutine_count
                or timeline_count != len(self.ecl.timelines)
                or timeline_count > ECL_MAXIMUM_TIMELINE_COUNT
                or subroutine_table != ecl_base + ECL_FILE_HEADER_SIZE
            ):
                raise ValueError("runtime ECL header identity mismatch")
            relocated_timeline_offsets = struct.unpack_from(
                "<16I",
                header,
                8,
            )
            if tuple(
                pointer - ecl_base
                for pointer in relocated_timeline_offsets[:timeline_count]
            ) != self.ecl.header.timeline_offsets:
                raise ValueError("runtime timeline offsets mismatch")
            if (
                relocated_timeline_offsets[timeline_count] - ecl_base
                != len(self._static_bytes)
            ):
                raise ValueError("runtime ECL data-end mismatch")

            difficulty_mask = reader.read(
                ECL_DIFFICULTY_MASK_ADDRESS,
                1,
            )
            if (
                len(difficulty_mask) != 1
                or difficulty_mask[0] != self.expected_difficulty_mask
            ):
                raise ValueError("runtime difficulty mask mismatch")
            if struct.unpack(
                "<I",
                reader.read(
                    TIMELINE_SPAWN_SUPPRESSED_ADDRESS,
                    4,
                ),
            )[0]:
                frame_after = int(
                    reader.u32(ADDR_ENEMY_MANAGER_FRAME)
                )
                return self._result(
                    None,
                    "timeline_spawn_suppressed",
                    frame_before=frame_before,
                    frame_after=frame_after,
                )
            spawn_gate = reader.read(
                FRSCREEN_STATE_ADDRESS
                + FRSCREEN_TIMELINE_SPAWN_GATE_OFFSET,
                1,
            )
            if len(spawn_gate) != 1 or spawn_gate[0]:
                frame_after = int(
                    reader.u32(ADDR_ENEMY_MANAGER_FRAME)
                )
                return self._result(
                    None,
                    "timeline_stage_transition_busy",
                    frame_before=frame_before,
                    frame_after=frame_after,
                )

            runtime_table = reader.read(
                TH08_TIMELINE_RUNTIME_BASE,
                TIMELINE_RUNTIME_SLOT_COUNT
                * TIMELINE_RUNTIME_SLOT_SIZE,
            )
            if len(runtime_table) != (
                TIMELINE_RUNTIME_SLOT_COUNT
                * TIMELINE_RUNTIME_SLOT_SIZE
            ):
                raise ValueError("short timeline runtime table")
            clocks: list[TimelineClockObservation] = []
            for timeline_index, timeline in enumerate(
                self.ecl.timelines
            ):
                base = timeline_index * TIMELINE_RUNTIME_SLOT_SIZE
                _, _, elapsed, instruction_pointer = struct.unpack_from(
                    "<iIiI",
                    runtime_table,
                    base,
                )
                instruction_offset = (
                    instruction_pointer - ecl_base
                    if instruction_pointer
                    else timeline.start
                )
                clocks.append(
                    TimelineClockObservation(
                        timeline_index=timeline_index,
                        elapsed=elapsed,
                        instruction_offset=instruction_offset,
                    )
                )
            target = forecast_upcoming_fixed_spawn(
                self.ecl,
                clocks,
                active_difficulty_mask=difficulty_mask[0],
                horizon_frames=self.horizon_frames,
            )
            if target is not None:
                clock = clocks[target.timeline_index]
                end_offset = (
                    target.instruction_offset
                    + next(
                        instruction.size
                        for instruction in self.ecl.timelines[
                            target.timeline_index
                        ].instructions
                        if (
                            instruction.offset
                            == target.instruction_offset
                        )
                    )
                )
                if not (
                    0 <= clock.instruction_offset < end_offset
                    <= len(self._static_bytes)
                ):
                    raise ValueError("forecast byte interval is invalid")
                runtime_bytes = reader.read(
                    ecl_base + clock.instruction_offset,
                    end_offset - clock.instruction_offset,
                )
                if runtime_bytes != self._static_bytes[
                    clock.instruction_offset:end_offset
                ]:
                    raise ValueError(
                        "runtime forecast instruction bytes mismatch"
                    )
            frame_after = int(reader.u32(ADDR_ENEMY_MANAGER_FRAME))
            if frame_after != frame_before:
                return self._result(
                    None,
                    "timeline_runtime_unstable",
                    frame_before=frame_before,
                    frame_after=frame_after,
                )
            return self._result(
                target,
                (
                    "upcoming_fixed_spawn_observed"
                    if target is not None
                    else "no_fixed_spawn_within_horizon"
                ),
                frame_before=frame_before,
                frame_after=frame_after,
            )
        except (OSError, RuntimeError, ValueError, struct.error) as error:
            frame_after = int(reader.u32(ADDR_ENEMY_MANAGER_FRAME))
            return self._result(
                None,
                f"timeline_forecast_error:{type(error).__name__}:{error}",
                frame_before=frame_before,
                frame_after=frame_after,
            )


__all__ = [
    "DEFAULT_SPAWN_FORECAST_HORIZON",
    "StageTimelineSpawnForecaster",
    "TimelineClockObservation",
    "UpcomingFixedSpawn",
    "UpcomingSpawnObservation",
    "forecast_upcoming_fixed_spawn",
]
