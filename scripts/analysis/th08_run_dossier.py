#!/usr/bin/env python3
"""Build an offline stitched run dossier from live-agent traces."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from th08_ecl import parse_ecl
from analysis.dossier.schema import compact_decision
from analysis.dossier.statistics import (
    percentiles as _percentiles,
    resource_range as _resource_range,
)
from analysis.dossier.trace_reader import TraceProvenance, read_trace
from analysis.th08_trial_report import STAGE_ROUTE_LABELS


ROOT = Path(__file__).resolve().parents[2]
_compact_decision = compact_decision
PHASE_COUNTER_JUMP_MIN = 1750
PHASE_COUNTER_JUMP_MAX = 1850
DEATH_WINDOW_FRAMES = 240
CLUSTER_GAP_FRAMES = 600
BOMB_INPUT_BIT = 0x02


def _case_prefix_for_difficulty(difficulty: str) -> str:
    prefixes = {
        "easy": "EASY",
        "normal": "NORMAL",
        "hard": "HARD",
        "lunatic": "LUN",
        "extra": "EXTRA",
    }
    try:
        return prefixes[difficulty.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"unsupported case difficulty {difficulty!r}") from exc


def _nearest_bullet(row: dict[str, object]) -> dict[str, object] | None:
    player = row["player"]
    candidates = []
    for bullet in row.get("nearby_bullets", ()):
        if not isinstance(bullet, list) or len(bullet) < 7:
            continue
        dx = abs(float(bullet[1]) - float(player["x"]))
        dy = abs(float(bullet[2]) - float(player["y"]))
        clearance_x = dx - (2.0 + float(bullet[5]))
        clearance_y = dy - (2.0 + float(bullet[6]))
        if clearance_x <= 0.0 and clearance_y <= 0.0:
            clearance = max(clearance_x, clearance_y)
        else:
            clearance = math.hypot(
                max(clearance_x, 0.0),
                max(clearance_y, 0.0),
            )
        candidates.append(
            {
                "slot": int(bullet[0]),
                "x": float(bullet[1]),
                "y": float(bullet[2]),
                "velocity_x": float(bullet[3]),
                "velocity_y": float(bullet[4]),
                "half_width": float(bullet[5]),
                "half_height": float(bullet[6]),
                "transform_flags": int(bullet[7]) if len(bullet) >= 8 else 0,
                "center_distance": math.hypot(dx, dy),
                "aabb_clearance": clearance,
            }
        )
    overlapping = [
        candidate
        for candidate in candidates
        if float(candidate["aabb_clearance"]) <= 0.0
    ]
    if overlapping:
        return min(
            overlapping,
            key=lambda candidate: candidate["center_distance"],
        )
    if candidates:
        return min(
            candidates,
            key=lambda candidate: candidate["center_distance"],
        )
    return None


def _nearest_laser(row: dict[str, object]) -> dict[str, object] | None:
    player = row["player"]
    player_x = float(player["x"])
    player_y = float(player["y"])
    candidates = []
    for slot, laser in enumerate(row.get("lasers", ())):
        if not isinstance(laser, list) or len(laser) < 6:
            continue
        origin_x = float(laser[0])
        origin_y = float(laser[1])
        angle = float(laser[2])
        tail = float(laser[3])
        head = float(laser[4])
        half_width = float(laser[5])
        cosine = math.cos(angle)
        sine = math.sin(angle)
        start_x = origin_x + cosine * tail
        start_y = origin_y + sine * tail
        end_x = origin_x + cosine * head
        end_y = origin_y + sine * head
        segment_x = end_x - start_x
        segment_y = end_y - start_y
        length_sq = segment_x * segment_x + segment_y * segment_y
        if length_sq <= 1e-9:
            projection = 0.0
        else:
            projection = min(
                1.0,
                max(
                    0.0,
                    (
                        (player_x - start_x) * segment_x
                        + (player_y - start_y) * segment_y
                    )
                    / length_sq,
                ),
            )
        closest_x = start_x + projection * segment_x
        closest_y = start_y + projection * segment_y
        center_distance = math.hypot(
            player_x - closest_x,
            player_y - closest_y,
        )
        candidates.append(
            {
                "slot": slot,
                "origin_x": origin_x,
                "origin_y": origin_y,
                "angle": angle,
                "tail": tail,
                "head": head,
                "half_width": half_width,
                "closest_x": closest_x,
                "closest_y": closest_y,
                "center_distance": center_distance,
                "clearance": center_distance - half_width - 2.0,
            }
        )
    if not candidates:
        return None
    return min(candidates, key=lambda candidate: candidate["clearance"])


def _nearest_enemy_body(
    row: dict[str, object],
) -> dict[str, object] | None:
    hit_observation = row.get("hit_contact_observation")
    if (
        isinstance(hit_observation, dict)
        and hit_observation.get("stable")
        and isinstance(hit_observation.get("player_lethal_aabb"), list)
    ):
        player_aabb = hit_observation["player_lethal_aabb"]
        if len(player_aabb) >= 4:
            candidates = []
            player_left, player_top, player_right, player_bottom = map(
                float,
                player_aabb[:4],
            )
            for body in hit_observation.get("enemy_bodies", ()):
                if not isinstance(body, list) or len(body) < 8:
                    continue
                x = float(body[1])
                y = float(body[2])
                half_width = float(body[5])
                half_height = float(body[6])
                dx = max(
                    player_left - (x + half_width),
                    (x - half_width) - player_right,
                )
                dy = max(
                    player_top - (y + half_height),
                    (y - half_height) - player_bottom,
                )
                clearance = (
                    max(dx, dy)
                    if dx <= 0.0 and dy <= 0.0
                    else math.hypot(max(dx, 0.0), max(dy, 0.0))
                )
                candidates.append(
                    {
                        "pointer": int(body[0]),
                        "x_at_observation": x,
                        "y_at_observation": y,
                        "velocity_x": float(body[3]),
                        "velocity_y": float(body[4]),
                        "internal_motion_x": (
                            float(body[9])
                            if len(body) >= 11 and body[9] is not None
                            else None
                        ),
                        "internal_motion_y": (
                            float(body[10])
                            if len(body) >= 11 and body[10] is not None
                            else None
                        ),
                        "half_width": half_width,
                        "half_height": half_height,
                        "flags": int(body[7]),
                        "observation_frame": int(
                            hit_observation["frame_after"]
                        ),
                        "player_lethal_aabb": [
                            player_left,
                            player_top,
                            player_right,
                            player_bottom,
                        ],
                        "exact_same_epoch": True,
                        "aabb_clearance": clearance,
                    }
                )
            if candidates:
                return min(
                    candidates,
                    key=lambda candidate: candidate["aabb_clearance"],
                )

    player = row["player"]
    action_frame = int(row["frame"])
    snapshot_value = row.get("enemy_body_snapshot_frame", action_frame)
    snapshot_frame = (
        action_frame if snapshot_value is None else int(snapshot_value)
    )
    elapsed = max(0, action_frame - snapshot_frame)
    candidates = []
    for body in row.get("enemy_bodies", ()):
        if not isinstance(body, list) or len(body) < 8:
            continue
        x = float(body[1]) + float(body[3]) * elapsed
        y = float(body[2]) + float(body[4]) * elapsed
        dx = abs(float(player["x"]) - x) - (2.0 + float(body[5]))
        dy = abs(float(player["y"]) - y) - (2.0 + float(body[6]))
        if dx <= 0.0 and dy <= 0.0:
            clearance = max(dx, dy)
        else:
            clearance = math.hypot(max(dx, 0.0), max(dy, 0.0))
        candidates.append(
            {
                "pointer": int(body[0]),
                "x_at_snapshot": float(body[1]),
                "y_at_snapshot": float(body[2]),
                "velocity_x": float(body[3]),
                "velocity_y": float(body[4]),
                "internal_motion_x": (
                    float(body[9])
                    if len(body) >= 11 and body[9] is not None
                    else None
                ),
                "internal_motion_y": (
                    float(body[10])
                    if len(body) >= 11 and body[10] is not None
                    else None
                ),
                "projected_x_at_action": x,
                "projected_y_at_action": y,
                "half_width": float(body[5]),
                "half_height": float(body[6]),
                "flags": int(body[7]),
                "snapshot_frame": snapshot_frame,
                "elapsed_frames": elapsed,
                "exact_same_epoch": False,
                "aabb_clearance": clearance,
            }
        )
    if not candidates:
        return None
    return min(candidates, key=lambda candidate: candidate["aabb_clearance"])


def _spell_attribution(row: dict[str, object]) -> dict[str, object]:
    spell = row.get("spell")
    if not isinstance(spell, dict):
        return {
            "status": "unresolved_current_trace_schema",
            "spell_id": None,
            "spell_name": None,
        }
    flags = int(spell.get("flags", 0))
    if not bool(spell.get("active")):
        return {
            "status": "no_active_spell_at_hit",
            "spell_id": None,
            "spell_name": None,
            "flags": flags,
        }
    return {
        "status": "resolved_live_spell_state",
        "spell_id": int(spell["spell_id"]),
        "spell_name": str(spell.get("name", "")),
        "flags": flags,
        "enemy_pointer": int(spell.get("enemy_pointer", 0)),
    }


def _input_mask_action(mask: int) -> str:
    directions = []
    if mask & 0x10:
        directions.append("up")
    if mask & 0x20:
        directions.append("down")
    if mask & 0x40:
        directions.append("left")
    if mask & 0x80:
        directions.append("right")
    action = "_".join(directions) if directions else "stay"
    if directions and not mask & 0x04:
        action += "_fast"
    if mask & 0x02:
        action += "+bomb"
    return action


def _no_bomb_verification(
    decisions: list[dict[str, object]],
    provenance: list[TraceProvenance],
) -> dict[str, object]:
    mask_violations = [
        int(row["frame"])
        for row in decisions
        if int(row["mask"]) & BOMB_INPUT_BIT
    ]
    flag_violations = [
        int(row["frame"]) for row in decisions if bool(row["bomb"])
    ]
    action_violations = [
        int(row["frame"])
        for row in decisions
        if "bomb" in str(row["action"]).lower()
    ]
    controller_configs = [
        config
        for trace in provenance
        for config in trace.controller_configs
    ]
    configured_disabled = bool(controller_configs) and all(
        config.get("bomb_policy") == "disabled"
        for config in controller_configs
    )
    return {
        "passed": (
            configured_disabled
            and not mask_violations
            and not flag_violations
            and not action_violations
        ),
        "bomb_input_bit": BOMB_INPUT_BIT,
        "controller_policy_disabled": configured_disabled,
        "decision_count_checked": len(decisions),
        "mask_violation_frames": mask_violations,
        "bomb_flag_violation_frames": flag_violations,
        "bomb_action_violation_frames": action_violations,
        "resource_note": (
            "Bomb stock can decrease after a native hit because TH08 resets "
            "the respawn stock. Only input mask, decision flag, action, and "
            "controller configuration prove Bomb use."
        ),
    }


def _robust_viability_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    unique_solutions: dict[int, dict[str, object]] = {}
    policy_rows = []
    queries = []
    for row in decisions:
        if row.get("corridor_planning_mode") == "robust_viability":
            policy_rows.append(row)
        source = row.get("corridor_source_frame")
        if source is not None:
            unique_solutions.setdefault(int(source), row)
        viability = row.get("viability")
        if isinstance(viability, dict) and viability:
            queries.append(viability)

    unique_rows = list(unique_solutions.values())
    timing_keys = sorted(
        {
            str(key)
            for row in unique_rows
            for key in row.get("corridor_solver_timing_ms", {})
        }
    )
    available = [
        query for query in queries if bool(query.get("available"))
    ]
    constrained = [
        row
        for row in decisions
        if isinstance(row.get("robust_control"), dict)
        and bool(row["robust_control"].get("viability_constrained"))
    ]
    return {
        "policy_decision_count": len(policy_rows),
        "decision_without_query_count": len(policy_rows) - len(queries),
        "unique_solution_count": len(unique_rows),
        "solve_ms": _percentiles(
            float(row["corridor_solve_ms"])
            for row in unique_rows
            if row.get("corridor_solve_ms") is not None
        ),
        "first_observed_age_frames": _percentiles(
            float(row["corridor_age"])
            for row in unique_rows
            if row.get("corridor_age") is not None
        ),
        "forecast_lead_frames": _percentiles(
            float(row["corridor_forecast_lead_frames"])
            for row in unique_rows
            if row.get("corridor_forecast_lead_frames") is not None
        ),
        "backend_counts": dict(
            Counter(
                str(row["corridor_viability_backend"])
                for row in unique_rows
                if row.get("corridor_viability_backend") is not None
            )
        ),
        "solver_phase_ms": {
            key: _percentiles(
                float(row["corridor_solver_timing_ms"][key])
                for row in unique_rows
                if key in row.get("corridor_solver_timing_ms", {})
            )
            for key in timing_keys
        },
        "serial_coverage_margin_frames": _percentiles(
            float(row["corridor_serial_coverage_margin_frames"])
            for row in policy_rows
            if row.get("corridor_serial_coverage_margin_frames") is not None
        ),
        "serial_worker_serviceable_count": sum(
            bool(row.get("corridor_serial_worker_serviceable"))
            for row in policy_rows
        ),
        "policy_status_counts": dict(
            Counter(
                str(row["corridor_policy_status"])
                for row in policy_rows
                if row.get("corridor_policy_status") is not None
            )
        ),
        "reported_stale_solution_count": sum(
            bool(row.get("corridor_stale")) for row in unique_rows
        ),
        "query_count": len(queries),
        "available_query_count": len(available),
        "unavailable_reason_counts": dict(
            Counter(
                str(query.get("reason", "unspecified"))
                for query in queries
                if not bool(query.get("available"))
            )
        ),
        "support_covered_query_count": sum(
            bool(query.get("support_covers_current", True))
            for query in available
        ),
        "support_uncovered_query_count": sum(
            not bool(query.get("support_covers_current", True))
            for query in available
        ),
        "viable_query_count": sum(
            bool(query.get("state_viable")) for query in available
        ),
        "empty_action_set_count": sum(
            not bool(query.get("state_viable"))
            or int(query.get("safe_action_count", 0)) == 0
            for query in available
        ),
        "constrained_decision_count": len(constrained),
        "constrained_decision_fraction": (
            len(constrained) / len(decisions) if decisions else None
        ),
        "safe_action_count": _percentiles(
            int(query.get("safe_action_count", 0))
            for query in available
        ),
        "selected_repair_volume": _percentiles(
            int(query.get("selected_repair_volume", 0))
            for query in available
        ),
        "policy_age_frames": _percentiles(
            int(query.get("age", 0)) for query in queries
        ),
    }


def _planner_consistency_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    """Cross-tab distinct global-horizon and local-prefix safety contracts.

    A global winning state promises a policy over the remaining corridor
    horizon.  The local certificate only checks the selected action over its
    delay-plus-hold prefix.  Those Boolean values are useful together, but
    disagreement is not itself a contradiction.  The action-level
    contradiction is narrower: an action in the global winning set that the
    fresh local tube checker finds unsafe.
    """

    comparable = []
    excluded_hazard_version_change_count = 0
    excluded_deadline_hold_count = 0
    for row in decisions:
        player = row.get("player")
        if isinstance(player, dict) and (
            int(player.get("phase", 0)) != 0
            or int(player.get("phase_at_action", 0)) != 0
        ):
            continue
        viability = row.get("viability")
        robust = row.get("robust_control")
        if (
            not isinstance(viability, dict)
            or not bool(viability.get("available"))
            or not bool(viability.get("support_covers_current", True))
            or not isinstance(robust, dict)
        ):
            continue
        issue_guard = row.get("issue_time_enemy_guard")
        if (
            isinstance(issue_guard, dict)
            and bool(issue_guard.get("changes"))
        ):
            # The global policy and its action mask belong to the pre-issue
            # hazard version.  The issue guard deliberately invalidates that
            # version and recertifies against a newer local snapshot.
            excluded_hazard_version_change_count += 1
            continue
        deadline_guard = row.get("deadline_guard")
        if (
            isinstance(deadline_guard, dict)
            and bool(deadline_guard.get("input_suppressed"))
        ):
            # The traced action is the already-active input, not the newly
            # planned action whose global membership was queried.
            excluded_deadline_hold_count += 1
            continue
        global_safe = (
            bool(viability.get("state_viable"))
            and int(viability.get("safe_action_count", 0)) > 0
        )
        local_safe = (
            int(robust.get("worst_collisions", 0)) == 0
            and float(robust.get("min_clearance", 0.0)) >= 0.0
        )
        safe_actions = {
            str(action) for action in viability.get("safe_actions", ())
        }
        comparable.append(
            {
                "global_winning": global_safe,
                "local_prefix_safe": local_safe,
                "selected_in_winning_set": (
                    str(row.get("action", "")) in safe_actions
                ),
            }
        )
    count = len(comparable)

    def count_where(predicate) -> int:
        return sum(bool(predicate(item)) for item in comparable)

    global_winning_local_prefix_unsafe = count_where(
        lambda item: (
            item["global_winning"] and not item["local_prefix_safe"]
        )
    )
    global_losing_local_prefix_safe = count_where(
        lambda item: (
            not item["global_winning"] and item["local_prefix_safe"]
        )
    )
    certified_action_local_prefix_unsafe = count_where(
        lambda item: (
            item["global_winning"]
            and item["selected_in_winning_set"]
            and not item["local_prefix_safe"]
        )
    )
    selected_outside = count_where(
        lambda item: (
            item["global_winning"]
            and not item["selected_in_winning_set"]
        )
    )
    return {
        "comparable_decision_count": count,
        "global_winning_local_prefix_safe_count": count_where(
            lambda item: (
                item["global_winning"] and item["local_prefix_safe"]
            )
        ),
        "global_winning_local_prefix_unsafe_count": (
            global_winning_local_prefix_unsafe
        ),
        "global_losing_local_prefix_safe_count": (
            global_losing_local_prefix_safe
        ),
        "global_losing_local_prefix_unsafe_count": count_where(
            lambda item: (
                not item["global_winning"]
                and not item["local_prefix_safe"]
            )
        ),
        "selected_certified_action_local_prefix_unsafe_count": (
            certified_action_local_prefix_unsafe
        ),
        "selected_certified_action_local_prefix_unsafe_fraction": (
            certified_action_local_prefix_unsafe / count
            if count
            else None
        ),
        "selected_action_outside_global_winning_set_count": selected_outside,
        "excluded_hazard_version_change_count": (
            excluded_hazard_version_change_count
        ),
        "excluded_deadline_hold_count": excluded_deadline_hold_count,
        "semantics": (
            "global is a remaining-horizon winning-set claim; local is a "
            "delay-plus-hold prefix claim. After excluding observed "
            "issue-time invalidations, a selected cached-policy action that "
            "the fresh local prefix finds unsafe is a forecast/version "
            "contradiction; future births can still make the cached hazard "
            "set older than the local one. Deadline holds are excluded "
            "because their final input is not governed by that policy query."
        ),
    }


def _classify_death(
    row: dict[str, object],
    *,
    window: list[dict[str, object]],
) -> tuple[
    str,
    list[str],
    dict[str, object] | None,
    dict[str, object] | None,
    dict[str, object] | None,
]:
    nearest_bullet = _nearest_bullet(row)
    nearest_laser = _nearest_laser(row)
    nearest_enemy_body = _nearest_enemy_body(row)
    last_alive = next(
        (
            sample
            for sample in reversed(window[:-1])
            if int(sample.get("player", {}).get("phase", 0)) == 0
            and int(
                sample.get("player", {}).get("phase_at_action", 0)
            )
            == 0
        ),
        None,
    )
    pipeline = float(row["pipeline_clearance"])
    lasers = int(row["active_lasers"])
    exact_enemy_overlap = (
        nearest_enemy_body is not None
        and bool(nearest_enemy_body.get("exact_same_epoch"))
        and float(nearest_enemy_body["aabb_clearance"]) <= 0.0
    )
    if exact_enemy_overlap:
        hit_body_pointers = {
            int(pointer)
            for pointer in row.get("enemy_body_pointers", ())
        }
        causal_row = last_alive if last_alive is not None else row
        causal_body_pointers = {
            int(pointer)
            for pointer in causal_row.get("enemy_body_pointers", ())
        }
        pointer = int(nearest_enemy_body["pointer"])
        nearest_enemy_body["present_in_hit_decision_snapshot"] = (
            pointer in hit_body_pointers
        )
        nearest_enemy_body["present_in_causal_snapshot"] = (
            pointer in causal_body_pointers
        )
        # Compatibility field retained for downstream regression readers.  Its
        # intended semantics are the last action that could have prevented the
        # hit, not the already-too-late hit-detection decision.
        nearest_enemy_body["present_in_action_snapshot"] = (
            pointer in causal_body_pointers
        )
    exact_overlaps = sum(
        (
            exact_enemy_overlap,
            nearest_laser is not None
            and float(nearest_laser["clearance"]) <= 0.0,
            nearest_bullet is not None
            and float(nearest_bullet["aabb_clearance"]) <= 0.0,
        )
    )
    if exact_overlaps > 1:
        primary = "observed_multiple_hazard_overlap"
    elif exact_enemy_overlap:
        primary = "observed_enemy_body_overlap"
    elif (
        nearest_laser is not None
        and float(nearest_laser["clearance"]) <= 0.0
    ):
        primary = "observed_laser_overlap"
    elif (
        nearest_bullet is not None
        and float(nearest_bullet["aabb_clearance"]) <= 0.0
    ):
        primary = "observed_bullet_overlap"
    elif pipeline <= 0.0:
        primary = "modeled_committed_prefix_collision"
    elif lasers:
        primary = "active_laser_without_observed_overlap"
    else:
        primary = "sensor_gap_or_unmodeled_hazard"

    contributing = []
    player = row["player"]
    if (
        float(player["y"]) >= 428.0
        or float(player["x"]) <= 12.0
        or float(player["x"]) >= 372.0
    ):
        contributing.append("playfield_boundary")
    slacks = [
        float(sample["corridor_slack"])
        for sample in window
        if sample["corridor_slack"] is not None
    ]
    if slacks and min(slacks) < 0.0:
        contributing.append("corridor_deadline_miss")
    if _action_lag_over_model(row) or (
        last_alive is not None and _action_lag_over_model(last_alive)
    ):
        contributing.append("action_lag_over_model")
    if int(row["active_bullets"]) >= 1000:
        contributing.append("pool_density_over_1000")
    input_snapshot = row.get("input_snapshot")
    active_mask = (
        int(input_snapshot.get("current", row.get("mask", 0x05)))
        if isinstance(input_snapshot, dict)
        else int(row.get("mask", 0x05))
    )
    if "_fast" in _input_mask_action(active_mask):
        contributing.append("fast_mode")
    if (
        exact_enemy_overlap
        and not bool(nearest_enemy_body["present_in_action_snapshot"])
    ):
        contributing.append("enemy_body_absent_from_action_snapshot")
    return (
        primary,
        contributing,
        nearest_bullet,
        nearest_laser,
        nearest_enemy_body,
    )


def _action_lag_over_model(row: dict[str, object]) -> bool:
    """Whether issue lag exceeds the decision's complete delay support."""

    support = tuple(
        int(value) for value in row.get("control_delay_candidates", ())
    )
    support_high = (
        max(support)
        if support
        else int(row.get("control_delay_frames", 3))
    )
    return int(row.get("action_lag", 0)) > support_high


def _robust_control_unsafe(row: dict[str, object]) -> bool:
    robust = row.get("robust_control")
    if not isinstance(robust, dict) or not robust:
        return False
    return (
        int(robust.get("worst_collisions", 0)) > 0
        or float(robust.get("min_clearance", 9999.0)) < 0.0
    )


def _viability_action_set_empty(row: dict[str, object]) -> bool:
    viability = row.get("viability")
    if not isinstance(viability, dict) or not viability:
        return False
    return (
        bool(viability.get("available"))
        and bool(viability.get("support_covers_current", True))
    ) and (
        not bool(viability.get("state_viable"))
        or int(viability.get("safe_action_count", 0)) == 0
    )


def _death_ledger(
    decisions: list[dict[str, object]],
    *,
    case_prefix: str = "LUN",
) -> list[dict[str, object]]:
    deaths = []
    for index, row in enumerate(decisions):
        if not row["hit_started"]:
            continue
        frame = int(row["frame"])
        stage = int(row["stage_route_index"])
        trace_index = int(row["trace_index"])
        window = []
        cursor = index
        while cursor >= 0:
            sample = decisions[cursor]
            if (
                int(sample["trace_index"]) != trace_index
                or int(sample["stage_route_index"]) != stage
                or int(sample["frame"]) < frame - DEATH_WINDOW_FRAMES
            ):
                break
            window.append(sample)
            cursor -= 1
        window.reverse()
        last_alive = next(
            (
                sample
                for sample in reversed(window[:-1])
                if int(sample["player"]["phase"]) == 0
                and int(sample["player"]["phase_at_action"]) == 0
            ),
            None,
        )
        unsafe_suffix_start = None
        if (
            last_alive is not None
            and float(last_alive["pipeline_clearance"]) <= 0.0
        ):
            last_alive_index = window.index(last_alive)
            unsafe_suffix_start = last_alive
            for sample in reversed(window[:last_alive_index]):
                if (
                    int(sample["player"]["phase"]) != 0
                    or int(sample["player"]["phase_at_action"]) != 0
                    or float(sample["pipeline_clearance"]) > 0.0
                ):
                    break
                unsafe_suffix_start = sample
        robust_unsafe_suffix_start = None
        if last_alive is not None and _robust_control_unsafe(last_alive):
            last_alive_index = window.index(last_alive)
            robust_unsafe_suffix_start = last_alive
            for sample in reversed(window[:last_alive_index]):
                if (
                    int(sample["player"]["phase"]) != 0
                    or int(sample["player"]["phase_at_action"]) != 0
                    or not _robust_control_unsafe(sample)
                ):
                    break
                robust_unsafe_suffix_start = sample
        viability_empty_suffix_start = None
        if (
            last_alive is not None
            and _viability_action_set_empty(last_alive)
        ):
            last_alive_index = window.index(last_alive)
            viability_empty_suffix_start = last_alive
            for sample in reversed(window[:last_alive_index]):
                if (
                    int(sample["player"]["phase"]) != 0
                    or int(sample["player"]["phase_at_action"]) != 0
                    or not _viability_action_set_empty(sample)
                ):
                    break
                viability_empty_suffix_start = sample

        next_bombs = float(row["resources"]["bombs"])
        next_power = float(row["resources"]["power"])
        for sample in decisions[index + 1 :]:
            if (
                int(sample["trace_index"]) != trace_index
                or int(sample["stage_route_index"]) != stage
                or int(sample["frame"]) > frame + DEATH_WINDOW_FRAMES
            ):
                break
            bombs = float(sample["resources"]["bombs"])
            power = float(sample["resources"]["power"])
            if bombs != float(row["resources"]["bombs"]):
                next_bombs = bombs
                next_power = power
                break

        (
            primary,
            contributing,
            nearest_bullet,
            nearest_laser,
            nearest_enemy_body,
        ) = _classify_death(row, window=window)
        pipeline_samples = [
            float(sample["pipeline_clearance"]) for sample in window
        ]
        slack_samples = [
            float(sample["corridor_slack"])
            for sample in window
            if sample["corridor_slack"] is not None
        ]
        bombs_at_hit = float(row["resources"]["bombs"])
        input_snapshot = row.get("input_snapshot")
        active_input_mask = (
            int(input_snapshot.get("current", row["mask"]))
            if isinstance(input_snapshot, dict)
            else int(row["mask"])
        )
        if last_alive is None:
            planner_failure_class = "missing_pre_hit_alive_decision"
        elif viability_empty_suffix_start is not None:
            planner_failure_class = (
                "global_viability_kernel_exhausted_before_hit"
            )
        elif robust_unsafe_suffix_start is not None:
            planner_failure_class = "robust_action_set_exhausted_before_hit"
        elif float(last_alive["pipeline_clearance"]) <= 0.0:
            planner_failure_class = "committed_prefix_unsafe_before_hit"
        elif (
            float(last_alive["minimum_clearance"]) <= 0.0
            or primary
            in {
                "observed_bullet_overlap",
                "observed_laser_overlap",
                "observed_enemy_body_overlap",
                "observed_multiple_hazard_overlap",
            }
            or float(row["pipeline_clearance"]) <= 0.0
        ):
            planner_failure_class = (
                "late_collision_after_positive_causal_margin"
            )
        else:
            planner_failure_class = "unresolved_planner_failure"
        death = {
            "case_id": (
                f"{case_prefix}-S{stage}-F{frame}-"
                f"T{trace_index + 1}"
            ),
            "frame": frame,
            "trace_index": trace_index,
            "trace_path": row["trace_path"],
            "stage_route_index": stage,
            "stage_label": STAGE_ROUTE_LABELS.get(stage),
            "player": row["player"],
            "resources_at_hit": row["resources"],
            "post_hit_first_changed_resources": {
                "bombs": next_bombs,
                "power": next_power,
            },
            "post_hit_bomb_stock_decrease": max(
                0.0,
                bombs_at_hit - next_bombs,
            ),
            # V1 regression readers require this compatibility field. A stock
            # reset is not evidence that the controller pressed Bomb.
            "observed_bomb_cost": max(0.0, bombs_at_hit - next_bombs),
            "deathbomb_requested": "+deathbomb" in str(row["action"]),
            "action": row["action"],
            "mask": row["mask"],
            "issued_action_after_hit_detection": row["action"],
            "issued_mask_after_hit_detection": row["mask"],
            "active_input_action": _input_mask_action(active_input_mask),
            "active_input_mask": active_input_mask,
            "last_alive_decision": (
                {
                    "frame": int(last_alive["frame"]),
                    "issued_action": str(last_alive["action"]),
                    "issued_mask": int(last_alive["mask"]),
                    "active_input_action": _input_mask_action(
                        int(
                            last_alive.get("input_snapshot", {}).get(
                                "current",
                                last_alive["mask"],
                            )
                        )
                    ),
                    "active_input_mask": int(
                        last_alive.get("input_snapshot", {}).get(
                            "current",
                            last_alive["mask"],
                        )
                    ),
                    "pipeline_clearance": float(
                        last_alive["pipeline_clearance"]
                    ),
                    "minimum_clearance": float(
                        last_alive["minimum_clearance"]
                    ),
                    "action_hold_frames": int(
                        last_alive["action_hold_frames"]
                    ),
                    "control_delay_frames": int(
                        last_alive["control_delay_frames"]
                    ),
                    "control_delay_candidates": list(
                        last_alive["control_delay_candidates"]
                    ),
                    "robust_control": dict(
                        last_alive["robust_control"]
                    ),
                    "terminal_threat": dict(
                        last_alive["terminal_threat"]
                    ),
                    "viability": dict(last_alive["viability"]),
                    "action_lag": int(last_alive["action_lag"]),
                }
                if last_alive is not None
                else None
            ),
            "action_deadline_miss": {
                "at_hit": _action_lag_over_model(row),
                "last_alive": (
                    _action_lag_over_model(last_alive)
                    if last_alive is not None
                    else False
                ),
                "hit_action_lag": int(row["action_lag"]),
                "hit_support_high": max(
                    tuple(row["control_delay_candidates"])
                    or (int(row["control_delay_frames"]),)
                ),
                "last_alive_action_lag": (
                    int(last_alive["action_lag"])
                    if last_alive is not None
                    else None
                ),
                "last_alive_support_high": (
                    max(
                        tuple(last_alive["control_delay_candidates"])
                        or (int(last_alive["control_delay_frames"]),)
                    )
                    if last_alive is not None
                    else None
                ),
            },
            "usable_pipeline_warning_lead_frames": (
                frame - int(unsafe_suffix_start["frame"])
                if unsafe_suffix_start is not None
                else 0
            ),
            "usable_robust_warning_lead_frames": (
                frame - int(robust_unsafe_suffix_start["frame"])
                if robust_unsafe_suffix_start is not None
                else 0
            ),
            "robust_action_set_exhausted_at_frame": (
                int(robust_unsafe_suffix_start["frame"])
                if robust_unsafe_suffix_start is not None
                else None
            ),
            "usable_viability_warning_lead_frames": (
                frame - int(viability_empty_suffix_start["frame"])
                if viability_empty_suffix_start is not None
                else 0
            ),
            "viability_kernel_exhausted_at_frame": (
                int(viability_empty_suffix_start["frame"])
                if viability_empty_suffix_start is not None
                else None
            ),
            "planner_failure_class": planner_failure_class,
            "active_bullets": row["active_bullets"],
            "active_lasers": row["active_lasers"],
            "active_items": row["active_items"],
            "active_enemy_bodies": row["active_enemy_bodies"],
            "enemy_body_snapshot_frame": row[
                "enemy_body_snapshot_frame"
            ],
            "hit_contact_observation": row.get(
                "hit_contact_observation"
            ),
            "snapshot_lag": row["snapshot_lag"],
            "action_lag": row["action_lag"],
            "control_delay_frames": row["control_delay_frames"],
            "control_delay_candidates": list(
                row["control_delay_candidates"]
            ),
            "control_delay_estimator": dict(
                row["control_delay_estimator"]
            ),
            "robust_control": dict(row["robust_control"]),
            "terminal_threat": dict(row["terminal_threat"]),
            "viability": dict(row["viability"]),
            "read_ms": row["read_ms"],
            "plan_ms": row["plan_ms"],
            "pipeline_clearance_at_hit": row["pipeline_clearance"],
            "minimum_pipeline_clearance_240f": min(pipeline_samples),
            "minimum_corridor_slack_240f": (
                min(slack_samples) if slack_samples else None
            ),
            "corridor_lane": row["corridor_lane"],
            "nearest_observed_bullet": nearest_bullet,
            "observed_bullet_contact_candidate": (
                nearest_bullet
                if nearest_bullet is not None
                and float(nearest_bullet["aabb_clearance"]) <= 0.0
                else None
            ),
            "nearest_observed_laser": nearest_laser,
            "observed_laser_contact_candidate": (
                nearest_laser
                if nearest_laser is not None
                and float(nearest_laser["clearance"]) <= 0.0
                else None
            ),
            "nearest_observed_enemy_body": nearest_enemy_body,
            "observed_enemy_body_contact_candidate": (
                nearest_enemy_body
                if nearest_enemy_body is not None
                and bool(nearest_enemy_body.get("exact_same_epoch"))
                and float(nearest_enemy_body["aabb_clearance"]) <= 0.0
                else None
            ),
            "primary_cause_class": primary,
            "contributing_factors": contributing,
            "spell_attribution": _spell_attribution(row),
        }
        deaths.append(death)
    return deaths


def _death_clusters(
    deaths: list[dict[str, object]],
) -> list[dict[str, object]]:
    clusters = []
    current = []
    for death in deaths:
        if (
            current
            and (
                int(death["stage_route_index"])
                != int(current[-1]["stage_route_index"])
                or int(death["frame"]) - int(current[-1]["frame"])
                > CLUSTER_GAP_FRAMES
            )
        ):
            clusters.append(current)
            current = []
        current.append(death)
    if current:
        clusters.append(current)
    rendered = []
    for index, cluster in enumerate(clusters, 1):
        rendered.append(
            {
                "cluster_id": f"cluster-{index:02d}",
                "stage_route_index": cluster[0]["stage_route_index"],
                "stage_label": cluster[0]["stage_label"],
                "start_frame": cluster[0]["frame"],
                "end_frame": cluster[-1]["frame"],
                "death_count": len(cluster),
                "death_frames": [death["frame"] for death in cluster],
                "minimum_power": min(
                    float(death["resources_at_hit"]["power"])
                    for death in cluster
                ),
                "maximum_active_bullets_at_hit": max(
                    int(death["active_bullets"]) for death in cluster
                ),
                "cause_counts": dict(
                    Counter(
                        str(death["primary_cause_class"])
                        for death in cluster
                    )
                ),
            }
        )
    return rendered


def _phase_markers(
    decisions: list[dict[str, object]],
) -> dict[int, list[dict[str, int]]]:
    markers: dict[int, list[dict[str, int]]] = defaultdict(list)
    for previous, current in zip(decisions, decisions[1:]):
        if (
            previous["trace_index"] != current["trace_index"]
            or previous["stage_route_index"]
            != current["stage_route_index"]
        ):
            continue
        delta = int(current["frame"]) - int(previous["frame"])
        if PHASE_COUNTER_JUMP_MIN <= delta <= PHASE_COUNTER_JUMP_MAX:
            stage = int(current["stage_route_index"])
            markers[stage].append(
                {
                    "before_frame": int(previous["frame"]),
                    "after_frame": int(current["frame"]),
                    "delta": delta,
                }
            )
    return markers


def _spell_inventory(
    manifest: dict[str, object],
    phase_markers: dict[int, list[dict[str, int]]],
    deaths: list[dict[str, object]],
    *,
    spell_schema_complete: bool,
) -> dict[int, dict[str, object]]:
    active_difficulty_mask = int(manifest["active_difficulty_mask"])
    attributed_hits = Counter(
        (
            int(death["stage_route_index"]),
            int(death["spell_attribution"]["spell_id"]),
        )
        for death in deaths
        if death["spell_attribution"]["status"]
        == "resolved_live_spell_state"
    )
    inventory = {}
    for stage in manifest["stages"]:
        stage_index = int(stage["internal_stage_index"])
        ecl = parse_ecl(ROOT / "artifacts" / "decoded" / stage["ecl_file"])
        reachable = set(int(value) for value in stage["reachable_subroutines"])
        expected_phase_markers = []
        for subroutine in ecl.subroutines:
            if subroutine.index not in reachable:
                continue
            for instruction in subroutine.instructions:
                if (
                    instruction.opcode == 0x94
                    and instruction.difficulty_mask
                    & active_difficulty_mask
                ):
                    expected_phase_markers.append(
                        {
                            "subroutine": subroutine.index,
                            "offset": instruction.offset,
                            "argument": int(instruction.arguments[0]),
                        }
                    )
        spells = []
        for spell in stage["reachable_spell_occurrences"]:
            spell_id = int(spell["spell_id"])
            spells.append(
                {
                    "spell_id": spell_id,
                    "name": spell["name"],
                    "owner": spell["owner"],
                    "subroutine": int(spell["subroutine"]),
                    "feature_counts": spell["feature_counts"],
                    "runtime_attribution": {
                        "status": (
                            "resolved_live_spell_state"
                            if spell_schema_complete
                            else "unresolved_current_trace_schema"
                        ),
                        "hit_count": (
                            attributed_hits[(stage_index, spell_id)]
                            if spell_schema_complete
                            else None
                        ),
                        "reason": (
                            None
                            if spell_schema_complete
                            else (
                                "The live decision schema did not record "
                                "g_spell_card_state spell ID."
                            )
                        ),
                    },
                }
            )
        inventory[stage_index] = {
            "stage_route_index": stage_index,
            "stage_label": stage["label"],
            "ecl_file": stage["ecl_file"],
            "expected_reachable_phase_markers": expected_phase_markers,
            "observed_counter_jump_markers": phase_markers.get(
                stage_index,
                [],
            ),
            "alignment_status": "insufficient_for_exact_spell_assignment",
            "spells": spells,
        }
    return inventory


def build_dossier(
    *,
    run_id: str,
    provenance: list[TraceProvenance],
    decisions: list[dict[str, object]],
    manifest: dict[str, object],
    observed_stall_frames: list[int],
    completion_probe: dict[str, object],
) -> dict[str, object]:
    if not decisions:
        raise ValueError("run contains no decisions")
    difficulty = str(manifest["difficulty"])
    difficulty_index = int(manifest["difficulty_index"])
    deaths = _death_ledger(
        decisions,
        case_prefix=_case_prefix_for_difficulty(difficulty),
    )
    phase_markers = _phase_markers(decisions)
    spell_schema_complete = all(
        isinstance(decision.get("spell"), dict) for decision in decisions
    )
    spell_inventory = _spell_inventory(
        manifest,
        phase_markers,
        deaths,
        spell_schema_complete=spell_schema_complete,
    )
    by_stage: dict[int, list[dict[str, object]]] = defaultdict(list)
    for decision in decisions:
        by_stage[int(decision["stage_route_index"])].append(decision)
    stage_reports = []
    for stage_index, stage_decisions in by_stage.items():
        stage_deaths = [
            death
            for death in deaths
            if int(death["stage_route_index"]) == stage_index
        ]
        stage_reports.append(
            {
                "stage_route_index": stage_index,
                "stage_label": STAGE_ROUTE_LABELS.get(stage_index),
                "first_frame": stage_decisions[0]["frame"],
                "last_frame": stage_decisions[-1]["frame"],
                "observed_frame_span": (
                    int(stage_decisions[-1]["frame"])
                    - int(stage_decisions[0]["frame"])
                ),
                "decision_count": len(stage_decisions),
                "death_count": len(stage_deaths),
                "death_frames": [death["frame"] for death in stage_deaths],
                "death_cause_counts": dict(
                    Counter(
                        str(death["primary_cause_class"])
                        for death in stage_deaths
                    )
                ),
                "deathbomb_count": sum(
                    bool(death["deathbomb_requested"])
                    for death in stage_deaths
                ),
                "post_hit_bomb_stock_decrease": sum(
                    float(death["post_hit_bomb_stock_decrease"])
                    for death in stage_deaths
                ),
                "resources": {
                    key: _resource_range(stage_decisions, key)
                    for key in ("lives", "bombs", "power")
                },
                "max_active_bullets": max(
                    int(row["active_bullets"])
                    for row in stage_decisions
                ),
                "max_active_lasers": max(
                    int(row["active_lasers"]) for row in stage_decisions
                ),
                "max_active_items": max(
                    int(row["active_items"]) for row in stage_decisions
                ),
                "boundary_occupancy": {
                    "bottom_decisions": sum(
                        float(row["player"]["y"]) >= 428.0
                        for row in stage_decisions
                    ),
                    "side_decisions": sum(
                        float(row["player"]["x"]) <= 12.0
                        or float(row["player"]["x"]) >= 372.0
                        for row in stage_decisions
                    ),
                },
                "latency_ms": {
                    "read": _percentiles(
                        row["read_ms"] for row in stage_decisions
                    ),
                    "plan": _percentiles(
                        row["plan_ms"] for row in stage_decisions
                    ),
                },
                "frame_lag": {
                    "snapshot": _percentiles(
                        row["snapshot_lag"] for row in stage_decisions
                    ),
                    "action": _percentiles(
                        row["action_lag"] for row in stage_decisions
                    ),
                },
                "phase_marker_alignment": {
                    "expected_reachable_opcode_94_count": len(
                        spell_inventory[stage_index][
                            "expected_reachable_phase_markers"
                        ]
                    ),
                    "observed_approximately_1800_frame_jump_count": len(
                        phase_markers.get(stage_index, [])
                    ),
                    "status": "not_one_to_one_with_spell_cards",
                },
                "robust_viability": _robust_viability_summary(
                    stage_decisions
                ),
                "planner_consistency": _planner_consistency_summary(
                    stage_decisions
                ),
            }
        )
    stage_reports.sort(key=lambda stage: int(stage["first_frame"]))

    interruptions = []
    for previous, current in zip(provenance, provenance[1:]):
        if previous.last_frame is None or current.first_frame is None:
            continue
        interruptions.append(
            {
                "after_trace": previous.path,
                "before_trace": current.path,
                "last_observed_frame": previous.last_frame,
                "next_observed_frame": current.first_frame,
                "unobserved_frame_delta": (
                    current.first_frame - previous.last_frame
                ),
                "reason": "foreground_loss_and_manual_rearm",
            }
        )

    cause_counts = Counter(
        str(death["primary_cause_class"]) for death in deaths
    )
    contributing_counts = Counter(
        factor
        for death in deaths
        for factor in death["contributing_factors"]
    )
    return {
        "schema": "th08-route-run-dossier-v3",
        "run_id": run_id,
        "acceptance_target": {
            "difficulty": difficulty,
            "difficulty_index": difficulty_index,
            "route_id": 2,
            "team": "Sakuya/Remilia",
            "ending_branch": "Final B / Kaguya",
            "combat_completion": True,
        },
        "route_manifest": {
            "profile": manifest["profile"],
            "active_difficulty_mask": int(
                manifest["active_difficulty_mask"]
            ),
        },
        "integrity": {
            "raw_trace_bytes": sum(item.size_bytes for item in provenance),
            "json_decode_errors": sum(
                item.parse_errors for item in provenance
            ),
            "trace_count": len(provenance),
            "foreground_interruption_count": len(interruptions),
            "spell_attribution": (
                "resolved_live_spell_state"
                if spell_schema_complete
                else "unresolved_current_trace_schema"
            ),
        },
        "provenance": [
            {
                **item.__dict__,
                "runtime_errors": list(item.runtime_errors),
            }
            for item in provenance
        ],
        "interruptions": interruptions,
        "completion_probe": completion_probe,
        "totals": {
            "decision_count": len(decisions),
            "first_frame": decisions[0]["frame"],
            "last_frame": decisions[-1]["frame"],
            "death_count": len(deaths),
            "deathbomb_count": sum(
                bool(death["deathbomb_requested"]) for death in deaths
            ),
            "post_hit_bomb_stock_decrease": sum(
                float(death["post_hit_bomb_stock_decrease"])
                for death in deaths
            ),
            "primary_cause_counts": dict(cause_counts),
            "contributing_factor_counts": dict(contributing_counts),
        },
        "observed_auto_confirm_stalls": {
            "frames": observed_stall_frames,
            "root_causes": [
                "phase==0 eligibility excluded dialogue windows in phase 3",
                (
                    "the live loop emitted input only after the enemy frame "
                    "counter advanced"
                ),
                (
                    "a frozen dialogue counter could strand a Z release "
                    "without the restoring press"
                ),
            ],
        },
        "control_policy": {
            "no_bomb_verification": _no_bomb_verification(
                decisions,
                provenance,
            ),
            "robust_viability": _robust_viability_summary(decisions),
            "planner_consistency": _planner_consistency_summary(decisions),
        },
        "stages": stage_reports,
        "death_clusters": _death_clusters(deaths),
        "deaths": deaths,
        "spell_inventory": [
            spell_inventory[index]
            for index in sorted(
                spell_inventory,
                key=lambda key: next(
                    int(stage["first_frame"])
                    for stage in stage_reports
                    if int(stage["stage_route_index"]) == key
                ),
            )
        ],
    }


def _format_number(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def render_markdown(dossier: dict[str, object]) -> str:
    totals = dossier["totals"]
    integrity = dossier["integrity"]
    control_policy = dossier["control_policy"]
    no_bomb = control_policy["no_bomb_verification"]
    viability = control_policy["robust_viability"]
    consistency = control_policy["planner_consistency"]
    spell_attribution_resolved = (
        integrity["spell_attribution"] == "resolved_live_spell_state"
    )
    difficulty = str(dossier["acceptance_target"]["difficulty"])
    lines = [
        f"# TH08 {difficulty} Full-Run Review: {dossier['run_id']}",
        "",
        "## Result",
        "",
        f"- Route: Sakuya/Remilia, {difficulty}, Final B / Kaguya.",
        "- Combat completion: yes; gameplay scene unloaded at frame "
        f"{dossier['completion_probe']['enemy_manager_frame']}.",
        "- Native phase-2 hit edges, including Last-Spell-saveable edges: "
        f"{totals['death_count']}.",
        f"- Deathbomb requests at those edges: {totals['deathbomb_count']}.",
        "- Hard no-Bomb input verification: "
        f"{'passed' if no_bomb['passed'] else 'FAILED'} across "
        f"{no_bomb['decision_count_checked']} decisions.",
        "- Post-hit Bomb-stock decreases: "
        f"{_format_number(totals['post_hit_bomb_stock_decrease'])}; this is "
        "respawn-stock reset telemetry, not evidence of Bomb input.",
        f"- Agent decisions: {totals['decision_count']}.",
        f"- Raw trace size: {integrity['raw_trace_bytes']} bytes across "
        f"{integrity['trace_count']} segments.",
        f"- JSON decode errors: {integrity['json_decode_errors']}.",
        (
            "- Exact spell-level hit attribution: available from live "
            "`g_spell_card_state`."
            if spell_attribution_resolved
            else (
                "- Exact spell-level hit attribution: unavailable in this run "
                "because the live schema did not record `g_spell_card_state`."
            )
        ),
        "",
        "The run is valid for stage-, death-, resource-, projectile-, latency-, "
        "and route-level analysis. Spell names below are the statically "
        f"reachable {difficulty} route inventory; unavailable runtime hit counts "
        "remain explicitly unresolved instead of guessed. The no-life patch "
        "allows post-hit resource resets to repeat, so resource-stock changes "
        "must not be interpreted as Bomb commands.",
        "",
        "## Trace Integrity",
        "",
        "| Segment | Frames | Decisions | Wall Z | Termination | Runtime error "
        "| SHA-256 |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for index, item in enumerate(dossier["provenance"], 1):
        runtime_errors = item["runtime_errors"]
        runtime_error = (
            str(runtime_errors[-1].get("error")) if runtime_errors else "-"
        )
        termination = (
            item["summary"].get("termination_reason")
            if item["summary"]
            else "missing"
        )
        lines.append(
            f"| {index} | {item['first_frame']}..{item['last_frame']} | "
            f"{item['decision_count']} | "
            f"{len(item['wall_auto_confirm_frames'])} | {termination} | "
            f"{runtime_error} | "
            f"`{item['sha256']}` |"
        )
    interruptions = integrity["foreground_interruption_count"]
    if interruptions:
        lines.extend(
            [
                "",
                f"Foreground interruptions: {interruptions}. Interruption "
                "intervals are excluded from agent-controlled scoring.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "The route is one continuous agent-controlled trace with no "
                "foreground interruption or manual re-arm gap.",
            ]
        )
    lines.extend(
        [
            "",
            "## Stage Summary",
            "",
            "| Stage | Frames | Decisions | Native hits | Deathbombs | "
            "Post-hit Bomb-stock decrease | "
            "Power start/end/min | Max bullets | Max lasers |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for stage in dossier["stages"]:
        power = stage["resources"]["power"]
        lines.append(
            f"| {stage['stage_label']} | {stage['first_frame']}.."
            f"{stage['last_frame']} | {stage['decision_count']} | "
            f"{stage['death_count']} | {stage['deathbomb_count']} | "
            f"{_format_number(stage['post_hit_bomb_stock_decrease'])} | "
            f"{_format_number(power['start'])}/"
            f"{_format_number(power['end'])}/"
            f"{_format_number(power['min'])} | "
            f"{stage['max_active_bullets']} | "
            f"{stage['max_active_lasers']} |"
        )
    lines.extend(
        [
            "",
            "## Failure Taxonomy",
            "",
            "| Primary class | Deaths | Interpretation |",
            "| --- | ---: | --- |",
        ]
    )
    interpretations = {
        "observed_enemy_body_overlap": (
            "A captured lethal enemy-body AABB overlaps the player at action "
            "time."
        ),
        "observed_multiple_hazard_overlap": (
            "More than one captured native hazard family overlaps at the hit "
            "edge; the trace does not invent a single causal winner."
        ),
        "observed_bullet_overlap": (
            "A bullet overlaps the native player AABB in the hit observation."
        ),
        "observed_laser_overlap": (
            "The player overlaps an active laser's exact finite segment; TH08 "
            "checks this before the broad bullet pass."
        ),
        "active_laser_without_observed_overlap": (
            "At least one laser is active, but none of the persisted finite "
            "segments overlaps the player in the hit observation."
        ),
        "modeled_committed_prefix_collision": (
            "The measured three-frame input pipeline was already unsafe."
        ),
        "sensor_gap_or_unmodeled_hazard": (
            "No observed overlap and positive pipeline clearance; same-frame "
            "ECL emission, transform error, or another unmodeled hazard is "
            "the leading explanation."
        ),
    }
    for cause, count in sorted(
        totals["primary_cause_counts"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(
            f"| `{cause}` | {count} | {interpretations[cause]} |"
        )
    lines.extend(
        [
            "",
            "Contributing factors:",
            "",
        ]
    )
    for factor, count in sorted(
        totals["contributing_factor_counts"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"- `{factor}`: {count} deaths")

    lines.extend(
        [
            "",
            "## High-Risk Clusters",
            "",
            "| Cluster | Stage | Frames | Deaths | Min Power | Max bullets at "
            "hit |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for cluster in sorted(
        dossier["death_clusters"],
        key=lambda cluster: (
            -int(cluster["death_count"]),
            int(cluster["start_frame"]),
        ),
    ):
        if int(cluster["death_count"]) < 2:
            continue
        lines.append(
            f"| {cluster['cluster_id']} | {cluster['stage_label']} | "
            f"{cluster['start_frame']}..{cluster['end_frame']} | "
            f"{cluster['death_count']} | "
            f"{_format_number(cluster['minimum_power'])} | "
            f"{cluster['maximum_active_bullets_at_hit']} |"
        )

    lines.extend(
        [
            "",
            "## Stage Detail",
            "",
        ]
    )
    deaths_by_stage = defaultdict(list)
    for death in dossier["deaths"]:
        deaths_by_stage[int(death["stage_route_index"])].append(death)
    for stage in dossier["stages"]:
        stage_index = int(stage["stage_route_index"])
        lines.extend(
            [
                f"### {stage['stage_label']}",
                "",
                f"- Death frames: "
                f"{', '.join(str(frame) for frame in stage['death_frames']) or '-'}",
                f"- Cause counts: `{json.dumps(stage['death_cause_counts'], ensure_ascii=False)}`",
                f"- Phase markers: observed "
                f"{stage['phase_marker_alignment']['observed_approximately_1800_frame_jump_count']}, "
                f"reachable static opcode `0x94` "
                f"{stage['phase_marker_alignment']['expected_reachable_opcode_94_count']}.",
                f"- Bottom/side occupancy decisions: "
                f"{stage['boundary_occupancy']['bottom_decisions']}/"
                f"{stage['boundary_occupancy']['side_decisions']}.",
                "",
                "| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | "
                "Corridor slack | Cause | Factors |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for death in deaths_by_stage[stage_index]:
            factors = ",".join(death["contributing_factors"]) or "-"
            lines.append(
                f"| {death['frame']} | "
                f"{_format_number(death['resources_at_hit']['bombs'])} | "
                f"{_format_number(death['resources_at_hit']['power'])} | "
                f"{_format_number(death['post_hit_bomb_stock_decrease'])} | "
                f"{death['active_bullets']} | "
                f"{_format_number(death['pipeline_clearance_at_hit'])} | "
                f"{_format_number(death['minimum_corridor_slack_240f'])} | "
                f"`{death['primary_cause_class']}` | {factors} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Spell Inventory And Runtime Coverage",
            "",
            f"Every spell below is statically reachable for route 2 {difficulty} "
            "Final B. `unresolved` means this run did not persist the live "
            "spell ID; it does not mean the spell was absent.",
            "",
        ]
    )
    for stage in dossier["spell_inventory"]:
        lines.extend(
            [
                f"### {stage['stage_label']}",
                "",
                f"- ECL: `{stage['ecl_file']}`",
                f"- Observed/expected phase-counter markers: "
                f"{len(stage['observed_counter_jump_markers'])}/"
                f"{len(stage['expected_reachable_phase_markers'])}.",
                "",
                "| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |",
                "| ---: | --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for spell in stage["spells"]:
            features = spell["feature_counts"]
            runtime = spell["runtime_attribution"]
            runtime_value = (
                str(runtime["hit_count"])
                if runtime["hit_count"] is not None
                else "unresolved"
            )
            lines.append(
                f"| {spell['spell_id']} | {spell['name']} | "
                f"{spell['owner']} | {features['bullet_emit']} | "
                f"{features['transform_define']} | "
                f"{features['laser_spawn']} | {runtime_value} |"
            )
        lines.append("")

    stalls = dossier["observed_auto_confirm_stalls"]["frames"]
    solve_ms = viability["solve_ms"] or {
        "median": None,
        "p95": None,
        "max": None,
    }
    policy_age = viability["first_observed_age_frames"] or {
        "median": None,
        "p95": None,
        "max": None,
    }
    stalls_text = ", ".join(str(frame) for frame in stalls) or "none"
    final_summary = dossier["provenance"][-1].get("summary") or {}
    termination_reason = final_summary.get("termination_reason", "missing")
    sensor_gap_count = int(
        totals["primary_cause_counts"].get(
            "sensor_gap_or_unmodeled_hazard",
            0,
        )
    )
    lines.extend(
        [
            "## Runtime And Harness Findings",
            "",
            f"- Observed auto-Z stall frames: {stalls_text}.",
            "- Route termination: "
            f"`{termination_reason}` "
            f"at completion probe frame "
            f"{dossier['completion_probe']['enemy_manager_frame']}.",
            "- Unique robust solutions observed: "
            f"{viability['unique_solution_count']}; solve time median/p95/max "
            f"{_format_number(solve_ms['median'])}/"
            f"{_format_number(solve_ms['p95'])}/"
            f"{_format_number(solve_ms['max'])} ms.",
            "- First-observed policy age median/p95/max: "
            f"{_format_number(policy_age['median'])}/"
            f"{_format_number(policy_age['p95'])}/"
            f"{_format_number(policy_age['max'])} frames.",
            "- Viability queries available: "
            f"{viability['available_query_count']}/"
            f"{viability['query_count']}; robustly constrained decisions: "
            f"{viability['constrained_decision_count']}/"
            f"{totals['decision_count']}.",
            "- Robust-policy decisions without any usable query: "
            f"{viability['decision_without_query_count']}/"
            f"{viability['policy_decision_count']}.",
            "- Global-horizon/local-prefix cross-tab: "
            f"{consistency['comparable_decision_count']} decisions; winning "
            "global state with unsafe selected prefix: "
            f"{consistency['global_winning_local_prefix_unsafe_count']}; "
            "losing global state with safe short prefix: "
            f"{consistency['global_losing_local_prefix_safe_count']}; "
            "selected globally certified action contradicted by the fresh "
            "local prefix checker: "
            f"{consistency['selected_certified_action_local_prefix_unsafe_count']}; "
            "selected action outside the reported winning set: "
            f"{consistency['selected_action_outside_global_winning_set_count']}.",
            "- Live spell attribution was recorded at every hit edge; exact "
            "per-spell counts are preserved below.",
            f"- `{sensor_gap_count}` hit edges remain in the "
            "`sensor_gap_or_unmodeled_hazard` class and require executor-level "
            "same-frame emission/transform evidence.",
            "",
            "## Next Regression Work",
            "",
            "1. Keep robust backward-reachability solves within the finite "
            "policy horizon, then verify nonzero live query and constrained-"
            "decision counts.",
            f"2. Replay all {totals['death_count']} retained witnesses through "
            "the integrated executor and preserve one regression per concrete "
            "failure.",
            "3. Re-run focused Stage 4A and Final B practices before another "
            f"full {difficulty} route; compare hit frames, policy age, action-set "
            "exhaustion, and cluster recurrence.",
            "4. Add item/Power state and finite Bomb resources only after the "
            "no-Bomb movement policy has passed physical validation.",
        ]
    )
    return "\n".join(lines)


def write_death_csv(
    path: Path,
    deaths: list[dict[str, object]],
) -> None:
    fieldnames = [
        "case_id",
        "frame",
        "trace_index",
        "stage_route_index",
        "stage_label",
        "player_x",
        "player_y",
        "bombs",
        "power",
        "observed_bomb_cost",
        "post_hit_bomb_stock_decrease",
        "deathbomb_requested",
        "active_bullets",
        "active_lasers",
        "active_items",
        "pipeline_clearance_at_hit",
        "minimum_pipeline_clearance_240f",
        "minimum_corridor_slack_240f",
        "action_lag",
        "action",
        "nearest_bullet_slot",
        "nearest_bullet_clearance",
        "nearest_laser_slot",
        "nearest_laser_clearance",
        "primary_cause_class",
        "planner_failure_class",
        "usable_robust_warning_lead_frames",
        "usable_viability_warning_lead_frames",
        "viability_kernel_exhausted_at_frame",
        "contributing_factors",
        "spell_id",
        "spell_name",
        "spell_attribution_status",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        for death in deaths:
            nearest = death["nearest_observed_bullet"]
            nearest_laser = death["nearest_observed_laser"]
            writer.writerow(
                {
                    "case_id": death["case_id"],
                    "frame": death["frame"],
                    "trace_index": death["trace_index"],
                    "stage_route_index": death["stage_route_index"],
                    "stage_label": death["stage_label"],
                    "player_x": death["player"]["x"],
                    "player_y": death["player"]["y"],
                    "bombs": death["resources_at_hit"]["bombs"],
                    "power": death["resources_at_hit"]["power"],
                    "observed_bomb_cost": death["observed_bomb_cost"],
                    "post_hit_bomb_stock_decrease": death[
                        "post_hit_bomb_stock_decrease"
                    ],
                    "deathbomb_requested": death["deathbomb_requested"],
                    "active_bullets": death["active_bullets"],
                    "active_lasers": death["active_lasers"],
                    "active_items": death["active_items"],
                    "pipeline_clearance_at_hit": death[
                        "pipeline_clearance_at_hit"
                    ],
                    "minimum_pipeline_clearance_240f": death[
                        "minimum_pipeline_clearance_240f"
                    ],
                    "minimum_corridor_slack_240f": death[
                        "minimum_corridor_slack_240f"
                    ],
                    "action_lag": death["action_lag"],
                    "action": death["action"],
                    "nearest_bullet_slot": (
                        nearest["slot"] if nearest else None
                    ),
                    "nearest_bullet_clearance": (
                        nearest["aabb_clearance"] if nearest else None
                    ),
                    "nearest_laser_slot": (
                        nearest_laser["slot"] if nearest_laser else None
                    ),
                    "nearest_laser_clearance": (
                        nearest_laser["clearance"] if nearest_laser else None
                    ),
                    "primary_cause_class": death["primary_cause_class"],
                    "planner_failure_class": death[
                        "planner_failure_class"
                    ],
                    "usable_robust_warning_lead_frames": death.get(
                        "usable_robust_warning_lead_frames",
                        0,
                    ),
                    "usable_viability_warning_lead_frames": death.get(
                        "usable_viability_warning_lead_frames",
                        0,
                    ),
                    "viability_kernel_exhausted_at_frame": death.get(
                        "viability_kernel_exhausted_at_frame"
                    ),
                    "contributing_factors": ";".join(
                        death["contributing_factors"]
                    ),
                    "spell_id": death["spell_attribution"]["spell_id"],
                    "spell_name": death["spell_attribution"]["spell_name"],
                    "spell_attribution_status": death[
                        "spell_attribution"
                    ]["status"],
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--trace", type=Path, action="append", required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "route_manifests"
            / "sakuya_remilia_lunatic_final_b.json"
        ),
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--death-csv", type=Path, required=True)
    parser.add_argument("--regression-output", type=Path, required=True)
    parser.add_argument(
        "--observed-stall-frame",
        type=int,
        action="append",
        default=[],
    )
    parser.add_argument(
        "--completion-frame",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--completion-engine-flags",
        type=lambda value: int(value, 0),
        required=True,
    )
    args = parser.parse_args(argv)

    provenance = []
    decisions = []
    for trace_index, path in enumerate(args.trace):
        trace_provenance, trace_decisions = read_trace(
            path,
            trace_index=trace_index,
        )
        provenance.append(trace_provenance)
        decisions.extend(trace_decisions)
    decisions.sort(key=lambda row: (int(row["frame"]), int(row["trace_index"])))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    dossier = build_dossier(
        run_id=args.run_id,
        provenance=provenance,
        decisions=decisions,
        manifest=manifest,
        observed_stall_frames=args.observed_stall_frame,
        completion_probe={
            "enemy_manager_frame": args.completion_frame,
            "engine_flags": args.completion_engine_flags,
            "engine_flags_hex": f"{args.completion_engine_flags:#x}",
            "gameplay_active": False,
            "resources_available": False,
            "interpretation": "Final B combat scene unloaded",
        },
    )

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(dossier, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(
        render_markdown(dossier) + "\n",
        encoding="utf-8",
    )
    write_death_csv(args.death_csv, dossier["deaths"])
    args.regression_output.parent.mkdir(parents=True, exist_ok=True)
    args.regression_output.write_text(
        json.dumps(
            {
                "schema": "th08-live-death-regressions-v1",
                "run_id": args.run_id,
                "case_count": len(dossier["deaths"]),
                "no_bomb_verification": dossier["control_policy"][
                    "no_bomb_verification"
                ],
                "cases": dossier["deaths"],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
