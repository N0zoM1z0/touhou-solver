"""Pure corridor-publication serialization for post-issue decision traces."""

from __future__ import annotations

from collections.abc import Callable
import math
from typing import Any

from th08_corridor_runtime import corridor_policy_status


def _finite_float_or_none(value: object) -> float | None:
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def build_corridor_trace_record(
    *,
    active_solution: Any,
    pending_solution: Any,
    issue_frame: int,
    query_frame: int,
    max_age_frames: int,
    viability_query: Any,
    safety_value_query: Any,
    policy_lead: Any,
    commitment: Any,
    context_key: tuple[int, int, int | None],
    observed_input_action: str,
    decision: Any,
    delay_support: tuple[int, ...],
    guidance: Any,
    pending_command_estimate: Any,
    target: tuple[float, float, int] | None,
    control_origin_x: float,
    control_origin_y: float,
    action_name_from_mask: Callable[[int], str],
    minimum_travel_frames: Callable[..., float],
) -> dict[str, object] | None:
    """Serialize only already-completed, lookup-only corridor state."""

    report_solution = active_solution or pending_solution
    if report_solution is None:
        return None
    status = corridor_policy_status(
        report_solution,
        current_frame=issue_frame,
        max_age_frames=max_age_frames,
    )
    audit_write_ms = report_solution.audit_write_ms
    audit_error = report_solution.audit_error
    audit_pending = False
    if report_solution.audit_future is not None:
        audit_pending = not report_solution.audit_future.done()
        if not audit_pending:
            audit_write_ms, audit_error = report_solution.audit_future.result()

    plan = report_solution.plan
    viability_policy = plan.viability_policy
    record: dict[str, object] = {
        "source_frame": report_solution.source_frame,
        "snapshot_frame": report_solution.snapshot_frame,
        "forecast_lead_frames": report_solution.forecast_lead_frames,
        "age": issue_frame - report_solution.source_frame,
        "solve_ms": report_solution.solve_ms,
        "worker_ms": report_solution.worker_ms,
        "background_priority_lowered": report_solution.background_priority_lowered,
        "native_viability_worker_limit": report_solution.native_viability_worker_limit,
        "native_viability_worker_limit_applied": (
            report_solution.native_viability_worker_limit_applied
        ),
        "reachable": plan.reachable,
        "planning_mode": plan.planning_mode,
        "viability_backend": plan.viability_backend,
        "viability_grid_step": plan.viability_grid_step,
        "survival_backend": (
            plan.survival_policy.backend if plan.survival_policy is not None else None
        ),
        "solver_timing_ms": dict(plan.solver_timing_ms),
        "audit_capsule": report_solution.audit_capsule,
        "audit_write_ms": audit_write_ms,
        "audit_error": audit_error,
        "audit_pending": audit_pending,
        "lane": plan.lane,
        "bottleneck_clearance": _finite_float_or_none(
            plan.bottleneck_clearance
        ),
        "initial_safe_action_count": plan.initial_safe_action_count,
        "initial_repair_volume": plan.initial_repair_volume,
        "policy_status": status,
        "stale": status in ("expired", "outside_policy_horizon"),
        "guidance_unavailable": viability_query is None,
        "lead_estimate_frames": policy_lead.frames,
        "lead_sample_count": policy_lead.sample_count,
        "lead_p90_solve_frames": policy_lead.p90_solve_frames,
        "serial_coverage_margin_frames": (
            policy_lead.serial_coverage_margin(viability_policy.horizon_frames)
            if viability_policy is not None
            else None
        ),
        "serial_worker_serviceable": (
            policy_lead.serial_worker_serviceable(viability_policy.horizon_frames)
            if viability_policy is not None
            else False
        ),
        "commitment": {
            "active_lane": commitment.active_lane(issue_frame),
            "expires_frame": commitment.expires_frame,
            "required_gate_lane": report_solution.required_gate_lane,
            "constraint_honored": report_solution.constraint_honored,
            "context": context_key,
        },
    }
    if active_solution is not None and pending_solution is not None:
        record["next_policy"] = {
            "source_frame": pending_solution.source_frame,
            "frames_until_epoch": max(
                0,
                pending_solution.source_frame - issue_frame,
            ),
            "solve_ms": pending_solution.solve_ms,
        }
    if viability_query is not None:
        if active_solution is None or active_solution.plan.viability_policy is None:
            raise ValueError("viability query requires an active viability policy")
        policy = active_solution.plan.viability_policy
        record["viability"] = {
            "query_frame": query_frame,
            "age": query_frame - active_solution.source_frame,
            "phase_frames": (
                (query_frame - active_solution.source_frame)
                % policy.config.frames_per_layer
            ),
            "layer": viability_query.layer,
            "available": viability_query.available,
            "state_viable": viability_query.state_viable,
            "active_action": viability_query.active_action,
            "observed_input_action": observed_input_action,
            "safe_action_count": viability_query.safe_action_count,
            "safe_actions": viability_query.safe_actions,
            "repair_volumes": dict(viability_query.repair_volumes),
            "recovery_distances": dict(viability_query.recovery_distances),
            "survival_frames": viability_query.survival_frames,
            "survival_bottleneck_margin": viability_query.survival_bottleneck_margin,
            "survival_best_actions": viability_query.survival_best_actions,
            "selected_action": decision.action,
            "selected_repair_volume": decision.viability_repair_volume,
            "selected_recovery_distance": decision.viability_recovery_distance,
            "selected_survival_preferred": decision.viability_survival_preferred,
            "position_error": viability_query.position_error,
            "delay_frames": policy.delay_frames,
            "current_delay_frames": delay_support,
            "support_covers_current": guidance.support_covers_current,
            "nominal_delay": policy.nominal_delay,
            "horizon_frames": policy.horizon_frames,
            "viable_state_count": (
                policy.viable_state_count(viability_query.layer)
                if viability_query.layer is not None
                and 0 <= viability_query.layer <= policy.layer_count
                else 0
            ),
            "reason": viability_query.reason,
        }
    record["pending_command"] = (
        {
            "desired_action": action_name_from_mask(
                pending_command_estimate.expected_mask
            ),
            "remaining_frames": pending_command_estimate.remaining_frames,
            "snapshot_age": pending_command_estimate.snapshot_age,
            "issue_age": pending_command_estimate.issue_age,
            "overdue": pending_command_estimate.overdue,
        }
        if pending_command_estimate is not None
        else None
    )
    if safety_value_query is not None:
        if active_solution is None or active_solution.plan.safety_value_policy is None:
            raise ValueError("safety-value query requires an active safety policy")
        safety_policy = active_solution.plan.safety_value_policy
        record["safety_value"] = {
            "query_frame": query_frame,
            "age": query_frame - active_solution.source_frame,
            "layer": safety_value_query.layer,
            "available": safety_value_query.available,
            "active_action": safety_value_query.active_action,
            "state_value": safety_value_query.state_value,
            "best_actions": safety_value_query.best_actions,
            "selected_action": decision.action,
            "selected_preferred": decision.viability_safety_value_preferred,
            "position_error": safety_value_query.position_error,
            "horizon_frames": safety_policy.horizon_frames,
            "guidance_active": bool(guidance.safety_actions),
            "reason": safety_value_query.reason,
        }
    if plan.gate is not None:
        record["gate"] = {
            "frame": plan.gate.frame,
            "x": plan.gate.x,
            "y": plan.gate.y,
            "clearance": plan.gate.clearance,
        }
    if target is not None:
        travel_frames = minimum_travel_frames(
            control_origin_x,
            control_origin_y,
            target[0],
            target[1],
        )
        record["target"] = {
            "x": target[0],
            "y": target[1],
            "deadline": target[2],
            "travel_frames": travel_frames,
            "slack": target[2] - travel_frames,
        }
    return record


__all__ = ["build_corridor_trace_record"]
