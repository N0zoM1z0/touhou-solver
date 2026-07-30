#!/usr/bin/env python3
"""Audit route-faithful Power-0 evidence strictly before the first native hit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "th08-power0-clean-prefix-audit-v1"
SESSION_SCHEMA = "th08-unattended-full-route-session-v1"
EXPECTED_EXE_SHA256 = (
    "330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924"
)
POWER_THRESHOLDS = (8, 24, 48, 80, 128)
POWER_ITEM_TYPES = frozenset((0, 2, 4))
SUPPORTED_ITEM_MOTION_STATES = frozenset((0, 1, 2, 3, 5))


class Power0CleanPrefixAuditError(ValueError):
    """Raised when retained evidence cannot support the declared projection."""


@dataclass(frozen=True)
class Power0RunInput:
    trace_path: Path
    session_path: Path
    expected_trace_sha256: str
    expected_session_sha256: str


def _exact_int(value: object, *, field: str, line_number: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        location = f"line {line_number}: " if line_number is not None else ""
        raise Power0CleanPrefixAuditError(
            f"{location}{field} must be an exact integer"
        )
    return value


def _finite_number(
    value: object,
    *,
    field: str,
    line_number: int | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        location = f"line {line_number}: " if line_number is not None else ""
        raise Power0CleanPrefixAuditError(
            f"{location}{field} must be numeric"
        )
    parsed = float(value)
    if not math.isfinite(parsed):
        location = f"line {line_number}: " if line_number is not None else ""
        raise Power0CleanPrefixAuditError(
            f"{location}{field} must be finite"
        )
    return parsed


def _read_json_with_sha256(path: Path) -> tuple[dict[str, Any], str]:
    payload = path.read_bytes()
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Power0CleanPrefixAuditError(
            f"{path}: invalid JSON: {error}"
        ) from error
    if not isinstance(value, dict):
        raise Power0CleanPrefixAuditError(f"{path}: JSON root must be an object")
    return value, hashlib.sha256(payload).hexdigest()


def _validate_session(
    run: Power0RunInput,
    *,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_sequence: tuple[int, ...],
) -> dict[str, object]:
    session, digest = _read_json_with_sha256(run.session_path)
    if digest != run.expected_session_sha256:
        raise Power0CleanPrefixAuditError("session SHA-256 mismatch")
    if session.get("schema") != SESSION_SCHEMA:
        raise Power0CleanPrefixAuditError("unexpected full-route session schema")
    run_id = session.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise Power0CleanPrefixAuditError("session run_id is missing")
    if run.trace_path.stem != run_id or run.session_path.name != f"{run_id}.session.json":
        raise Power0CleanPrefixAuditError("trace/session run identity mismatch")
    if session.get("trial_accepted") is not True:
        raise Power0CleanPrefixAuditError("session gameplay trial was not accepted")
    if session.get("hard_no_bomb") is not True:
        raise Power0CleanPrefixAuditError("session is not hard no-Bomb")
    if _exact_int(session.get("route_id"), field="session route_id") != expected_route_id:
        raise Power0CleanPrefixAuditError("session route identity mismatch")
    if (
        _exact_int(
            session.get("difficulty_index"),
            field="session difficulty_index",
        )
        != expected_difficulty_index
    ):
        raise Power0CleanPrefixAuditError("session difficulty identity mismatch")
    stage_sequence = session.get("expected_stage_sequence")
    if stage_sequence != list(expected_stage_sequence):
        raise Power0CleanPrefixAuditError("session stage sequence mismatch")
    target = session.get("target")
    if not isinstance(target, dict) or target.get("sha256") != EXPECTED_EXE_SHA256:
        raise Power0CleanPrefixAuditError("session executable identity mismatch")
    patch = target.get("runtime_patch")
    if not isinstance(patch, dict) or patch.get("no_life_decrement") is not True:
        raise Power0CleanPrefixAuditError("no-life-decrement patch is not verified")
    completion = session.get("completion_scene")
    if (
        not isinstance(completion, dict)
        or completion.get("status") != "terminal_unload"
    ):
        raise Power0CleanPrefixAuditError("session did not retain terminal unload")
    return {
        "run_id": run_id,
        "session_sha256": digest,
        "status": session.get("status"),
        "trial_accepted": True,
        "hard_no_bomb": True,
        "completion_status": completion.get("status"),
        "post_gameplay_error_type": session.get("error_type"),
    }


def _validate_item_rows(
    rows: object,
    *,
    line_number: int,
) -> dict[int, tuple[float | int | bool, ...]]:
    if not isinstance(rows, list):
        raise Power0CleanPrefixAuditError(
            f"line {line_number}: items must be a list"
        )
    result: dict[int, tuple[float | int | bool, ...]] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 8:
            raise Power0CleanPrefixAuditError(
                f"line {line_number}: item row must contain eight fields"
            )
        slot = _exact_int(row[0], field="item slot", line_number=line_number)
        if not 0 <= slot < 2096 or slot in result:
            raise Power0CleanPrefixAuditError(
                f"line {line_number}: invalid or duplicate item slot"
            )
        x = _finite_number(row[1], field="item x", line_number=line_number)
        y = _finite_number(row[2], field="item y", line_number=line_number)
        vx = _finite_number(row[3], field="item vx", line_number=line_number)
        vy = _finite_number(row[4], field="item vy", line_number=line_number)
        item_type = _exact_int(
            row[5],
            field="item type",
            line_number=line_number,
        )
        motion_state = _exact_int(
            row[6],
            field="item motion state",
            line_number=line_number,
        )
        if not 0 <= item_type <= 255:
            raise Power0CleanPrefixAuditError(
                f"line {line_number}: item type is outside one byte"
            )
        if motion_state not in SUPPORTED_ITEM_MOTION_STATES:
            raise Power0CleanPrefixAuditError(
                f"line {line_number}: unsupported item motion state"
            )
        if not isinstance(row[7], bool):
            raise Power0CleanPrefixAuditError(
                f"line {line_number}: item full-value flag must be Boolean"
            )
        result[slot] = (slot, x, y, vx, vy, item_type, motion_state, row[7])
    return result


def _thresholds_crossed(before: int, after: int) -> list[int]:
    return [
        threshold
        for threshold in POWER_THRESHOLDS
        if before < threshold <= after
    ]


def _candidate_record(
    item: tuple[float | int | bool, ...],
    *,
    player_x: float,
    player_y: float,
) -> dict[str, object]:
    return {
        "slot": int(item[0]),
        "x": float(item[1]),
        "y": float(item[2]),
        "item_type": int(item[5]),
        "motion_state": int(item[6]),
        "center_distance_to_previous_player": math.hypot(
            float(item[1]) - player_x,
            float(item[2]) - player_y,
        ),
    }


def _power_at_or_before(trace: dict[str, object], frame: int) -> int:
    power = int(trace["initial_power"])
    for event in trace["observed_power_gain_events"]:
        if int(event["at_or_before_frame"]) > frame:
            break
        power = int(event["power_after"])
    return power


def audit_power0_run(
    run: Power0RunInput,
    *,
    expected_route_id: int = 2,
    expected_difficulty_index: int = 3,
    expected_stage_route_index: int = 0,
    expected_stage_sequence: tuple[int, ...] = (0, 1, 2, 3, 5, 7),
) -> dict[str, object]:
    session = _validate_session(
        run,
        expected_route_id=expected_route_id,
        expected_difficulty_index=expected_difficulty_index,
        expected_stage_sequence=expected_stage_sequence,
    )
    digest = hashlib.sha256()
    line_count = 0
    identity_count = 0
    config_count = 0
    stage_identity_count = 0
    prefix_closed = False
    first_hit_frame: int | None = None
    clean_decision_count = 0
    previous_frame: int | None = None
    previous_power: int | None = None
    previous_items: dict[int, tuple[float | int | bool, ...]] = {}
    previous_player = (0.0, 0.0)
    initial_power: int | None = None
    initial_lives: int | None = None
    initial_bombs: int | None = None
    first_clean_frame: int | None = None
    last_clean_frame: int | None = None
    last_clean_power: int | None = None
    power_events: list[dict[str, object]] = []
    threshold_crossings: list[dict[str, object]] = []
    decision_gap_counts: Counter[int] = Counter()
    item_type_counts: Counter[int] = Counter()
    item_motion_counts: Counter[int] = Counter()
    focus_counts: Counter[bool] = Counter()
    safe_action_count_distribution: Counter[int] = Counter()
    decisions_with_power_items = 0
    power_item_row_observations = 0
    power_item_minimum_distance: float | None = None
    power_item_decisions_with_positive_safe_set = 0
    power_item_decisions_with_multiple_safe_actions = 0

    with run.trace_path.open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            digest.update(raw_line)
            line_count = line_number
            if prefix_closed:
                continue
            try:
                record = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: invalid JSON: {error}"
                ) from error
            if not isinstance(record, dict):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: trace row must be an object"
                )
            kind = record.get("kind")
            if kind == "identity":
                identity_count += 1
                if record.get("sha256") != EXPECTED_EXE_SHA256:
                    raise Power0CleanPrefixAuditError(
                        "trace executable identity mismatch"
                    )
                patch = record.get("runtime_patch")
                if (
                    not isinstance(patch, dict)
                    or patch.get("no_life_decrement") is not True
                ):
                    raise Power0CleanPrefixAuditError(
                        "trace no-life-decrement patch is not verified"
                    )
                continue
            if kind == "controller_config":
                config_count += 1
                if record.get("bomb_policy") != "disabled":
                    raise Power0CleanPrefixAuditError(
                        "trace Bomb policy was not disabled"
                    )
                if record.get("item_policy") != "survival_only_passive_collection":
                    raise Power0CleanPrefixAuditError(
                        "trace item policy was not passive-only"
                    )
                continue
            if kind == "runtime_ecl_identity":
                if (
                    record.get("route_id") == expected_route_id
                    and record.get("difficulty_index")
                    == expected_difficulty_index
                    and record.get("stage_route_index")
                    == expected_stage_route_index
                ):
                    stage_identity_count += 1
                continue
            if kind != "decision":
                continue

            frame = _exact_int(
                record.get("frame"),
                field="decision frame",
                line_number=line_number,
            )
            stage = _exact_int(
                record.get("stage_route_index"),
                field="stage route index",
                line_number=line_number,
            )
            epoch = _exact_int(
                record.get("gameplay_epoch"),
                field="gameplay epoch",
                line_number=line_number,
            )
            if stage != expected_stage_route_index or epoch != 0:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: clean prefix left Stage 1/epoch 0"
                )
            if previous_frame is not None and frame <= previous_frame:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: decision frames are not increasing"
                )
            hit_started = record.get("hit_started")
            if not isinstance(hit_started, bool):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: hit_started must be Boolean"
                )
            if hit_started:
                first_hit_frame = frame
                prefix_closed = True
                continue
            if _exact_int(
                record.get("hit_count"),
                field="hit count",
                line_number=line_number,
            ) != 0:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: hit count is nonzero before first hit"
                )
            mask = _exact_int(
                record.get("mask"),
                field="issued mask",
                line_number=line_number,
            )
            bomb = record.get("bomb")
            if not isinstance(bomb, bool):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: Bomb marker must be Boolean"
                )
            if mask & 0x02 or bomb:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: Bomb appears in clean prefix"
                )
            planner_objective = record.get("planner_objective")
            if (
                not isinstance(planner_objective, dict)
                or planner_objective.get("item_objectives_enabled") is not False
            ):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: item objective was not disabled"
                )
            if record.get("predicted_collections") != []:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: predicted collection is nonempty"
                )
            if _finite_number(
                record.get("item_utility"),
                field="item utility",
                line_number=line_number,
            ) != 0.0:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: item utility is nonzero"
                )

            resources = record.get("resources")
            if not isinstance(resources, dict):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: resources are missing"
                )
            power_value = _finite_number(
                resources.get("power"),
                field="Power",
                line_number=line_number,
            )
            lives_value = _finite_number(
                resources.get("lives"),
                field="lives",
                line_number=line_number,
            )
            bombs_value = _finite_number(
                resources.get("bombs"),
                field="Bomb stock",
                line_number=line_number,
            )
            if not power_value.is_integer() or not 0 <= power_value <= 128:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: Power is not an integral 0..128 value"
                )
            if not lives_value.is_integer() or not bombs_value.is_integer():
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: lives/Bombs are not integral"
                )
            power = int(power_value)
            lives = int(lives_value)
            bombs = int(bombs_value)
            if initial_power is None:
                initial_power = power
                initial_lives = lives
                initial_bombs = bombs
                first_clean_frame = frame
                if (initial_power, initial_lives, initial_bombs) != (0, 2, 3):
                    raise Power0CleanPrefixAuditError(
                        "trace is not a natural Game Start Power-0 prefix"
                    )
            elif lives != initial_lives or bombs != initial_bombs:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: clean-prefix lives/Bombs changed"
                )

            items = _validate_item_rows(
                record.get("items"),
                line_number=line_number,
            )
            if _exact_int(
                record.get("active_items"),
                field="active item count",
                line_number=line_number,
            ) != len(items):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: active item count mismatch"
                )
            player = record.get("player")
            if not isinstance(player, dict):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: player state is missing"
                )
            player_x = _finite_number(
                player.get("projected_x"),
                field="projected player x",
                line_number=line_number,
            )
            player_y = _finite_number(
                player.get("projected_y"),
                field="projected player y",
                line_number=line_number,
            )
            robust = record.get("robust_control")
            if not isinstance(robust, dict):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: robust-control telemetry is missing"
                )
            safe_action_count = _exact_int(
                robust.get("viability_safe_action_count"),
                field="viability safe action count",
                line_number=line_number,
            )
            if not 0 <= safe_action_count <= 17:
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: invalid safe action count"
                )

            if previous_frame is not None:
                decision_gap_counts[frame - previous_frame] += 1
            if previous_power is not None:
                if power < previous_power:
                    raise Power0CleanPrefixAuditError(
                        f"line {line_number}: Power decreased before first hit"
                    )
                if power > previous_power:
                    disappeared = [
                        item
                        for slot, item in previous_items.items()
                        if slot not in items and int(item[5]) in POWER_ITEM_TYPES
                    ]
                    candidates = [
                        _candidate_record(
                            item,
                            player_x=previous_player[0],
                            player_y=previous_player[1],
                        )
                        for item in disappeared
                    ]
                    matching_small = [
                        item for item in candidates if item["item_type"] == 0
                    ]
                    delta = power - previous_power
                    source_classification = "unobserved_interval_source"
                    if delta == 1 and len(matching_small) == 1:
                        source_classification = (
                            "single_visible_disappeared_small_power_candidate"
                        )
                    event = {
                        "after_frame": previous_frame,
                        "at_or_before_frame": frame,
                        "power_before": previous_power,
                        "power_after": power,
                        "delta": delta,
                        "thresholds_crossed": _thresholds_crossed(
                            previous_power,
                            power,
                        ),
                        "visible_disappeared_power_candidates": candidates,
                        "source_classification": source_classification,
                        "verified_item_source": False,
                    }
                    power_events.append(event)
                    for threshold in event["thresholds_crossed"]:
                        threshold_crossings.append(
                            {
                                "threshold": threshold,
                                "after_frame": previous_frame,
                                "at_or_before_frame": frame,
                            }
                        )

            for item in items.values():
                item_type_counts[int(item[5])] += 1
                item_motion_counts[int(item[6])] += 1
            relevant = [
                item
                for item in items.values()
                if int(item[5]) in POWER_ITEM_TYPES and power < 128
            ]
            if relevant:
                decisions_with_power_items += 1
                power_item_row_observations += len(relevant)
                power_item_decisions_with_positive_safe_set += int(
                    safe_action_count > 0
                )
                power_item_decisions_with_multiple_safe_actions += int(
                    safe_action_count > 1
                )
                nearest = min(
                    math.hypot(
                        float(item[1]) - player_x,
                        float(item[2]) - player_y,
                    )
                    for item in relevant
                )
                power_item_minimum_distance = (
                    nearest
                    if power_item_minimum_distance is None
                    else min(power_item_minimum_distance, nearest)
                )
            focused = record.get("focused")
            if not isinstance(focused, bool):
                raise Power0CleanPrefixAuditError(
                    f"line {line_number}: focused marker must be Boolean"
                )
            focus_counts[focused] += 1
            safe_action_count_distribution[safe_action_count] += 1
            clean_decision_count += 1
            previous_frame = frame
            previous_power = power
            previous_items = items
            previous_player = (player_x, player_y)
            last_clean_frame = frame
            last_clean_power = power

    trace_sha256 = digest.hexdigest()
    if trace_sha256 != run.expected_trace_sha256:
        raise Power0CleanPrefixAuditError("trace SHA-256 mismatch")
    if identity_count != 1 or config_count != 1 or stage_identity_count < 1:
        raise Power0CleanPrefixAuditError(
            "trace lacks unique identity/config or Stage-1 route identity"
        )
    if (
        first_hit_frame is None
        or clean_decision_count == 0
        or last_clean_frame is None
        or first_clean_frame is None
        or initial_power is None
        or last_clean_power is None
    ):
        raise Power0CleanPrefixAuditError(
            "trace lacks a bounded nonempty first-hit prefix"
        )
    return {
        **session,
        "trace_sha256": trace_sha256,
        "trace_line_count": line_count,
        "first_hit_frame": first_hit_frame,
        "clean_prefix_excludes_first_hit_row": True,
        "clean_decision_count": clean_decision_count,
        "first_clean_frame": first_clean_frame,
        "last_clean_frame": last_clean_frame,
        "initial_power": initial_power,
        "last_clean_power": last_clean_power,
        "power_to_next_threshold": min(
            threshold - last_clean_power
            for threshold in POWER_THRESHOLDS
            if threshold > last_clean_power
        ),
        "observed_power_gain": last_clean_power - initial_power,
        "observed_power_gain_events": power_events,
        "shot_threshold_crossings": threshold_crossings,
        "decision_gap_counts": {
            str(key): value
            for key, value in sorted(decision_gap_counts.items())
        },
        "item_observation": {
            "authority": "decision_observation_rows_only",
            "native_generation_authority": False,
            "pickup_source_authority": False,
            "row_counts_by_type": {
                str(key): value
                for key, value in sorted(item_type_counts.items())
            },
            "row_counts_by_motion_state": {
                str(key): value
                for key, value in sorted(item_motion_counts.items())
            },
            "decisions_with_power_items": decisions_with_power_items,
            "power_item_row_observations": power_item_row_observations,
            "minimum_power_item_center_distance": power_item_minimum_distance,
            "power_item_decisions_with_positive_safe_set_telemetry": (
                power_item_decisions_with_positive_safe_set
            ),
            "power_item_decisions_with_multiple_safe_actions_telemetry": (
                power_item_decisions_with_multiple_safe_actions
            ),
        },
        "focus_decision_counts": {
            "focused": focus_counts[True],
            "unfocused": focus_counts[False],
        },
        "viability_safe_action_count_distribution": {
            str(key): value
            for key, value in sorted(
                safe_action_count_distribution.items()
            )
        },
        "retained_planner_telemetry_authority": False,
        "post_hit_rows_used": 0,
    }


def build_power0_clean_prefix_report(
    runs: tuple[Power0RunInput, ...],
) -> dict[str, object]:
    if len(runs) < 2:
        raise Power0CleanPrefixAuditError(
            "at least two natural Power-0 runs are required"
        )
    traces = [audit_power0_run(run) for run in runs]
    common_frame = min(int(trace["first_hit_frame"]) for trace in traces)
    common_power = {
        str(trace["run_id"]): _power_at_or_before(trace, common_frame)
        for trace in traces
    }
    report: dict[str, object] = {
        "schema": SCHEMA,
        "taskbook_card": "POWER-ROUTE-01",
        "trace_count": len(traces),
        "traces": traces,
        "comparison": {
            "same_executable": True,
            "same_route": 2,
            "same_difficulty_index": 3,
            "same_initial_resources": {
                "power": 0,
                "lives": 2,
                "bombs": 3,
            },
            "same_item_policy": "survival_only_passive_collection",
            "common_clean_horizon_frame": common_frame,
            "power_at_or_before_common_frame": common_power,
            "different_rng_or_world_roots": True,
            "causal_policy_comparison_authority": False,
        },
        "classification": {
            "route_faithful_clean_prefix_evidence": True,
            "observed_power_acquisition_authority": True,
            "item_specific_pickup_authority": False,
            "shot_threshold_effect_observed": any(
                trace["shot_threshold_crossings"] for trace in traces
            ),
            "survival_feasible_collection_policy_gate_passed": False,
            "reason": (
                "the retained passive-only runs expose different natural "
                "Power histories but provide no same-root counterfactual "
                "action branches and no clean prefix reaches the first "
                "normal-shot Power threshold"
            ),
        },
        "authority": {
            "kind": "offline_first-hit-bounded_route_resource_audit",
            "physical_trial_run": False,
            "planner_action_authority": False,
            "live_item_objective_authority": False,
            "post_death_recovery_authority": False,
        },
        "next_gate": {
            "requires_first_hit_bounded_natural_route_root": True,
            "requires_same_root_survival_feasible_action_branches": True,
            "requires_same_update_item_end_or_pickup_event": True,
            "requires_threshold_and_later_damage_join": True,
            "practice_mode_max_power_is_route_authority": False,
        },
    }
    payload = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_digest"] = hashlib.sha256(payload).hexdigest()
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run",
        action="append",
        nargs=4,
        metavar=("TRACE", "SESSION", "TRACE_SHA256", "SESSION_SHA256"),
        required=True,
    )
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runs = tuple(
        Power0RunInput(
            Path(trace),
            Path(session),
            trace_sha256,
            session_sha256,
        )
        for trace, session, trace_sha256, session_sha256 in args.run
    )
    report = build_power0_clean_prefix_report(runs)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
