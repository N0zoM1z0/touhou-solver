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

import argparse
import hashlib
import json
import math
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from th08_ecl_opcodes import OPCODE_SPECS, opcode_spec


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


def _format_float(value: float) -> str:
    if not math.isfinite(value):
        return str(value)
    return f"{value:.7g}"


def _format_words(words: Iterable[int]) -> str:
    return "[" + ", ".join(f"0x{word:08x}" for word in words) + "]"


def _format_word_views(words: Iterable[int]) -> str:
    return "[" + ", ".join(
        f"0x{word:08x}(s={_signed(word)},f={_format_float(_float(word))})"
        for word in words
    ) + "]"


def _dynamic_i16(value: int) -> str:
    value &= 0xFFFF
    return f"$i16({value if value < 0x8000 else value - 0x10000})"


def _dynamic_i32(value: int) -> str:
    return f"$i32({_signed(value)})"


def _dynamic_float(value: int) -> str:
    return f"$f({_format_float(_float(value))})"


def decode_bullet_emission(insn: SubInstruction) -> dict[str, int | float | str]:
    if not 0x60 <= insn.opcode <= 0x68 or len(insn.arguments) != 8:
        raise EclError(
            f"instruction at {insn.offset:#x} is not a 44-byte bullet emission"
        )
    packed, count_1, count_2, speed_1, speed_2, angle_1, angle_2, flags = (
        insn.arguments
    )
    mask = insn.parameter_mask
    return {
        "mode": insn.opcode - 0x60,
        "bullet_type": (
            _dynamic_i16(packed) if mask & 0x01 else packed & 0xFFFF
        ),
        "color": (
            _dynamic_i16(packed >> 16) if mask & 0x02 else packed >> 16
        ),
        "count_1": _dynamic_i32(count_1) if mask & 0x04 else _signed(count_1),
        "count_2": _dynamic_i32(count_2) if mask & 0x08 else _signed(count_2),
        "speed_1": _dynamic_float(speed_1) if mask & 0x10 else _float(speed_1),
        "speed_2": _dynamic_float(speed_2) if mask & 0x20 else _float(speed_2),
        "angle_1": _dynamic_float(angle_1) if mask & 0x40 else _float(angle_1),
        "angle_2": _dynamic_float(angle_2) if mask & 0x80 else _float(angle_2),
        "flags": flags,
    }


def decode_bullet_transform(insn: SubInstruction) -> dict[str, int | float | str]:
    """Decode opcode 0x6F into the recovered 24-byte transform record."""
    if insn.opcode != 0x6F or len(insn.arguments) != 7:
        raise EclError(f"instruction at {insn.offset:#x} is not a transform definition")
    index, kind, wait_for_clear, int_0, int_1, float_0, float_1 = insn.arguments
    mask = insn.parameter_mask
    return {
        "index": _dynamic_i32(index) if mask & 0x01 else _signed(index),
        "kind": _dynamic_i32(kind) if mask & 0x02 else _signed(kind),
        "wait_for_clear": (
            _dynamic_i32(wait_for_clear) if mask & 0x04 else _signed(wait_for_clear)
        ),
        "int_0": _dynamic_i32(int_0) if mask & 0x08 else _signed(int_0),
        "int_1": _dynamic_i32(int_1) if mask & 0x10 else _signed(int_1),
        "float_0": _dynamic_float(float_0) if mask & 0x20 else _float(float_0),
        "float_1": _dynamic_float(float_1) if mask & 0x40 else _float(float_1),
    }


def decode_laser_spawn(insn: SubInstruction) -> dict[str, int | float | str]:
    """Decode opcodes 0x72/0x73 into the descriptor consumed by 0x430F20."""
    if insn.opcode not in {0x72, 0x73} or len(insn.arguments) != 13:
        raise EclError(f"instruction at {insn.offset:#x} is not a laser spawn")
    packed, *args = insn.arguments
    mask = insn.parameter_mask
    floats = [
        _dynamic_float(args[i]) if mask & (1 << (i + 2)) else _float(args[i])
        for i in range(6)
    ]
    ints = [
        _dynamic_i32(args[i]) if mask & (1 << (i + 2)) else _signed(args[i])
        for i in range(6, 9)
    ]
    return {
        "aim_mode": "absolute" if insn.opcode == 0x72 else "player_relative",
        "laser_type": packed & 0xFFFF,
        "color": _dynamic_i16(packed >> 16) if mask & 0x02 else packed >> 16,
        "angle": floats[0],
        "speed": floats[1],
        "tail_distance": floats[2],
        "head_distance": floats[3],
        "max_length": floats[4],
        "width": floats[5],
        "warmup_frames": ints[0],
        "active_frames": ints[1],
        "fade_frames": ints[2],
        "collision_enable_frame": _signed(args[9]),
        "collision_disable_frame": _signed(args[10]),
        "flags": args[11],
    }


def _decode_xor_text(words: Iterable[int], key: int, size: int) -> str:
    raw = struct.pack(f"<{size // 4}I", *tuple(words))
    decoded = bytes(value ^ key for value in raw).split(b"\0", 1)[0]
    try:
        return decoded.decode("cp932")
    except UnicodeDecodeError as exc:
        raise EclError(f"invalid CP932 text in spell-card payload: {exc}") from exc


def decode_spell_card_start(insn: SubInstruction) -> dict[str, int | str]:
    """Decode opcode 0x7A's payload consumed by 0x421280/0x4152A0."""
    if insn.opcode != 0x7A or len(insn.arguments) != 58:
        raise EclError(
            f"instruction at {insn.offset:#x} is not a 244-byte spell-card start"
        )
    packed = insn.arguments[0]
    return {
        "field_00": packed & 0xFFFF,
        "spell_id": packed >> 16,
        "base_score": _signed(insn.arguments[1]),
        "name": _decode_xor_text(insn.arguments[2:14], 0xAA, 48),
        "owner": _decode_xor_text(insn.arguments[14:26], 0xBB, 48),
        "description_1": _decode_xor_text(insn.arguments[26:42], 0xDD, 64),
        "description_2": _decode_xor_text(insn.arguments[42:58], 0xEE, 64),
    }


def _format_bullet_value(value: int | float | str) -> str:
    return _format_float(value) if isinstance(value, float) else str(value)


def _format_bullet(insn: SubInstruction) -> str:
    bullet = decode_bullet_emission(insn)
    return (
        "fire "
        f"mode={bullet['mode']} type={bullet['bullet_type']} color={bullet['color']} "
        f"count=({bullet['count_1']},{bullet['count_2']}) "
        f"speed=({_format_bullet_value(bullet['speed_1'])},"
        f"{_format_bullet_value(bullet['speed_2'])}) "
        f"angle=({_format_bullet_value(bullet['angle_1'])},"
        f"{_format_bullet_value(bullet['angle_2'])}) flags=0x{bullet['flags']:08x}"
    )


def _format_transform(insn: SubInstruction) -> str:
    transform = decode_bullet_transform(insn)
    return "define_transform " + " ".join(
        f"{key}={_format_bullet_value(value)}" for key, value in transform.items()
    )


def _format_laser(insn: SubInstruction) -> str:
    laser = decode_laser_spawn(insn)
    return "spawn_laser " + " ".join(
        f"{key}={_format_bullet_value(value)}" for key, value in laser.items()
    )


def _format_spell_card(insn: SubInstruction) -> str:
    spell = decode_spell_card_start(insn)
    return (
        f"start_spell_card id={spell['spell_id']} "
        f"score={spell['base_score']} field_00={spell['field_00']} "
        f"name={spell['name']!r} owner={spell['owner']!r}"
    )


def _format_sub_annotation(insn: SubInstruction) -> str:
    if 0x60 <= insn.opcode <= 0x68:
        return _format_bullet(insn)
    if insn.opcode == 0x6F:
        return _format_transform(insn)
    if insn.opcode in {0x72, 0x73}:
        return _format_laser(insn)
    if insn.opcode == 0x7A:
        return _format_spell_card(insn)
    spec = opcode_spec(insn.opcode)
    return f"{spec.name} args={_format_word_views(insn.arguments)}"


def _format_timeline_annotation(insn: TimelineInstruction) -> str:
    name = TIMELINE_OPCODE_NAMES.get(insn.opcode, f"opcode_{insn.opcode:02x}")
    words = insn.arguments
    if insn.opcode in {0x00, 0x01, 0x0F} and len(words) >= 3:
        return (
            f"{name} sub={_signed(words[0])} "
            f"pos=({_format_float(_float(words[1]))},{_format_float(_float(words[2]))}) "
            f"rest={_format_words(words[3:])}"
        )
    if insn.opcode in {0x02, 0x04} and len(words) >= 4:
        return (
            f"{name} sub={_signed(words[0])} "
            f"x_range=({_format_float(_float(words[1]))},"
            f"{_format_float(_float(words[2]))}) y={_format_float(_float(words[3]))} "
            f"rest={_format_words(words[4:])}"
        )
    if insn.opcode in {0x03, 0x05} and len(words) >= 2:
        return (
            f"{name} sub={_signed(words[0])} y={_format_float(_float(words[1]))} "
            f"rest={_format_words(words[2:])}"
        )
    if insn.opcode in {0x0B, 0x0C} and len(words) >= 3:
        return (
            f"{name} sub={_signed(words[0])} "
            f"pos=({_format_float(_float(words[1]))},{_format_float(_float(words[2]))}) "
            f"rest={_format_words(words[3:])}"
        )
    return f"{name} args={_format_word_views(words)}"


def format_listing(ecl: EclFile) -> str:
    lines = [
        f"# {ecl.path.name}",
        f"sha256: {ecl.sha256}",
        (
            f"header: subroutines={ecl.header.subroutine_count} "
            f"timelines={ecl.header.timeline_count} "
            f"data_end=0x{ecl.header.data_end_offset:08x}"
        ),
        "",
    ]

    for timeline in ecl.timelines:
        lines.append(
            f"## timeline {timeline.index} [0x{timeline.start:08x}, "
            f"0x{timeline.end:08x})"
        )
        for insn in timeline.instructions:
            lines.append(
                f"0x{insn.offset:08x} t={insn.time:6d} op=0x{insn.opcode:02x} "
                f"size={insn.size:2d} diff=0x{insn.difficulty_mask:02x}  "
                f"{_format_timeline_annotation(insn)}"
            )
        lines.append(
            f"0x{timeline.stop_offset:08x} stop (negative time); "
            f"{timeline.trailing_bytes} bytes remain in timeline region"
        )
        lines.append("")

    for subroutine in ecl.subroutines:
        lines.append(
            f"## sub {subroutine.index} [0x{subroutine.start:08x}, "
            f"0x{subroutine.end:08x})"
        )
        for insn in subroutine.instructions:
            annotation = _format_sub_annotation(insn)
            lines.append(
                f"0x{insn.offset:08x} t={insn.time:6d} op=0x{insn.opcode:04x} "
                f"size={insn.size:2d} b08=0x{insn.byte_08:02x} "
                f"diff=0x{insn.difficulty_mask:02x} "
                f"pmask=0x{insn.parameter_mask:04x}  {annotation}"
            )
        lines.append(f"0x{subroutine.footer_offset:08x} sub-footer")
        lines.append("")

    return "\n".join(lines)


def summarize(ecl: EclFile) -> dict[str, object]:
    sub_histogram = Counter(
        insn.opcode for sub in ecl.subroutines for insn in sub.instructions
    )
    timeline_histogram = Counter(
        insn.opcode for timeline in ecl.timelines for insn in timeline.instructions
    )
    bullet_histogram = Counter()
    bullet_types = Counter()
    bullet_instruction_count = 0
    dynamic_type_count = 0
    dynamic_color_count = 0
    transform_definition_count = 0
    laser_spawn_count = 0
    laser_control_count = 0
    spell_card_start_count = 0
    spell_cards = []
    for sub in ecl.subroutines:
        for insn in sub.instructions:
            if 0x60 <= insn.opcode <= 0x68:
                bullet = decode_bullet_emission(insn)
                bullet_instruction_count += 1
                bullet_histogram[bullet["mode"]] += 1
                if isinstance(bullet["bullet_type"], str):
                    dynamic_type_count += 1
                if isinstance(bullet["color"], str):
                    dynamic_color_count += 1
                if isinstance(bullet["bullet_type"], int) and isinstance(
                    bullet["color"], int
                ):
                    bullet_types[(bullet["bullet_type"], bullet["color"])] += 1
            if insn.opcode == 0x6F:
                decode_bullet_transform(insn)
                transform_definition_count += 1
            if insn.opcode in {0x72, 0x73}:
                decode_laser_spawn(insn)
                laser_spawn_count += 1
            if opcode_spec(insn.opcode).category == "laser" and insn.opcode not in {
                0x72,
                0x73,
            }:
                laser_control_count += 1
            if insn.opcode == 0x7A:
                spell = decode_spell_card_start(insn)
                spell_card_start_count += 1
                spell_cards.append(
                    {
                        "subroutine": sub.index,
                        "time": insn.time,
                        "offset": insn.offset,
                        "difficulty_mask": insn.difficulty_mask,
                        **spell,
                    }
                )

    return {
        "file": ecl.path.name,
        "path": str(ecl.path),
        "sha256": ecl.sha256,
        "subroutine_count": ecl.header.subroutine_count,
        "timeline_count": ecl.header.timeline_count,
        "sub_instruction_count": sum(
            len(sub.instructions) for sub in ecl.subroutines
        ),
        "timeline_instruction_count": sum(
            len(timeline.instructions) for timeline in ecl.timelines
        ),
        "bullet_instruction_count": bullet_instruction_count,
        "dynamic_bullet_type_count": dynamic_type_count,
        "dynamic_bullet_color_count": dynamic_color_count,
        "transform_definition_count": transform_definition_count,
        "laser_spawn_count": laser_spawn_count,
        "laser_control_count": laser_control_count,
        "spell_card_start_count": spell_card_start_count,
        "spell_cards": spell_cards,
        "sub_opcode_histogram": {
            f"0x{opcode:02x}": count for opcode, count in sorted(sub_histogram.items())
        },
        "timeline_opcode_histogram": {
            f"0x{opcode:02x}": count
            for opcode, count in sorted(timeline_histogram.items())
        },
        "bullet_mode_histogram": {
            str(mode): count for mode, count in sorted(bullet_histogram.items())
        },
        "bullet_type_color_histogram": [
            {"type": bullet_type, "color": color, "count": count}
            for (bullet_type, color), count in sorted(bullet_types.items())
        ],
    }


def _expand_inputs(paths: Iterable[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(sorted(path.glob("*.ecl")))
        else:
            expanded.append(path)
    if not expanded:
        raise EclError("no ECL inputs found")
    return expanded


def build_opcode_catalog(ecls: Iterable[EclFile]) -> tuple[list[dict[str, object]], str]:
    counts: Counter[int] = Counter()
    sizes: dict[int, Counter[int]] = {}
    files: dict[int, set[str]] = {}
    for ecl in ecls:
        for sub in ecl.subroutines:
            for insn in sub.instructions:
                counts[insn.opcode] += 1
                sizes.setdefault(insn.opcode, Counter())[insn.size] += 1
                files.setdefault(insn.opcode, set()).add(ecl.path.name)

    rows: list[dict[str, object]] = []
    for spec in OPCODE_SPECS:
        rows.append(
            {
                **spec.to_dict(),
                "opcode_hex": f"0x{spec.opcode:02x}",
                "corpus_count": counts[spec.opcode],
                "instruction_sizes": {
                    str(size): count
                    for size, count in sorted(sizes.get(spec.opcode, {}).items())
                },
                "files": sorted(files.get(spec.opcode, set())),
            }
        )

    lines = [
        "# TH08 Enemy ECL Opcode Catalog",
        "",
        "This table is generated from the locally recovered VM switch and decoded shipped corpus.",
        "Confidence values keep observed behavior separate from provisional naming and unknowns.",
        "",
        "| Opcode | Name | Category | Confidence | Count | Sizes | Description |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        size_text = ", ".join(row["instruction_sizes"].keys()) or "-"
        lines.append(
            f"| `{row['opcode_hex']}` | `{row['name']}` | {row['category']} | "
            f"{row['confidence']} | {row['corpus_count']} | {size_text} | "
            f"{row['description']} |"
        )
    return rows, "\n".join(lines) + "\n"


def build_spell_catalog(ecls: Iterable[EclFile]) -> tuple[list[dict[str, object]], str]:
    by_id: dict[int, dict[str, object]] = {}
    for ecl in ecls:
        for sub in ecl.subroutines:
            for insn in sub.instructions:
                if insn.opcode != 0x7A:
                    continue
                spell = decode_spell_card_start(insn)
                spell_id = int(spell["spell_id"])
                occurrence = {
                    "file": ecl.path.name,
                    "subroutine": sub.index,
                    "time": insn.time,
                    "offset": insn.offset,
                    "difficulty_mask": insn.difficulty_mask,
                }
                row = by_id.setdefault(
                    spell_id,
                    {
                        **spell,
                        "occurrences": [],
                    },
                )
                for key, value in spell.items():
                    if row[key] != value:
                        raise EclError(
                            f"spell ID {spell_id} has conflicting {key}: "
                            f"{row[key]!r} != {value!r}"
                        )
                row["occurrences"].append(occurrence)

    rows = [by_id[spell_id] for spell_id in sorted(by_id)]
    lines = [
        "# TH08 Spell Card Catalog",
        "",
        "Generated only from opcode 0x7A payloads in the decoded shipped ECL corpus.",
        "Names and descriptions are decoded with the XOR keys observed in spell_card_start/spell_card_finish.",
        "",
        "| ID | Name | Owner | Base score | ECL occurrences |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        occurrences = ", ".join(
            f"`{item['file']}:sub{item['subroutine']}@0x{item['offset']:x}/mask0x{item['difficulty_mask']:02x}`"
            for item in row["occurrences"]
        )
        lines.append(
            f"| {row['spell_id']} | {row['name']} | {row['owner']} | "
            f"{row['base_score']} | {occurrences} |"
        )
    return rows, "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    info = subparsers.add_parser("info", help="validate files and print summaries")
    info.add_argument("inputs", type=Path, nargs="+")
    info.add_argument("--json", action="store_true", help="emit JSON")

    dump = subparsers.add_parser("dump", help="write a complete instruction listing")
    dump.add_argument("input", type=Path)
    dump.add_argument("-o", "--output", type=Path)

    corpus = subparsers.add_parser(
        "corpus", help="write listings and a JSON summary for an ECL corpus"
    )
    corpus.add_argument("input", type=Path, help="decoded ECL directory")
    corpus.add_argument("output", type=Path, help="report output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "info":
            reports = [summarize(parse_ecl(path)) for path in _expand_inputs(args.inputs)]
            if args.json:
                print(json.dumps(reports, indent=2, sort_keys=True))
            else:
                for report in reports:
                    print(
                        f"{report['file']}: subs={report['subroutine_count']} "
                        f"timelines={report['timeline_count']} "
                        f"sub_insns={report['sub_instruction_count']} "
                        f"timeline_insns={report['timeline_instruction_count']} "
                        f"fire_insns={report['bullet_instruction_count']}"
                    )
            return 0

        if args.command == "dump":
            listing = format_listing(parse_ecl(args.input))
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(listing, encoding="utf-8")
            else:
                print(listing)
            return 0

        ecl_paths = _expand_inputs([args.input])
        args.output.mkdir(parents=True, exist_ok=True)
        reports = []
        parsed_ecls = []
        for path in ecl_paths:
            ecl = parse_ecl(path)
            parsed_ecls.append(ecl)
            reports.append(summarize(ecl))
            (args.output / f"{path.stem}.txt").write_text(
                format_listing(ecl), encoding="utf-8"
            )
        (args.output / "corpus_summary.json").write_text(
            json.dumps(reports, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        opcode_rows, opcode_markdown = build_opcode_catalog(parsed_ecls)
        (args.output / "opcode_catalog.json").write_text(
            json.dumps(opcode_rows, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.output / "opcode_catalog.md").write_text(
            opcode_markdown, encoding="utf-8"
        )
        spell_rows, spell_markdown = build_spell_catalog(parsed_ecls)
        (args.output / "spell_catalog.json").write_text(
            json.dumps(spell_rows, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (args.output / "spell_catalog.md").write_text(
            spell_markdown, encoding="utf-8"
        )
        print(
            f"wrote {len(reports)} listings, corpus_summary.json, opcode catalog, "
            f"and {len(spell_rows)} spell cards "
            f"to {args.output}"
        )
        return 0
    except (EclError, OSError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
