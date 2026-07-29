#!/usr/bin/env python3
"""Summarize frame-bracketed TH08 player/enemy mode trace evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Iterable

REPORT_SCHEMA = "th08-enemy-mode-capture-report-v1"
_FOCUS_INPUT_BIT = 0x04


def _records(path: Path) -> Iterable[tuple[int, dict[str, object]]]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"line {line_number}: trace row is not an object")
            yield line_number, record


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def _mode_state(
    capture: dict[str, object],
    *,
    line_number: int,
) -> dict[str, object]:
    raw = capture.get("player_after")
    if not isinstance(raw, dict):
        raise ValueError(
            f"line {line_number}: mode capture lacks player_after object"
        )
    required = (
        "input_current",
        "focus_logic",
        "secondary_character_active",
        "focus_transition_counter",
        "effective_focus",
    )
    if any(field not in raw for field in required):
        raise ValueError(
            f"line {line_number}: incomplete player_after mode state"
        )
    return raw


def _mode_bodies(
    capture: dict[str, object],
    *,
    line_number: int,
) -> list[list[int]]:
    raw = capture.get("mode_sensitive_bodies")
    if not isinstance(raw, list):
        raise ValueError(
            f"line {line_number}: mode capture lacks body evidence"
        )
    bodies: list[list[int]] = []
    for item in raw:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not all(isinstance(value, int) for value in item)
        ):
            raise ValueError(
                f"line {line_number}: malformed mode-sensitive body"
            )
        bodies.append([item[0], item[1]])
    return bodies


def build_report(path: Path) -> dict[str, object]:
    """Build a compact, reviewable whole-stage mode-capture report."""

    total_rows = 0
    decision_rows = 0
    capture_rows = 0
    coherent_rows = 0
    status_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    attempt_counts: Counter[str] = Counter()
    mode_state_counts: Counter[str] = Counter()
    unique_body_pairs: set[tuple[int, int]] = set()
    read_ms_values: list[float] = []
    input_focus_edges = 0
    secondary_transitions: list[dict[str, object]] = []
    authority_violations: list[int] = []
    role_violations: list[int] = []
    coherent_sync_mismatch_rows: list[int] = []
    diagnostic_scale_config: bool | None = None
    scale_unknown_rows = 0
    scale_fallback_counts: Counter[str] = Counter()
    scale_root_bits_counts: Counter[str] = Counter()
    scale_hard_authority_lines: list[int] = []
    first_capture_frame: int | None = None
    last_capture_frame: int | None = None
    previous_coherent: dict[str, object] | None = None
    previous_epoch: object = None

    for line_number, record in _records(path):
        total_rows += 1
        kind = record.get("kind")
        if kind == "controller_config":
            configured = record.get(
                "diagnostic_continue_root_only_scale"
            )
            if isinstance(configured, bool):
                diagnostic_scale_config = configured
        elif kind == "time_scale_authority_unknown":
            scale_unknown_rows += 1
            scale_fallback_counts[
                str(record.get("fallback", "missing"))
            ] += 1
            scale_root_bits_counts[
                str(record.get("root_scale_bits", "missing"))
            ] += 1
            if record.get("hard_authority") is not False:
                scale_hard_authority_lines.append(line_number)
        if kind != "decision":
            continue
        decision_rows += 1
        capture = record.get("player_enemy_mode_capture")
        if capture is None:
            continue
        if not isinstance(capture, dict):
            raise ValueError(
                f"line {line_number}: player_enemy_mode_capture is not an object"
            )
        capture_rows += 1
        frame = record.get("frame")
        if isinstance(frame, int):
            if first_capture_frame is None:
                first_capture_frame = frame
            last_capture_frame = frame
        stage = record.get("stage_route_index")
        stage_counts[str(stage) if stage is not None else "unknown"] += 1
        status = str(capture.get("status", "missing"))
        status_counts[status] += 1
        attempts = capture.get("attempts")
        attempt_counts[str(attempts) if attempts is not None else "missing"] += 1
        read_ms = capture.get("read_ms")
        if isinstance(read_ms, (int, float)) and math.isfinite(read_ms):
            read_ms_values.append(float(read_ms))
        if capture.get("action_authority") is not False:
            authority_violations.append(line_number)
        if capture.get("role") != "diagnostic_shadow":
            role_violations.append(line_number)

        coherent = capture.get("coherent") is True
        mismatches = capture.get("sync_mismatch_pointers")
        if coherent and mismatches != []:
            coherent_sync_mismatch_rows.append(line_number)
        if not coherent:
            previous_coherent = None
            previous_epoch = None
            continue

        coherent_rows += 1
        mode = _mode_state(capture, line_number=line_number)
        bodies = _mode_bodies(capture, line_number=line_number)
        unique_body_pairs.update((body[0], body[1]) for body in bodies)
        mode_state_counts[
            (
                f"{int(mode['focus_logic'])}:"
                f"{int(bool(mode['secondary_character_active']))}:"
                f"{int(mode['focus_transition_counter'])}"
            )
        ] += 1

        epoch = record.get("gameplay_epoch")
        if previous_coherent is not None and epoch == previous_epoch:
            previous_mode = previous_coherent["mode"]
            assert isinstance(previous_mode, dict)
            if bool(
                int(previous_mode["input_current"]) & _FOCUS_INPUT_BIT
            ) != bool(int(mode["input_current"]) & _FOCUS_INPUT_BIT):
                input_focus_edges += 1
            before_secondary = bool(
                previous_mode["secondary_character_active"]
            )
            after_secondary = bool(mode["secondary_character_active"])
            if before_secondary != after_secondary:
                secondary_transitions.append(
                    {
                        "previous_frame": previous_coherent["frame"],
                        "frame": frame,
                        "secondary_before": before_secondary,
                        "secondary_after": after_secondary,
                        "input_current": int(mode["input_current"]),
                        "focus_logic": int(mode["focus_logic"]),
                        "focus_transition_counter": int(
                            mode["focus_transition_counter"]
                        ),
                        "mode_sensitive_bodies_before": (
                            previous_coherent["bodies"]
                        ),
                        "mode_sensitive_bodies_after": bodies,
                    }
                )
        previous_coherent = {
            "frame": frame,
            "mode": mode,
            "bodies": bodies,
        }
        previous_epoch = epoch

    integrity_errors = {
        "action_authority_true_or_missing_lines": authority_violations,
        "non_diagnostic_role_lines": role_violations,
        "coherent_rows_with_sync_mismatches": coherent_sync_mismatch_rows,
        "scale_unknown_rows_with_hard_authority": (
            scale_hard_authority_lines
        ),
    }
    integrity_passed = bool(
        capture_rows
        and coherent_rows
        and not any(integrity_errors.values())
    )
    return {
        "schema": REPORT_SCHEMA,
        "source": {
            "path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        },
        "scope": {
            "role": "diagnostic_shadow",
            "action_authority": False,
            "physical_survival_authority": False,
        },
        "rows": {
            "total": total_rows,
            "decision": decision_rows,
            "capture": capture_rows,
            "coherent": coherent_rows,
            "incoherent": capture_rows - coherent_rows,
        },
        "capture_status_counts": dict(sorted(status_counts.items())),
        "capture_attempt_counts": dict(sorted(attempt_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "frame_scope": {
            "first": first_capture_frame,
            "last": last_capture_frame,
        },
        "read_ms": {
            "samples": len(read_ms_values),
            "minimum": min(read_ms_values) if read_ms_values else None,
            "mean": (
                sum(read_ms_values) / len(read_ms_values)
                if read_ms_values
                else None
            ),
            "p95": _percentile(read_ms_values, 0.95),
            "maximum": max(read_ms_values) if read_ms_values else None,
        },
        "mode_state_counts": dict(sorted(mode_state_counts.items())),
        "input_focus_edges_between_adjacent_coherent_rows": input_focus_edges,
        "secondary_character_transitions": secondary_transitions,
        "unique_mode_sensitive_body_pairs": [
            [pointer, flags]
            for pointer, flags in sorted(unique_body_pairs)
        ],
        "diagnostic_time_scale_fallback": {
            "configured": diagnostic_scale_config,
            "unknown_rows": scale_unknown_rows,
            "fallback_counts": dict(sorted(scale_fallback_counts.items())),
            "root_scale_bits_counts": dict(
                sorted(scale_root_bits_counts.items())
            ),
            "hard_authority": False,
            "physical_survival_authority": False,
        },
        "integrity": {
            "passed": integrity_passed,
            "errors": integrity_errors,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.trace)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if report["integrity"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
