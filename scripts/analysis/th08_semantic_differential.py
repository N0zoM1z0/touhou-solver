#!/usr/bin/env python3
"""Generate, replay, differentially test, time, and shrink TH08-like cases."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import time

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import th08_live_dodge_agent as live
from th08_semantic_cases import (
    FAMILIES,
    SemanticCase,
    generate_cases,
    shrink_case,
)
from th08_time_scale import TH08_UNIT_TIME_SCALE_BITS
from touhou_control import native_backend
from touhou_control.supplemental_local_beam import (
    SupplementalAction,
    SupplementalNode,
    search_supplemental_local_beam,
    search_supplemental_local_beam_native,
)


@dataclass(frozen=True)
class CaseResult:
    identity: str
    family: str
    difficulty: str
    bullet_count: int
    laser_count: int
    body_count: int
    position_count: int
    horizon: int
    lowering_ms: float
    numpy_geometry_ms: float
    native_geometry_ms: float
    python_supplemental_ms: float
    native_supplemental_ms: float
    collision_mismatch_count: int
    clearance_sign_mismatch_count: int
    clearance_mismatch_count: int
    risk_mismatch_count: int
    batch_invariance_mismatch_count: int
    supplemental_mismatch: str | None
    passed: bool


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _summary(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {
        "median": statistics.median(values),
        "p95": _p95(values),
        "max": max(values),
        "mean": statistics.fmean(values),
    }


def _body_fields(
    case: SemanticCase,
) -> tuple[np.ndarray, ...]:
    return tuple(
        np.fromiter(values, dtype=np.float32, count=len(case.enemy_bodies))
        for values in (
            (body.x for body in case.enemy_bodies),
            (body.y for body in case.enemy_bodies),
            (body.vx for body in case.enemy_bodies),
            (body.vy for body in case.enemy_bodies),
            (
                body.half_width + body.uncertainty
                for body in case.enemy_bodies
            ),
            (
                body.half_height + body.uncertainty
                for body in case.enemy_bodies
            ),
        )
    )


def _supplemental_inputs(
    case: SemanticCase,
    bullet_frames: tuple[tuple[np.ndarray, ...], ...],
    laser_frames: tuple[object, ...],
) -> tuple[list[SupplementalNode], list[SupplementalNode], float, float]:
    actions = tuple(
        SupplementalAction(
            action.name,
            action.direction,
            action.dx,
            action.dy,
            action.focused,
        )
        for action in live._PLANNER_ACTIONS
    )
    delayed_mask = case.previous_direction | (
        live.FOCUS if case.previous_focused else 0
    )
    unit_scale_bits = (
        TH08_UNIT_TIME_SCALE_BITS,
    ) * case.control_delay_frames
    prefix = live._control_prefix_hazards(
        player_x=case.player_x,
        player_y=case.player_y,
        input_mask=delayed_mask,
        bullets=case.bullets,
        lasers=case.lasers,
        enemy_bodies=case.enemy_bodies,
        snapshot_lag=0,
        frames=case.control_delay_frames,
        player_scale_bits=unit_scale_bits,
        laser_scale_bits=unit_scale_bits,
    )
    initial_x, initial_y = live._project_player_for_read_lag(
        case.player_x,
        case.player_y,
        delayed_mask,
        case.control_delay_frames,
        player_scale_bits=unit_scale_bits,
    )
    initial = SupplementalNode(
        initial_x,
        initial_y,
        0,
        0,
        float(prefix[0]),
        int(prefix[1]),
        float(prefix[2]),
        float(prefix[2]),
    )
    action_count = len(actions)
    rng = np.random.default_rng(
        np.random.SeedSequence(
            [case.seed & 0xFFFFFFFF, case.index, 0x51A7E]
        )
    )
    certificate_collisions = rng.integers(
        0, 3, action_count, dtype=np.int32
    )
    certificate_minimum = rng.uniform(-8.0, 32.0, action_count)
    survival = rng.integers(0, 2, action_count, dtype=np.uint8)
    safety = rng.integers(0, 2, action_count, dtype=np.uint8)
    recovery = rng.uniform(0.0, 120.0, action_count)
    repair = rng.integers(0, 4096, action_count, dtype=np.int32)
    allowed = frozenset(case.allowed_first_actions)

    def transition(
        node: SupplementalNode,
        action: SupplementalAction,
        x: float,
        y: float,
        step: int,
    ) -> float:
        last = actions[node.last_action]
        risk = live._boundary_risk(x, y)
        if action.direction != last.direction:
            risk += 0.08
        if live._directions_opposed(action.direction, last.direction):
            risk += 24.0
        if action.focused != last.focused:
            risk += 0.12
        if step == 1:
            if action.direction != case.previous_direction:
                risk += 0.08
            if live._directions_opposed(
                action.direction,
                case.previous_direction,
            ):
                risk += 24.0
            if action.focused != case.previous_focused:
                risk += 0.12
        return risk

    def hazards(
        positions_x: np.ndarray,
        positions_y: np.ndarray,
        absolute_step: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        step = absolute_step - case.control_delay_frames
        return live._native_hazards_for_positions(
            positions_x,
            positions_y,
            step=absolute_step,
            bullet_frame=bullet_frames[step - 1],
            lasers=laser_frames[step - 1],
            enemy_bodies=case.enemy_bodies,
        )

    common = {
        "initial": initial,
        "actions": actions,
        "allowed_first_actions": allowed,
        "action_hold_frames": case.action_hold_frames,
        "horizon": case.horizon,
        "beam_width": case.beam_width,
        "control_delay_frames": case.control_delay_frames,
        "target_x": 192.0,
        "target_y": 400.0,
        "target_deadline": case.horizon + 8,
        "item_safety_clearance": live.ITEM_SAFETY_CLEARANCE,
        "playfield_left": live.PLAYFIELD_LEFT,
        "playfield_right": live.PLAYFIELD_RIGHT,
        "playfield_top": live.PLAYFIELD_TOP,
        "playfield_bottom": live.PLAYFIELD_BOTTOM,
        "recovery_reserve_distance": 12.0,
        "supplemental_reserve_distance": 16.0,
        "diagonal_speed": live.UNFOCUSED_DIAGONAL_SPEED,
        "cardinal_speed": live.UNFOCUSED_CARDINAL_SPEED,
        "certificate_collisions": certificate_collisions,
        "certificate_minimum": certificate_minimum,
        "survival_preferred": survival,
        "safety_preferred": safety,
        "recovery_distance": recovery,
        "repair_volume": repair,
    }
    started = time.perf_counter_ns()
    python_nodes = search_supplemental_local_beam(
        **common,
        beam_dedup_mode="quantized",
        hazard_query=hazards,
        transition_risk=transition,
        use_native_reducer=False,
    )
    python_ms = (time.perf_counter_ns() - started) / 1_000_000.0
    body_fields = _body_fields(case)
    started = time.perf_counter_ns()
    native_nodes = search_supplemental_local_beam_native(
        **common,
        bullet_frames=bullet_frames,
        laser_frames=tuple(
            frame.fields_for_native() for frame in laser_frames
        ),
        body_base_x=body_fields[0],
        body_base_y=body_fields[1],
        body_velocity_x=body_fields[2],
        body_velocity_y=body_fields[3],
        body_half_width=body_fields[4],
        body_half_height=body_fields[5],
        player_radius=live.PLAYER_RADIUS,
        previous_direction=case.previous_direction,
        previous_focused=case.previous_focused,
        preserve_previous_direction_inertia=True,
    )
    native_ms = (time.perf_counter_ns() - started) / 1_000_000.0
    return python_nodes, native_nodes, python_ms, native_ms


def _supplemental_mismatch(
    python_nodes: list[SupplementalNode],
    native_nodes: list[SupplementalNode],
) -> str | None:
    if len(python_nodes) != len(native_nodes):
        return f"count:{len(python_nodes)}!={len(native_nodes)}"
    for index, (reference, candidate) in enumerate(
        zip(python_nodes, native_nodes)
    ):
        if (
            reference.first_action != candidate.first_action
            or reference.last_action != candidate.last_action
            or reference.collisions != candidate.collisions
        ):
            return f"discrete_endpoint:{index}"
        for field in (
            "x",
            "y",
            "risk",
            "min_clearance",
            "immediate_clearance",
        ):
            left = float(getattr(reference, field))
            right = float(getattr(candidate, field))
            if field in {"x", "y"}:
                relative_tolerance = 1e-12
                absolute_tolerance = 1e-10
            elif field == "risk":
                relative_tolerance = 2e-6
                absolute_tolerance = 1e-3
            else:
                relative_tolerance = 1e-6
                absolute_tolerance = 1e-4
            if not math.isclose(
                left,
                right,
                rel_tol=relative_tolerance,
                abs_tol=absolute_tolerance,
            ):
                return f"{field}:{index}:{left!r}!={right!r}"
    return None


def evaluate_case(case: SemanticCase) -> CaseResult:
    positions_x = np.asarray(case.positions_x, dtype=np.float32)
    positions_y = np.asarray(case.positions_y, dtype=np.float32)
    lowering_started = time.perf_counter_ns()
    bullet_frames = live._build_bullet_frames(
        case.bullets,
        horizon=case.horizon,
        snapshot_lag=case.control_delay_frames,
    )
    laser_timeline = live._build_packed_laser_collision_frames(
        case.lasers,
        horizon=case.control_delay_frames + case.horizon,
    )
    laser_frames = laser_timeline[
        case.control_delay_frames :
        case.control_delay_frames + case.horizon
    ]
    lowering_ms = (
        time.perf_counter_ns() - lowering_started
    ) / 1_000_000.0
    collisions = 0
    signs = 0
    clearances = 0
    risks = 0
    batch = 0
    numpy_ns = 0
    native_ns = 0
    for local_step in range(1, case.horizon + 1):
        values = {
            "step": case.control_delay_frames + local_step,
            "bullet_frame": bullet_frames[local_step - 1],
            "lasers": laser_frames[local_step - 1],
            "enemy_bodies": case.enemy_bodies,
        }
        started = time.perf_counter_ns()
        reference = live._numpy_hazards_for_positions(
            positions_x,
            positions_y,
            **values,
        )
        numpy_ns += time.perf_counter_ns() - started
        started = time.perf_counter_ns()
        candidate = live._native_hazards_for_positions(
            positions_x,
            positions_y,
            **values,
        )
        native_ns += time.perf_counter_ns() - started
        collisions += int(not np.array_equal(reference[1], candidate[1]))
        signs += int(
            not np.array_equal(reference[2] <= 0.0, candidate[2] <= 0.0)
        )
        clearances += int(
            not np.allclose(
                reference[2],
                candidate[2],
                rtol=1e-6,
                atol=1e-4,
                equal_nan=False,
            )
        )
        risks += int(
            not np.allclose(
                reference[0],
                candidate[0],
                rtol=2e-5,
                atol=1e-3,
                equal_nan=False,
            )
        )
        if local_step in {1, case.horizon}:
            for probe in {
                0,
                len(positions_x) // 2,
                len(positions_x) - 1,
            }:
                isolated = live._native_hazards_for_positions(
                    positions_x[probe : probe + 1],
                    positions_y[probe : probe + 1],
                    **values,
                )
                batch += int(
                    int(isolated[1][0]) != int(candidate[1][probe])
                    or not math.isclose(
                        float(isolated[2][0]),
                        float(candidate[2][probe]),
                        rel_tol=1e-7,
                        abs_tol=1e-5,
                    )
                )
    python_nodes, native_nodes, python_ms, native_ms = (
        _supplemental_inputs(case, bullet_frames, laser_frames)
    )
    supplemental = _supplemental_mismatch(python_nodes, native_nodes)
    passed = not any(
        (collisions, signs, clearances, risks, batch)
    ) and supplemental is None
    return CaseResult(
        identity=case.identity,
        family=case.family,
        difficulty=case.difficulty,
        bullet_count=len(case.bullets),
        laser_count=len(case.lasers),
        body_count=len(case.enemy_bodies),
        position_count=len(case.positions_x),
        horizon=case.horizon,
        lowering_ms=lowering_ms,
        numpy_geometry_ms=numpy_ns / 1_000_000.0,
        native_geometry_ms=native_ns / 1_000_000.0,
        python_supplemental_ms=python_ms,
        native_supplemental_ms=native_ms,
        collision_mismatch_count=collisions,
        clearance_sign_mismatch_count=signs,
        clearance_mismatch_count=clearances,
        risk_mismatch_count=risks,
        batch_invariance_mismatch_count=batch,
        supplemental_mismatch=supplemental,
        passed=passed,
    )


def _load_cases(
    paths: list[Path],
) -> tuple[SemanticCase, ...]:
    return tuple(
        SemanticCase.from_payload(
            json.loads(path.read_text(encoding="utf-8"))
        )
        for path in paths
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--failure-dir",
        type=Path,
        default=Path("artifacts/counterexamples/th08_semantic"),
    )
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0xCE0132)
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument(
        "--profile",
        choices=("quick", "gate", "research"),
        default="quick",
    )
    parser.add_argument("--replay", type=Path, action="append", default=[])
    parser.add_argument("--shrink-attempts", type=int, default=256)
    args = parser.parse_args(argv)
    if args.count <= 0 or args.shrink_attempts < 0:
        raise ValueError("count must be positive and shrink attempts nonnegative")
    if not native_backend.available():
        raise RuntimeError("native backend is unavailable")
    cases = (
        _load_cases(args.replay)
        if args.replay
        else generate_cases(
            seed=args.seed,
            count=args.count,
            profile=args.profile,
        )
    )
    results: list[CaseResult] = []
    failures: list[dict[str, object]] = []
    started = time.perf_counter()
    for case in cases:
        result = evaluate_case(case)
        results.append(result)
        if result.passed:
            continue
        args.failure_dir.mkdir(parents=True, exist_ok=True)
        original_path = args.failure_dir / (
            f"{case.seed:016x}_{case.index:06d}_original.json"
        )
        original_path.write_text(
            json.dumps(case.to_payload(), indent=2) + "\n",
            encoding="utf-8",
        )
        shrunk, attempts = shrink_case(
            case,
            fails=lambda candidate: not evaluate_case(candidate).passed,
            maximum_attempts=args.shrink_attempts,
        )
        shrunk_result = evaluate_case(shrunk)
        shrunk_path = args.failure_dir / (
            f"{case.seed:016x}_{case.index:06d}_shrunk.json"
        )
        shrunk_path.write_text(
            json.dumps(shrunk.to_payload(), indent=2) + "\n",
            encoding="utf-8",
        )
        failures.append(
            {
                "identity": case.identity,
                "original": str(original_path),
                "shrunk": str(shrunk_path),
                "shrink_attempts": attempts,
                "original_result": asdict(result),
                "shrunk_result": asdict(shrunk_result),
            }
        )
    reports = [asdict(result) for result in results]
    result = {
        "schema": "th08-semantic-differential-v1",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "native_library": str(native_backend._library_path()),
        "seed": args.seed,
        "profile": args.profile,
        "case_count": len(cases),
        "families": list(FAMILIES),
        "elapsed_seconds": time.perf_counter() - started,
        "timing_ms": {
            field: _summary([float(report[field]) for report in reports])
            for field in (
                "lowering_ms",
                "numpy_geometry_ms",
                "native_geometry_ms",
                "python_supplemental_ms",
                "native_supplemental_ms",
            )
        },
        "totals": {
            field: sum(int(report[field]) for report in reports)
            for field in (
                "bullet_count",
                "laser_count",
                "body_count",
                "collision_mismatch_count",
                "clearance_sign_mismatch_count",
                "clearance_mismatch_count",
                "risk_mismatch_count",
                "batch_invariance_mismatch_count",
            )
        },
        "supplemental_mismatch_count": sum(
            report["supplemental_mismatch"] is not None
            for report in reports
        ),
        "reports": reports,
        "failures": failures,
        "passed": all(result.passed for result in results),
        "authority": (
            "offline generated finite-semantics parity only; no physical "
            "or live action authority"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "case_count": len(cases),
                "passed": result["passed"],
                "totals": result["totals"],
                "supplemental_mismatch_count": (
                    result["supplemental_mismatch_count"]
                ),
                "timing_ms": result["timing_ms"],
                "failures": failures,
            },
            indent=2,
        )
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
