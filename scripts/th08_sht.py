#!/usr/bin/env python3
"""Parse TH08 player SHT resources from locally recovered executable layouts.

The file header and relocation behavior come from player_sht_load (0x0044DD70).
The 56-byte shot record is consumed by player_shot_initialize (0x0044FB70),
and level selection is performed by player_emit_shot_level (0x00450F60).

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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


FIXED_HEADER_SIZE = 0x38
LEVEL_ENTRY_SIZE = 8
SHOT_RECORD_SIZE = 56
SHOT_RECORD_FORMAT = "<hh6f6h4I"
SENTINEL_SIZE = 4


class ShtError(ValueError):
    """Raised when an SHT file violates a recovered structural invariant."""


@dataclass(frozen=True)
class ShtHeader:
    unknown_00: int
    shot_level_count: int
    unknown_float_04: float
    bomb_gate_reset_value: int
    player_hitbox_width: float
    player_aux_collision_width: float
    item_homing_speed: float
    item_collection_box_width: float
    point_value_line_y: float
    unknown_int_20: int
    unfocused_cardinal_speed: float
    focused_cardinal_speed: float
    unfocused_diagonal_axis_speed: float
    focused_diagonal_axis_speed: float
    item_fall_scale: float


@dataclass(frozen=True)
class ShtShotRecord:
    offset: int
    fire_period: int
    fire_phase: int
    spawn_offset_x: float
    spawn_offset_y: float
    hitbox_width: float
    hitbox_height: float
    angle: float
    speed: float
    damage: int
    field_1e: int
    source_index: int
    shot_type: int
    animation_id: int
    sound_id: int
    callback_0_index: int
    callback_1_index: int
    callback_2_index: int
    callback_3_index: int


@dataclass(frozen=True)
class ShtLevel:
    index: int
    start: int
    end: int
    power_upper_bound: int
    sentinel_offset: int
    sentinel_field_02: int
    shots: tuple[ShtShotRecord, ...]


@dataclass(frozen=True)
class ShtFile:
    path: Path
    sha256: str
    header: ShtHeader
    levels: tuple[ShtLevel, ...]


def _require_range(data: bytes, offset: int, size: int, label: str) -> None:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ShtError(
            f"{label} is outside file: offset={offset:#x}, size={size:#x}, "
            f"file_size={len(data):#x}"
        )


def _parse_header(data: bytes) -> ShtHeader:
    _require_range(data, 0, FIXED_HEADER_SIZE, "SHT fixed header")
    values = struct.unpack_from("<HHfI5fI5f", data, 0)
    header = ShtHeader(*values)
    if not 1 <= header.shot_level_count <= 32:
        raise ShtError(f"implausible shot level count: {header.shot_level_count}")
    table_end = FIXED_HEADER_SIZE + header.shot_level_count * LEVEL_ENTRY_SIZE
    _require_range(data, FIXED_HEADER_SIZE, table_end - FIXED_HEADER_SIZE, "level table")
    float_values = (
        header.unknown_float_04,
        header.player_hitbox_width,
        header.player_aux_collision_width,
        header.item_homing_speed,
        header.item_collection_box_width,
        header.point_value_line_y,
        header.unfocused_cardinal_speed,
        header.focused_cardinal_speed,
        header.unfocused_diagonal_axis_speed,
        header.focused_diagonal_axis_speed,
        header.item_fall_scale,
    )
    if not all(math.isfinite(value) for value in float_values):
        raise ShtError("header contains a non-finite float")
    return header


def _parse_shot(data: bytes, offset: int) -> ShtShotRecord:
    _require_range(data, offset, SHOT_RECORD_SIZE, "shot record")
    values = struct.unpack_from(SHOT_RECORD_FORMAT, data, offset)
    shot = ShtShotRecord(offset, *values)
    float_values = (
        shot.spawn_offset_x,
        shot.spawn_offset_y,
        shot.hitbox_width,
        shot.hitbox_height,
        shot.angle,
        shot.speed,
    )
    if not all(math.isfinite(value) for value in float_values):
        raise ShtError(f"shot at {offset:#x} contains a non-finite float")
    return shot


def _parse_level(
    data: bytes, index: int, start: int, end: int, power_upper_bound: int
) -> ShtLevel:
    if start >= end:
        raise ShtError(f"level {index} has invalid region [{start:#x}, {end:#x})")
    offset = start
    shots: list[ShtShotRecord] = []
    sentinel_offset = -1
    sentinel_field_02 = 0
    while offset < end:
        _require_range(data, offset, SENTINEL_SIZE, f"level {index} record marker")
        fire_period, field_02 = struct.unpack_from("<hh", data, offset)
        if fire_period < 0:
            sentinel_offset = offset
            sentinel_field_02 = field_02
            offset += SENTINEL_SIZE
            break
        if offset + SHOT_RECORD_SIZE > end:
            raise ShtError(
                f"level {index} shot at {offset:#x} crosses region end {end:#x}"
            )
        shots.append(_parse_shot(data, offset))
        offset += SHOT_RECORD_SIZE

    if sentinel_offset < 0:
        raise ShtError(f"level {index} has no negative-period sentinel")
    if offset != end:
        raise ShtError(
            f"level {index} sentinel ends at {offset:#x}, expected {end:#x}"
        )
    return ShtLevel(
        index=index,
        start=start,
        end=end,
        power_upper_bound=power_upper_bound,
        sentinel_offset=sentinel_offset,
        sentinel_field_02=sentinel_field_02,
        shots=tuple(shots),
    )


def parse_sht(path: Path) -> ShtFile:
    data = path.read_bytes()
    header = _parse_header(data)
    table_end = FIXED_HEADER_SIZE + header.shot_level_count * LEVEL_ENTRY_SIZE
    entries = tuple(
        struct.unpack_from("<Ii", data, FIXED_HEADER_SIZE + index * LEVEL_ENTRY_SIZE)
        for index in range(header.shot_level_count)
    )
    offsets = tuple(offset for offset, _ in entries)
    if offsets[0] != table_end:
        raise ShtError(
            f"first level starts at {offsets[0]:#x}, expected table end {table_end:#x}"
        )
    if any(offset % 4 for offset in offsets):
        raise ShtError("level offset is not dword-aligned")
    ordered = (*offsets, len(data))
    if any(left >= right for left, right in zip(ordered, ordered[1:])):
        raise ShtError("level offsets and file end are not strictly increasing")
    thresholds = tuple(threshold for _, threshold in entries)
    if any(left > right for left, right in zip(thresholds, thresholds[1:])):
        raise ShtError("power upper bounds decrease")

    ends = (*offsets[1:], len(data))
    levels = tuple(
        _parse_level(data, index, start, end, threshold)
        for index, ((start, threshold), end) in enumerate(
            zip(entries, ends, strict=True)
        )
    )
    return ShtFile(
        path=path,
        sha256=hashlib.sha256(data).hexdigest(),
        header=header,
        levels=levels,
    )


def _float_text(value: float) -> str:
    return f"{value:.8g}"


def format_listing(sht: ShtFile) -> str:
    header = sht.header
    lines = [
        f"# {sht.path.name}",
        f"sha256: {sht.sha256}",
        f"shot_levels: {header.shot_level_count}",
        f"bomb_gate_reset_value: {header.bomb_gate_reset_value}",
        (
            "movement: "
            f"unfocused_cardinal={_float_text(header.unfocused_cardinal_speed)} "
            f"unfocused_diagonal_axis={_float_text(header.unfocused_diagonal_axis_speed)} "
            f"focused_cardinal={_float_text(header.focused_cardinal_speed)} "
            f"focused_diagonal_axis={_float_text(header.focused_diagonal_axis_speed)}"
        ),
        f"item_homing_speed: {_float_text(header.item_homing_speed)}",
        f"item_fall_scale: {_float_text(header.item_fall_scale)}",
        f"player_hitbox_width: {_float_text(header.player_hitbox_width)}",
        f"player_aux_collision_width: "
        f"{_float_text(header.player_aux_collision_width)}",
        f"item_collection_box_width: "
        f"{_float_text(header.item_collection_box_width)}",
        f"point_value_line_y: {_float_text(header.point_value_line_y)}",
        "",
    ]
    for level in sht.levels:
        lines.append(
            f"## level {level.index} power<{level.power_upper_bound} "
            f"[0x{level.start:08x}, 0x{level.end:08x}) shots={len(level.shots)}"
        )
        for shot in level.shots:
            lines.append(
                f"0x{shot.offset:08x} period={shot.fire_period} "
                f"phase={shot.fire_phase} source={shot.source_index} "
                f"type={shot.shot_type} damage={shot.damage} "
                f"spawn=({_float_text(shot.spawn_offset_x)},"
                f"{_float_text(shot.spawn_offset_y)}) "
                f"hitbox=({_float_text(shot.hitbox_width)},"
                f"{_float_text(shot.hitbox_height)}) "
                f"angle={_float_text(shot.angle)} speed={_float_text(shot.speed)} "
                f"anm={shot.animation_id} sound={shot.sound_id} "
                f"callbacks=({shot.callback_0_index},{shot.callback_1_index},"
                f"{shot.callback_2_index},{shot.callback_3_index}) "
                f"field_1e={shot.field_1e}"
            )
        lines.append(
            f"0x{level.sentinel_offset:08x} sentinel "
            f"field_02={level.sentinel_field_02}"
        )
        lines.append("")
    return "\n".join(lines)


def summarize(sht: ShtFile) -> dict[str, object]:
    return {
        "file": sht.path.name,
        "path": str(sht.path),
        "sha256": sht.sha256,
        "header": asdict(sht.header),
        "level_count": len(sht.levels),
        "shot_count": sum(len(level.shots) for level in sht.levels),
        "levels": [
            {
                "index": level.index,
                "start": level.start,
                "end": level.end,
                "power_upper_bound": level.power_upper_bound,
                "shot_count": len(level.shots),
                "sentinel_offset": level.sentinel_offset,
                "sentinel_field_02": level.sentinel_field_02,
                "shots": [asdict(shot) for shot in level.shots],
            }
            for level in sht.levels
        ],
    }


def _expand_inputs(paths: Iterable[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(sorted(path.glob("*.sht")))
        else:
            expanded.append(path)
    if not expanded:
        raise ShtError("no SHT inputs found")
    return expanded


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    info = subparsers.add_parser("info", help="validate files and print summaries")
    info.add_argument("inputs", type=Path, nargs="+")
    info.add_argument("--json", action="store_true", help="emit JSON")

    dump = subparsers.add_parser("dump", help="write a complete shot listing")
    dump.add_argument("input", type=Path)
    dump.add_argument("-o", "--output", type=Path)

    corpus = subparsers.add_parser(
        "corpus", help="write listings and JSON reports for an SHT corpus"
    )
    corpus.add_argument("input", type=Path, help="decoded SHT directory")
    corpus.add_argument("output", type=Path, help="report output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "info":
            reports = [summarize(parse_sht(path)) for path in _expand_inputs(args.inputs)]
            if args.json:
                print(json.dumps(reports, indent=2, sort_keys=True))
            else:
                for report in reports:
                    header = report["header"]
                    print(
                        f"{report['file']}: levels={report['level_count']} "
                        f"shots={report['shot_count']} "
                        f"bomb_gate={header['bomb_gate_reset_value']} "
                        f"speed=({header['unfocused_cardinal_speed']},"
                        f"{header['focused_cardinal_speed']})"
                    )
            return 0

        if args.command == "dump":
            listing = format_listing(parse_sht(args.input))
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(listing, encoding="utf-8")
            else:
                print(listing)
            return 0

        paths = _expand_inputs([args.input])
        args.output.mkdir(parents=True, exist_ok=True)
        reports = []
        for path in paths:
            sht = parse_sht(path)
            report = summarize(sht)
            reports.append(report)
            (args.output / f"{path.stem}.txt").write_text(
                format_listing(sht), encoding="utf-8"
            )
            (args.output / f"{path.stem}.json").write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        corpus = {
            "file_count": len(reports),
            "total_shot_count": sum(report["shot_count"] for report in reports),
            "files": reports,
        }
        (args.output / "corpus_summary.json").write_text(
            json.dumps(corpus, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {len(reports)} SHT listings and JSON reports to {args.output}")
        return 0
    except (OSError, ShtError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
