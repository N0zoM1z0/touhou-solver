#!/usr/bin/env python3
"""Retained exact held-prefix gate into the ordinary 4px lower kernel."""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from analysis import (  # noqa: E402
    th08_ordinary_future_source_retained_gate as retained,
)
from th08_corridor_adapter import (  # noqa: E402
    TH08_CORRIDOR_CONFIG,
    TH08_VIABILITY_ACTIONS,
    lower_th08_corridor_hazards,
    plan_prepared_lowered_th08_corridor,
    prepare_lowered_th08_corridor,
)
from th08_live.enemy_sensor import enemy_body_contact_enabled  # noqa: E402
from th08_live.controller import _robust_action_certificates  # noqa: E402
from th08_live.models import EnemyBody  # noqa: E402
from th08_live.movement import (  # noqa: E402
    PLANNER_ACTIONS,
    project_player_for_read_lag,
)
from th08_ordinary_future_sources import (  # noqa: E402
    ORDINARY_FUTURE_SOURCE_SEMANTICS_VERSION,
)
from th08_trace_replay import (  # noqa: E402
    bullet_from_trace,
    laser_from_trace,
    local_pipeline_root_from_trace,
)
from touhou_control import native_backend  # noqa: E402
from touhou_control.hazard_coverage import rebase_hazard_coverage  # noqa: E402
from touhou_control.prepublication import (  # noqa: E402
    build_causal_prepublication_filter,
)
from touhou_control.query_survival import (  # noqa: E402
    PendingCommand,
    SurvivalQueryProblem,
)


REPORT = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_ordinary_factorized_prefix_gate_20260731.json"
)
GRID_STEP = 4.0
CELL_RADIUS = math.sqrt(2.0) * GRID_STEP / 2.0
PUBLICATION_LEAD_FRAMES = 16
DECISION_FRAME_SUPPORT = (2, 3, 4)
NEW_COMMAND_DELAY_FRAMES = tuple(range(1, 7))
FUTURE_DELAY_FRAMES = tuple(range(7))
NATIVE_WORKERS = 16


def _terminal_viability_margins(
    *,
    policy: object,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Encode one Boolean lower-kernel layer as terminal set margins."""

    grid_y, grid_x = np.meshgrid(
        y_axis.astype(np.float64),
        x_axis.astype(np.float64),
        indexing="ij",
    )
    policy_x_step = float(policy.x_axis[1] - policy.x_axis[0])
    policy_y_step = float(policy.y_axis[1] - policy.y_axis[0])
    columns = np.clip(
        np.rint(
            (grid_x - float(policy.x_axis[0])) / policy_x_step
        ).astype(np.intp),
        0,
        len(policy.x_axis) - 1,
    )
    rows = np.clip(
        np.rint(
            (grid_y - float(policy.y_axis[0])) / policy_y_step
        ).astype(np.intp),
        0,
        len(policy.y_axis) - 1,
    )
    action_count = len(policy.actions)
    positive = np.float32(np.inf)
    negative = np.float32(-np.inf)
    state_margins = np.empty(
        (action_count, len(y_axis), len(x_axis)),
        dtype=np.float32,
    )
    action_margins = np.empty(
        (action_count, action_count, len(y_axis), len(x_axis)),
        dtype=np.float32,
    )
    for active_index in range(action_count):
        state_margins[active_index] = np.where(
            policy.viable[0, active_index, rows, columns],
            positive,
            negative,
        )
        masks = policy.safe_action_masks[0, active_index, rows, columns]
        for selected_index in range(action_count):
            action_margins[active_index, selected_index] = np.where(
                masks & np.uint32(1 << selected_index),
                positive,
                negative,
            )
    return state_margins, action_margins


def probe_point(
    *,
    decision_frame: int,
    observation_frame: int,
    trace_row: dict[str, object],
    ecl: object,
) -> dict[str, object]:
    _, _, payload = retained._native_payload(observation_frame)
    compact = payload["compact_state"]
    root, held_mask, _, _ = local_pipeline_root_from_trace(trace_row)
    closure_started = time.perf_counter()
    closure = retained.project_ordinary_future_sources(
        payload,
        ecl,
        horizon_frames=retained.FUTURE_SOURCE_HORIZON_FRAMES,
    )
    closure_ms = (time.perf_counter() - closure_started) * 1000.0
    projection = closure.projection
    bullets = tuple(
        bullet_from_trace(values) for values in payload["bullets"]
    )
    lasers = tuple(
        laser_from_trace(values) for values in payload["lasers"]
    )
    bodies = tuple(
        EnemyBody(**values) for values in payload["enemy_bodies"]
    )
    hostile_bodies = tuple(
        body for body in bodies if enemy_body_contact_enabled(body)
    )
    scale = retained.Th08TimeScaleSchedule.constant(
        retained.TH08_UNIT_TIME_SCALE_BITS,
        horizon=retained.FUTURE_SOURCE_HORIZON_FRAMES,
        provenance="retained_factorized_prefix_gate",
        source_frame=observation_frame,
    )
    forecast_x, forecast_y = project_player_for_read_lag(
        float(compact["player_x"]),
        float(compact["player_y"]),
        held_mask,
        PUBLICATION_LEAD_FRAMES,
        player_scale_bits=scale.player_scale_bits,
    )

    future_config = replace(
        TH08_CORRIDOR_CONFIG,
        grid_step=GRID_STEP,
        required_clearance=CELL_RADIUS,
    )
    future_started = time.perf_counter()
    future_hazards = lower_th08_corridor_hazards(
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=hostile_bodies,
        snapshot_lag=0,
        forecast_frames=PUBLICATION_LEAD_FRAMES,
        horizon_frames=future_config.horizon_frames,
        laser_time_scale_bits=scale.laser_scale_bits,
        future_aabb_trajectories=(
            projection.aabb_trajectories_for_policy(
                source_frame=(
                    observation_frame + PUBLICATION_LEAD_FRAMES
                ),
                horizon_frames=future_config.horizon_frames,
            )
        ),
        future_annular_sector_trajectories=(
            projection.trajectories_for_policy(
                source_frame=(
                    observation_frame + PUBLICATION_LEAD_FRAMES
                ),
                horizon_frames=future_config.horizon_frames,
            )
        ),
    )
    future_prepared = prepare_lowered_th08_corridor(
        hazards=future_hazards,
        config=future_config,
        control_delay_candidates=FUTURE_DELAY_FRAMES,
        nominal_control_delay=retained.NOMINAL_PICKUP_DELAY_FRAMES,
        active_action=root.active_action,
    )
    future_plan = plan_prepared_lowered_th08_corridor(
        player_x=forecast_x,
        player_y=forecast_y,
        prepared_problem=future_prepared,
    )
    future_solve_ms = (time.perf_counter() - future_started) * 1000.0
    terminal_policy = future_plan.viability_policy
    if terminal_policy is None:
        raise RuntimeError("future Boolean lower kernel is unavailable")

    prefix_config = replace(
        TH08_CORRIDOR_CONFIG,
        horizon_frames=PUBLICATION_LEAD_FRAMES,
        grid_step=GRID_STEP,
    )
    prefix_hazards = lower_th08_corridor_hazards(
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=hostile_bodies,
        snapshot_lag=0,
        forecast_frames=0,
        horizon_frames=PUBLICATION_LEAD_FRAMES,
        laser_time_scale_bits=scale.laser_scale_bits,
        future_aabb_trajectories=(
            projection.aabb_trajectories_for_policy(
                source_frame=observation_frame,
                horizon_frames=PUBLICATION_LEAD_FRAMES,
            )
        ),
        future_annular_sector_trajectories=(
            projection.trajectories_for_policy(
                source_frame=observation_frame,
                horizon_frames=PUBLICATION_LEAD_FRAMES,
            )
        ),
    )
    prefix_prepared = prepare_lowered_th08_corridor(
        hazards=prefix_hazards,
        config=prefix_config,
        control_delay_candidates=NEW_COMMAND_DELAY_FRAMES,
        nominal_control_delay=retained.NOMINAL_PICKUP_DELAY_FRAMES,
        active_action=root.active_action,
        retain_query_survival_problem=True,
    )
    base_problem = prefix_prepared.survival_query_problem
    if base_problem is None:
        raise RuntimeError("prefix survival problem is unavailable")
    terminal_state, terminal_actions = _terminal_viability_margins(
        policy=terminal_policy,
        x_axis=base_problem.x_axis,
        y_axis=base_problem.y_axis,
    )
    problem = SurvivalQueryProblem(
        x_axis=base_problem.x_axis,
        y_axis=base_problem.y_axis,
        clearance_volume=base_problem.clearance_volume,
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=NEW_COMMAND_DELAY_FRAMES,
        nominal_delay=retained.NOMINAL_PICKUP_DELAY_FRAMES,
        config=base_problem.config,
        terminal_state_margins=terminal_state,
        terminal_action_margins=terminal_actions,
    )
    row, column, root_error = problem.project_to_lattice(
        x=float(compact["player_x"]),
        y=float(compact["player_y"]),
    )
    pending = (
        PendingCommand(
            root.pending_action,
            root.remaining_delay_support,
        )
        if root.pending_action is not None
        else None
    )
    winning_actions: list[str] = []
    unresolved_actions: list[str] = []
    certificate_started = time.perf_counter()
    hidden_simulations = 0
    for action in problem.actions:
        version = (
            "retained-factorized-held-prefix-v1",
            decision_frame,
            action.name,
        )
        with problem.build_belief_pipeline_workspace(
            policy_version=version,
            decision_frame_support=DECISION_FRAME_SUPPORT,
            continuation_actions=(action.name,),
        ) as workspace:
            certificate = workspace.certify_exact_winning_actions(
                policy_version=version,
                frame=0,
                row=row,
                column=column,
                observed_action=root.active_action,
                pending_command=pending,
                target_frames=PUBLICATION_LEAD_FRAMES,
                target_margin=root_error,
                timeout_ms=30_000,
            )
        if action.name in certificate.winning_actions:
            winning_actions.append(action.name)
        if action.name in certificate.unresolved_actions:
            unresolved_actions.append(action.name)
        hidden_simulations += (
            certificate.workspace_stats.hidden_simulation_count
        )
    certificate_ms = (
        time.perf_counter() - certificate_started
    ) * 1000.0
    live_delay_frames = tuple(range(7))
    prefix_certificates = _robust_action_certificates(
        player_x=float(compact["player_x"]),
        player_y=float(compact["player_y"]),
        previous_mask=held_mask,
        actions=PLANNER_ACTIONS,
        delay_frames=live_delay_frames,
        action_hold_frames=(
            PUBLICATION_LEAD_FRAMES - max(live_delay_frames)
        ),
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=hostile_bodies,
        snapshot_lag=0,
        player_scale_bits=scale.player_scale_bits[
            : PUBLICATION_LEAD_FRAMES
        ],
        laser_scale_bits=scale.laser_scale_bits[
            : PUBLICATION_LEAD_FRAMES
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
    live_adapter = build_causal_prepublication_filter(
        enabled=True,
        root=root,
        selected_actions=tuple(
            action.name for action in TH08_VIABILITY_ACTIONS
        ),
        action_velocities={
            action.name: (action.velocity_x, action.velocity_y)
            for action in TH08_VIABILITY_ACTIONS
        },
        delay_frames=live_delay_frames,
        current_frame=observation_frame,
        publication_frame=(
            observation_frame + PUBLICATION_LEAD_FRAMES
        ),
        prefix_certified_frames=PUBLICATION_LEAD_FRAMES,
        prefix_safe_actions=prefix_safe_actions,
        start_x=float(compact["player_x"]),
        start_y=float(compact["player_y"]),
        future_safety_policy=None,
        future_viability_policy=terminal_policy,
        future_recovery_policy=terminal_policy,
        hazard_coverage=rebase_hazard_coverage(
            projection.coverage,
            root_frame=observation_frame,
            horizon_frame=(
                observation_frame
                + PUBLICATION_LEAD_FRAMES
                + terminal_policy.horizon_frames
            ),
        ),
        required_hazard_version=projection.version,
        policy_query_frame=0,
        policy_source_frame=(
            observation_frame + PUBLICATION_LEAD_FRAMES
        ),
    )
    return {
        "decision_frame": decision_frame,
        "observation_frame": observation_frame,
        "pipeline_root": {
            "active_action": root.active_action,
            "held_desired_action": root.held_desired_action,
            "pending_action": root.pending_action,
            "remaining_delay_support": root.remaining_delay_support,
        },
        "publication_lead_frames": PUBLICATION_LEAD_FRAMES,
        "decision_frame_support": DECISION_FRAME_SUPPORT,
        "new_command_delay_frames": NEW_COMMAND_DELAY_FRAMES,
        "future_delay_frames": FUTURE_DELAY_FRAMES,
        "future_grid_step": GRID_STEP,
        "future_required_clearance": CELL_RADIUS,
        "root_position_error": root_error,
        "source_closure_complete": projection.source_closure_complete,
        "future_coverage_complete": projection.coverage.complete,
        "future_projection_digest": projection.digest,
        "source_closure_ms": closure_ms,
        "future_solve_ms": future_solve_ms,
        "certificate_ms": certificate_ms,
        "hidden_simulations": hidden_simulations,
        "winning_actions": tuple(winning_actions),
        "unresolved_actions": tuple(unresolved_actions),
        "complete": not unresolved_actions,
        "live_adapter_authority_eligible": (
            live_adapter.authority_eligible
        ),
        "live_adapter_allowed_actions": (
            live_adapter.allowed_actions
        ),
        "live_adapter_reason": live_adapter.reason,
    }


def main() -> int:
    worker_limit_applied = (
        native_backend.set_current_thread_viability_worker_limit(
            NATIVE_WORKERS
        )
    )
    rows = retained._load_trace_rows()
    ecl = retained.parse_ecl(retained.ECL_PATH)
    points = [
        probe_point(
            decision_frame=decision_frame,
            observation_frame=observation_frame,
            trace_row=rows[decision_frame],
            ecl=ecl,
        )
        for decision_frame, observation_frame in zip(
            retained.DECISION_FRAMES,
            retained.OBSERVATION_FRAMES,
        )
    ]
    first = points[0]
    semantic_gate_passed = bool(
        worker_limit_applied
        and all(
            point["source_closure_complete"]
            and point["future_coverage_complete"]
            and point["complete"]
            and point["live_adapter_authority_eligible"]
            for point in points
        )
        and first["winning_actions"]
        == ("left_fast", "down_left_fast")
        and first["live_adapter_allowed_actions"]
        == first["winning_actions"]
        and "up_fast" not in first["winning_actions"]
        and "up_left_fast" not in first["winning_actions"]
    )
    report = {
        "schema": "th08-ordinary-factorized-prefix-gate-v1",
        "platform": platform.system(),
        "authority": (
            "offline_exact_finite_model_no_physical_promotion"
        ),
        "future_source_semantics_version": (
            ORDINARY_FUTURE_SOURCE_SEMANTICS_VERSION
        ),
        "native_workers": NATIVE_WORKERS,
        "native_worker_limit_applied": worker_limit_applied,
        "semantic_gate_passed": semantic_gate_passed,
        "maximum_future_solve_ms": max(
            point["future_solve_ms"] for point in points
        ),
        "maximum_certificate_ms": max(
            point["certificate_ms"] for point in points
        ),
        "points": points,
    }
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if semantic_gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
