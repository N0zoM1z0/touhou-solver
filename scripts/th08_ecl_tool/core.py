#!/usr/bin/env python3
"""Parse decoded TH08 ECL files without third-party format knowledge.

The layouts implemented here were recovered from these TH08 routines:

* 0x00418330: file header relocation
* 0x0042DFB0 / 0x0042DFD0: stage timeline count/pointer access
* 0x0042A8A0: stage timeline scheduler
* 0x004184B0: per-enemy ECL VM
* 0x00422720: ECL opcodes 0x60..0x68 (bullet emission)

Input files must already have their optional ``edz?`` wrapper removed. Use
``th08_resource.py`` for that step.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path


ECL_MAGIC = 0x800
HEADER_SIZE = 0x48
TIMELINE_SLOT_COUNT = 16
SUB_INSTRUCTION_HEADER_SIZE = 12
TIMELINE_INSTRUCTION_HEADER_SIZE = 8


class EclError(ValueError):
    """Raised when an ECL file violates a recovered structural invariant."""


@dataclass(frozen=True)
class EclHeader:
    subroutine_count: int
    timeline_count: int
    timeline_offsets: tuple[int, ...]
    data_end_offset: int
    subroutine_offsets: tuple[int, ...]


@dataclass(frozen=True)
class SubInstruction:
    offset: int
    time: int
    opcode: int
    size: int
    byte_08: int
    difficulty_mask: int
    parameter_mask: int
    arguments: tuple[int, ...]


@dataclass(frozen=True)
class Subroutine:
    index: int
    start: int
    end: int
    instructions: tuple[SubInstruction, ...]
    footer_offset: int


@dataclass(frozen=True)
class TimelineInstruction:
    offset: int
    time: int
    opcode: int
    size: int
    difficulty_mask: int
    arguments: tuple[int, ...]


@dataclass(frozen=True)
class Timeline:
    index: int
    start: int
    end: int
    instructions: tuple[TimelineInstruction, ...]
    stop_offset: int
    trailing_bytes: int


@dataclass(frozen=True)
class EclFile:
    path: Path
    sha256: str
    header: EclHeader
    subroutines: tuple[Subroutine, ...]
    timelines: tuple[Timeline, ...]


TIMELINE_OPCODE_NAMES = {
    0x00: "spawn_enemy",
    0x01: "spawn_enemy_variant",
    0x02: "spawn_enemy_random_x_range",
    0x03: "spawn_enemy_random_x_playfield",
    0x04: "spawn_enemy_random_x_range_variant",
    0x05: "spawn_enemy_random_x_playfield_variant",
    0x06: "engine_event_06",
    0x07: "conditional_timeline_stop",
    0x08: "set_enemy_field",
    0x09: "engine_event_09",
    0x0A: "wait_enemy_inactive",
    0x0B: "spawn_enemy_extended",
    0x0C: "spawn_enemy_extended_variant",
    0x0D: "wait_marker",
    0x0E: "publish_marker",
    0x0F: "spawn_enemy_opcode_0f",
    0x10: "set_stage_flag",
}


def _require_range(data: bytes, offset: int, size: int, label: str) -> None:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise EclError(
            f"{label} is outside file: offset={offset:#x}, size={size:#x}, "
            f"file_size={len(data):#x}"
        )


def _u32_words(data: bytes, offset: int, size: int, label: str) -> tuple[int, ...]:
    if size % 4:
        raise EclError(f"{label} argument area is not dword-aligned: {size:#x}")
    _require_range(data, offset, size, label)
    return tuple(struct.unpack_from(f"<{size // 4}I", data, offset)) if size else ()


def _parse_header(data: bytes) -> EclHeader:
    _require_range(data, 0, HEADER_SIZE, "ECL header")
    magic, subroutine_count, timeline_count = struct.unpack_from("<IHH", data, 0)
    if magic != ECL_MAGIC:
        raise EclError(
            f"bad ECL magic {magic:#x}; expected decoded magic {ECL_MAGIC:#x}"
        )
    if timeline_count >= TIMELINE_SLOT_COUNT:
        raise EclError(
            f"timeline count {timeline_count} leaves no slot for the end sentinel"
        )

    all_timeline_offsets = struct.unpack_from("<16I", data, 8)
    timeline_offsets = tuple(all_timeline_offsets[:timeline_count])
    data_end_offset = all_timeline_offsets[timeline_count]

    sub_table_size = subroutine_count * 4
    _require_range(data, HEADER_SIZE, sub_table_size, "subroutine offset table")
    subroutine_offsets = tuple(
        struct.unpack_from(f"<{subroutine_count}I", data, HEADER_SIZE)
    )

    if data_end_offset != len(data):
        raise EclError(
            f"header data-end offset {data_end_offset:#x} != file size {len(data):#x}"
        )
    if not subroutine_offsets:
        raise EclError("ECL contains no enemy subroutines")
    if timeline_count and not timeline_offsets:
        raise EclError("ECL contains no stage timeline offsets")

    ordered = (*subroutine_offsets, *timeline_offsets, data_end_offset)
    if any(left >= right for left, right in zip(ordered, ordered[1:])):
        raise EclError("subroutine/timeline offsets are not strictly increasing")

    return EclHeader(
        subroutine_count=subroutine_count,
        timeline_count=timeline_count,
        timeline_offsets=timeline_offsets,
        data_end_offset=data_end_offset,
        subroutine_offsets=subroutine_offsets,
    )


def _parse_subroutine(
    data: bytes, index: int, start: int, end: int
) -> Subroutine:
    instructions: list[SubInstruction] = []
    offset = start
    footer_offset = -1

    while offset < end:
        _require_range(data, offset, SUB_INSTRUCTION_HEADER_SIZE, f"sub {index} header")
        time, opcode, size, byte_08, difficulty_mask, parameter_mask = (
            struct.unpack_from("<iHHBBH", data, offset)
        )

        if time == -1 and opcode == 0xFFFF:
            if size != SUB_INSTRUCTION_HEADER_SIZE or offset + size != end:
                raise EclError(
                    f"sub {index} has malformed footer at {offset:#x}: "
                    f"size={size:#x}, end={end:#x}"
                )
            footer_offset = offset
            offset += size
            break

        if size < SUB_INSTRUCTION_HEADER_SIZE or size % 4:
            raise EclError(
                f"sub {index} has invalid instruction size {size:#x} at {offset:#x}"
            )
        if offset + size > end:
            raise EclError(
                f"sub {index} instruction at {offset:#x} crosses end {end:#x}"
            )
        if opcode > 0xB8:
            raise EclError(f"sub {index} has unknown opcode {opcode:#x} at {offset:#x}")

        arguments = _u32_words(
            data,
            offset + SUB_INSTRUCTION_HEADER_SIZE,
            size - SUB_INSTRUCTION_HEADER_SIZE,
            f"sub {index} instruction {offset:#x}",
        )
        instructions.append(
            SubInstruction(
                offset=offset,
                time=time,
                opcode=opcode,
                size=size,
                byte_08=byte_08,
                difficulty_mask=difficulty_mask,
                parameter_mask=parameter_mask,
                arguments=arguments,
            )
        )
        offset += size

    if offset != end or footer_offset < 0:
        raise EclError(f"sub {index} did not terminate exactly at {end:#x}")

    return Subroutine(
        index=index,
        start=start,
        end=end,
        instructions=tuple(instructions),
        footer_offset=footer_offset,
    )


def _parse_timeline(data: bytes, index: int, start: int, end: int) -> Timeline:
    instructions: list[TimelineInstruction] = []
    offset = start
    stop_offset = -1

    while offset < end:
        _require_range(data, offset, TIMELINE_INSTRUCTION_HEADER_SIZE, "timeline header")
        time, opcode, size, difficulty_mask = struct.unpack_from("<iHBB", data, offset)
        if time < 0:
            stop_offset = offset
            break
        if size < TIMELINE_INSTRUCTION_HEADER_SIZE or size % 4:
            raise EclError(
                f"timeline {index} has invalid size {size:#x} at {offset:#x}"
            )
        if offset + size > end:
            raise EclError(
                f"timeline {index} instruction at {offset:#x} crosses end {end:#x}"
            )
        if opcode > 0x10:
            raise EclError(
                f"timeline {index} has unknown opcode {opcode:#x} at {offset:#x}"
            )

        arguments = _u32_words(
            data,
            offset + TIMELINE_INSTRUCTION_HEADER_SIZE,
            size - TIMELINE_INSTRUCTION_HEADER_SIZE,
            f"timeline {index} instruction {offset:#x}",
        )
        instructions.append(
            TimelineInstruction(
                offset=offset,
                time=time,
                opcode=opcode,
                size=size,
                difficulty_mask=difficulty_mask,
                arguments=arguments,
            )
        )
        offset += size

    if stop_offset < 0:
        raise EclError(f"timeline {index} has no negative-time stop record")

    return Timeline(
        index=index,
        start=start,
        end=end,
        instructions=tuple(instructions),
        stop_offset=stop_offset,
        trailing_bytes=end - stop_offset,
    )


def parse_ecl(path: Path) -> EclFile:
    data = path.read_bytes()
    header = _parse_header(data)

    first_timeline = (
        header.timeline_offsets[0] if header.timeline_offsets else header.data_end_offset
    )
    sub_ends = (*header.subroutine_offsets[1:], first_timeline)
    subroutines = tuple(
        _parse_subroutine(data, index, start, end)
        for index, (start, end) in enumerate(
            zip(header.subroutine_offsets, sub_ends, strict=True)
        )
    )

    timeline_ends = (*header.timeline_offsets[1:], header.data_end_offset)
    timelines = tuple(
        _parse_timeline(data, index, start, end)
        for index, (start, end) in enumerate(
            zip(header.timeline_offsets, timeline_ends, strict=True)
        )
    )

    return EclFile(
        path=path,
        sha256=hashlib.sha256(data).hexdigest(),
        header=header,
        subroutines=subroutines,
        timelines=timelines,
    )


def _signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def _float(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]
