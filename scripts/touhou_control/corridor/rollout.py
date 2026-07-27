"""Representative path selection inside a robust corridor kernel."""

from __future__ import annotations

import math
import time

from .grid import lane
from .model import CorridorBounds, CorridorPlan, CorridorPoint
from .prepared import PreparedCorridorProblem
from .robust import RobustCorridorInduction


def _lane_target(
    required_gate_lane: str | None,
    *,
    bounds: CorridorBounds,
    preferred_x: float | None,
) -> float:
    if required_gate_lane == "left":
        return bounds.left + (bounds.right - bounds.left) / 6.0
    if required_gate_lane == "right":
        return bounds.right - (bounds.right - bounds.left) / 6.0
    if required_gate_lane == "center":
        return (bounds.left + bounds.right) * 0.5
    if preferred_x is not None:
        return preferred_x
    return (bounds.left + bounds.right) * 0.5


def rollout_robust_corridor(
    *,
    prepared_problem: PreparedCorridorProblem,
    induction: RobustCorridorInduction,
    start_x: float,
    start_y: float,
    preferred_x: float | None,
    preferred_y: float | None,
    required_gate_lane: str | None,
) -> CorridorPlan:
    """Select the historical deterministic path inside a robust kernel."""

    bounds = prepared_problem.bounds
    control = prepared_problem.robust_control
    config = induction.config
    x_axis = induction.x_axis
    y_axis = induction.y_axis
    clearance_volume = induction.clearance_volume
    policy = induction.policy
    start_query = induction.start_query
    base_timing = induction.base_timing_ms

    if not start_query.state_viable:
        return CorridorPlan(
            reachable=False,
            path=(),
            bottleneck_clearance=-math.inf,
            terminal_clearance=-math.inf,
            lane="none",
            gate=None,
            reason="initial robust viability action set is empty",
            planning_mode="robust_viability",
            viability_policy=policy,
            safety_value_policy=induction.safety_value_policy,
            survival_policy=induction.survival_policy,
            survival_query_problem=induction.survival_query_problem,
            viability_backend=policy.backend,
            viability_grid_step=config.grid_step,
            solver_timing_ms=(
                *base_timing,
                ("rollout", 0.0),
            ),
        )

    target_x = _lane_target(
        required_gate_lane,
        bounds=bounds,
        preferred_x=preferred_x,
    )
    target_y = start_y if preferred_y is None else preferred_y
    current_x = float(x_axis[start_query.column])
    current_y = float(y_axis[start_query.row])
    active_action = control.active_action
    path = [CorridorPoint(0, current_x, current_y, math.inf)]
    bottleneck = math.inf
    initial_repair_volume = 0
    for layer_index in range(policy.layer_count):
        frame = layer_index * config.frames_per_layer
        query = policy.query(
            frame=frame,
            x=current_x,
            y=current_y,
            active_action=active_action,
        )
        if not query.safe_actions:
            return CorridorPlan(
                reachable=False,
                path=(),
                bottleneck_clearance=-math.inf,
                terminal_clearance=-math.inf,
                lane="none",
                gate=None,
                reason=(
                    "representative rollout could not remain in the "
                    "backward kernel"
                ),
                planning_mode="robust_viability",
                viability_policy=policy,
                safety_value_policy=(
                    induction.safety_value_policy
                ),
                survival_policy=induction.survival_policy,
                survival_query_problem=(
                    induction.survival_query_problem
                ),
                initial_safe_action_count=(
                    start_query.safe_action_count
                ),
                initial_repair_volume=initial_repair_volume,
                viability_backend=policy.backend,
                viability_grid_step=config.grid_step,
                solver_timing_ms=(
                    *base_timing,
                    (
                        "rollout",
                        (
                            time.perf_counter()
                            - induction.rollout_started_at
                        )
                        * 1000.0,
                    ),
                ),
            )
        candidates: list[
            tuple[tuple[float, ...], str, float, float, int, float]
        ] = []
        for action_name in query.safe_actions:
            endpoint_x, endpoint_y = policy.transition_endpoint(
                x=current_x,
                y=current_y,
                active_action=active_action,
                next_action=action_name,
            )
            (
                endpoint_x,
                endpoint_y,
                row,
                column,
                _,
            ) = policy.project_to_lattice(
                x=endpoint_x,
                y=endpoint_y,
            )
            next_frame = (
                layer_index + 1
            ) * config.frames_per_layer
            hazard_clearance = float(
                clearance_volume[next_frame, row, column]
            )
            boundary_clearance = min(
                endpoint_x - bounds.left,
                bounds.right - endpoint_x,
                endpoint_y - bounds.top,
                bounds.bottom - endpoint_y,
            )
            clearance = min(
                hazard_clearance,
                boundary_clearance,
            )
            repair_volume = query.repair_volume(action_name)
            position_cost = (
                (endpoint_x - target_x) ** 2
                + (endpoint_y - target_y) ** 2
            )
            candidates.append(
                (
                    (
                        -float(repair_volume),
                        -clearance,
                        position_cost,
                        (
                            0.0
                            if action_name == active_action
                            else 1.0
                        ),
                    ),
                    action_name,
                    endpoint_x,
                    endpoint_y,
                    repair_volume,
                    clearance,
                )
            )
        (
            _,
            selected_action,
            current_x,
            current_y,
            repair_volume,
            clearance,
        ) = min(candidates, key=lambda candidate: candidate[0])
        if layer_index == 0:
            initial_repair_volume = repair_volume
        bottleneck = min(bottleneck, clearance)
        active_action = selected_action
        path.append(
            CorridorPoint(
                frame=(
                    layer_index + 1
                )
                * config.frames_per_layer,
                x=current_x,
                y=current_y,
                clearance=clearance,
            )
        )

    terminal = path[-1]
    gate = min(path[1:], key=lambda point: point.clearance)
    gate_lane = lane(gate.x, bounds)
    if (
        required_gate_lane is not None
        and gate_lane != required_gate_lane
    ):
        return CorridorPlan(
            reachable=False,
            path=(),
            bottleneck_clearance=-math.inf,
            terminal_clearance=-math.inf,
            lane="none",
            gate=None,
            reason=(
                "robust policy has no representative path through required "
                f"{required_gate_lane} gate lane"
            ),
            planning_mode="robust_viability",
            viability_policy=policy,
            safety_value_policy=induction.safety_value_policy,
            survival_policy=induction.survival_policy,
            survival_query_problem=induction.survival_query_problem,
            initial_safe_action_count=start_query.safe_action_count,
            initial_repair_volume=initial_repair_volume,
            viability_backend=policy.backend,
            viability_grid_step=config.grid_step,
            solver_timing_ms=(
                *base_timing,
                (
                    "rollout",
                    (
                        time.perf_counter()
                        - induction.rollout_started_at
                    )
                    * 1000.0,
                ),
            ),
        )
    return CorridorPlan(
        reachable=True,
        path=tuple(path),
        bottleneck_clearance=bottleneck,
        terminal_clearance=terminal.clearance,
        lane=gate_lane,
        gate=gate,
        reason=(
            "delay-robust viable corridor found"
            if required_gate_lane is None
            else (
                f"delay-robust {required_gate_lane} "
                "gate policy found"
            )
        ),
        planning_mode="robust_viability",
        viability_policy=policy,
        safety_value_policy=induction.safety_value_policy,
        survival_policy=induction.survival_policy,
        survival_query_problem=induction.survival_query_problem,
        initial_safe_action_count=start_query.safe_action_count,
        initial_repair_volume=initial_repair_volume,
        viability_backend=policy.backend,
        viability_grid_step=config.grid_step,
        solver_timing_ms=(
            *base_timing,
            (
                "rollout",
                (
                    time.perf_counter()
                    - induction.rollout_started_at
                )
                * 1000.0,
            ),
        ),
    )


__all__ = ["rollout_robust_corridor"]
