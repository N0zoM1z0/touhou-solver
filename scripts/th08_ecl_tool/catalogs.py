"""Structured summaries and corpus catalogs for parsed TH08 ECL."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from th08_ecl_opcodes import OPCODE_SPECS, opcode_spec
from th08_ecl_tool.core import EclError, EclFile
from th08_ecl_tool.formatting import (
    decode_bullet_emission,
    decode_bullet_transform,
    decode_laser_spawn,
    decode_spell_card_start,
)


def summarize(ecl: EclFile) -> dict[str, object]:
    sub_histogram = Counter(
        insn.opcode for sub in ecl.subroutines for insn in sub.instructions
    )
    timeline_histogram = Counter(
        insn.opcode
        for timeline in ecl.timelines
        for insn in timeline.instructions
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
                    bullet_types[
                        (bullet["bullet_type"], bullet["color"])
                    ] += 1
            if insn.opcode == 0x6F:
                decode_bullet_transform(insn)
                transform_definition_count += 1
            if insn.opcode in {0x72, 0x73}:
                decode_laser_spawn(insn)
                laser_spawn_count += 1
            if (
                opcode_spec(insn.opcode).category == "laser"
                and insn.opcode not in {0x72, 0x73}
            ):
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
            f"0x{opcode:02x}": count
            for opcode, count in sorted(sub_histogram.items())
        },
        "timeline_opcode_histogram": {
            f"0x{opcode:02x}": count
            for opcode, count in sorted(timeline_histogram.items())
        },
        "bullet_mode_histogram": {
            str(mode): count
            for mode, count in sorted(bullet_histogram.items())
        },
        "bullet_type_color_histogram": [
            {"type": bullet_type, "color": color, "count": count}
            for (bullet_type, color), count in sorted(bullet_types.items())
        ],
    }


def expand_inputs(paths: Iterable[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(sorted(path.glob("*.ecl")))
        else:
            expanded.append(path)
    if not expanded:
        raise EclError("no ECL inputs found")
    return expanded


def build_opcode_catalog(
    ecls: Iterable[EclFile],
) -> tuple[list[dict[str, object]], str]:
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
                    for size, count in sorted(
                        sizes.get(spec.opcode, {}).items()
                    )
                },
                "files": sorted(files.get(spec.opcode, set())),
            }
        )

    lines = [
        "# TH08 Enemy ECL Opcode Catalog",
        "",
        (
            "This table is generated from the locally recovered VM switch "
            "and decoded shipped corpus."
        ),
        (
            "Confidence values keep observed behavior separate from "
            "provisional naming and unknowns."
        ),
        "",
        (
            "| Opcode | Name | Category | Confidence | Count | Sizes | "
            "Description |"
        ),
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        size_text = ", ".join(row["instruction_sizes"].keys()) or "-"
        lines.append(
            f"| `{row['opcode_hex']}` | `{row['name']}` | "
            f"{row['category']} | {row['confidence']} | "
            f"{row['corpus_count']} | {size_text} | "
            f"{row['description']} |"
        )
    return rows, "\n".join(lines) + "\n"


def build_spell_catalog(
    ecls: Iterable[EclFile],
) -> tuple[list[dict[str, object]], str]:
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
        (
            "Generated only from opcode 0x7A payloads in the decoded shipped "
            "ECL corpus."
        ),
        (
            "Names and descriptions are decoded with the XOR keys observed "
            "in spell_card_start/spell_card_finish."
        ),
        "",
        "| ID | Name | Owner | Base score | ECL occurrences |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        occurrences = ", ".join(
            (
                f"`{item['file']}:sub{item['subroutine']}"
                f"@0x{item['offset']:x}/"
                f"mask0x{item['difficulty_mask']:02x}`"
            )
            for item in row["occurrences"]
        )
        lines.append(
            f"| {row['spell_id']} | {row['name']} | {row['owner']} | "
            f"{row['base_score']} | {occurrences} |"
        )
    return rows, "\n".join(lines) + "\n"
