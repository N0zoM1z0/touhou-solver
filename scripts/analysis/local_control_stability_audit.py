#!/usr/bin/env python3
"""Measure short-horizon TH08 command and native-input oscillation.

The report deliberately separates desired/issued input from native active
input.  A command reversal is not treated as physical motion until
``input_snapshot.current`` shows it, and old traces without the explicit
``planner_objective`` or ``planner_guidance`` fields are never classified as
objective-free idle or globally unconstrained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

MOVEMENT_FOCUS_MASK = 0xF4
LEFT = 0x40
RIGHT = 0x80
DEFAULT_TARGET_X = 192.0
DEFAULT_TARGET_Y = 400.0


@dataclass(frozen=True)
class DirectionSample:
    ordinal: int
    frame: int
    gameplay_epoch: int
    x: float
    y: float
    desired_mask: int
    active_mask: int
    desired_horizontal: int
    active_horizontal: int
    controllable: bool
    prehit: bool
    open_hazards: bool
    hard_slack: bool
    objective_known: bool
    default_only_objective: bool
    settled_default_target: bool
    guidance_known: bool
    guidance_horizontally_unconstrained: bool
    inertia_known: bool
    inertia_enabled: bool
    corridor_context_changed: bool
    corridor_target_x: float | None
    active_bullets: int
    active_lasers: int
    active_enemy_bodies: int
    robust_min_clearance: float
    action: str


def horizontal_sign(mask: int) -> int:
    left = bool(mask & LEFT)
    right = bool(mask & RIGHT)
    if left == right:
        return 0
    return -1 if left else 1


def _finite_float(value: object, default: float) -> float:
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return default
    return converted if math.isfinite(converted) else default


def _action_horizontal_sign(action: str) -> int:
    components = action.split("_")
    if "left" in components:
        return -1
    if "right" in components:
        return 1
    return 0


def _sample_from_row(
    row: dict[str, object],
    *,
    ordinal: int,
    slack_clearance: float,
    settled_radius: float,
) -> DirectionSample | None:
    if row.get("kind") != "decision":
        return None
    player = row.get("player")
    input_snapshot = row.get("input_snapshot")
    if not isinstance(player, dict) or not isinstance(input_snapshot, dict):
        return None
    robust = row.get("robust_control")
    terminal = row.get("terminal_threat")
    deadline = row.get("deadline_guard")
    robust = robust if isinstance(robust, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    deadline = deadline if isinstance(deadline, dict) else {}
    desired_mask = int(row.get("mask", 0)) & MOVEMENT_FOCUS_MASK
    active_mask = int(input_snapshot.get("current", 0)) & MOVEMENT_FOCUS_MASK
    active_bullets = int(row.get("active_bullets", 0))
    active_lasers = int(row.get("active_lasers", 0))
    active_enemy_bodies = int(row.get("active_enemy_bodies", 0))
    robust_clearance = _finite_float(
        robust.get("min_clearance"),
        float("-inf"),
    )
    terminal_clearance = _finite_float(
        terminal.get("min_clearance"),
        float("-inf"),
    )
    hard_slack = bool(
        int(robust.get("worst_collisions", 1)) == 0
        and robust_clearance >= slack_clearance
        and int(terminal.get("collisions", 1)) == 0
        and terminal_clearance >= slack_clearance
    )
    open_hazards = (
        active_bullets == 0
        and active_lasers == 0
        and active_enemy_bodies == 0
    )
    objective_known = "planner_objective" in row
    objective = row.get("planner_objective")
    objective = objective if isinstance(objective, dict) else {}
    corridor_target = objective.get("corridor_target")
    corridor_target = (
        corridor_target if isinstance(corridor_target, dict) else None
    )
    corridor_target_x = (
        _finite_float(corridor_target.get("x"), float("nan"))
        if corridor_target is not None
        else None
    )
    if corridor_target_x is not None and not math.isfinite(
        corridor_target_x
    ):
        corridor_target_x = None
    item_objective = bool(
        objective.get("item_objectives_enabled")
        and int(objective.get("active_items", 0)) > 0
    )
    damage_objective = bool(
        objective.get("damage_action_authority")
        and objective.get("damageable")
        and objective.get("damage_target_x") is not None
    )
    default_only_objective = bool(
        objective_known
        and corridor_target is None
        and not item_objective
        and not damage_objective
    )
    guidance_known = "planner_guidance" in row
    guidance = row.get("planner_guidance")
    guidance = guidance if isinstance(guidance, dict) else {}
    allowed_first_actions = guidance.get("allowed_first_actions")
    if allowed_first_actions is None:
        guidance_horizontally_unconstrained = guidance_known
    elif isinstance(allowed_first_actions, (list, tuple)):
        allowed_signs = {
            _action_horizontal_sign(str(action))
            for action in allowed_first_actions
        }
        guidance_horizontally_unconstrained = (
            -1 in allowed_signs and 1 in allowed_signs
        )
    else:
        guidance_horizontally_unconstrained = False
    inertia_known = "preserve_previous_direction_inertia" in objective
    inertia_enabled = bool(
        objective.get("preserve_previous_direction_inertia")
    )
    corridor_context_changed = bool(
        objective.get("corridor_context_changed")
    )
    x = _finite_float(player.get("x"), float("nan"))
    y = _finite_float(player.get("y"), float("nan"))
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    settled_default_target = bool(
        default_only_objective
        and math.hypot(x - DEFAULT_TARGET_X, y - DEFAULT_TARGET_Y)
        <= settled_radius
    )
    phase = int(player.get("phase", -1))
    phase_at_action = int(player.get("phase_at_action", phase))
    controllable = bool(
        phase == 0
        and phase_at_action == 0
        and not deadline.get("missed", False)
    )
    return DirectionSample(
        ordinal=ordinal,
        frame=int(row["frame"]),
        gameplay_epoch=int(row.get("gameplay_epoch", 0)),
        x=x,
        y=y,
        desired_mask=desired_mask,
        active_mask=active_mask,
        desired_horizontal=horizontal_sign(desired_mask),
        active_horizontal=horizontal_sign(active_mask),
        controllable=controllable,
        prehit=int(row.get("hit_count", 0)) == 0,
        open_hazards=open_hazards,
        hard_slack=hard_slack,
        objective_known=objective_known,
        default_only_objective=default_only_objective,
        settled_default_target=settled_default_target,
        guidance_known=guidance_known,
        guidance_horizontally_unconstrained=(
            guidance_horizontally_unconstrained
        ),
        inertia_known=inertia_known,
        inertia_enabled=inertia_enabled,
        corridor_context_changed=corridor_context_changed,
        corridor_target_x=corridor_target_x,
        active_bullets=active_bullets,
        active_lasers=active_lasers,
        active_enemy_bodies=active_enemy_bodies,
        robust_min_clearance=robust_clearance,
        action=str(row.get("action", "")),
    )


def _direction_reversals(
    samples: list[DirectionSample],
    *,
    field: str,
    maximum_gap_frames: int,
) -> list[dict[str, object]]:
    reversals: list[dict[str, object]] = []
    last_nonzero_index: int | None = None
    for index, sample in enumerate(samples):
        sign = int(getattr(sample, field))
        if not sample.controllable or sign == 0:
            continue
        if last_nonzero_index is not None:
            previous = samples[last_nonzero_index]
            previous_sign = int(getattr(previous, field))
            same_epoch = previous.gameplay_epoch == sample.gameplay_epoch
            gap = sample.frame - previous.frame
            if (
                same_epoch
                and sign == -previous_sign
                and 0 < gap <= maximum_gap_frames
            ):
                interval = samples[last_nonzero_index:index + 1]
                reversals.append(
                    {
                        "from_index": last_nonzero_index,
                        "to_index": index,
                        "from_frame": previous.frame,
                        "to_frame": sample.frame,
                        "frame_gap": gap,
                        "from_sign": previous_sign,
                        "to_sign": sign,
                        "prehit": previous.prehit and sample.prehit,
                        "open_slack": all(
                            point.open_hazards and point.hard_slack
                            for point in interval
                        ),
                        "default_only_objective": all(
                            point.default_only_objective
                            for point in interval
                        ),
                        "settled_default_target": all(
                            point.settled_default_target
                            for point in interval
                        ),
                        "objective_known": all(
                            point.objective_known for point in interval
                        ),
                        "guidance_known": all(
                            point.guidance_known for point in interval
                        ),
                        "guidance_horizontally_unconstrained": all(
                            point.guidance_horizontally_unconstrained
                            for point in interval
                        ),
                        "inertia_known": all(
                            point.inertia_known for point in interval
                        ),
                        "inertia_enabled": all(
                            point.inertia_enabled for point in interval
                        ),
                        "corridor_context_changed": any(
                            point.corridor_context_changed
                            for point in interval
                        ),
                    }
                )
        last_nonzero_index = index
    return reversals


def _ping_pong_episodes(
    samples: list[DirectionSample],
    reversals: list[dict[str, object]],
    *,
    maximum_span_frames: int,
    example_count: int,
) -> tuple[dict[str, int], list[dict[str, object]]]:
    counts = {
        "count": 0,
        "prehit_count": 0,
        "open_slack_count": 0,
        "default_only_objective_count": 0,
        "settled_default_target_count": 0,
        "objective_unknown_count": 0,
        "corridor_target_present_count": 0,
        "guidance_unknown_count": 0,
        "guidance_horizontally_unconstrained_count": 0,
        "inertia_enabled_count": 0,
        "corridor_context_changed_count": 0,
    }
    examples: list[dict[str, object]] = []
    for first, second in zip(reversals, reversals[1:]):
        if (
            first["to_sign"] != second["from_sign"]
            or first["from_sign"] != second["to_sign"]
            or second["to_frame"] - first["from_frame"]
            > maximum_span_frames
        ):
            continue
        start = int(first["from_index"])
        end = int(second["to_index"])
        interval = samples[start:end + 1]
        if not interval:
            continue
        path_length = sum(
            abs(right.x - left.x)
            for left, right in zip(interval, interval[1:])
        )
        net_displacement = abs(interval[-1].x - interval[0].x)
        cancellation_ratio = (
            0.0
            if path_length <= 1e-9
            else max(0.0, 1.0 - net_displacement / path_length)
        )
        prehit = all(point.prehit for point in interval)
        open_slack = all(
            point.open_hazards and point.hard_slack for point in interval
        )
        default_only = all(
            point.default_only_objective for point in interval
        )
        settled = all(point.settled_default_target for point in interval)
        objective_known = all(point.objective_known for point in interval)
        target_present = any(
            point.corridor_target_x is not None for point in interval
        )
        guidance_known = all(point.guidance_known for point in interval)
        guidance_horizontally_unconstrained = all(
            point.guidance_horizontally_unconstrained
            for point in interval
        )
        inertia_enabled = all(
            point.inertia_known and point.inertia_enabled
            for point in interval
        )
        corridor_context_changed = any(
            point.corridor_context_changed for point in interval
        )
        counts["count"] += 1
        counts["prehit_count"] += int(prehit)
        counts["open_slack_count"] += int(open_slack)
        counts["default_only_objective_count"] += int(default_only)
        counts["settled_default_target_count"] += int(settled)
        counts["objective_unknown_count"] += int(not objective_known)
        counts["corridor_target_present_count"] += int(target_present)
        counts["guidance_unknown_count"] += int(not guidance_known)
        counts["guidance_horizontally_unconstrained_count"] += int(
            guidance_horizontally_unconstrained
        )
        counts["inertia_enabled_count"] += int(inertia_enabled)
        counts["corridor_context_changed_count"] += int(
            corridor_context_changed
        )
        if len(examples) < example_count:
            examples.append(
                {
                    "start_frame": interval[0].frame,
                    "middle_frame": int(first["to_frame"]),
                    "end_frame": interval[-1].frame,
                    "span_frames": interval[-1].frame - interval[0].frame,
                    "direction_pattern": (
                        int(first["from_sign"]),
                        int(first["to_sign"]),
                        int(second["to_sign"]),
                    ),
                    "x_start": interval[0].x,
                    "x_min": min(point.x for point in interval),
                    "x_max": max(point.x for point in interval),
                    "x_end": interval[-1].x,
                    "x_path_length": path_length,
                    "x_net_displacement": net_displacement,
                    "x_cancellation_ratio": cancellation_ratio,
                    "prehit": prehit,
                    "open_slack": open_slack,
                    "default_only_objective": default_only,
                    "settled_default_target": settled,
                    "objective_known": objective_known,
                    "corridor_target_present": target_present,
                    "guidance_known": guidance_known,
                    "guidance_horizontally_unconstrained": (
                        guidance_horizontally_unconstrained
                    ),
                    "inertia_enabled": inertia_enabled,
                    "corridor_context_changed": corridor_context_changed,
                    "actions": tuple(
                        point.action for point in interval
                    ),
                }
            )
    return counts, examples


def _sequence_metrics(
    samples: list[DirectionSample],
    *,
    field: str,
    maximum_reversal_gap_frames: int,
    maximum_ping_pong_span_frames: int,
    example_count: int,
) -> dict[str, object]:
    reversals = _direction_reversals(
        samples,
        field=field,
        maximum_gap_frames=maximum_reversal_gap_frames,
    )
    ping_pong, examples = _ping_pong_episodes(
        samples,
        reversals,
        maximum_span_frames=maximum_ping_pong_span_frames,
        example_count=example_count,
    )
    controllable_frames = [
        sample.frame for sample in samples if sample.controllable
    ]
    physical_span = (
        max(controllable_frames) - min(controllable_frames)
        if controllable_frames
        else 0
    )
    signs = [
        int(getattr(sample, field))
        for sample in samples
        if sample.controllable
    ]
    return {
        "controllable_samples": len(signs),
        "left_samples": sum(sign < 0 for sign in signs),
        "neutral_samples": sum(sign == 0 for sign in signs),
        "right_samples": sum(sign > 0 for sign in signs),
        "physical_frame_span": physical_span,
        "reversals": {
            "count": len(reversals),
            "per_1000_physical_frames": (
                0.0
                if physical_span <= 0
                else len(reversals) * 1000.0 / physical_span
            ),
            "prehit_count": sum(
                bool(reversal["prehit"]) for reversal in reversals
            ),
            "open_slack_count": sum(
                bool(reversal["open_slack"]) for reversal in reversals
            ),
            "default_only_objective_count": sum(
                bool(reversal["default_only_objective"])
                for reversal in reversals
            ),
            "settled_default_target_count": sum(
                bool(reversal["settled_default_target"])
                for reversal in reversals
            ),
            "objective_unknown_count": sum(
                not bool(reversal["objective_known"])
                for reversal in reversals
            ),
            "guidance_unknown_count": sum(
                not bool(reversal["guidance_known"])
                for reversal in reversals
            ),
            "guidance_horizontally_unconstrained_count": sum(
                bool(reversal["guidance_horizontally_unconstrained"])
                for reversal in reversals
            ),
            "inertia_enabled_count": sum(
                bool(reversal["inertia_enabled"])
                for reversal in reversals
            ),
            "corridor_context_changed_count": sum(
                bool(reversal["corridor_context_changed"])
                for reversal in reversals
            ),
        },
        "ping_pong": ping_pong,
        "examples": examples,
    }


def _sampled_explicit_root_switches(
    rows: list[dict[str, object]],
    samples: list[DirectionSample],
    *,
    example_count: int,
) -> dict[str, object]:
    by_ordinal = {sample.ordinal: sample for sample in samples}
    counts = {
        "complete_shadow_samples": 0,
        "opposed_horizontal_writes": 0,
        "held_action_hard_safe": 0,
        "selected_action_hard_safe": 0,
        "both_actions_hard_safe": 0,
        "selected_hard_better": 0,
        "hard_equivalent_soft_switch": 0,
        "default_only_hard_equivalent_soft_switch": 0,
        "prehit_hard_equivalent_soft_switch": 0,
        "held_globally_allowed": 0,
        "both_actions_globally_allowed": 0,
        "hard_equivalent_selected_cvar_better": 0,
        "hard_equivalent_selected_cvar_equal": 0,
        "hard_equivalent_selected_cvar_worse": 0,
        "hard_equivalent_selected_clearance_better": 0,
        "hard_equivalent_selected_clearance_equal": 0,
        "hard_equivalent_selected_clearance_worse": 0,
    }
    examples: list[dict[str, object]] = []
    for ordinal, row in enumerate(rows):
        sample = by_ordinal.get(ordinal)
        if sample is None:
            continue
        shadow = row.get("local_pipeline_certificate_shadow")
        root = row.get("local_pipeline_root")
        if (
            not isinstance(shadow, dict)
            or shadow.get("status") != "complete"
            or not isinstance(root, dict)
        ):
            continue
        counts["complete_shadow_samples"] += 1
        held_sign = horizontal_sign(int(root.get("held_desired_mask", 0)))
        selected_sign = sample.desired_horizontal
        if held_sign == 0 or selected_sign != -held_sign:
            continue
        counts["opposed_horizontal_writes"] += 1
        certificates = {
            str(certificate.get("action")): certificate
            for certificate in shadow.get("certificates", ())
            if isinstance(certificate, dict)
        }
        held_action = str(root.get("held_desired_action", ""))
        selected_action = sample.action.split("+", 1)[0]
        guidance = row.get("planner_guidance")
        guidance = guidance if isinstance(guidance, dict) else {}
        allowed = guidance.get("allowed_first_actions")
        if sample.guidance_known and allowed is None:
            held_globally_allowed = True
            selected_globally_allowed = True
        elif isinstance(allowed, (list, tuple)):
            held_globally_allowed = held_action in allowed
            selected_globally_allowed = selected_action in allowed
        else:
            held_globally_allowed = False
            selected_globally_allowed = False
        counts["held_globally_allowed"] += int(held_globally_allowed)
        counts["both_actions_globally_allowed"] += int(
            held_globally_allowed and selected_globally_allowed
        )
        held = certificates.get(held_action)
        selected = certificates.get(selected_action)
        if held is None or selected is None:
            continue

        def label(certificate: dict[str, object]) -> tuple[int, float]:
            collisions = int(certificate.get("worst_collisions", 1))
            clearance = _finite_float(
                certificate.get("min_clearance"),
                float("-inf"),
            )
            return collisions, max(-clearance, 0.0)

        held_label = label(held)
        selected_label = label(selected)
        held_safe = held_label == (0, 0.0)
        selected_safe = selected_label == (0, 0.0)
        hard_better = selected_label < held_label
        hard_equivalent = selected_label == held_label
        counts["held_action_hard_safe"] += int(held_safe)
        counts["selected_action_hard_safe"] += int(selected_safe)
        counts["both_actions_hard_safe"] += int(
            held_safe and selected_safe
        )
        counts["selected_hard_better"] += int(hard_better)
        counts["hard_equivalent_soft_switch"] += int(hard_equivalent)
        counts[
            "default_only_hard_equivalent_soft_switch"
        ] += int(hard_equivalent and sample.default_only_objective)
        counts["prehit_hard_equivalent_soft_switch"] += int(
            hard_equivalent and sample.prehit
        )
        if hard_equivalent:
            held_cvar = _finite_float(
                held.get("cvar_risk"),
                float("inf"),
            )
            selected_cvar = _finite_float(
                selected.get("cvar_risk"),
                float("inf"),
            )
            cvar_difference = selected_cvar - held_cvar
            counts[
                "hard_equivalent_selected_cvar_better"
                if cvar_difference < -1e-6
                else (
                    "hard_equivalent_selected_cvar_worse"
                    if cvar_difference > 1e-6
                    else "hard_equivalent_selected_cvar_equal"
                )
            ] += 1
            held_clearance = _finite_float(
                held.get("min_clearance"),
                float("-inf"),
            )
            selected_clearance = _finite_float(
                selected.get("min_clearance"),
                float("-inf"),
            )
            clearance_difference = selected_clearance - held_clearance
            counts[
                "hard_equivalent_selected_clearance_better"
                if clearance_difference > 1e-6
                else (
                    "hard_equivalent_selected_clearance_worse"
                    if clearance_difference < -1e-6
                    else "hard_equivalent_selected_clearance_equal"
                )
            ] += 1
        if hard_equivalent and len(examples) < example_count:
            examples.append(
                {
                    "frame": sample.frame,
                    "prehit": sample.prehit,
                    "held_action": held_action,
                    "selected_action": selected_action,
                    "held_certificate": held,
                    "selected_certificate": selected,
                    "default_only_objective": (
                        sample.default_only_objective
                    ),
                    "corridor_target_x": sample.corridor_target_x,
                    "active_bullets": sample.active_bullets,
                    "active_lasers": sample.active_lasers,
                    "active_enemy_bodies": sample.active_enemy_bodies,
                    "selected_local_slack": sample.hard_slack,
                    "held_globally_allowed": held_globally_allowed,
                    "selected_globally_allowed": (
                        selected_globally_allowed
                    ),
                }
            )
    return {
        "claim_boundary": (
            "periodic post-issue samples only; hard-equivalent means the "
            "explicit-root short certificate did not force the opposed write, "
            "not that the full-horizon objective was wrong"
        ),
        **counts,
        "examples": examples,
    }


def analyze_rows(
    rows: Iterable[dict[str, object]],
    *,
    slack_clearance: float = 24.0,
    settled_radius: float = 8.0,
    maximum_reversal_gap_frames: int = 12,
    maximum_ping_pong_span_frames: int = 30,
    example_count: int = 12,
) -> dict[str, object]:
    rows = list(rows)
    samples = [
        sample
        for ordinal, row in enumerate(rows)
        if (
            sample := _sample_from_row(
                row,
                ordinal=ordinal,
                slack_clearance=slack_clearance,
                settled_radius=settled_radius,
            )
        )
        is not None
    ]
    desired_changes = 0
    active_changes = 0
    for previous, current in zip(samples, samples[1:]):
        if previous.gameplay_epoch != current.gameplay_epoch:
            continue
        desired_changes += int(
            previous.desired_mask != current.desired_mask
        )
        active_changes += int(previous.active_mask != current.active_mask)
    controllable = [sample for sample in samples if sample.controllable]
    return {
        "decision_samples": len(samples),
        "controllable_samples": len(controllable),
        "prehit_controllable_samples": sum(
            sample.prehit for sample in controllable
        ),
        "objective_schema_samples": sum(
            sample.objective_known for sample in samples
        ),
        "guidance_schema_samples": sum(
            sample.guidance_known for sample in samples
        ),
        "inertia_schema_samples": sum(
            sample.inertia_known for sample in samples
        ),
        "open_slack_controllable_samples": sum(
            sample.open_hazards and sample.hard_slack
            for sample in controllable
        ),
        "default_only_controllable_samples": sum(
            sample.open_hazards
            and sample.hard_slack
            and sample.default_only_objective
            for sample in controllable
        ),
        "settled_default_target_samples": sum(
            sample.open_hazards
            and sample.hard_slack
            and sample.settled_default_target
            for sample in controllable
        ),
        "desired_active_horizontal_disagreement_samples": sum(
            sample.desired_horizontal != sample.active_horizontal
            for sample in controllable
        ),
        "desired_supported_mask_changes": desired_changes,
        "native_active_supported_mask_changes": active_changes,
        "sampled_explicit_root_opposed_switches": (
            _sampled_explicit_root_switches(
                rows,
                samples,
                example_count=example_count,
            )
        ),
        "desired": _sequence_metrics(
            samples,
            field="desired_horizontal",
            maximum_reversal_gap_frames=(
                maximum_reversal_gap_frames
            ),
            maximum_ping_pong_span_frames=(
                maximum_ping_pong_span_frames
            ),
            example_count=example_count,
        ),
        "native_active": _sequence_metrics(
            samples,
            field="active_horizontal",
            maximum_reversal_gap_frames=(
                maximum_reversal_gap_frames
            ),
            maximum_ping_pong_span_frames=(
                maximum_ping_pong_span_frames
            ),
            example_count=example_count,
        ),
    }


def _read_trace(path: Path) -> tuple[list[dict[str, object]], str]:
    payload = path.read_bytes()
    rows = [
        json.loads(line)
        for line in payload.decode("utf-8").splitlines()
        if line.strip()
    ]
    return rows, hashlib.sha256(payload).hexdigest()


def audit_trace(
    path: Path,
    *,
    slack_clearance: float,
    settled_radius: float,
    maximum_reversal_gap_frames: int,
    maximum_ping_pong_span_frames: int,
    example_count: int,
) -> dict[str, object]:
    rows, digest = _read_trace(path)
    return {
        "trace": str(path),
        "trace_sha256": digest,
        **analyze_rows(
            rows,
            slack_clearance=slack_clearance,
            settled_radius=settled_radius,
            maximum_reversal_gap_frames=(
                maximum_reversal_gap_frames
            ),
            maximum_ping_pong_span_frames=(
                maximum_ping_pong_span_frames
            ),
            example_count=example_count,
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--slack-clearance", type=float, default=24.0)
    parser.add_argument("--settled-radius", type=float, default=8.0)
    parser.add_argument(
        "--maximum-reversal-gap-frames",
        type=int,
        default=12,
    )
    parser.add_argument(
        "--maximum-ping-pong-span-frames",
        type=int,
        default=30,
    )
    parser.add_argument("--example-count", type=int, default=12)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.slack_clearance < 0.0 or not math.isfinite(
        args.slack_clearance
    ):
        raise ValueError("slack clearance must be finite and nonnegative")
    if args.settled_radius < 0.0 or not math.isfinite(
        args.settled_radius
    ):
        raise ValueError("settled radius must be finite and nonnegative")
    if min(
        args.maximum_reversal_gap_frames,
        args.maximum_ping_pong_span_frames,
        args.example_count,
    ) <= 0:
        raise ValueError("audit frame windows and example count must be positive")
    report = {
        "schema": "th08-local-control-stability-audit-v1",
        "claim_boundary": {
            "desired": "controller-selected mask at issue",
            "native_active": (
                "native input_snapshot.current observed before that issue"
            ),
            "objective_free": (
                "only rows with explicit planner_objective telemetry may be "
                "classified as default-only or settled idle"
            ),
        },
        "parameters": {
            "slack_clearance": args.slack_clearance,
            "settled_radius": args.settled_radius,
            "maximum_reversal_gap_frames": (
                args.maximum_reversal_gap_frames
            ),
            "maximum_ping_pong_span_frames": (
                args.maximum_ping_pong_span_frames
            ),
        },
        "traces": [
            audit_trace(
                trace,
                slack_clearance=args.slack_clearance,
                settled_radius=args.settled_radius,
                maximum_reversal_gap_frames=(
                    args.maximum_reversal_gap_frames
                ),
                maximum_ping_pong_span_frames=(
                    args.maximum_ping_pong_span_frames
                ),
                example_count=args.example_count,
            )
            for trace in args.traces
        ],
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
