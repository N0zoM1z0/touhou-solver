"""Versioned exact continuation leases for ordinary non-spell control.

A lease is not a new planner.  It retains one action that already passed the
computation-delay/action-conditioned predecessor.  Later observations may
condition away hidden pickup branches, but may not add a branch or change the
held complete mask.  Any contract mismatch revokes the lease.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from .models import EnemyBody, EnemyPoolSnapshot
from touhou_control.local_pipeline_oracle import (
    DelayedIssuePipelineBranch,
    LocalPipelineRoot,
)
from touhou_control.pipeline_identity import VersionIdentity


@dataclass(frozen=True)
class OrdinaryContinuationLease:
    """One immutable delayed-predecessor witness retained across decisions."""

    lease_id: str
    gameplay_epoch: int
    stage_route_index: int
    action: str
    mask: int
    root_frame: int
    issue_frame: int
    horizon_frames: int
    projection_digest: str
    projection_source: str
    projection_version: VersionIdentity
    pipeline_root: LocalPipelineRoot
    issue_delay: int
    pickup_delay_support: tuple[int, ...]
    branches: tuple[DelayedIssuePipelineBranch, ...]
    positions_by_step: tuple[tuple[tuple[float, float], ...], ...]
    certified_enemy_boxes_by_step: tuple[
        tuple[ContinuationCertifiedAabb, ...], ...
    ]
    minimum_clearance: float
    fresh_geometry_frame: int
    fresh_geometry_changed: bool

    def __post_init__(self) -> None:
        if not self.lease_id or not self.action or not self.projection_digest:
            raise ValueError("continuation lease identity cannot be empty")
        if self.issue_frame < self.root_frame:
            raise ValueError("lease issue precedes its root")
        if self.issue_delay != self.issue_frame - self.root_frame:
            raise ValueError("lease issue delay does not match its clocks")
        if self.horizon_frames <= self.issue_delay:
            raise ValueError("lease horizon must extend beyond issue")
        if len(self.positions_by_step) != self.horizon_frames + 1:
            raise ValueError("lease positions do not cover its horizon")
        if len(self.certified_enemy_boxes_by_step) != self.horizon_frames + 1:
            raise ValueError("lease enemy boxes do not cover its horizon")
        if not self.branches:
            raise ValueError("continuation lease requires hidden branches")
        if any(
            len(step) != len(self.branches)
            for step in self.positions_by_step
        ):
            raise ValueError("lease position and branch counts differ")
        if any(
            branch.selected_action != self.action
            or branch.issue_delay != self.issue_delay
            for branch in self.branches
        ):
            raise ValueError("lease branches do not match selected action")
        if self.minimum_clearance <= 0.0:
            raise ValueError("continuation lease requires positive clearance")

    @property
    def horizon_frame(self) -> int:
        return self.root_frame + self.horizon_frames

    def record(self) -> dict[str, object]:
        return {
            "schema": "th08-ordinary-terminal-continuation-lease-v3",
            "lease_id": self.lease_id,
            "gameplay_epoch": self.gameplay_epoch,
            "stage_route_index": self.stage_route_index,
            "action": self.action,
            "mask": self.mask,
            "root_frame": self.root_frame,
            "issue_frame": self.issue_frame,
            "horizon_frame": self.horizon_frame,
            "projection_digest": self.projection_digest,
            "projection_source": self.projection_source,
            "projection_version": self.projection_version.record(),
            "issue_delay": self.issue_delay,
            "pickup_delay_support": self.pickup_delay_support,
            "input_publication_to_motion_lag_frames": (
                self.pipeline_root.input_publication_to_motion_lag_frames
            ),
            "pipeline_branch_count": len(self.branches),
            "minimum_clearance": self.minimum_clearance,
            "maximum_certified_enemy_box_count": max(
                map(len, self.certified_enemy_boxes_by_step),
                default=0,
            ),
            "fresh_geometry_frame": self.fresh_geometry_frame,
            "fresh_geometry_changed": self.fresh_geometry_changed,
        }


@dataclass(frozen=True)
class ContinuationLeaseCheck:
    """Fail-closed result for one observable lease-consumption seam."""

    valid: bool
    reason: str
    age_frames: int
    remaining_frames: int
    matched_branch_count: int = 0

    def record(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "age_frames": self.age_frames,
            "remaining_frames": self.remaining_frames,
            "matched_branch_count": self.matched_branch_count,
        }


@dataclass(frozen=True)
class ContinuationCertifiedAabb:
    """One already-certified enemy occupancy envelope at one frame."""

    x: float
    y: float
    half_width: float
    half_height: float

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value)
            for value in (self.x, self.y, self.half_width, self.half_height)
        ):
            raise ValueError("certified enemy AABB must be finite")
        if self.half_width < 0.0 or self.half_height < 0.0:
            raise ValueError("certified enemy AABB extent cannot be negative")


@dataclass(frozen=True)
class ContinuationGeometryCheck:
    """Set-containment result for fresh bodies under one old witness."""

    valid: bool
    reason: str
    checked_frame_count: int
    checked_body_count: int
    first_uncontained_pointer: int | None = None
    first_uncontained_frame: int | None = None

    def record(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "checked_frame_count": self.checked_frame_count,
            "checked_body_count": self.checked_body_count,
            "first_uncontained_pointer": self.first_uncontained_pointer,
            "first_uncontained_frame": self.first_uncontained_frame,
        }


def _float32_bits(value: float) -> bytes:
    return struct.pack("<f", value)


def _branch_observation(
    lease: OrdinaryContinuationLease,
    branch: DelayedIssuePipelineBranch,
    *,
    age_frames: int,
) -> tuple[str, bool, int | None]:
    active_action = (
        lease.pipeline_root.active_action
        if age_frames == 0
        else branch.published_actions[age_frames - 1]
    )
    if branch.write_required:
        assert branch.new_delay is not None
        pending_end = branch.issue_delay + branch.new_delay
        pending = age_frames <= pending_end
        remaining = pending_end - age_frames if pending else None
    elif (
        lease.pipeline_root.pending_action is not None
        and branch.older_remaining is not None
    ):
        pending_end = branch.older_remaining
        pending = age_frames <= pending_end
        remaining = pending_end - age_frames if pending else None
    else:
        pending = False
        remaining = None
    return active_action, pending, remaining


def check_continuation_lease_capture(
    lease: OrdinaryContinuationLease,
    *,
    gameplay_epoch: int,
    stage_route_index: int,
    spell_active: bool,
    player_phase: int,
    unit_time_scale: bool,
    current_frame: int,
    player_x: float,
    player_y: float,
    pipeline_root: LocalPipelineRoot | None,
    minimum_remaining_frames: int,
) -> ContinuationLeaseCheck:
    """Condition an old witness on the newly observable pipeline root."""

    age = current_frame - lease.root_frame
    remaining = lease.horizon_frames - age

    def reject(reason: str) -> ContinuationLeaseCheck:
        return ContinuationLeaseCheck(False, reason, age, remaining)

    if gameplay_epoch != lease.gameplay_epoch:
        return reject("gameplay_epoch_mismatch")
    if stage_route_index != lease.stage_route_index:
        return reject("stage_route_mismatch")
    if spell_active:
        return reject("spell_active")
    if player_phase in (1, 2):
        return reject("player_phase_ineligible")
    if not unit_time_scale:
        return reject("nonunit_time_scale")
    if current_frame < lease.issue_frame:
        return reject("observation_precedes_lease_issue")
    if minimum_remaining_frames <= 0:
        return reject("invalid_minimum_remaining_frames")
    if remaining < minimum_remaining_frames:
        return reject("terminal_continuation_expired")
    if age < 0 or age >= len(lease.positions_by_step):
        return reject("age_outside_witness")
    if pipeline_root is None:
        return reject("pipeline_root_unavailable")
    if pipeline_root.held_desired_action != lease.action:
        return reject("held_action_mismatch")
    if (
        pipeline_root.input_publication_to_motion_lag_frames
        != lease.pipeline_root.input_publication_to_motion_lag_frames
    ):
        return reject("input_motion_phase_contract_mismatch")
    if (
        pipeline_root.pending_action is not None
        and pipeline_root.pending_action != lease.action
    ):
        return reject("pending_action_mismatch")

    observed_x = _float32_bits(player_x)
    observed_y = _float32_bits(player_y)
    matched_remaining: set[int] = set()
    matched_count = 0
    for branch_index, branch in enumerate(lease.branches):
        active_action, pending, branch_remaining = _branch_observation(
            lease,
            branch,
            age_frames=age,
        )
        if active_action != pipeline_root.active_action:
            continue
        expected_x, expected_y = lease.positions_by_step[age][branch_index]
        if (
            _float32_bits(expected_x) != observed_x
            or _float32_bits(expected_y) != observed_y
        ):
            continue
        if pipeline_root.pending_action is None:
            if pending:
                continue
        else:
            if not pending or branch_remaining is None:
                continue
            if branch_remaining not in pipeline_root.remaining_delay_support:
                continue
            matched_remaining.add(branch_remaining)
        matched_count += 1

    if not matched_count:
        return reject("pipeline_branch_or_position_mismatch")
    if (
        pipeline_root.pending_action is not None
        and matched_remaining != set(pipeline_root.remaining_delay_support)
    ):
        return reject("pending_support_not_covered")
    return ContinuationLeaseCheck(
        True,
        "exact_continuation_branch_observed",
        age,
        remaining,
        matched_count,
    )


def check_continuation_lease_issue(
    lease: OrdinaryContinuationLease,
    *,
    gameplay_epoch: int,
    stage_route_index: int,
    spell_active: bool,
    player_phase: int,
    issue_frame: int,
    selected_action: str,
    selected_mask: int,
    minimum_remaining_frames: int,
) -> ContinuationLeaseCheck:
    """Recheck immutable context and remaining horizon at final issue."""

    age = issue_frame - lease.root_frame
    remaining = lease.horizon_frames - age

    def reject(reason: str) -> ContinuationLeaseCheck:
        return ContinuationLeaseCheck(False, reason, age, remaining)

    if gameplay_epoch != lease.gameplay_epoch:
        return reject("gameplay_epoch_mismatch_at_issue")
    if stage_route_index != lease.stage_route_index:
        return reject("stage_route_mismatch_at_issue")
    if spell_active:
        return reject("spell_active_at_issue")
    if player_phase in (1, 2):
        return reject("player_phase_ineligible_at_issue")
    if selected_action != lease.action or selected_mask != lease.mask:
        return reject("selected_action_changed_without_predecessor")
    if remaining < minimum_remaining_frames:
        return reject("terminal_continuation_expired_at_issue")
    return ContinuationLeaseCheck(
        True,
        "exact_continuation_issue_valid",
        age,
        remaining,
    )


def check_continuation_enemy_geometry(
    lease: OrdinaryContinuationLease,
    *,
    body_root_frame: int,
    valid_from_frame: int,
    enemy_bodies: tuple[EnemyBody, ...],
    numeric_guard: float = 2.0e-4,
) -> ContinuationGeometryCheck:
    """Require the fresh observed body seam to remain inside the old proof.

    ``enemy_bodies`` are rooted at ``body_root_frame``.  Their linearly
    aligned AABBs at the first observable frame must be contained in the union
    of body boxes already consumed by the lease.  The remaining future is the
    immutable causal source trajectory from the original exact predecessor;
    restarting a second linear forecast from each observation would replace,
    rather than condition, that proof and spuriously reject timed native
    acceleration.  Removed bodies are harmless; new or changed bodies are
    accepted only when an old active/future-source box contains the observed
    seam.  Complete source/topology coverage is a lease-construction
    precondition outside this function.
    """

    if not math.isfinite(numeric_guard) or numeric_guard < 0.0:
        raise ValueError("geometry numeric guard must be finite and nonnegative")
    start_frame = max(body_root_frame, valid_from_frame)
    end_frame = lease.horizon_frame
    if body_root_frame < lease.root_frame:
        return ContinuationGeometryCheck(
            False,
            "body_root_precedes_lease_root",
            0,
            len(enemy_bodies),
        )
    if start_frame > end_frame:
        return ContinuationGeometryCheck(
            False,
            "geometry_check_after_lease_horizon",
            0,
            len(enemy_bodies),
        )

    frame = start_frame
    lease_step = frame - lease.root_frame
    body_step = frame - body_root_frame
    certified = lease.certified_enemy_boxes_by_step[lease_step]
    for body in enemy_bodies:
        robust_expansion = min(12.0, 0.5 * body_step)
        x = body.x + body.vx * body_step
        y = body.y + body.vy * body_step
        half_width = (
            body.half_width
            + body.uncertainty
            + robust_expansion
        )
        half_height = (
            body.half_height
            + body.uncertainty
            + robust_expansion
        )
        if any(
            abs(x - box.x) + half_width
            <= box.half_width + numeric_guard
            and abs(y - box.y) + half_height
            <= box.half_height + numeric_guard
            for box in certified
        ):
            continue
        return ContinuationGeometryCheck(
            False,
            "fresh_body_envelope_not_contained",
            1,
            len(enemy_bodies),
            body.pointer,
            frame,
        )
    return ContinuationGeometryCheck(
        True,
        "fresh_body_observation_seam_contained",
        1,
        len(enemy_bodies),
    )


def check_continuation_enemy_snapshot(
    lease: OrdinaryContinuationLease,
    *,
    snapshot: EnemyPoolSnapshot,
    numeric_guard: float = 2.0e-4,
) -> ContinuationGeometryCheck:
    """Condition a lease on one stable native observation at its own frame."""

    if not snapshot.stable:
        return ContinuationGeometryCheck(
            False,
            "fresh_enemy_snapshot_unstable",
            0,
            len(snapshot.bodies),
        )
    return check_continuation_enemy_geometry(
        lease,
        body_root_frame=snapshot.frame_after,
        valid_from_frame=snapshot.frame_after,
        enemy_bodies=snapshot.bodies,
        numeric_guard=numeric_guard,
    )


__all__ = [
    "ContinuationCertifiedAabb",
    "ContinuationGeometryCheck",
    "ContinuationLeaseCheck",
    "OrdinaryContinuationLease",
    "check_continuation_lease_capture",
    "check_continuation_enemy_geometry",
    "check_continuation_enemy_snapshot",
    "check_continuation_lease_issue",
]
