#!/usr/bin/env python3
"""Rebuild the retained Stage-4A ordinary future-source hard gate.

This analysis joins five observation-aligned immutable native replay roots to
the retained physical first-hit chain.  It consumes future ECL/timeline births
both before and after the asynchronous global-policy publication epoch, then
computes the exact held/pending pickup predecessor into signed hazard-space
viability values.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from th08_corridor_adapter import TH08_CORRIDOR_CONFIG  # noqa: E402
from th08_corridor_runtime import solve_corridor  # noqa: E402
from th08_ecl_tool.core import parse_ecl  # noqa: E402
from th08_live.controller import _robust_action_certificates  # noqa: E402
from th08_live.enemy_sensor import enemy_body_contact_enabled  # noqa: E402
from th08_live.models import EnemyBody  # noqa: E402
from th08_live.movement import (  # noqa: E402
    LOCAL_PIPELINE_STATE_ACTIONS,
    PLANNER_ACTIONS,
    project_player_for_read_lag,
)
from th08_live.pipeline_shadow import corridor_hazard_version  # noqa: E402
from th08_ordinary_future_sources import (  # noqa: E402
    project_ordinary_future_sources,
)
from th08_time_scale import (  # noqa: E402
    TH08_UNIT_TIME_SCALE_BITS,
    Th08TimeScaleSchedule,
)
from th08_trace_replay import (  # noqa: E402
    bullet_from_trace,
    laser_from_trace,
    local_pipeline_root_from_trace,
)
from touhou_control.prepublication import (  # noqa: E402
    build_causal_prepublication_filter,
)


TRACE = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "lunatic_route2_stage4a_unattended_20260731_152921.jsonl"
)
HISTORICAL_GATE = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_ordinary_prepublication_retained_gate_20260731.json"
)
ECL_PATH = ROOT / "artifacts" / "decoded" / "ecldata4a.ecl"
REPORT = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_ordinary_future_source_retained_gate_20260731.json"
)
DECISION_FRAMES = (817, 833, 835, 850, 910)
OBSERVATION_FRAMES = (816, 831, 834, 848, 908)
PUBLICATION_LEAD_FRAMES = 16
PICKUP_DELAY_FRAMES = tuple(range(7))
OBSERVED_PICKUP_DELAY_FRAMES = tuple(range(1, 7))
NOMINAL_PICKUP_DELAY_FRAMES = 3
PREFIX_HOLD_FRAMES = (
    PUBLICATION_LEAD_FRAMES - max(PICKUP_DELAY_FRAMES)
)
FUTURE_SOURCE_HORIZON_FRAMES = 268
SAFETY_VALUE_HORIZON_FRAMES = TH08_CORRIDOR_CONFIG.horizon_frames
REPLAY_SHA256 = (
    "4588af47384d38ed0b50f51299b836c0a03972f11f93c0ec48a8845a45e1a990"
)
NATIVE_ROOT = (
    ROOT
    / "artifacts"
    / "native_snapshot_rolling"
    / "raw"
    / "th08_stage4a_obs{frame}_source_v12_rootonly_20260731.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _finite(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _load_trace_rows() -> dict[int, dict[str, object]]:
    wanted = set(DECISION_FRAMES)
    rows: dict[int, dict[str, object]] = {}
    with TRACE.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            frame = row.get("frame")
            if row.get("kind") == "decision" and frame in wanted:
                rows[int(frame)] = row
    if set(rows) != wanted:
        raise RuntimeError(
            f"retained decision chain incomplete: {sorted(rows)}"
        )
    return rows


def _native_payload(
    observation_frame: int,
) -> tuple[Path, dict[str, object], dict[str, object]]:
    path = Path(str(NATIVE_ROOT).format(frame=observation_frame))
    trial = json.loads(path.read_text(encoding="utf-8"))
    result = trial["result"]
    if (
        trial.get("schema") != "th08-native-snapshot-rolling-trial-v12"
        or result.get("status")
        != "native_collision_control_root_capture_passed"
        or result.get("changes_gameplay_input") is not False
    ):
        raise RuntimeError(f"native root {observation_frame} is not coherent")
    projection = result["root_collision_control_projection"]
    payload = projection["model_payload"]
    if (
        projection.get("schema")
        != "th08-native-snapshot-collision-control-projection-v12"
        or payload.get("schema")
        != "th08-native-snapshot-collision-control-projection-v12"
    ):
        raise RuntimeError(
            f"native root {observation_frame} has the wrong projection schema"
        )
    auxiliary_rows = (
        payload["enemy_manager_template_source"]["auxiliary_ecl_contexts"][
            "rows"
        ]
        + payload["enemy_auxiliary_ecl_contexts"]["rows"]
    )
    if auxiliary_rows:
        raise RuntimeError(
            "legacy v12 retained root cannot be uplifted without its "
            "auxiliary delay timer"
        )
    # These fixed v12 roots contain no auxiliary VM.  Their omitted +0x90
    # delay timer is therefore vacuous, so they are semantically identical to
    # v13 for the retained deterministic chain.
    phase_groups = (
        payload["enemy_manager_template_source"]["phase_transition_state"],
        payload["enemy_phase_transition_state"],
    )
    for group in phase_groups:
        for row in group["rows"]:
            if (
                any(int(value) >= 0 for value in row["health_thresholds"])
                or int(row["timeout_frame"]) >= 0
            ):
                raise RuntimeError(
                    "legacy v12 retained root cannot be uplifted with an "
                    "armed phase transition"
                )
            # Successor and phase-timer bytes are irrelevant when every
            # transition register is disabled.  Fill only that vacuous state;
            # an armed legacy row remains rejected above.
            row["health_successor_subroutines"] = [-1, -1, -1, -1]
            row["phase_timer_previous"] = -1
            row["phase_timer_fraction_bits"] = 0
            row["phase_timer_elapsed"] = 0
    for group in (
        payload["enemy_manager_template_source"]["motion_state"],
        payload["enemy_motion_state"],
    ):
        for row in group["rows"]:
            if int(row["movement_state"]) in (2, 3):
                raise RuntimeError(
                    "legacy retained timed/orbit root lacks exact current "
                    "motion timer state"
                )
            row["timed_mode"] = 0
            row["timed_displacement"] = [0.0, 0.0, 0.0]
            row["motion_timer_fraction_bits"] = 0
    payload["schema"] = "th08-native-snapshot-collision-control-projection-v14"
    return path, trial, payload


def _certificate_record(certificate: object) -> dict[str, object]:
    return {
        "action": certificate.action,
        "write_required": certificate.write_required,
        "pipeline_branch_count": certificate.pipeline_branch_count,
        "worst_collisions": certificate.worst_collisions,
        "min_clearance": certificate.min_clearance,
        "cvar_risk": certificate.cvar_risk,
        "worst_new_delay": certificate.worst_delay,
        "worst_pending_remaining": (
            certificate.worst_pending_remaining
        ),
    }


def _point_record(
    *,
    decision_frame: int,
    observation_frame: int,
    trace_row: dict[str, object],
    ecl: object,
) -> dict[str, object]:
    root_path, trial, payload = _native_payload(observation_frame)
    compact = payload["compact_state"]
    if (
        int(compact["manager_frame"]) != observation_frame
        or int(trace_row["snapshot_frame"]) != observation_frame
    ):
        raise RuntimeError("trace/native observation clocks disagree")
    trace_player = trace_row["player"]
    trace_player_matches_native = bool(
        float(trace_player["x"]) == float(compact["player_x"])
        and float(trace_player["y"]) == float(compact["player_y"])
        and int(trace_player["phase"]) == int(compact["player_phase"])
    )
    if not trace_player_matches_native:
        raise RuntimeError("trace/native player root disagrees")
    root, held_mask, issue_age, overdue = local_pipeline_root_from_trace(
        trace_row
    )
    closure_started = time.perf_counter()
    closure = project_ordinary_future_sources(
        payload,
        ecl,
        horizon_frames=FUTURE_SOURCE_HORIZON_FRAMES,
    )
    closure_ms = (time.perf_counter() - closure_started) * 1000.0
    projection = closure.projection

    bullets = tuple(
        bullet_from_trace(values) for values in payload["bullets"]
    )
    lasers = tuple(
        laser_from_trace(values) for values in payload["lasers"]
    )
    observed_bodies = tuple(
        EnemyBody(**values) for values in payload["enemy_bodies"]
    )
    hostile_bodies = tuple(
        body for body in observed_bodies if enemy_body_contact_enabled(body)
    )
    scale = Th08TimeScaleSchedule.constant(
        TH08_UNIT_TIME_SCALE_BITS,
        horizon=FUTURE_SOURCE_HORIZON_FRAMES,
        provenance="retained_native_unit_scale_root",
        source_frame=observation_frame,
    )
    forecast_player_x, forecast_player_y = project_player_for_read_lag(
        float(compact["player_x"]),
        float(compact["player_y"]),
        held_mask,
        PUBLICATION_LEAD_FRAMES,
        player_scale_bits=scale.player_scale_bits,
    )
    solve_started = time.perf_counter()
    solution = solve_corridor(
        source_frame=observation_frame + PUBLICATION_LEAD_FRAMES,
        snapshot_frame=observation_frame,
        forecast_lead_frames=PUBLICATION_LEAD_FRAMES,
        player_x=forecast_player_x,
        player_y=forecast_player_y,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=hostile_bodies,
        future_hazard_projection=projection,
        snapshot_lag=0,
        control_delay_candidates=PICKUP_DELAY_FRAMES,
        observed_control_delay_candidates=OBSERVED_PICKUP_DELAY_FRAMES,
        nominal_control_delay=NOMINAL_PICKUP_DELAY_FRAMES,
        active_action=root.active_action,
        safety_value_horizon_frames=SAFETY_VALUE_HORIZON_FRAMES,
        retain_safety_action_values=True,
        native_viability_worker_limit=4,
        time_scale_schedule=scale,
    )
    solve_wall_ms = (time.perf_counter() - solve_started) * 1000.0
    prefix_certificates = _robust_action_certificates(
        player_x=float(compact["player_x"]),
        player_y=float(compact["player_y"]),
        previous_mask=held_mask,
        actions=PLANNER_ACTIONS,
        delay_frames=PICKUP_DELAY_FRAMES,
        action_hold_frames=PREFIX_HOLD_FRAMES,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=hostile_bodies,
        snapshot_lag=0,
        player_scale_bits=scale.player_scale_bits[
            :PUBLICATION_LEAD_FRAMES
        ],
        laser_scale_bits=scale.laser_scale_bits[
            :PUBLICATION_LEAD_FRAMES
        ],
        pipeline_root=root,
        future_hazard_projection=projection,
        future_projection_offset=0,
    )
    prefix_safe_actions = tuple(
        action.name
        for action in PLANNER_ACTIONS
        if (
            prefix_certificates[action.name].worst_collisions == 0
            and prefix_certificates[action.name].min_clearance > 0.0
        )
    )
    predecessor = build_causal_prepublication_filter(
        enabled=True,
        root=root,
        selected_actions=tuple(action.name for action in PLANNER_ACTIONS),
        action_velocities={
            action.name: (action.dx, action.dy)
            for action in LOCAL_PIPELINE_STATE_ACTIONS
        },
        delay_frames=PICKUP_DELAY_FRAMES,
        current_frame=observation_frame,
        publication_frame=(
            observation_frame + PUBLICATION_LEAD_FRAMES
        ),
        prefix_certified_frames=PUBLICATION_LEAD_FRAMES,
        prefix_safe_actions=prefix_safe_actions,
        start_x=float(compact["player_x"]),
        start_y=float(compact["player_y"]),
        future_safety_policy=solution.plan.safety_value_policy,
        future_recovery_policy=solution.plan.viability_policy,
        hazard_coverage=projection.coverage,
        required_hazard_version=corridor_hazard_version(solution),
    )
    predecessor_record = predecessor.record()
    action_assessments = {
        action.action: action for action in predecessor.actions
    }
    finite_assessments = tuple(
        action
        for action in predecessor.actions
        if math.isfinite(action.worst_certified_margin)
    )
    best = (
        max(finite_assessments, key=lambda item: item.worst_certified_margin)
        if finite_assessments
        else None
    )
    issued_action = str(trace_row["action"])
    actual_active = action_assessments[root.active_action]
    held = action_assessments[root.held_desired_action]
    issued = action_assessments[issued_action]
    viable_state_count = (
        solution.plan.viability_policy.viable_state_count(0)
        if solution.plan.viability_policy is not None
        else None
    )
    return {
        "decision_frame": decision_frame,
        "observation_frame": observation_frame,
        "native_root": {
            "path": str(root_path.relative_to(ROOT)),
            "sha256": _sha256(root_path),
            "trial_schema": trial["schema"],
            "projection_schema": payload["schema"],
            "projection_sha256": trial["result"][
                "root_collision_control_projection"
            ]["sha256"],
            "status": trial["result"]["status"],
            "replay_sha256": trial["replay_contract"]["sha256"],
            "thread_epoch_stable": True,
        },
        "trace_alignment": {
            "snapshot_frame": trace_row["snapshot_frame"],
            "player_root_exact": trace_player_matches_native,
            "player_phase": compact["player_phase"],
            "predeath_counter": compact["predeath_counter"],
            "issued_action": issued_action,
        },
        "pipeline_root": {
            "active_action": root.active_action,
            "held_desired_action": root.held_desired_action,
            "pending_action": root.pending_action,
            "remaining_delay_support": root.remaining_delay_support,
            "held_desired_mask": held_mask,
            "issue_age": issue_age,
            "overdue": overdue,
        },
        "current_hazards": {
            "bullets": len(bullets),
            "lasers": len(lasers),
            "observed_enemy_bodies": len(observed_bodies),
            "contact_enabled_enemy_bodies": len(hostile_bodies),
        },
        "future_source_closure": {
            **projection.record(),
            "closure_wall_ms": closure_ms,
            "source_count": closure.source_count,
            "auxiliary_count": closure.auxiliary_count,
            "silent_child_count": closure.silent_child_count,
            "timeline_steps": closure.timeline_steps,
            "timeline_spawn_count": closure.timeline_spawn_count,
            "direct_fire_event_count": len(closure.direct_fire_events),
        },
        "corridor": {
            "source_frame": solution.source_frame,
            "publication_lead_frames": PUBLICATION_LEAD_FRAMES,
            "forecast_player": [forecast_player_x, forecast_player_y],
            "reachable": solution.plan.reachable,
            "reason": solution.plan.reason,
            "solve_ms": solution.solve_ms,
            "solve_wall_ms": solve_wall_ms,
            "viability_backend": solution.plan.viability_backend,
            "viable_state_count_layer0": viable_state_count,
            "initial_safe_action_count": (
                solution.plan.initial_safe_action_count
            ),
            "bottleneck_clearance": _finite(
                solution.plan.bottleneck_clearance
            ),
            "future_projection_retained_for_prefix": (
                solution.future_hazard_projection is projection
            ),
        },
        "publication_prefix": {
            "frames": PUBLICATION_LEAD_FRAMES,
            "pickup_delay_frames": PICKUP_DELAY_FRAMES,
            "selected_hold_frames": PREFIX_HOLD_FRAMES,
            "future_projection_consumed": True,
            "future_projection_version": projection.version.record(),
            "safe_actions": prefix_safe_actions,
            "certificates": [
                _certificate_record(prefix_certificates[action.name])
                for action in PLANNER_ACTIONS
            ],
        },
        "causal_predecessor": predecessor_record,
        "directional_summary": {
            "active_action": root.active_action,
            "active_action_allowed": bool(
                predecessor.allowed_actions is not None
                and root.active_action in predecessor.allowed_actions
            ),
            "active_action_margin": _finite(
                actual_active.worst_certified_margin
            ),
            "held_action": root.held_desired_action,
            "held_action_allowed": bool(
                predecessor.allowed_actions is not None
                and root.held_desired_action in predecessor.allowed_actions
            ),
            "held_action_margin": _finite(
                held.worst_certified_margin
            ),
            "issued_action": issued_action,
            "issued_action_allowed": bool(
                predecessor.allowed_actions is not None
                and issued_action in predecessor.allowed_actions
            ),
            "issued_action_margin": _finite(
                issued.worst_certified_margin
            ),
            "best_action": best.action if best is not None else None,
            "best_margin": (
                best.worst_certified_margin if best is not None else None
            ),
        },
    }


def _deterministic_gate(points: list[dict[str, object]]) -> dict[str, object]:
    first = points[0]
    pending = next(
        point for point in points if point["decision_frame"] == 850
    )
    all_actions = tuple(action.name for action in PLANNER_ACTIONS)
    complete_future_coverage = all(
        point["future_source_closure"]["source_closure_complete"]
        and point["future_source_closure"]["coverage"]["status"]
        == "complete"
        for point in points
    )
    prefix_consumes_future_geometry = all(
        point["publication_prefix"]["future_projection_consumed"]
        and point["corridor"]["future_projection_retained_for_prefix"]
        for point in points
    )
    signed_action_values = all(
        len(point["causal_predecessor"]["actions"]) == len(all_actions)
        and all(
            action["unavailable_branch_count"] == 0
            and action["worst_certified_margin"] is not None
            for action in point["causal_predecessor"]["actions"]
        )
        for point in points
    )
    exact_authority_all_roots = all(
        point["causal_predecessor"]["authority_eligible"]
        for point in points
    )
    first_allowed = first["causal_predecessor"]["allowed_actions"] or ()
    first_nontrivial = 0 < len(first_allowed) < len(all_actions)
    first_active_excluded = bool(
        first["directional_summary"]["active_action_allowed"] is False
    )
    first_positive_recovery = any(
        action["worst_certified_margin"] is not None
        and action["worst_certified_margin"] > 0.0
        for action in first["causal_predecessor"]["actions"]
    )
    pending_exact = bool(
        pending["pipeline_root"]["pending_action"] is not None
        and min(
            action["branch_count"]
            for action in pending["causal_predecessor"]["actions"]
        )
        > 1
        and max(
            action["branch_count"]
            for action in pending["causal_predecessor"]["actions"]
        )
        > min(
            action["branch_count"]
            for action in pending["causal_predecessor"]["actions"]
        )
    )
    checks = {
        "observation_aligned_native_roots": all(
            point["trace_alignment"]["player_root_exact"]
            and point["native_root"]["status"]
            == "native_collision_control_root_capture_passed"
            and point["native_root"]["replay_sha256"] == REPLAY_SHA256
            for point in points
        ),
        "complete_future_birth_ecl_timeline_coverage": (
            complete_future_coverage
        ),
        "future_geometry_consumed_across_publication_lead": (
            prefix_consumes_future_geometry
        ),
        "signed_per_action_terminal_values": signed_action_values,
        "coverage_version_exact_authority_all_roots": (
            exact_authority_all_roots
        ),
        "nontrivial_exact_allowed_set_before_exhaustion": first_nontrivial,
        "retained_losing_active_action_excluded": first_active_excluded,
        "positive_directional_recovery_retained": first_positive_recovery,
        "pending_command_pickup_branches_exact": pending_exact,
    }
    passed = all(checks.values())
    return {
        **checks,
        "hard_gate_passed": passed,
        "blockers": [] if passed else [
            name for name, value in checks.items() if not value
        ],
        "physical_disposition": (
            "stage4a_physical_gate_authorized"
            if passed
            else "do_not_run_until_hard_gate_passes"
        ),
    }


def build_report() -> dict[str, object]:
    historical = json.loads(HISTORICAL_GATE.read_text(encoding="utf-8"))
    historical_chain = tuple(
        (
            int(row["decision_frame"]),
            int(row["observation_frame"]),
        )
        for row in historical["chain"]
    )
    expected_chain = tuple(zip(DECISION_FRAMES, OBSERVATION_FRAMES))
    if historical_chain != expected_chain:
        raise RuntimeError("historical retained chain identity changed")
    rows = _load_trace_rows()
    ecl = parse_ecl(ECL_PATH)
    points = [
        _point_record(
            decision_frame=decision_frame,
            observation_frame=observation_frame,
            trace_row=rows[decision_frame],
            ecl=ecl,
        )
        for decision_frame, observation_frame in expected_chain
    ]
    return {
        "schema": "th08-ordinary-future-source-retained-gate-v2",
        "scope": "ordinary_nonspell_only",
        "authority": (
            "deterministic_native_replay_regression_not_physical_outcome"
        ),
        "source": {
            "physical_run_id": (
                "lunatic_route2_stage4a_unattended_20260731_152921"
            ),
            "trace_path": str(TRACE.relative_to(ROOT)),
            "trace_sha256": _sha256(TRACE),
            "historical_gate_path": str(
                HISTORICAL_GATE.relative_to(ROOT)
            ),
            "historical_gate_sha256": _sha256(HISTORICAL_GATE),
            "accepted_replay_sha256": REPLAY_SHA256,
            "ecl_path": str(ECL_PATH.relative_to(ROOT)),
            "ecl_sha256": ecl.sha256,
            "hard_no_bomb": True,
        },
        "contract": {
            "future_source_horizon_frames": (
                FUTURE_SOURCE_HORIZON_FRAMES
            ),
            "publication_lead_frames": PUBLICATION_LEAD_FRAMES,
            "pickup_delay_frames": PICKUP_DELAY_FRAMES,
            "prefix_hold_frames": PREFIX_HOLD_FRAMES,
            "corridor_horizon_frames": (
                TH08_CORRIDOR_CONFIG.horizon_frames
            ),
            "safety_value_horizon_frames": (
                SAFETY_VALUE_HORIZON_FRAMES
            ),
            "future_geometry_before_publication": (
                "consumed_by_exact_local_pipeline_prefix"
            ),
            "future_geometry_after_publication": (
                "consumed_by_corridor_hazard_space_policy"
            ),
            "unsupported_source_semantics": "fail_closed",
        },
        "chain": points,
        "deterministic_gate": _deterministic_gate(points),
    }


def main() -> int:
    report = build_report()
    REPORT.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(REPORT)
    gate = report["deterministic_gate"]
    print(json.dumps(gate, indent=2))
    return 0 if gate["hard_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
