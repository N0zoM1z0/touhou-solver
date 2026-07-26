#!/usr/bin/env python3
"""Offline ablation of boundary reserve on empty-kernel decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import time
from pathlib import Path

from th08_laser_model import LaserPhase, LaserState
from th08_live_dodge_agent import (
    Bullet,
    EnemyBody,
    Item,
    Laser,
    choose_action,
)
from touhou_control.trajectory import VelocityChange


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _laser_from_trace(values: list[object]) -> Laser:
    state = None
    if len(values) >= 22 and values[7] is not None:
        state = LaserState(
            origin_x=float(values[0]),
            origin_y=float(values[1]),
            angle=float(values[2]),
            tail_distance=float(values[3]),
            head_distance=float(values[4]),
            maximum_length=float(values[7]),
            width=float(values[8]),
            speed=float(values[10]),
            warmup_frames=int(values[15]),
            active_frames=int(values[17]),
            fade_frames=int(values[18]),
            collision_enable_frame=int(values[16]),
            collision_disable_frame=int(values[19]),
            flags=int(values[13]),
            current_width=float(values[9]),
            phase=LaserPhase(int(values[11])),
            timer=int(values[12]),
            timer_fraction=float(values[20]),
            active=True,
        )
    return Laser(
        origin_x=float(values[0]),
        origin_y=float(values[1]),
        angle=float(values[2]),
        tail=float(values[3]),
        head=float(values[4]),
        half_width=float(values[5]),
        state=state,
        slot=int(values[6]),
        collision_flag=int(values[14]) if len(values) > 14 else 0,
        uncertainty=float(values[21]) if len(values) > 21 else 0.0,
        uncertainty_per_frame=(
            float(values[22])
            if len(values) > 22
            else (0.0 if state is not None else 0.08)
        ),
    )


def _bullet_from_trace(values: list[object]) -> Bullet:
    """Reconstruct the gameplay trajectory retained by the live trace."""

    runtime = values[8] if len(values) > 8 else None
    projection = values[9] if len(values) > 9 else None
    diagnostic_runtime = isinstance(runtime, list) and len(runtime) >= 12
    planning_projection = (
        not diagnostic_runtime
        and isinstance(projection, list)
        and len(projection) >= 8
    )
    payload = runtime if diagnostic_runtime else projection
    if diagnostic_runtime:
        callback_phase = int(runtime[12]) if len(runtime) > 12 else 0
        callback_aux = int(runtime[13]) if len(runtime) > 13 else 0
        raw_changes = runtime[14] if len(runtime) > 14 else ()
        uncertainty_x = float(runtime[15]) if len(runtime) > 15 else 0.0
        uncertainty_y = float(runtime[16]) if len(runtime) > 16 else 0.0
    elif planning_projection:
        assert isinstance(projection, list)
        callback_phase = int(projection[3])
        callback_aux = int(projection[4])
        raw_changes = projection[5]
        uncertainty_x = float(projection[6])
        uncertainty_y = float(projection[7])
    else:
        callback_phase = 0
        callback_aux = 0
        raw_changes = ()
        uncertainty_x = 0.0
        uncertainty_y = 0.0
    changes = tuple(
        VelocityChange(
            int(change[0]),
            float(change[1]),
            float(change[2]),
        )
        for change in raw_changes
    )
    return Bullet(
        x=float(values[1]),
        y=float(values[2]),
        vx=float(values[3]),
        vy=float(values[4]),
        half_width=float(values[5]),
        half_height=float(values[6]),
        transform_flags=int(values[7]),
        slot=int(values[0]),
        speed=(
            float(payload[0])
            if isinstance(payload, list) and payload[0] is not None
            else None
        ),
        angle=(
            float(payload[1])
            if isinstance(payload, list) and payload[1] is not None
            else None
        ),
        callback_phase_state=callback_phase,
        callback_aux_state=callback_aux,
        velocity_changes=changes,
        trajectory_uncertainty_x=uncertainty_x,
        trajectory_uncertainty_y=uncertainty_y,
        original_transform_flags=(
            int(payload[2]) if isinstance(payload, list) else 0
        ),
    )


def _replay_decision(
    row: dict[str, object],
    *,
    recovery_control_reserve: bool,
    relax_stale_viability_contradiction: bool = False,
    enforce_fresh_viability_intersection: bool = True,
    viability_safety_actions: tuple[str, ...] = (),
    viability_safety_state_value: float | None = None,
    viability_survival_actions: tuple[str, ...] = (),
    viability_survival_frames: int | None = None,
    viability_survival_bottleneck_margin: float | None = None,
    losing_control_reserve: bool = False,
):
    bullets = tuple(
        _bullet_from_trace(values)
        for values in row.get("nearby_bullets", ())
    )
    lasers = tuple(
        _laser_from_trace(values)
        for values in row.get("lasers", ())
    )
    enemy_bodies = tuple(
        EnemyBody(*values)
        for values in row.get("enemy_bodies", ())
    )
    items = tuple(
        Item(*values)
        for values in row.get("items", ())
    )
    corridor = row["corridor"]
    viability = corridor["viability"]
    target = corridor.get("target")
    input_mask = int(row["input_snapshot"]["current"])
    safe_actions = tuple(viability["safe_actions"])
    return choose_action(
        player_x=float(row["player"]["x"]),
        player_y=float(row["player"]["y"]),
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        items=items,
        power=float(row["resources"]["power"]),
        bombs=float(row["resources"]["bombs"]),
        previous_direction=input_mask & 0xF0,
        previous_focus=bool(input_mask & 0x04),
        can_bomb=False,
        snapshot_lag=int(row["snapshot_lag"]),
        control_delay_frames=int(row["control_delay_frames"]),
        control_delay_candidates=tuple(row["control_delay_candidates"]),
        action_hold_frames=int(row["action_hold_frames"]),
        horizon=10,
        threat_horizon=32,
        target_x=float(target["x"]) if target is not None else None,
        target_y=float(target["y"]) if target is not None else None,
        target_deadline=(
            int(target["deadline"]) if target is not None else None
        ),
        allowed_first_actions=safe_actions or None,
        viability_repair_volumes=tuple(
            viability["repair_volumes"].items()
        ),
        viability_recovery_distances=tuple(
            viability["recovery_distances"].items()
        ),
        viability_position_error=float(
            viability.get("position_error", 0.0)
        ),
        viability_safety_actions=viability_safety_actions,
        viability_safety_state_value=viability_safety_state_value,
        viability_survival_actions=viability_survival_actions,
        viability_survival_frames=viability_survival_frames,
        viability_survival_bottleneck_margin=(
            viability_survival_bottleneck_margin
        ),
        recovery_control_reserve=recovery_control_reserve,
        losing_control_reserve=losing_control_reserve,
        relax_stale_viability_contradiction=(
            relax_stale_viability_contradiction
        ),
        enforce_fresh_viability_intersection=(
            enforce_fresh_viability_intersection
        ),
    )


def _eligible_reserve_row(
    row: dict[str, object],
    *,
    losing_state_reserve: bool,
) -> bool:
    viability = row.get("corridor", {}).get("viability", {})
    if not (
        isinstance(viability, dict)
        and viability.get("support_covers_current", True)
    ):
        return False
    if losing_state_reserve:
        return (
            not viability.get("safe_actions")
            and bool(
                viability.get("repair_volumes")
                or viability.get("recovery_distances")
            )
        )
    return bool(viability.get("recovery_distances"))


def _hard_vector(decision: object) -> tuple[object, ...]:
    return (
        decision.robust_collisions,
        max(-decision.robust_min_clearance, 0.0),
        decision.terminal_threat_collisions,
        max(-decision.terminal_threat_min_clearance, 0.0),
        max(-decision.min_clearance, 0.0),
    )


def _reservoir_sample(
    rows: list[dict[str, object]],
    *,
    seen_count: int,
    sample_count: int,
    generator: random.Random,
    row: dict[str, object],
) -> None:
    if len(rows) < sample_count:
        rows.append(row)
        return
    slot = generator.randrange(seen_count)
    if slot < sample_count:
        rows[slot] = row


def _next_hit_frame(hit_frames: list[int], frame: int) -> int | None:
    return next(
        (hit_frame for hit_frame in hit_frames if hit_frame >= frame),
        None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument(
        "--prehit-window",
        type=int,
        default=0,
        help="retain only decisions this many frames before a native hit",
    )
    parser.add_argument(
        "--losing-state-reserve",
        action="store_true",
        help=(
            "ablate the default-off reserve for empty-kernel repair states; "
            "the default preserves the historical distant-recovery ablation"
        ),
    )
    args = parser.parse_args(argv)
    if args.samples <= 0 or args.prehit_window < 0:
        raise ValueError("sample count must be positive and window nonnegative")

    digest = hashlib.sha256()
    hit_frames: list[int] = []
    with args.trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if row.get("kind") != "decision":
                continue
            if row.get("hit_started"):
                hit_frames.append(int(row["frame"]))
    decisions: list[dict[str, object]] = []
    eligible_count = 0
    generator = random.Random(0xCE0126)
    with args.trace.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("kind") != "decision":
                continue
            frame = int(row["frame"])
            if args.prehit_window and not any(
                0 <= hit_frame - frame <= args.prehit_window
                for hit_frame in hit_frames
            ):
                continue
            if not _eligible_reserve_row(
                row,
                losing_state_reserve=args.losing_state_reserve,
            ):
                continue
            eligible_count += 1
            _reservoir_sample(
                decisions,
                seen_count=eligible_count,
                sample_count=args.samples,
                generator=generator,
                row=row,
            )
    if not decisions:
        raise RuntimeError("trace contains no eligible recovery decisions")

    variants = {False: [], True: []}
    durations = {False: [], True: []}
    for index, row in enumerate(decisions):
        order = (False, True) if index % 2 == 0 else (True, False)
        for enabled in order:
            started = time.perf_counter()
            decision = _replay_decision(
                row,
                recovery_control_reserve=(
                    True if args.losing_state_reserve else enabled
                ),
                losing_control_reserve=(
                    enabled if args.losing_state_reserve else False
                ),
            )
            durations[enabled].append(
                (time.perf_counter() - started) * 1000.0
            )
            variants[enabled].append(decision)

    def summarize(enabled: bool) -> dict[str, object]:
        deficits = [
            decision.viability_control_reserve_deficit
            for decision in variants[enabled]
        ]
        recovery = [
            decision.viability_recovery_distance
            for decision in variants[enabled]
            if decision.viability_recovery_distance is not None
        ]
        return {
            "median_ms": statistics.median(durations[enabled]),
            "p95_ms": _p95(durations[enabled]),
            "selected_reserve_deficit": {
                "median": statistics.median(deficits),
                "p95": _p95(deficits),
                "zero_count": sum(deficit <= 1e-6 for deficit in deficits),
            },
            "selected_recovery_distance": {
                "median": statistics.median(recovery),
                "p95": _p95(recovery),
            }
            if recovery
            else None,
            "robust_collision_count": sum(
                decision.robust_collisions > 0
                for decision in variants[enabled]
            ),
            "negative_robust_clearance_count": sum(
                decision.robust_min_clearance < 0.0
                for decision in variants[enabled]
            ),
            "terminal_collision_count": sum(
                decision.terminal_threat_collisions > 0
                for decision in variants[enabled]
            ),
            "minimum_clearance": {
                "median": statistics.median(
                    decision.min_clearance
                    for decision in variants[enabled]
                ),
                "p05": sorted(
                    decision.min_clearance
                    for decision in variants[enabled]
                )[
                    round(0.05 * (len(variants[enabled]) - 1))
                ],
            },
        }

    action_changes = []
    for row, disabled, enabled in zip(
        decisions,
        variants[False],
        variants[True],
    ):
        if disabled.action == enabled.action:
            continue
        frame = int(row["frame"])
        next_hit_frame = _next_hit_frame(hit_frames, frame)
        action_changes.append(
            {
                "frame": int(row["frame"]),
                "stage_route_index": int(row["stage_route_index"]),
                "next_hit_frame": next_hit_frame,
                "time_to_hit": (
                    next_hit_frame - frame
                    if next_hit_frame is not None
                    else None
                ),
                "disabled": disabled.action,
                "enabled": enabled.action,
                "disabled_reserve_deficit": (
                    disabled.viability_control_reserve_deficit
                ),
                "enabled_reserve_deficit": (
                    enabled.viability_control_reserve_deficit
                ),
            }
        )
    hard_changes = [
        (
            "improved"
            if _hard_vector(enabled) < _hard_vector(disabled)
            else (
                "regressed"
                if _hard_vector(enabled) > _hard_vector(disabled)
                else "equal"
            )
        )
        for disabled, enabled in zip(
            variants[False],
            variants[True],
        )
    ]
    result = {
        "schema": "th08-recovery-control-reserve-benchmark-v2",
        "trace": str(args.trace),
        "trace_sha256": digest.hexdigest(),
        "eligible_count": eligible_count,
        "sample_count": len(decisions),
        "prehit_window": args.prehit_window,
        "reserve_mode": (
            "empty_kernel_repair_and_recovery"
            if args.losing_state_reserve
            else "distant_recovery_only"
        ),
        "scope": (
            "Offline ablation over retained trace-radius hazards and exact "
            "laser lifecycle state; this is not physical survival evidence."
        ),
        "reserve_distance": (
            "unfocused_cardinal_speed * maximum current delay support"
        ),
        "variants": {
            "disabled": summarize(False),
            "enabled": summarize(True),
        },
        "action_change_count": len(action_changes),
        "hard_vector_change_counts": {
            name: hard_changes.count(name)
            for name in ("improved", "equal", "regressed")
        },
        "reserve_deficit_change_counts": {
            "improved": sum(
                float(change["enabled_reserve_deficit"])
                < float(change["disabled_reserve_deficit"])
                for change in action_changes
            ),
            "equal": sum(
                float(change["enabled_reserve_deficit"])
                == float(change["disabled_reserve_deficit"])
                for change in action_changes
            ),
            "regressed": sum(
                float(change["enabled_reserve_deficit"])
                > float(change["disabled_reserve_deficit"])
                for change in action_changes
            ),
        },
        "action_change_stage_counts": {
            str(stage): sum(
                int(change["stage_route_index"]) == stage
                for change in action_changes
            )
            for stage in sorted(
                {
                    int(change["stage_route_index"])
                    for change in action_changes
                }
            )
        },
        "action_changes": action_changes,
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["variants"], indent=2))
    print(f"action changes: {len(action_changes)}/{len(decisions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
