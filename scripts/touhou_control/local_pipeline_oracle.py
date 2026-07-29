"""Independent scalar oracle for one local input-pipeline certificate.

This module deliberately contains no TH08 geometry or NumPy batching.  It
enumerates the physical action history implied by one observed active action,
one held desired action, and at most one older pending command.  Callers
supply kinematics and a scalar hazard sampler.

The oracle certifies a fixed finite lease.  It does not model a future
controller maximization and therefore makes no recursive-cadence or global
viability claim.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping


@dataclass(frozen=True)
class LocalPipelineRoot:
    """Observable/estimated actuator state at one local decision.

    The current one-pending estimator invariant is explicit:

    * without a pending command, held desired equals observed active;
    * with a pending command, held desired equals that pending command.

    A caller that cannot establish this invariant must not manufacture a
    certificate from this root.
    """

    active_action: str
    held_desired_action: str
    pending_action: str | None = None
    remaining_delay_support: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not self.active_action or not self.held_desired_action:
            raise ValueError("pipeline action names cannot be empty")
        if self.pending_action is None:
            if self.remaining_delay_support:
                raise ValueError(
                    "remaining delay requires an older pending command"
                )
            if self.held_desired_action != self.active_action:
                raise ValueError(
                    "held desired must equal active without a pending command"
                )
            return
        if self.pending_action != self.held_desired_action:
            raise ValueError(
                "one-pending root requires held desired to equal pending"
            )
        if (
            not self.remaining_delay_support
            or tuple(sorted(set(self.remaining_delay_support)))
            != self.remaining_delay_support
            or self.remaining_delay_support[0] <= 0
        ):
            raise ValueError(
                "pending remaining-delay support must be sorted, unique, "
                "and positive"
            )


@dataclass(frozen=True)
class LocalPipelineBranch:
    """One exact hidden actuation history for a selected desired action."""

    selected_action: str
    write_required: bool
    older_remaining: int | None
    new_delay: int | None
    active_actions: tuple[str, ...]


@dataclass(frozen=True)
class ScalarLocalPipelineCertificate:
    """Lexicographic hard measurements over every hidden local branch."""

    action: str
    delay_frames: tuple[int, ...]
    write_required: bool
    branch_count: int
    worst_collisions: int
    min_clearance: float
    cvar_risk: float
    worst_new_delay: int | None
    worst_pending_remaining: int | None


ScalarHazardSample = Callable[[float, float, int], tuple[float, int, float]]
ScalarBoundaryRisk = Callable[[float, float], float]


def enumerate_local_pipeline_branches(
    *,
    root: LocalPipelineRoot,
    selected_action: str,
    delay_frames: tuple[int, ...],
    horizon_frames: int,
) -> tuple[LocalPipelineBranch, ...]:
    """Enumerate exact physical action sequences for one local lease."""

    if not selected_action:
        raise ValueError("selected action cannot be empty")
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
    ):
        raise ValueError(
            "new-command delay support must be sorted, unique, and nonnegative"
        )
    if horizon_frames <= 0:
        raise ValueError("local certificate horizon must be positive")

    write_required = selected_action != root.held_desired_action
    older_support: tuple[int | None, ...] = (
        tuple(root.remaining_delay_support)
        if root.pending_action is not None
        else (None,)
    )
    new_delay_support: tuple[int | None, ...] = (
        tuple(delay_frames) if write_required else (None,)
    )
    branches: list[LocalPipelineBranch] = []
    for older_remaining in older_support:
        for new_delay in new_delay_support:
            actions: list[str] = []
            for physical_step in range(1, horizon_frames + 1):
                if (
                    write_required
                    and new_delay is not None
                    and physical_step > new_delay
                ):
                    motion = selected_action
                elif (
                    root.pending_action is not None
                    and older_remaining is not None
                    and physical_step > older_remaining
                ):
                    motion = root.pending_action
                else:
                    motion = root.active_action
                actions.append(motion)
            branches.append(
                LocalPipelineBranch(
                    selected_action=selected_action,
                    write_required=write_required,
                    older_remaining=older_remaining,
                    new_delay=new_delay,
                    active_actions=tuple(actions),
                )
            )
    return tuple(branches)


def scalar_local_pipeline_certificates(
    *,
    root: LocalPipelineRoot,
    selected_actions: tuple[str, ...],
    action_velocities: Mapping[str, tuple[float, float]],
    delay_frames: tuple[int, ...],
    horizon_frames: int,
    start_x: float,
    start_y: float,
    bounds: tuple[float, float, float, float],
    hazard_sample: ScalarHazardSample,
    boundary_risk: ScalarBoundaryRisk,
    movement_scales: tuple[float, ...] | None = None,
) -> dict[str, ScalarLocalPipelineCertificate]:
    """Evaluate every selected action using scalar branch-by-branch loops."""

    if (
        not selected_actions
        or len(set(selected_actions)) != len(selected_actions)
    ):
        raise ValueError("selected actions must be nonempty and unique")
    required_actions = {
        root.active_action,
        root.held_desired_action,
        *selected_actions,
    }
    if root.pending_action is not None:
        required_actions.add(root.pending_action)
    missing = required_actions - set(action_velocities)
    if missing:
        raise ValueError(f"missing action velocities: {sorted(missing)}")
    left, right, top, bottom = bounds
    if not left <= start_x <= right or not top <= start_y <= bottom:
        raise ValueError("local pipeline root is outside the supplied bounds")
    if movement_scales is not None and len(movement_scales) < horizon_frames:
        raise ValueError(
            "movement scale schedule does not cover the oracle horizon"
        )

    certificates: dict[str, ScalarLocalPipelineCertificate] = {}
    for selected_action in selected_actions:
        branches = enumerate_local_pipeline_branches(
            root=root,
            selected_action=selected_action,
            delay_frames=delay_frames,
            horizon_frames=horizon_frames,
        )
        branch_values: list[
            tuple[int, float, float, int | None, int | None]
        ] = []
        for branch in branches:
            x = float(start_x)
            y = float(start_y)
            risk = 0.0
            collisions = 0
            clearance = math.inf
            for step, active_action in enumerate(
                branch.active_actions,
                start=1,
            ):
                velocity_x, velocity_y = action_velocities[active_action]
                scale = (
                    1.0
                    if movement_scales is None
                    else movement_scales[step - 1]
                )
                x = min(right, max(left, x + velocity_x * scale))
                y = min(bottom, max(top, y + velocity_y * scale))
                hazard_risk, hazard_collisions, hazard_clearance = (
                    hazard_sample(x, y, step)
                )
                risk += boundary_risk(x, y) + hazard_risk
                collisions += hazard_collisions
                clearance = min(clearance, hazard_clearance)
            branch_values.append(
                (
                    collisions,
                    clearance,
                    risk,
                    branch.new_delay,
                    branch.older_remaining,
                )
            )

        worst = max(
            branch_values,
            key=lambda value: (value[0], -value[1], value[2]),
        )
        tail_count = max(1, math.ceil(0.5 * len(branch_values)))
        tail_risks = sorted(
            (value[2] for value in branch_values),
            reverse=True,
        )[:tail_count]
        minimum = min(value[1] for value in branch_values)
        certificates[selected_action] = ScalarLocalPipelineCertificate(
            action=selected_action,
            delay_frames=delay_frames,
            write_required=(
                selected_action != root.held_desired_action
            ),
            branch_count=len(branches),
            worst_collisions=max(value[0] for value in branch_values),
            min_clearance=9999.0 if math.isinf(minimum) else minimum,
            cvar_risk=sum(tail_risks) / len(tail_risks),
            worst_new_delay=worst[3],
            worst_pending_remaining=worst[4],
        )
    return certificates


__all__ = [
    "LocalPipelineBranch",
    "LocalPipelineRoot",
    "ScalarLocalPipelineCertificate",
    "enumerate_local_pipeline_branches",
    "scalar_local_pipeline_certificates",
]
