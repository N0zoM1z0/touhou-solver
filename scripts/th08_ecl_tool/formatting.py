"""Semantic decoders and human-readable listings for parsed TH08 ECL."""

from __future__ import annotations

import math
import struct
from collections.abc import Iterable

from th08_ecl_opcodes import opcode_spec
from th08_ecl_tool.core import (
    TIMELINE_OPCODE_NAMES,
    EclError,
    EclFile,
    SubInstruction,
    TimelineInstruction,
    _float,
    _signed,
)


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


def decode_bullet_emission(
    insn: SubInstruction,
) -> dict[str, int | float | str]:
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
        "count_1": (
            _dynamic_i32(count_1) if mask & 0x04 else _signed(count_1)
        ),
        "count_2": (
            _dynamic_i32(count_2) if mask & 0x08 else _signed(count_2)
        ),
        "speed_1": (
            _dynamic_float(speed_1) if mask & 0x10 else _float(speed_1)
        ),
        "speed_2": (
            _dynamic_float(speed_2) if mask & 0x20 else _float(speed_2)
        ),
        "angle_1": (
            _dynamic_float(angle_1) if mask & 0x40 else _float(angle_1)
        ),
        "angle_2": (
            _dynamic_float(angle_2) if mask & 0x80 else _float(angle_2)
        ),
        "flags": flags,
    }


def decode_bullet_transform(
    insn: SubInstruction,
) -> dict[str, int | float | str]:
    """Decode opcode 0x6F into the recovered 24-byte transform record."""

    if insn.opcode != 0x6F or len(insn.arguments) != 7:
        raise EclError(
            f"instruction at {insn.offset:#x} is not a transform definition"
        )
    index, kind, wait_for_clear, int_0, int_1, float_0, float_1 = insn.arguments
    mask = insn.parameter_mask
    return {
        "index": _dynamic_i32(index) if mask & 0x01 else _signed(index),
        "kind": _dynamic_i32(kind) if mask & 0x02 else _signed(kind),
        "wait_for_clear": (
            _dynamic_i32(wait_for_clear)
            if mask & 0x04
            else _signed(wait_for_clear)
        ),
        "int_0": _dynamic_i32(int_0) if mask & 0x08 else _signed(int_0),
        "int_1": _dynamic_i32(int_1) if mask & 0x10 else _signed(int_1),
        "float_0": (
            _dynamic_float(float_0) if mask & 0x20 else _float(float_0)
        ),
        "float_1": (
            _dynamic_float(float_1) if mask & 0x40 else _float(float_1)
        ),
    }


def decode_laser_spawn(
    insn: SubInstruction,
) -> dict[str, int | float | str]:
    """Decode opcodes 0x72/0x73 into the descriptor consumed by 0x430F20."""

    if insn.opcode not in {0x72, 0x73} or len(insn.arguments) != 13:
        raise EclError(
            f"instruction at {insn.offset:#x} is not a laser spawn"
        )
    packed, *args = insn.arguments
    mask = insn.parameter_mask
    floats = [
        _dynamic_float(args[i])
        if mask & (1 << (i + 2))
        else _float(args[i])
        for i in range(6)
    ]
    ints = [
        _dynamic_i32(args[i])
        if mask & (1 << (i + 2))
        else _signed(args[i])
        for i in range(6, 9)
    ]
    return {
        "aim_mode": (
            "absolute" if insn.opcode == 0x72 else "player_relative"
        ),
        "laser_type": packed & 0xFFFF,
        "color": (
            _dynamic_i16(packed >> 16) if mask & 0x02 else packed >> 16
        ),
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
        raise EclError(
            f"invalid CP932 text in spell-card payload: {exc}"
        ) from exc


def decode_spell_card_start(
    insn: SubInstruction,
) -> dict[str, int | str]:
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
        "description_1": _decode_xor_text(
            insn.arguments[26:42], 0xDD, 64
        ),
        "description_2": _decode_xor_text(
            insn.arguments[42:58], 0xEE, 64
        ),
    }


def _format_bullet_value(value: int | float | str) -> str:
    return _format_float(value) if isinstance(value, float) else str(value)


def _format_bullet(insn: SubInstruction) -> str:
    bullet = decode_bullet_emission(insn)
    return (
        "fire "
        f"mode={bullet['mode']} type={bullet['bullet_type']} "
        f"color={bullet['color']} "
        f"count=({bullet['count_1']},{bullet['count_2']}) "
        f"speed=({_format_bullet_value(bullet['speed_1'])},"
        f"{_format_bullet_value(bullet['speed_2'])}) "
        f"angle=({_format_bullet_value(bullet['angle_1'])},"
        f"{_format_bullet_value(bullet['angle_2'])}) "
        f"flags=0x{bullet['flags']:08x}"
    )


def _format_transform(insn: SubInstruction) -> str:
    transform = decode_bullet_transform(insn)
    return "define_transform " + " ".join(
        f"{key}={_format_bullet_value(value)}"
        for key, value in transform.items()
    )


def _format_laser(insn: SubInstruction) -> str:
    laser = decode_laser_spawn(insn)
    return "spawn_laser " + " ".join(
        f"{key}={_format_bullet_value(value)}"
        for key, value in laser.items()
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
    name = TIMELINE_OPCODE_NAMES.get(
        insn.opcode, f"opcode_{insn.opcode:02x}"
    )
    words = insn.arguments
    if insn.opcode in {0x00, 0x01, 0x0F} and len(words) >= 3:
        return (
            f"{name} sub={_signed(words[0])} "
            f"pos=({_format_float(_float(words[1]))},"
            f"{_format_float(_float(words[2]))}) "
            f"rest={_format_words(words[3:])}"
        )
    if insn.opcode in {0x02, 0x04} and len(words) >= 4:
        return (
            f"{name} sub={_signed(words[0])} "
            f"x_range=({_format_float(_float(words[1]))},"
            f"{_format_float(_float(words[2]))}) "
            f"y={_format_float(_float(words[3]))} "
            f"rest={_format_words(words[4:])}"
        )
    if insn.opcode in {0x03, 0x05} and len(words) >= 2:
        return (
            f"{name} sub={_signed(words[0])} "
            f"y={_format_float(_float(words[1]))} "
            f"rest={_format_words(words[2:])}"
        )
    if insn.opcode in {0x0B, 0x0C} and len(words) >= 3:
        return (
            f"{name} sub={_signed(words[0])} "
            f"pos=({_format_float(_float(words[1]))},"
            f"{_format_float(_float(words[2]))}) "
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
                f"0x{insn.offset:08x} t={insn.time:6d} "
                f"op=0x{insn.opcode:02x} "
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
                f"0x{insn.offset:08x} t={insn.time:6d} "
                f"op=0x{insn.opcode:04x} "
                f"size={insn.size:2d} b08=0x{insn.byte_08:02x} "
                f"diff=0x{insn.difficulty_mask:02x} "
                f"pmask=0x{insn.parameter_mask:04x}  {annotation}"
            )
        lines.append(f"0x{subroutine.footer_offset:08x} sub-footer")
        lines.append("")

    return "\n".join(lines)
