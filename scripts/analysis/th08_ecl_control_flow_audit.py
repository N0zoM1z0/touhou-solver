#!/usr/bin/env python3
"""Replay callback coverage after the fail-closed ECL control correction."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import BinaryIO

from th08_ecl_runtime import (
    EclInstructionCache,
    EclVmSnapshot,
    analyze_tagged_velocity_toggles,
)


SCHEMA = "th08-ecl-control-flow-audit-v1"
DEFAULT_HORIZON_FRAMES = 256
DEFAULT_DIFFICULTY_MASK = 0x08


class _MappedEcl:
    def __init__(self, *, base: int, code: bytes) -> None:
        self.base = base
        self.code = code

    def read(self, address: int, size: int) -> bytes:
        start = address - self.base
        end = start + size
        if size <= 0:
            raise ValueError("ECL read size must be positive")
        if start < 0 or end > len(self.code):
            raise OSError(f"ECL address outside decoded image: {address:#x}")
        return self.code[start:end]


def _percent_reduction(old: int, new: int) -> float | None:
    if old <= 0:
        return None
    return (old - new) / old * 100.0


def _coverage_status(lookahead: dict[str, object]) -> str:
    status = lookahead.get("coverage_status")
    if status in {"complete", "unknown"}:
        return str(status)
    return "complete" if lookahead.get("horizon_covered") is True else "unknown"


def _spell_key(decision: dict[str, object]) -> str:
    spell = decision.get("spell")
    if not isinstance(spell, dict) or not spell.get("active"):
        return "nonspell"
    return str(spell.get("spell_id"))


def _replay(
    lookahead: dict[str, object],
    *,
    mapped_ecl: _MappedEcl,
    instruction_cache: EclInstructionCache,
    horizon_frames: int,
    active_difficulty_mask: int,
):
    last_instruction = None

    def instruction_at(address: int):
        nonlocal last_instruction
        last_instruction = instruction_cache.instruction(
            mapped_ecl.read,
            address,
        )
        return last_instruction

    result = analyze_tagged_velocity_toggles(
        EclVmSnapshot(
            int(lookahead["instruction_pointer"]),
            float(lookahead["timer_fraction"]),
            int(lookahead["timer_elapsed"]),
            int(lookahead["tag_mask"]),
            0.0,
            0.0,
            float(lookahead["time_scale"]),
        ),
        instruction_at=instruction_at,
        horizon_frames=horizon_frames,
        active_difficulty_mask=active_difficulty_mask,
    )
    return result, last_instruction


def _iter_hashed_lines(stream: BinaryIO, digest):
    for raw_line in stream:
        digest.update(raw_line)
        yield raw_line


def audit_trace(
    trace_path: Path,
    *,
    ecl_path: Path,
    runtime_base: int,
    horizon_frames: int = DEFAULT_HORIZON_FRAMES,
    active_difficulty_mask: int = DEFAULT_DIFFICULTY_MASK,
) -> dict[str, object]:
    code = ecl_path.read_bytes()
    ecl_sha256 = hashlib.sha256(code).hexdigest()
    mapped_ecl = _MappedEcl(base=runtime_base, code=code)
    instruction_cache = EclInstructionCache()
    trace_digest = hashlib.sha256()

    decision_rows = 0
    callback_rows = 0
    replayed_rows = 0
    mapping_exclusion_count = 0
    mapping_exclusions: list[dict[str, object]] = []
    mapping_invalidation: dict[str, object] | None = None
    unknown_to_complete: list[dict[str, object]] = []
    transition_counts: Counter[str] = Counter()
    old_stop_counts: Counter[str] = Counter()
    new_stop_counts: Counter[str] = Counter()
    old_instructions = 0
    new_instructions = 0
    new_prefix_events = 0
    per_spell: dict[str, Counter[str]] = defaultdict(Counter)
    control_boundaries: Counter[str] = Counter()

    with trace_path.open("rb") as stream:
        for raw_line in _iter_hashed_lines(stream, trace_digest):
            try:
                decision = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if decision.get("kind") != "decision":
                continue
            decision_rows += 1
            lookahead = decision.get("bullet_velocity_lookahead")
            if not isinstance(lookahead, dict):
                continue
            if lookahead.get("error") is not None:
                continue
            required = (
                "instruction_pointer",
                "timer_fraction",
                "timer_elapsed",
                "tag_mask",
                "time_scale",
                "instructions_scanned",
                "stop_reason",
            )
            if not all(name in lookahead for name in required):
                continue
            callback_rows += 1
            frame = decision.get("frame")
            spell = _spell_key(decision)
            old_status = _coverage_status(lookahead)
            old_reason = str(lookahead["stop_reason"])
            if mapping_invalidation is not None:
                mapping_exclusion_count += 1
                if len(mapping_exclusions) < 20:
                    mapping_exclusions.append(
                        {
                            "frame": frame,
                            "spell": spell,
                            "old_status": old_status,
                            "old_reason": old_reason,
                            "error": (
                                "static mapping invalidated by earlier "
                                "runtime-image mismatch"
                            ),
                        }
                    )
                continue
            try:
                replay, stop_instruction = _replay(
                    lookahead,
                    mapped_ecl=mapped_ecl,
                    instruction_cache=instruction_cache,
                    horizon_frames=horizon_frames,
                    active_difficulty_mask=active_difficulty_mask,
                )
            except (KeyError, OSError, RuntimeError, ValueError) as error:
                mapping_invalidation = {
                    "frame": frame,
                    "spell": spell,
                    "error": f"{type(error).__name__}: {error}",
                }
                mapping_exclusion_count += 1
                if len(mapping_exclusions) < 20:
                    mapping_exclusions.append(
                        {
                            "frame": frame,
                            "spell": spell,
                            "old_status": old_status,
                            "old_reason": old_reason,
                            "error": f"{type(error).__name__}: {error}",
                        }
                    )
                continue

            replayed_rows += 1
            new_status = replay.coverage_status
            transition = (
                f"{old_status}:{old_reason}"
                f"->{new_status}:{replay.stop_reason}"
            )
            transition_counts[transition] += 1
            old_stop_counts[old_reason] += 1
            new_stop_counts[replay.stop_reason] += 1
            old_instructions += int(lookahead["instructions_scanned"])
            new_instructions += replay.instructions_scanned
            new_prefix_events += len(replay.events)
            per_spell[spell]["rows"] += 1
            per_spell[spell]["old_instructions"] += int(
                lookahead["instructions_scanned"]
            )
            per_spell[spell]["new_instructions"] += replay.instructions_scanned
            per_spell[spell][f"transition:{transition}"] += 1
            per_spell[spell][f"new_stop:{replay.stop_reason}"] += 1
            per_spell[spell]["new_max_instructions"] = max(
                per_spell[spell]["new_max_instructions"],
                replay.instructions_scanned,
            )
            if (
                replay.stop_reason == "unsupported_control_flow"
                and stop_instruction is not None
            ):
                offset = stop_instruction.address - runtime_base
                boundary = (
                    f"spell={spell},opcode=0x{stop_instruction.opcode:02X},"
                    f"offset=0x{offset:X}"
                )
                control_boundaries[boundary] += 1
            if old_status == "unknown" and new_status == "complete":
                if len(unknown_to_complete) < 20:
                    unknown_to_complete.append(
                        {
                            "frame": frame,
                            "spell": spell,
                            "old_reason": old_reason,
                            "new_reason": replay.stop_reason,
                        }
                    )

    spell57 = per_spell.get("57", Counter())
    spell73 = per_spell.get("73", Counter())
    gates = {
        "all_callback_rows_accounted": (
            callback_rows > 0
            and callback_rows
            == replayed_rows + mapping_exclusion_count
        ),
        "all_callback_rows_replayed": (
            callback_rows > 0
            and callback_rows == replayed_rows
            and mapping_exclusion_count == 0
        ),
        "decoded_mapping_covers_at_least_99_percent": (
            replayed_rows / callback_rows >= 0.99
        ),
        "no_unknown_rows_excluded_by_static_mapping": all(
            exclusion["old_status"] == "complete"
            for exclusion in mapping_exclusions
        ),
        "no_unknown_to_complete": not unknown_to_complete,
        "spell57_stops_at_unsupported_control": (
            spell57["rows"] > 0
            and spell57["new_stop:unsupported_control_flow"]
            == spell57["rows"]
        ),
        "spell57_inspects_fewer_than_64_instructions": (
            spell57["rows"] > 0
            and spell57["new_max_instructions"] < 64
        ),
        "spell73_dynamic_control_boundary_observed": (
            spell73["new_stop:unsupported_control_flow"] > 0
        ),
    }
    spell_records: dict[str, object] = {}
    for spell, counts in sorted(per_spell.items()):
        spell_records[spell] = {
            "rows": counts["rows"],
            "old_instructions": counts["old_instructions"],
            "new_instructions": counts["new_instructions"],
            "instruction_reduction_percent": _percent_reduction(
                counts["old_instructions"],
                counts["new_instructions"],
            ),
            "new_max_instructions": counts["new_max_instructions"],
            "new_stop_counts": dict(
                sorted(
                    (
                        key.removeprefix("new_stop:"),
                        value,
                    )
                    for key, value in counts.items()
                    if key.startswith("new_stop:")
                )
            ),
            "transitions": dict(
                sorted(
                    (
                        key.removeprefix("transition:"),
                        value,
                    )
                    for key, value in counts.items()
                    if key.startswith("transition:")
                )
            ),
        }

    return {
        "schema": SCHEMA,
        "source": {
            "trace_name": trace_path.name,
            "trace_sha256": trace_digest.hexdigest(),
            "ecl_name": ecl_path.name,
            "ecl_sha256": ecl_sha256,
            "runtime_base": f"0x{runtime_base:08X}",
        },
        "model": {
            "horizon_frames": horizon_frames,
            "active_difficulty_mask": active_difficulty_mask,
            "callback_angle_speed_source": (
                "unavailable_in_trace_zeroed_for_control_coverage_replay"
            ),
            "schedule_value_parity_claimed": False,
            "coverage_control_replay_claimed": True,
        },
        "counts": {
            "decision_rows": decision_rows,
            "callback_rows": callback_rows,
            "replayed_rows": replayed_rows,
            "old_stop_counts": dict(sorted(old_stop_counts.items())),
            "new_stop_counts": dict(sorted(new_stop_counts.items())),
            "control_boundaries": dict(sorted(control_boundaries.items())),
            "transitions": dict(sorted(transition_counts.items())),
            "old_instructions": old_instructions,
            "new_instructions": new_instructions,
            "instruction_reduction_percent": _percent_reduction(
                old_instructions,
                new_instructions,
            ),
            "new_prefix_events": new_prefix_events,
        },
        "per_spell": spell_records,
        "violations": {
            "unknown_to_complete": unknown_to_complete,
        },
        "mapping_exclusions": {
            "count": mapping_exclusion_count,
            "invalidation": mapping_invalidation,
            "reason": (
                "the first decode/read failure invalidates the static "
                "runtime-to-file mapping for every later callback row; "
                "no raw instruction bytes or replacement image identity "
                "were retained"
            ),
            "samples": mapping_exclusions,
        },
        "gates": gates,
        "passed": all(gates.values()),
    }


def _parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--ecl", type=Path, required=True)
    parser.add_argument("--runtime-base", type=_parse_int, required=True)
    parser.add_argument(
        "--horizon-frames",
        type=int,
        default=DEFAULT_HORIZON_FRAMES,
    )
    parser.add_argument(
        "--difficulty-mask",
        type=_parse_int,
        default=DEFAULT_DIFFICULTY_MASK,
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = audit_trace(
        arguments.trace,
        ecl_path=arguments.ecl,
        runtime_base=arguments.runtime_base,
        horizon_frames=arguments.horizon_frames,
        active_difficulty_mask=arguments.difficulty_mask,
    )
    encoded = json.dumps(
        report,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    if arguments.output is None:
        print(encoded, end="")
    else:
        arguments.output.write_text(encoded, encoding="utf-8", newline="\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
