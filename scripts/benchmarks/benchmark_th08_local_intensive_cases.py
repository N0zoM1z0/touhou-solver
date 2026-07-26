#!/usr/bin/env python3
"""Generated TH08-semantic stress gate for local geometry and selection."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import statistics
import time

import numpy as np

import th08_live_dodge_agent as live
from th08_laser_model import LaserPhase, LaserState
from th08_laser_runtime import Laser
from touhou_control.trajectory import VelocityChange


@dataclass(frozen=True)
class IntensiveCase:
    name: str
    positions_x: np.ndarray
    positions_y: np.ndarray
    bullets: tuple[live.Bullet, ...]
    lasers: tuple[Laser, ...]
    enemy_bodies: tuple[live.EnemyBody, ...]


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[round(0.95 * (len(ordered) - 1))]


def _timing(values: list[float]) -> dict[str, float]:
    return {
        "median_ms": statistics.median(values),
        "p95_ms": _p95(values),
        "max_ms": max(values),
    }


def _changes(
    index: int,
    velocity_x: float,
    velocity_y: float,
) -> tuple[VelocityChange, ...]:
    mode = index % 6
    if mode == 0:
        return (
            VelocityChange(2, 0.0, 0.0),
            VelocityChange(5, velocity_x, velocity_y),
        )
    if mode == 1:
        return (
            VelocityChange(4, -velocity_x, -velocity_y),
        )
    if mode == 2:
        return (
            VelocityChange(3, velocity_y, -velocity_x),
            VelocityChange(7, -velocity_y, velocity_x),
        )
    if mode == 3:
        return (
            VelocityChange(2, 1.5 * velocity_x, 1.5 * velocity_y),
            VelocityChange(6, -0.5 * velocity_x, -0.5 * velocity_y),
        )
    if mode == 4:
        return (
            VelocityChange(5, 0.0, velocity_y),
        )
    return ()


def _bullet_cloud(
    generator: np.random.Generator,
    *,
    count: int,
    distant: bool = False,
) -> tuple[live.Bullet, ...]:
    if distant:
        x = generator.uniform(800.0, 1600.0, count)
        y = generator.uniform(800.0, 1600.0, count)
    else:
        x = generator.uniform(-96.0, 480.0, count)
        y = generator.uniform(-96.0, 544.0, count)
    velocity_x = generator.uniform(-6.0, 6.0, count)
    velocity_y = generator.uniform(-6.0, 6.0, count)
    return tuple(
        live.Bullet(
            x=float(x[index]),
            y=float(y[index]),
            vx=float(velocity_x[index]),
            vy=float(velocity_y[index]),
            half_width=float(generator.uniform(0.5, 12.0)),
            half_height=float(generator.uniform(0.5, 12.0)),
            transform_flags=(0x202 if index % 3 == 0 else 0),
            slot=index,
            speed=float(
                math.hypot(
                    velocity_x[index],
                    velocity_y[index],
                )
            ),
            angle=float(
                math.atan2(
                    velocity_y[index],
                    velocity_x[index],
                )
            ),
            callback_phase_state=index % 5,
            callback_aux_state=index % 3,
            velocity_changes=_changes(
                index,
                float(velocity_x[index]),
                float(velocity_y[index]),
            ),
            trajectory_uncertainty_x=float(index % 5) * 0.125,
            trajectory_uncertainty_y=float(index % 7) * 0.125,
            original_transform_flags=(0x202 if index % 3 == 0 else 0),
        )
        for index in range(count)
    )


def _tangent_bullets(
    positions_x: np.ndarray,
    positions_y: np.ndarray,
    *,
    count: int,
) -> tuple[live.Bullet, ...]:
    epsilons = (-1e-5, 0.0, 1e-5, 0.25, -0.25)
    bullets: list[live.Bullet] = []
    for index in range(count):
        position = index % len(positions_x)
        half_width = 2.0 + (index % 4)
        half_height = 2.0 + ((index // 4) % 4)
        side = (index // len(positions_x)) % 4
        epsilon = epsilons[index % len(epsilons)]
        x = float(positions_x[position])
        y = float(positions_y[position])
        if side == 0:
            x += live.PLAYER_RADIUS + half_width + epsilon
        elif side == 1:
            x -= live.PLAYER_RADIUS + half_width + epsilon
        elif side == 2:
            y += live.PLAYER_RADIUS + half_height + epsilon
        else:
            y -= live.PLAYER_RADIUS + half_height + epsilon
        bullets.append(
            live.Bullet(
                x=x,
                y=y,
                vx=0.0,
                vy=0.0,
                half_width=half_width,
                half_height=half_height,
                transform_flags=(0x200 if index % 5 == 0 else 0),
                slot=index,
            )
        )
    return tuple(bullets)


def _lasers(
    generator: np.random.Generator,
    *,
    count: int,
    distant: bool = False,
    degenerate: bool = False,
    lifecycle: bool = True,
) -> tuple[Laser, ...]:
    output: list[Laser] = []
    for index in range(count):
        if distant:
            origin_x = float(generator.uniform(900.0, 1600.0))
            origin_y = float(generator.uniform(900.0, 1600.0))
        else:
            origin_x = float(generator.uniform(-128.0, 512.0))
            origin_y = float(generator.uniform(-128.0, 576.0))
        angle = float(generator.uniform(-math.pi, math.pi))
        if degenerate and index % 3 == 0:
            tail = float(generator.uniform(-16.0, 16.0))
            head = tail + (0.0 if index % 2 else 1e-7)
        else:
            tail = float(generator.uniform(-64.0, 64.0))
            head = tail + float(generator.uniform(48.0, 800.0))
        half_width = float(generator.uniform(1.0, 18.0))
        state = None
        if lifecycle and index % 4 == 0:
            phase = (
                LaserPhase.WARMUP
                if index % 8 == 0
                else LaserPhase.ACTIVE
            )
            state = LaserState(
                origin_x=origin_x,
                origin_y=origin_y,
                angle=angle,
                tail_distance=tail,
                head_distance=head,
                maximum_length=float(generator.uniform(64.0, 800.0)),
                width=2.0 * half_width,
                speed=float(generator.uniform(-8.0, 12.0)),
                warmup_frames=24,
                active_frames=90,
                fade_frames=24,
                collision_enable_frame=4,
                collision_disable_frame=18,
                flags=index & 3,
                current_width=2.0 * half_width,
                phase=phase,
                timer=index % 20,
                timer_fraction=0.5 if index % 2 else 0.0,
                active=True,
            )
        output.append(
            Laser(
                origin_x=origin_x,
                origin_y=origin_y,
                angle=angle,
                tail=tail,
                head=head,
                half_width=half_width,
                state=state,
                slot=index,
                collision_flag=1,
                uncertainty=float(index % 5) * 0.25,
                uncertainty_per_frame=float(index % 4) * 0.04,
            )
        )
    return tuple(output)


def _bodies(
    generator: np.random.Generator,
    *,
    count: int,
    distant: bool = False,
) -> tuple[live.EnemyBody, ...]:
    return tuple(
        live.EnemyBody(
            pointer=index + 1,
            x=float(
                generator.uniform(800.0, 1200.0)
                if distant
                else generator.uniform(0.0, 384.0)
            ),
            y=float(
                generator.uniform(800.0, 1200.0)
                if distant
                else generator.uniform(16.0, 448.0)
            ),
            vx=float(generator.uniform(-4.0, 4.0)),
            vy=float(generator.uniform(-4.0, 4.0)),
            half_width=float(generator.uniform(2.0, 24.0)),
            half_height=float(generator.uniform(2.0, 24.0)),
            flags=0,
            uncertainty=float(generator.uniform(0.0, 8.0)),
        )
        for index in range(count)
    )


def build_intensive_cases(seed: int = 0xCE0130) -> tuple[IntensiveCase, ...]:
    generator = np.random.default_rng(seed)

    def positions(
        count: int,
        *,
        clustered: bool = False,
    ) -> tuple[np.ndarray, np.ndarray]:
        if clustered:
            return (
                generator.uniform(160.0, 224.0, count).astype(
                    np.float32
                ),
                generator.uniform(256.0, 320.0, count).astype(
                    np.float32
                ),
            )
        return (
            generator.uniform(8.0, 376.0, count).astype(np.float32),
            generator.uniform(16.0, 432.0, count).astype(np.float32),
        )

    live_x, live_y = positions(240)
    clustered_x, clustered_y = positions(240, clustered=True)
    beyond_x, beyond_y = positions(384)
    off_x, off_y = positions(384, clustered=True)
    boundary_x = np.concatenate(
        (
            np.full(64, live.PLAYFIELD_LEFT, dtype=np.float32),
            np.full(64, live.PLAYFIELD_RIGHT, dtype=np.float32),
            np.linspace(
                live.PLAYFIELD_LEFT,
                live.PLAYFIELD_RIGHT,
                128,
                dtype=np.float32,
            ),
        )
    )
    boundary_y = np.concatenate(
        (
            np.linspace(
                live.PLAYFIELD_TOP,
                live.PLAYFIELD_BOTTOM,
                64,
                dtype=np.float32,
            ),
            np.linspace(
                live.PLAYFIELD_BOTTOM,
                live.PLAYFIELD_TOP,
                64,
                dtype=np.float32,
            ),
            np.tile(
                np.asarray(
                    [live.PLAYFIELD_TOP, live.PLAYFIELD_BOTTOM],
                    dtype=np.float32,
                ),
                64,
            ),
        )
    )
    laser_x, laser_y = positions(384)
    return (
        IntensiveCase(
            "native_pool_live_like",
            live_x,
            live_y,
            _bullet_cloud(generator, count=1536),
            _lasers(generator, count=256),
            _bodies(generator, count=8),
        ),
        IntensiveCase(
            "native_pool_reachable_tube",
            clustered_x,
            clustered_y,
            _bullet_cloud(generator, count=1536),
            _lasers(generator, count=256),
            _bodies(generator, count=8),
        ),
        IntensiveCase(
            "beyond_pool_piecewise_transform",
            beyond_x,
            beyond_y,
            _bullet_cloud(generator, count=4096),
            _lasers(generator, count=512),
            _bodies(generator, count=32),
        ),
        IntensiveCase(
            "off_tube_broadphase",
            off_x,
            off_y,
            _bullet_cloud(generator, count=4096, distant=True),
            _lasers(
                generator,
                count=1024,
                distant=True,
                lifecycle=False,
            ),
            _bodies(generator, count=64, distant=True),
        ),
        IntensiveCase(
            "boundary_near_tangent",
            boundary_x,
            boundary_y,
            _tangent_bullets(boundary_x, boundary_y, count=2048),
            _lasers(
                generator,
                count=256,
                degenerate=True,
            ),
            _bodies(generator, count=8),
        ),
        IntensiveCase(
            "laser_degenerate_crossing",
            laser_x,
            laser_y,
            _bullet_cloud(generator, count=512),
            _lasers(
                generator,
                count=2048,
                degenerate=True,
            ),
            (),
        ),
    )


def _finite_maximum_difference(
    left: np.ndarray,
    right: np.ndarray,
) -> float:
    finite = np.isfinite(left) & np.isfinite(right)
    if not np.any(finite):
        return 0.0
    return float(np.max(np.abs(left[finite] - right[finite])))


def _hard_decision(decision: live.Decision) -> tuple[object, ...]:
    return (
        decision.action,
        decision.bomb,
        decision.robust_collisions,
        decision.robust_min_clearance < 0.0,
        decision.local_collisions,
        decision.terminal_threat_collisions,
        decision.terminal_threat_min_clearance < 0.0,
        decision.min_clearance < 0.0,
        decision.preloss_historical_action,
        decision.preloss_selected_from_supplemental,
    )


def evaluate_case(
    case: IntensiveCase,
    *,
    horizon: int,
    timing_samples: int,
) -> dict[str, object]:
    lowering_started_ns = time.perf_counter_ns()
    bullet_frames = live._build_bullet_frames(
        case.bullets,
        horizon=horizon,
        snapshot_lag=2,
    )
    laser_frames = live._build_packed_laser_collision_frames(
        case.lasers,
        horizon=horizon,
    )
    lowering_ms = (
        time.perf_counter_ns() - lowering_started_ns
    ) / 1_000_000.0

    maximum_risk_difference = 0.0
    maximum_clearance_difference = 0.0
    collision_mismatch_count = 0
    clearance_sign_mismatch_count = 0
    batch_invariance_mismatch_count = 0
    for step in range(1, horizon + 1):
        values = {
            "step": 2 + step,
            "bullet_frame": bullet_frames[step - 1],
            "lasers": laser_frames[step - 1],
            "enemy_bodies": case.enemy_bodies,
        }
        reference = live._numpy_hazards_for_positions(
            case.positions_x,
            case.positions_y,
            **values,
        )
        native = live._native_hazards_for_positions(
            case.positions_x,
            case.positions_y,
            **values,
        )
        collision_mismatch_count += int(
            not np.array_equal(reference[1], native[1])
        )
        clearance_sign_mismatch_count += int(
            not np.array_equal(reference[2] <= 0.0, native[2] <= 0.0)
        )
        maximum_risk_difference = max(
            maximum_risk_difference,
            _finite_maximum_difference(reference[0], native[0]),
        )
        maximum_clearance_difference = max(
            maximum_clearance_difference,
            _finite_maximum_difference(reference[2], native[2]),
        )
        if step in (1, horizon):
            probes = np.linspace(
                0,
                len(case.positions_x) - 1,
                8,
                dtype=np.int32,
            )
            for backend, batched in (
                (live._numpy_hazards_for_positions, reference),
                (live._native_hazards_for_positions, native),
            ):
                for probe in probes:
                    isolated = backend(
                        case.positions_x[probe : probe + 1],
                        case.positions_y[probe : probe + 1],
                        **values,
                    )
                    if (
                        int(isolated[1][0]) != int(batched[1][probe])
                        or (
                            float(isolated[2][0]) <= 0.0
                            and float(batched[2][probe]) > 0.0
                        )
                        or (
                            float(isolated[2][0]) > 0.0
                            and float(batched[2][probe]) <= 0.0
                        )
                        or _finite_maximum_difference(
                            isolated[2],
                            batched[2][probe : probe + 1],
                        )
                        > 1e-5
                    ):
                        batch_invariance_mismatch_count += 1

    def sequence(backend: str) -> None:
        function = (
            live._native_hazards_for_positions
            if backend == "native"
            else live._numpy_hazards_for_positions
        )
        for step in range(1, horizon + 1):
            function(
                case.positions_x,
                case.positions_y,
                step=2 + step,
                bullet_frame=bullet_frames[step - 1],
                lasers=laser_frames[step - 1],
                enemy_bodies=case.enemy_bodies,
            )

    sequence("native")
    native_timings: list[float] = []
    for _ in range(timing_samples):
        started_ns = time.perf_counter_ns()
        sequence("native")
        native_timings.append(
            (time.perf_counter_ns() - started_ns) / 1_000_000.0
        )
    started_ns = time.perf_counter_ns()
    sequence("numpy")
    numpy_ms = (
        time.perf_counter_ns() - started_ns
    ) / 1_000_000.0

    decision_bullets = case.bullets[:2048]
    decision_lasers = case.lasers[:256]
    decision_arguments = {
        "player_x": float(case.positions_x[len(case.positions_x) // 2]),
        "player_y": float(case.positions_y[len(case.positions_y) // 2]),
        "bullets": decision_bullets,
        "lasers": decision_lasers,
        "enemy_bodies": case.enemy_bodies[:16],
        "previous_direction": live.LEFT,
        "previous_focus": True,
        "can_bomb": False,
        "snapshot_lag": 1,
        "control_delay_frames": 2,
        "control_delay_candidates": (1, 2, 3),
        "action_hold_frames": 3,
        "horizon": horizon,
        "threat_horizon": horizon,
        "beam_width": 24,
        "target_x": 192.0,
        "target_y": 400.0,
        "target_deadline": horizon + 8,
        "allowed_first_actions": ("stay", "left", "right", "up"),
        "viability_repair_volumes": (
            ("stay", 5),
            ("left", 7),
            ("right", 11),
            ("up", 3),
        ),
        "preloss_continuation_preference": True,
        "preloss_supplemental_beam_width": 4,
    }
    live._configure_local_hazard_backend("numpy")
    live._configure_local_beam_reducer("python")
    reference_decision = live.choose_action(**decision_arguments)
    live._configure_local_hazard_backend("native")
    live._configure_local_beam_reducer("native")
    native_decision = live.choose_action(**decision_arguments)
    end_to_end_equal = (
        _hard_decision(reference_decision)
        == _hard_decision(native_decision)
    )
    passed = bool(
        collision_mismatch_count == 0
        and clearance_sign_mismatch_count == 0
        and maximum_clearance_difference <= 1e-4
        and batch_invariance_mismatch_count == 0
        and end_to_end_equal
    )
    return {
        "name": case.name,
        "position_count": len(case.positions_x),
        "bullet_count": len(case.bullets),
        "laser_count": len(case.lasers),
        "body_count": len(case.enemy_bodies),
        "horizon": horizon,
        "lowering_ms": lowering_ms,
        "native_sequence": _timing(native_timings),
        "numpy_single_sequence_ms": numpy_ms,
        "collision_mismatch_count": collision_mismatch_count,
        "clearance_sign_mismatch_count": (
            clearance_sign_mismatch_count
        ),
        "maximum_clearance_absolute_difference": (
            maximum_clearance_difference
        ),
        "maximum_risk_absolute_difference": maximum_risk_difference,
        "batch_invariance_mismatch_count": (
            batch_invariance_mismatch_count
        ),
        "end_to_end": {
            "reference": _hard_decision(reference_decision),
            "native": _hard_decision(native_decision),
            "equal": end_to_end_equal,
        },
        "passed": passed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=0xCE0130)
    parser.add_argument("--horizon", type=int, default=10)
    parser.add_argument("--timing-samples", type=int, default=10)
    args = parser.parse_args(argv)
    if args.horizon <= 0 or args.timing_samples <= 0:
        raise ValueError("horizon and timing samples must be positive")
    reports = [
        evaluate_case(
            case,
            horizon=args.horizon,
            timing_samples=args.timing_samples,
        )
        for case in build_intensive_cases(args.seed)
    ]
    result = {
        "schema": "th08-local-intensive-cases-v1",
        "boundary": (
            "Generated TH08 bullet piecewise events, transform uncertainty, "
            "executable laser lifecycles, dense packed segments, bodies, "
            "batch composition, native/NumPy geometry, and end-to-end "
            "Python/native local selection. Timing separates lowering from "
            "ten already-lowered geometry queries."
        ),
        "seed": args.seed,
        "reports": reports,
        "passed": all(report["passed"] for report in reports),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
