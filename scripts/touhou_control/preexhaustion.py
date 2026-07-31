"""Causal player-control reserve before a local action set is exhausted.

This module deliberately makes no hostile-future or global-collision claim.
It uses only the observed/estimated actuator root, complete-mask no-write
semantics, pickup-delay support, bounded movement scale, and playfield bounds.
Near a boundary it retains actions whose worst terminal controllability
reserve does not decrease.  If an older pending command makes that impossible,
it retains the actions with the largest worst reserve.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from .local_pipeline_oracle import (
    LocalPipelineRoot,
    enumerate_local_pipeline_branches,
)


@dataclass(frozen=True)
class ActionControlReserve:
    """Worst boundary reserve across one complete desired-action lease."""

    action: str
    branch_count: int
    worst_lease_reserve: float

    def record(self) -> dict[str, object]:
        return {
            "action": self.action,
            "branch_count": self.branch_count,
            "worst_lease_reserve": self.worst_lease_reserve,
        }


@dataclass(frozen=True)
class CausalPreexhaustionFilter:
    """Auditable authority result for one finite player-control lease."""

    enabled: bool
    authority_eligible: bool
    applicable: bool
    reason: str
    allowed_actions: tuple[str, ...] | None
    current_reserve: float | None
    activation_reserve: float | None
    lease_frames: int | None
    pickup_delay_frames: tuple[int, ...]
    root_active_action: str | None
    root_held_desired_action: str | None
    root_pending_action: str | None
    hostile_birth_uncertainty_frames: int
    movement_scale_bounds: tuple[float, float]
    actions: tuple[ActionControlReserve, ...] = ()

    def record(self) -> dict[str, object]:
        return {
            "schema": "causal-preexhaustion-control-reserve-v1",
            "role": (
                "causal_player_control_reserve_action_authority"
                if self.authority_eligible
                else "no_action_authority"
            ),
            "enabled": self.enabled,
            "authority_eligible": self.authority_eligible,
            "applicable": self.applicable,
            "reason": self.reason,
            "allowed_actions": self.allowed_actions,
            "current_reserve": self.current_reserve,
            "activation_reserve": self.activation_reserve,
            "lease_frames": self.lease_frames,
            "pickup_delay_frames": self.pickup_delay_frames,
            "pipeline_root": {
                "active_action": self.root_active_action,
                "held_desired_action": self.root_held_desired_action,
                "pending_action": self.root_pending_action,
            },
            "pickup_clock_authority": (
                "every_physical_pickup_order_within_lease_including_"
                "no_pickup_not_enemy_manager_frame"
            ),
            "hostile_birth_uncertainty_frames": (
                self.hostile_birth_uncertainty_frames
            ),
            "movement_scale_bounds": self.movement_scale_bounds,
            "actions": [action.record() for action in self.actions],
            "hazard_authority": (
                "none_reaction_reserve_only_no_future_birth_geometry_claim"
            ),
        }


def unavailable_causal_preexhaustion_filter(
    *,
    enabled: bool,
    reason: str,
    hostile_birth_uncertainty_frames: int,
    movement_scale_bounds: tuple[float, float] = (0.0, 1.0),
    pickup_delay_frames: tuple[int, ...] = (),
) -> CausalPreexhaustionFilter:
    """Return an explicit fail-closed result for an unsupported live root."""

    if not reason:
        raise ValueError("unavailable reason must not be empty")
    return CausalPreexhaustionFilter(
        enabled=enabled,
        authority_eligible=False,
        applicable=False,
        reason=reason,
        allowed_actions=None,
        current_reserve=None,
        activation_reserve=None,
        lease_frames=None,
        pickup_delay_frames=pickup_delay_frames,
        root_active_action=None,
        root_held_desired_action=None,
        root_pending_action=None,
        hostile_birth_uncertainty_frames=(
            hostile_birth_uncertainty_frames
        ),
        movement_scale_bounds=movement_scale_bounds,
    )


def _reserve(
    x_low: float,
    x_high: float,
    y_low: float,
    y_high: float,
    bounds: tuple[float, float, float, float],
) -> float:
    left, right, top, bottom = bounds
    return min(
        x_low - left,
        right - x_high,
        y_low - top,
        bottom - y_high,
    )


def _advance_interval(
    low: float,
    high: float,
    *,
    velocity: float,
    minimum_scale: float,
    maximum_scale: float,
    lower_bound: float,
    upper_bound: float,
) -> tuple[float, float]:
    first = velocity * minimum_scale
    second = velocity * maximum_scale
    delta_low = min(first, second)
    delta_high = max(first, second)
    if velocity == 0.0:
        return low, high
    advanced_low = min(
        upper_bound,
        max(lower_bound, low + delta_low),
    )
    advanced_high = min(
        upper_bound,
        max(lower_bound, high + delta_high),
    )
    conservative_low = (
        advanced_low
        if delta_low == 0.0
        else math.nextafter(advanced_low, -math.inf)
    )
    conservative_high = (
        advanced_high
        if delta_high == 0.0
        else math.nextafter(advanced_high, math.inf)
    )
    return (
        max(lower_bound, conservative_low),
        min(upper_bound, conservative_high),
    )


def build_causal_preexhaustion_filter(
    *,
    enabled: bool,
    root: LocalPipelineRoot | None,
    selected_actions: tuple[str, ...],
    action_velocities: Mapping[str, tuple[float, float]],
    delay_frames: tuple[int, ...],
    action_hold_frames: int,
    start_x: float,
    start_y: float,
    bounds: tuple[float, float, float, float],
    player_radius: float,
    hostile_birth_uncertainty_frames: int,
    movement_scale_bounds: tuple[float, float] = (0.0, 1.0),
    physical_lease_frames: int | None = None,
) -> CausalPreexhaustionFilter:
    """Build a finite causal control-reserve filter.

    The hostile-birth term activates the reserve early enough to retain one
    additional observation/reaction lease.  It does not assume a birth
    position or certify future hostile geometry.
    """

    if not enabled:
        return unavailable_causal_preexhaustion_filter(
            enabled=False,
            reason="disabled",
            hostile_birth_uncertainty_frames=(
                hostile_birth_uncertainty_frames
            ),
            movement_scale_bounds=movement_scale_bounds,
            pickup_delay_frames=delay_frames,
        )
    if root is None:
        return unavailable_causal_preexhaustion_filter(
            enabled=True,
            reason="pipeline_root_unavailable",
            hostile_birth_uncertainty_frames=(
                hostile_birth_uncertainty_frames
            ),
            movement_scale_bounds=movement_scale_bounds,
            pickup_delay_frames=delay_frames,
        )
    if (
        not selected_actions
        or len(set(selected_actions)) != len(selected_actions)
    ):
        raise ValueError("selected actions must be nonempty and unique")
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
    ):
        raise ValueError(
            "delay support must be sorted, unique, and nonnegative"
        )
    if action_hold_frames <= 0:
        raise ValueError("action hold must be positive")
    if physical_lease_frames is not None and physical_lease_frames <= 0:
        raise ValueError("physical lease must be positive")
    if hostile_birth_uncertainty_frames < 0:
        raise ValueError("hostile birth uncertainty cannot be negative")
    minimum_scale, maximum_scale = movement_scale_bounds
    if (
        not math.isfinite(minimum_scale)
        or not math.isfinite(maximum_scale)
        or minimum_scale < 0.0
        or maximum_scale < minimum_scale
    ):
        raise ValueError("invalid movement scale bounds")
    left, right, top, bottom = bounds
    if not left < right or not top < bottom:
        raise ValueError("invalid movement bounds")
    if not left <= start_x <= right or not top <= start_y <= bottom:
        raise ValueError("player root is outside movement bounds")
    if not math.isfinite(player_radius) or player_radius < 0.0:
        raise ValueError("player radius must be finite and nonnegative")

    required_actions = {
        root.active_action,
        root.held_desired_action,
        *selected_actions,
    }
    if root.pending_action is not None:
        required_actions.add(root.pending_action)
    missing = required_actions - action_velocities.keys()
    if missing:
        raise ValueError(f"missing action velocities: {sorted(missing)}")

    lease_frames = (
        action_hold_frames + max(delay_frames)
        if physical_lease_frames is None
        else physical_lease_frames
    )
    reaction_frames = lease_frames + hostile_birth_uncertainty_frames
    maximum_axis_speed = max(
        max(abs(velocity_x), abs(velocity_y))
        for velocity_x, velocity_y in action_velocities.values()
    )
    current_reserve = _reserve(
        start_x,
        start_x,
        start_y,
        start_y,
        bounds,
    )
    activation_reserve = (
        player_radius
        + maximum_axis_speed * maximum_scale * reaction_frames
    )
    if current_reserve > activation_reserve:
        return CausalPreexhaustionFilter(
            enabled=True,
            authority_eligible=True,
            applicable=False,
            reason="interior_reserve_sufficient",
            allowed_actions=None,
            current_reserve=current_reserve,
            activation_reserve=activation_reserve,
            lease_frames=lease_frames,
            pickup_delay_frames=delay_frames,
            root_active_action=root.active_action,
            root_held_desired_action=root.held_desired_action,
            root_pending_action=root.pending_action,
            hostile_birth_uncertainty_frames=(
                hostile_birth_uncertainty_frames
            ),
            movement_scale_bounds=movement_scale_bounds,
        )

    action_reserves: list[ActionControlReserve] = []
    for selected_action in selected_actions:
        branches = enumerate_local_pipeline_branches(
            root=root,
            selected_action=selected_action,
            delay_frames=delay_frames,
            horizon_frames=lease_frames,
        )
        branch_lease_reserves: list[float] = []
        for branch in branches:
            x_low = x_high = float(start_x)
            y_low = y_high = float(start_y)
            minimum_lease_reserve = current_reserve
            for active_action in branch.active_actions:
                velocity_x, velocity_y = action_velocities[active_action]
                x_low, x_high = _advance_interval(
                    x_low,
                    x_high,
                    velocity=velocity_x,
                    minimum_scale=minimum_scale,
                    maximum_scale=maximum_scale,
                    lower_bound=left,
                    upper_bound=right,
                )
                y_low, y_high = _advance_interval(
                    y_low,
                    y_high,
                    velocity=velocity_y,
                    minimum_scale=minimum_scale,
                    maximum_scale=maximum_scale,
                    lower_bound=top,
                    upper_bound=bottom,
                )
                minimum_lease_reserve = min(
                    minimum_lease_reserve,
                    _reserve(x_low, x_high, y_low, y_high, bounds),
                )
            branch_lease_reserves.append(minimum_lease_reserve)
        action_reserves.append(
            ActionControlReserve(
                action=selected_action,
                branch_count=len(branches),
                worst_lease_reserve=min(branch_lease_reserves),
            )
        )

    allowed = tuple(
        action.action
        for action in action_reserves
        if action.worst_lease_reserve >= current_reserve
    )
    reason = "nondegrading_control_reserve_found"
    if not allowed:
        best = max(
            action.worst_lease_reserve for action in action_reserves
        )
        allowed = tuple(
            action.action
            for action in action_reserves
            if action.worst_lease_reserve == best
        )
        reason = "pending_motion_forces_reserve_loss_choose_maximum"

    return CausalPreexhaustionFilter(
        enabled=True,
        authority_eligible=True,
        applicable=True,
        reason=reason,
        allowed_actions=allowed,
        current_reserve=current_reserve,
        activation_reserve=activation_reserve,
        lease_frames=lease_frames,
        pickup_delay_frames=delay_frames,
        root_active_action=root.active_action,
        root_held_desired_action=root.held_desired_action,
        root_pending_action=root.pending_action,
        hostile_birth_uncertainty_frames=hostile_birth_uncertainty_frames,
        movement_scale_bounds=movement_scale_bounds,
        actions=tuple(action_reserves),
    )


__all__ = [
    "ActionControlReserve",
    "CausalPreexhaustionFilter",
    "build_causal_preexhaustion_filter",
    "unavailable_causal_preexhaustion_filter",
]
