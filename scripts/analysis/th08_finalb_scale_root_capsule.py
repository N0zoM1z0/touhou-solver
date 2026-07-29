#!/usr/bin/env python3
"""Retain the physical Final-B quarter-scale root observations.

The historical traces were produced before the player projection consumed the
native global time scale.  This tool reconstructs the old unit-scale helper
input from its retained output and replays the corrected native-order player
primitive at the observed root scale.  The comparison is conditional on the
same reconstructed movement input: it isolates the scale defect but does not
claim that a desired input was the native active input.

A post-update root observation proves one next player scale and no next laser
scale.  Repeating the root across the old multi-frame control-delay projection
is retained only as an explicitly non-causal diagnostic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Iterable, Sequence


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from movement_model import MovementBounds
from th08_ecl_vm_state import float32_from_bits
from th08_live.movement import (
    DOWN,
    FOCUS,
    FOCUSED_CARDINAL_SPEED,
    FOCUSED_DIAGONAL_SPEED,
    LEFT,
    PLAYFIELD_BOTTOM,
    PLAYFIELD_LEFT,
    PLAYFIELD_RIGHT,
    PLAYFIELD_TOP,
    RIGHT,
    UNFOCUSED_CARDINAL_SPEED,
    UNFOCUSED_DIAGONAL_SPEED,
    UP,
    local_pipeline_action_from_mask,
)
from th08_movement_model import step_route2_movement
from th08_time_scale import (
    TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
    TH08_UNIT_TIME_SCALE_BITS,
    canonical_time_scale_bits,
)


CAPSULE_SCHEMA = "th08-finalb-scale-root-capsule-v1"
TARGET_SPELL_ID = 190
TARGET_SCALE_BITS = 0x3E800000
HISTORICAL_BASELINE_COMMIT = "c19ffb0ad98a298bba93f1085d191d8057f70173"
_DIRECTION_MASK = UP | DOWN | LEFT | RIGHT
_LIVE_BOUNDS = MovementBounds(
    PLAYFIELD_LEFT,
    PLAYFIELD_TOP,
    PLAYFIELD_RIGHT,
    PLAYFIELD_BOTTOM,
)
_CANONICAL_MOVEMENT_MASKS = tuple(
    direction | focus
    for direction in (
        0,
        UP,
        DOWN,
        LEFT,
        RIGHT,
        UP | LEFT,
        UP | RIGHT,
        DOWN | LEFT,
        DOWN | RIGHT,
    )
    for focus in (0, FOCUS)
)


def _legacy_unit_project(
    x: float,
    y: float,
    input_mask: int,
    frames: int,
) -> tuple[float, float]:
    """Reproduce the pre-SEM-SCALE-A live projection exactly.

    This deliberately retains the old double-precision multiply-and-clamp
    behavior.  It is a baseline reconstruction, not the corrected primitive.
    """

    direction = input_mask & _DIRECTION_MASK
    if not direction or frames <= 0:
        return x, y
    horizontal = (-1 if direction & LEFT else 0) + (
        1 if direction & RIGHT else 0
    )
    vertical = (-1 if direction & UP else 0) + (
        1 if direction & DOWN else 0
    )
    if horizontal == 0 and vertical == 0:
        return x, y
    focused = bool(input_mask & FOCUS)
    diagonal = horizontal != 0 and vertical != 0
    if focused:
        speed = (
            FOCUSED_DIAGONAL_SPEED
            if diagonal
            else FOCUSED_CARDINAL_SPEED
        )
    else:
        speed = (
            UNFOCUSED_DIAGONAL_SPEED
            if diagonal
            else UNFOCUSED_CARDINAL_SPEED
        )
    return (
        min(
            PLAYFIELD_RIGHT,
            max(PLAYFIELD_LEFT, x + horizontal * speed * frames),
        ),
        min(
            PLAYFIELD_BOTTOM,
            max(PLAYFIELD_TOP, y + vertical * speed * frames),
        ),
    )


def _native_project(
    x: float,
    y: float,
    input_mask: int,
    scale_bits: int,
    frames: int,
) -> tuple[float, float]:
    current_x = x
    current_y = y
    for _ in range(frames):
        step = step_route2_movement(
            x=current_x,
            y=current_y,
            input_mask=input_mask,
            time_scale_bits=scale_bits,
            bounds=_LIVE_BOUNDS,
        )
        current_x = step.x
        current_y = step.y
    return current_x, current_y


def _same_position(
    first: tuple[float, float],
    second: tuple[float, float],
) -> bool:
    return math.isclose(
        first[0],
        second[0],
        rel_tol=0.0,
        abs_tol=1e-9,
    ) and math.isclose(
        first[1],
        second[1],
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def _legacy_input_candidates(
    *,
    x: float,
    y: float,
    frames: int,
    target_x: float,
    target_y: float,
) -> tuple[int, ...]:
    target = (target_x, target_y)
    return tuple(
        mask
        for mask in _CANONICAL_MOVEMENT_MASKS
        if _same_position(
            _legacy_unit_project(x, y, mask, frames),
            target,
        )
    )


def _action_names(masks: Iterable[int]) -> tuple[str, ...]:
    return tuple(
        sorted({local_pipeline_action_from_mask(mask) for mask in masks})
    )


def _mask_for_action(action: str) -> int:
    for mask in _CANONICAL_MOVEMENT_MASKS:
        if local_pipeline_action_from_mask(mask) == action:
            return mask
    raise ValueError(f"unknown canonical movement action {action!r}")


def _distance(
    first: tuple[float, float],
    second: tuple[float, float],
) -> float:
    return math.hypot(first[0] - second[0], first[1] - second[1])


def _scale_bits_from_trace(row: dict[str, object]) -> int | None:
    lookahead = row.get("bullet_velocity_lookahead")
    if not isinstance(lookahead, dict):
        return None
    bits = lookahead.get("time_scale_bits")
    if type(bits) is int:
        return bits
    value = lookahead.get("time_scale")
    if type(value) in (int, float):
        try:
            return canonical_time_scale_bits(float(value))
        except ValueError:
            return None
    return None


def _required_dict(
    value: object,
    *,
    field: str,
    source: Path,
    line_number: int,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(
            f"{source}:{line_number}: {field} must be an object"
        )
    return value


def _required_number(
    value: object,
    *,
    field: str,
    source: Path,
    line_number: int,
) -> float:
    if type(value) not in (int, float):
        raise ValueError(
            f"{source}:{line_number}: {field} must be numeric"
        )
    return float(value)


def _required_int(
    value: object,
    *,
    field: str,
    source: Path,
    line_number: int,
) -> int:
    if type(value) is not int:
        raise ValueError(
            f"{source}:{line_number}: {field} must be an integer"
        )
    return value


def _capsule_record(
    row: dict[str, object],
    *,
    source: Path,
    line_number: int,
    scale_bits: int,
) -> dict[str, object]:
    player = _required_dict(
        row.get("player"),
        field="player",
        source=source,
        line_number=line_number,
    )
    spell = _required_dict(
        row.get("spell"),
        field="spell",
        source=source,
        line_number=line_number,
    )
    input_snapshot = _required_dict(
        row.get("input_snapshot"),
        field="input_snapshot",
        source=source,
        line_number=line_number,
    )
    lookahead = _required_dict(
        row.get("bullet_velocity_lookahead"),
        field="bullet_velocity_lookahead",
        source=source,
        line_number=line_number,
    )
    resources = _required_dict(
        row.get("resources"),
        field="resources",
        source=source,
        line_number=line_number,
    )
    x = _required_number(
        player.get("x"),
        field="player.x",
        source=source,
        line_number=line_number,
    )
    y = _required_number(
        player.get("y"),
        field="player.y",
        source=source,
        line_number=line_number,
    )
    projected = (
        _required_number(
            player.get("projected_x"),
            field="player.projected_x",
            source=source,
            line_number=line_number,
        ),
        _required_number(
            player.get("projected_y"),
            field="player.projected_y",
            source=source,
            line_number=line_number,
        ),
    )
    control_origin = (
        _required_number(
            player.get("control_origin_x"),
            field="player.control_origin_x",
            source=source,
            line_number=line_number,
        ),
        _required_number(
            player.get("control_origin_y"),
            field="player.control_origin_y",
            source=source,
            line_number=line_number,
        ),
    )
    snapshot_lag = _required_int(
        row.get("snapshot_lag"),
        field="snapshot_lag",
        source=source,
        line_number=line_number,
    )
    control_delay_frames = _required_int(
        row.get("control_delay_frames"),
        field="control_delay_frames",
        source=source,
        line_number=line_number,
    )
    if snapshot_lag < 0 or control_delay_frames < 0:
        raise ValueError(
            f"{source}:{line_number}: projection horizons cannot be negative"
        )

    projection_candidates = _legacy_input_candidates(
        x=x,
        y=y,
        frames=snapshot_lag,
        target_x=projected[0],
        target_y=projected[1],
    )
    control_candidates = _legacy_input_candidates(
        x=x,
        y=y,
        frames=control_delay_frames,
        target_x=control_origin[0],
        target_y=control_origin[1],
    )
    if not projection_candidates:
        raise ValueError(
            f"{source}:{line_number}: cannot reconstruct legacy read-lag "
            "projection"
        )
    if not control_candidates:
        raise ValueError(
            f"{source}:{line_number}: cannot reconstruct legacy control "
            "origin"
        )
    if snapshot_lag > 0:
        shared = tuple(
            mask for mask in control_candidates if mask in projection_candidates
        )
        if not shared:
            raise ValueError(
                f"{source}:{line_number}: retained projections disagree on "
                "the legacy held movement input"
            )
        held_candidates = shared
    else:
        held_candidates = control_candidates
    held_actions = _action_names(held_candidates)
    chosen_action = held_actions[0]
    chosen_mask = _mask_for_action(chosen_action)

    legacy_read_lag = _legacy_unit_project(
        x,
        y,
        chosen_mask,
        snapshot_lag,
    )
    if not _same_position(legacy_read_lag, projected):
        raise ValueError(
            f"{source}:{line_number}: selected reconstructed action does not "
            "replay the legacy projection"
        )
    corrected_read_lag: tuple[float, float] | None
    read_lag_authority: str
    if snapshot_lag <= 1:
        corrected_read_lag = _native_project(
            x,
            y,
            chosen_mask,
            scale_bits,
            snapshot_lag,
        )
        read_lag_authority = (
            "scale_exact_for_same_legacy_input_assumption"
        )
    else:
        corrected_read_lag = None
        read_lag_authority = "unknown_root_does_not_cover_read_lag"

    legacy_one_step = _legacy_unit_project(x, y, chosen_mask, 1)
    native_unit_one_step = _native_project(
        x,
        y,
        chosen_mask,
        TH08_UNIT_TIME_SCALE_BITS,
        1,
    )
    corrected_one_step = _native_project(
        x,
        y,
        chosen_mask,
        scale_bits,
        1,
    )
    repeated_root_control = _native_project(
        x,
        y,
        chosen_mask,
        scale_bits,
        control_delay_frames,
    )

    record: dict[str, object] = {
        "source_line": line_number,
        "frame": _required_int(
            row.get("frame"),
            field="frame",
            source=source,
            line_number=line_number,
        ),
        "snapshot_frame": row.get("snapshot_frame"),
        "snapshot_lag": snapshot_lag,
        "gameplay_epoch": row.get("gameplay_epoch"),
        "stage_route_index": row.get("stage_route_index"),
        "spell": {
            "active": spell.get("active"),
            "spell_id": spell.get("spell_id"),
            "name": spell.get("name"),
        },
        "observed_root_scale": {
            "value": _required_number(
                lookahead.get("time_scale"),
                field="bullet_velocity_lookahead.time_scale",
                source=source,
                line_number=line_number,
            ),
            "bits": f"0x{scale_bits:08x}",
            "trace_encoding": "json_float_reencoded_to_binary32",
        },
        "observed_player": {"x": x, "y": y},
        "observed_inputs": {
            "native_current": input_snapshot.get("current"),
            "native_previous": input_snapshot.get("previous"),
            "issued_mask": row.get("mask"),
            "issued_action": row.get("action"),
        },
        "legacy_held_input_reconstruction": {
            "actions": held_actions,
            "chosen_equivalent_action": chosen_action,
            "ambiguous_only_when_movement_equivalent": (
                len(held_actions) > 1
            ),
            "read_lag_trace_replayed_exactly": True,
            "control_origin_trace_replayed_exactly": True,
            "baseline_commit": HISTORICAL_BASELINE_COMMIT,
        },
        "read_lag_scale_comparison": {
            "frames": snapshot_lag,
            "historical_unit_projection": {
                "x": projected[0],
                "y": projected[1],
            },
            "corrected_observed_scale_projection": (
                {
                    "x": corrected_read_lag[0],
                    "y": corrected_read_lag[1],
                }
                if corrected_read_lag is not None
                else None
            ),
            "position_delta": (
                _distance(projected, corrected_read_lag)
                if corrected_read_lag is not None
                else None
            ),
            "authority": read_lag_authority,
        },
        "one_player_phase_scale_comparison": {
            "historical_legacy_unit": {
                "x": legacy_one_step[0],
                "y": legacy_one_step[1],
            },
            "corrected_native_unit": {
                "x": native_unit_one_step[0],
                "y": native_unit_one_step[1],
            },
            "corrected_observed_scale": {
                "x": corrected_one_step[0],
                "y": corrected_one_step[1],
            },
            "native_scale_only_position_delta": _distance(
                native_unit_one_step,
                corrected_one_step,
            ),
            "authority": (
                "root_scale_exact_input_conditional_not_active_input_proof"
            ),
        },
        "multi_frame_control_origin_diagnostic": {
            "frames": control_delay_frames,
            "historical_unit_projection": {
                "x": control_origin[0],
                "y": control_origin[1],
            },
            "repeated_root_scale_projection": {
                "x": repeated_root_control[0],
                "y": repeated_root_control[1],
            },
            "position_delta": _distance(
                control_origin,
                repeated_root_control,
            ),
            "authority": (
                "noncausal_counterfactual_root_repetition_after_first_frame"
            ),
        },
        "physical_context": {
            "active_bullets": row.get("active_bullets"),
            "active_lasers": row.get("active_lasers"),
            "hit_count": row.get("hit_count"),
            "hit_started": row.get("hit_started"),
            "bomb_emitted": row.get("bomb"),
            "resources": {
                "lives": resources.get("lives"),
                "bombs": resources.get("bombs"),
                "power": resources.get("power"),
            },
        },
    }
    return record


def _nearest_rank(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return ordered[index]


def _session_summary(
    records: Sequence[dict[str, object]],
) -> dict[str, object]:
    frames = [int(record["frame"]) for record in records]
    lags = [int(record["snapshot_lag"]) for record in records]
    contexts = [
        record["physical_context"]
        for record in records
        if isinstance(record.get("physical_context"), dict)
    ]
    return {
        "selected_record_count": len(records),
        "frame_range": [min(frames), max(frames)] if frames else None,
        "snapshot_lag_counts": {
            str(lag): lags.count(lag) for lag in sorted(set(lags))
        },
        "active_laser_values": sorted(
            {
                context.get("active_lasers")
                for context in contexts
            },
            key=lambda value: (value is None, value),
        ),
        "hit_count_values": sorted(
            {context.get("hit_count") for context in contexts},
            key=lambda value: (value is None, value),
        ),
        "bomb_emitted_values": sorted(
            {context.get("bomb_emitted") for context in contexts},
            key=str,
        ),
        "power_values": sorted(
            {
                (
                    context.get("resources")
                    if isinstance(context.get("resources"), dict)
                    else {}
                ).get("power")
                for context in contexts
            },
            key=lambda value: (value is None, value),
        ),
    }


def _aggregate(
    sessions: Sequence[dict[str, object]],
) -> dict[str, object]:
    records = [
        record
        for session in sessions
        for record in session["records"]  # type: ignore[index]
    ]
    read_lag_deltas = [
        float(comparison["position_delta"])
        for record in records
        for comparison in [record["read_lag_scale_comparison"]]
        if comparison["position_delta"] is not None
    ]
    one_step_deltas = [
        float(record["one_player_phase_scale_comparison"][
            "native_scale_only_position_delta"
        ])
        for record in records
    ]
    control_deltas = [
        float(record["multi_frame_control_origin_diagnostic"][
            "position_delta"
        ])
        for record in records
    ]
    exact_read_lag_rows = sum(
        record["read_lag_scale_comparison"]["position_delta"] is not None
        for record in records
    )
    active_laser_rows = sum(
        record["physical_context"]["active_lasers"] not in (None, 0)
        for record in records
    )
    bomb_rows = sum(
        bool(record["physical_context"]["bomb_emitted"])
        for record in records
    )
    return {
        "source_count": len(sessions),
        "selected_record_count": len(records),
        "exact_root_covered_read_lag_rows": exact_read_lag_rows,
        "unknown_read_lag_rows": len(records) - exact_read_lag_rows,
        "snapshot_lag_one_rows": sum(
            int(record["snapshot_lag"]) == 1 for record in records
        ),
        "physical_active_laser_rows": active_laser_rows,
        "physical_bomb_rows": bomb_rows,
        "read_lag_unit_to_observed_scale_delta": {
            "changed_rows": sum(value > 0.0 for value in read_lag_deltas),
            "mean": statistics.fmean(read_lag_deltas)
            if read_lag_deltas
            else 0.0,
            "p95": _nearest_rank(read_lag_deltas, 0.95),
            "maximum": max(read_lag_deltas, default=0.0),
        },
        "one_player_phase_native_scale_only_delta": {
            "changed_rows": sum(value > 0.0 for value in one_step_deltas),
            "mean": statistics.fmean(one_step_deltas)
            if one_step_deltas
            else 0.0,
            "p95": _nearest_rank(one_step_deltas, 0.95),
            "maximum": max(one_step_deltas, default=0.0),
        },
        "noncausal_repeated_root_control_delta": {
            "mean": statistics.fmean(control_deltas)
            if control_deltas
            else 0.0,
            "p95": _nearest_rank(control_deltas, 0.95),
            "maximum": max(control_deltas, default=0.0),
        },
    }


def build_capsule(
    traces: Sequence[Path],
    *,
    target_spell_id: int = TARGET_SPELL_ID,
    target_scale_bits: int = TARGET_SCALE_BITS,
) -> dict[str, object]:
    if not traces:
        raise ValueError("at least one physical trace is required")
    sessions: list[dict[str, object]] = []
    for trace in traces:
        digest = hashlib.sha256()
        line_count = 0
        decision_count = 0
        records: list[dict[str, object]] = []
        try:
            stream = trace.open("rb")
        except OSError as exc:
            raise ValueError(f"cannot open physical trace {trace}: {exc}") from exc
        with stream:
            for line_number, raw in enumerate(stream, 1):
                digest.update(raw)
                line_count += 1
                try:
                    row = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        f"{trace}:{line_number}: invalid JSON record"
                    ) from exc
                if not isinstance(row, dict):
                    raise ValueError(
                        f"{trace}:{line_number}: trace record must be an object"
                    )
                if row.get("kind") != "decision":
                    continue
                decision_count += 1
                spell = row.get("spell")
                if not isinstance(spell, dict):
                    continue
                scale_bits = _scale_bits_from_trace(row)
                if (
                    spell.get("active") is not True
                    or spell.get("spell_id") != target_spell_id
                    or scale_bits != target_scale_bits
                ):
                    continue
                records.append(
                    _capsule_record(
                        row,
                        source=trace,
                        line_number=line_number,
                        scale_bits=scale_bits,
                    )
                )
        if not records:
            raise ValueError(
                f"{trace}: no active spell {target_spell_id} records at "
                f"scale bits 0x{target_scale_bits:08x}"
            )
        sessions.append(
            {
                "source": {
                    "path": trace.as_posix(),
                    "sha256": digest.hexdigest(),
                    "bytes": trace.stat().st_size,
                    "line_count": line_count,
                    "decision_count": decision_count,
                },
                "summary": _session_summary(records),
                "records": records,
            }
        )

    aggregate = _aggregate(sessions)
    checks = {
        "three_physical_sources_retained": len(sessions) == 3,
        "all_selected_read_lags_covered_by_root": (
            aggregate["unknown_read_lag_rows"] == 0
        ),
        "no_active_laser_scale_claim": (
            aggregate["physical_active_laser_rows"] == 0
        ),
        "no_bomb_emitted_on_selected_rows": (
            aggregate["physical_bomb_rows"] == 0
        ),
        "legacy_projection_reconstruction_complete": True,
    }
    capsule: dict[str, object] = {
        "schema": CAPSULE_SCHEMA,
        "workload": {
            "route": "Sakuya/Remilia route 2",
            "difficulty": "Lunatic",
            "stage": "Final-B",
            "stage_route_index": 7,
            "spell_id": target_spell_id,
            "spell_name": "「永夜返し  -世明け-」",
            "target_scale_bits": f"0x{target_scale_bits:08x}",
            "target_scale": float32_from_bits(target_scale_bits),
        },
        "semantics": {
            "player_laser_scale_version": (
                TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION
            ),
            "historical_projection_baseline_commit": (
                HISTORICAL_BASELINE_COMMIT
            ),
        },
        "authority": {
            "observed": (
                "The selected shipped-game decision rows physically observed "
                "a binary32 0.25 root scale during Final-B spell 190."
            ),
            "inferred": (
                "The old held movement state is reconstructed from retained "
                "unit-scale projected-player and control-origin outputs."
            ),
            "counterfactual": (
                "Corrected player coordinates hold that reconstructed input "
                "fixed to isolate time-scale semantics; they are not proof of "
                "the native active or pending input history."
            ),
            "root_schedule_limit": (
                "One post-update root proves one next player scale and no next "
                "laser scale. Repeated-root control-delay outputs are "
                "diagnostic only after their first frame."
            ),
            "physical_acceptance_limit": (
                "This retained capsule is not a clean-pass, survival, laser, "
                "future-schedule, or NMNB certificate."
            ),
        },
        "sessions": sessions,
        "aggregate": aggregate,
        "checks": checks,
        "gate": {
            "name": "SEM-SCALE-C1 Final-B physical root capsule",
            "passed": all(checks.values()),
            "scope": (
                "physical root provenance plus input-conditional one-player-"
                "phase scale replay only"
            ),
        },
    }
    payload = json.dumps(
        capsule,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    capsule["capsule_payload_sha256"] = hashlib.sha256(payload).hexdigest()
    return capsule


def write_capsule(capsule: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(capsule, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "retain Final-B quarter-scale roots and replay the corrected "
            "player primitive"
        )
    )
    parser.add_argument(
        "traces",
        type=Path,
        nargs="+",
        help="physical runtime JSONL traces",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="compact retained JSON report",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    capsule = build_capsule(arguments.traces)
    write_capsule(capsule, arguments.output)
    print(
        json.dumps(
            {
                "output": arguments.output.as_posix(),
                "gate": capsule["gate"],
                "aggregate": capsule["aggregate"],
                "capsule_payload_sha256": (
                    capsule["capsule_payload_sha256"]
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if capsule["gate"]["passed"] else 1  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
