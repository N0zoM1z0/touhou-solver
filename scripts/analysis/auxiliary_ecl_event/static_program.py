"""Exact-image summaries for observed auxiliary target subroutines."""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Iterable
from pathlib import Path

from th08_ecl_tool.core import EclFile, parse_ecl


def _target_program(
    ecl: EclFile,
    image: bytes,
    target: int,
) -> dict[str, object]:
    if not 0 <= target < len(ecl.subroutines):
        return {
            "target_subroutine": target,
            "status": "invalid_target",
            "instructions": [],
            "literal_fire_cycle": False,
        }
    instructions = ecl.subroutines[target].instructions
    rows = [
        {
            "file_offset": instruction.offset,
            "file_offset_hex": f"{instruction.offset:#x}",
            "time": instruction.time,
            "opcode": instruction.opcode,
            "opcode_hex": f"{instruction.opcode:#04x}",
            "size": instruction.size,
            "difficulty_mask": instruction.difficulty_mask,
            "parameter_mask": instruction.parameter_mask,
        }
        for instruction in instructions
    ]
    literal_cycle = False
    timer_threshold: int | None = None
    jump_target_offset: int | None = None
    requested_count_fields: int | None = None
    if (
        len(instructions) == 3
        and instructions[0].opcode == 0x6F
        and instructions[0].time == 0
        and instructions[0].parameter_mask == 0
        and 0x60 <= instructions[1].opcode <= 0x68
        and instructions[1].time == 0
        and instructions[2].opcode == 0x04
        and instructions[2].parameter_mask == 0
        and instructions[2].size == 20
    ):
        jump_payload = image[
            instructions[2].offset + 12
            : instructions[2].offset + instructions[2].size
        ]
        jump_timer, jump_relative = struct.unpack("<ii", jump_payload)
        fire_payload = image[
            instructions[1].offset + 12
            : instructions[1].offset + instructions[1].size
        ]
        if len(fire_payload) == 32:
            _type, _color, count1, count2 = struct.unpack_from(
                "<hhii",
                fire_payload,
            )
            if not instructions[1].parameter_mask & (0x04 | 0x08):
                requested_count_fields = (
                    0 if count1 <= 0 or count2 <= 0 else count1 * count2
                )
        jump_target_offset = instructions[2].offset + jump_relative
        timer_threshold = instructions[2].time
        literal_cycle = (
            jump_timer == 0
            and jump_target_offset == instructions[1].offset
        )
    return {
        "target_subroutine": target,
        "status": "ok",
        "instructions": rows,
        "literal_fire_cycle": literal_cycle,
        "timer_threshold": timer_threshold,
        "jump_target_offset": jump_target_offset,
        "jump_target_offset_hex": (
            f"{jump_target_offset:#x}"
            if jump_target_offset is not None
            else None
        ),
        "literal_requested_count_fields": requested_count_fields,
    }


def summarize_observed_target_programs(
    path: Path,
    targets: Iterable[int],
    *,
    expected_sha256: str,
) -> dict[str, object]:
    image = path.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != expected_sha256:
        raise ValueError("static ECL image digest does not match expectation")
    ecl = parse_ecl(path)
    if ecl.sha256 != digest:
        raise ValueError("parsed ECL identity does not match exact bytes")
    programs = [
        _target_program(ecl, image, target)
        for target in sorted(set(targets))
    ]
    return {
        "path": str(path),
        "sha256": digest,
        "bytes": len(image),
        "target_programs": programs,
        "all_observed_targets_are_literal_fire_cycles": (
            bool(programs)
            and all(program["literal_fire_cycle"] for program in programs)
        ),
    }


__all__ = ["summarize_observed_target_programs"]
