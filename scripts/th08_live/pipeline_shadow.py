"""TH08 adapter for canonical pipeline roots and fail-closed coverage trace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from touhou_control.hazard_coverage import (
    HazardCoverageAssessment,
    HazardCoverageClass,
    HazardCoverageSlab,
    assess_hazard_coverage,
)
from touhou_control.local_pipeline_oracle import LocalPipelineRoot
from touhou_control.pipeline_identity import (
    CanonicalPipelineRoot,
    PipelineObservationIdentity,
    PipelineQueryIdentity,
    VersionIdentity,
)


PIPELINE_SHADOW_ROLE = "shadow_no_action_authority"


class PendingEstimate(Protocol):
    expected_mask: int
    remaining_frames: tuple[int, ...]
    snapshot_age: int
    issue_age: int
    overdue: bool


class CorridorVersionSource(Protocol):
    source_frame: int
    snapshot_frame: int | None
    context_key: tuple[int, int, int | None] | None
    future_hazard_version: VersionIdentity | None


@dataclass(frozen=True)
class PipelineShadowSnapshot:
    local_root: LocalPipelineRoot | None
    canonical_identity: PipelineQueryIdentity | None
    hazard_coverage: HazardCoverageAssessment
    record: dict[str, object]


def _corridor_version(
    namespace: str,
    solution: CorridorVersionSource | None,
) -> VersionIdentity:
    if solution is None:
        return VersionIdentity.from_mapping(
            namespace,
            {"available": False},
        )
    context = solution.context_key
    return VersionIdentity.from_mapping(
        namespace,
        {
            "available": True,
            "context_epoch": context[0] if context is not None else None,
            "context_route": context[1] if context is not None else None,
            "context_spell": context[2] if context is not None else None,
            "snapshot_frame": solution.snapshot_frame,
            "source_frame": solution.source_frame,
        },
    )


def corridor_hazard_version(
    solution: CorridorVersionSource | None,
) -> VersionIdentity:
    """Return the exact hazard-snapshot identity for one corridor policy."""

    future_version = (
        getattr(solution, "future_hazard_version", None)
        if solution is not None
        else None
    )
    if future_version is not None:
        return future_version
    return _corridor_version("th08-corridor-hazard-snapshot-v1", solution)


def unknown_future_coverage(
    *,
    root_frame: int,
    horizon_frames: int,
    hazard_version: VersionIdentity,
) -> HazardCoverageAssessment:
    horizon_frame = root_frame + horizon_frames
    slab = HazardCoverageSlab(
        start_frame=root_frame + 1,
        end_frame=horizon_frame,
        coverage_class=HazardCoverageClass.UNKNOWN,
        source="th08_unseen_future_hazard_events",
        version=hazard_version,
        rationale=(
            "current snapshots project observed entities but do not "
            "exhaustively cover unseen future births and event geometry"
        ),
    )
    return assess_hazard_coverage(
        root_frame=root_frame,
        horizon_frame=horizon_frame,
        slabs=(slab,),
    )


def build_pipeline_shadow_snapshot(
    *,
    supported_mask: int,
    native_active_mask: int,
    held_desired_mask: int,
    pending_estimate: PendingEstimate | None,
    action_from_mask: Callable[[int], str],
    gameplay_epoch: int,
    stage_route_index: int,
    spell_id: int | None,
    manager_frame: int,
    query_frame: int,
    target_frame: int,
    player_x: float,
    player_y: float,
    hazard_horizon_frames: int,
    corridor_solution: CorridorVersionSource | None,
) -> PipelineShadowSnapshot:
    """Build one trace-only root without modifying estimator or action state."""

    if type(hazard_horizon_frames) is not int or hazard_horizon_frames <= 0:
        raise ValueError("hazard coverage horizon must be positive")
    active_mask = int(native_active_mask) & supported_mask
    held_mask = int(held_desired_mask) & supported_mask
    pending_mask = (
        int(pending_estimate.expected_mask) & supported_mask
        if pending_estimate is not None
        else None
    )
    remaining_support = (
        tuple(pending_estimate.remaining_frames)
        if pending_estimate is not None
        else ()
    )
    estimator_consistent = (
        pending_estimate is None and held_mask == active_mask
    ) or (
        pending_estimate is not None and pending_mask == held_mask
    )

    active_action = action_from_mask(active_mask)
    held_action = action_from_mask(held_mask)
    pending_action = (
        action_from_mask(pending_mask)
        if pending_mask is not None
        else None
    )
    local_root = (
        LocalPipelineRoot(
            active_action=active_action,
            held_desired_action=held_action,
            pending_action=pending_action,
            remaining_delay_support=remaining_support,
        )
        if estimator_consistent
        else None
    )

    hazard_version = corridor_hazard_version(corridor_solution)
    hazard_coverage = unknown_future_coverage(
        root_frame=query_frame,
        horizon_frames=hazard_horizon_frames,
        hazard_version=hazard_version,
    )
    canonical_identity = None
    if estimator_consistent:
        canonical_identity = PipelineQueryIdentity(
            observation=PipelineObservationIdentity.from_coordinates(
                gameplay_epoch=gameplay_epoch,
                stage_route_index=stage_route_index,
                spell_id=spell_id,
                manager_frame=manager_frame,
                query_frame=query_frame,
                target_frame=target_frame,
                player_x=player_x,
                player_y=player_y,
            ),
            root=CanonicalPipelineRoot(
                supported_mask=supported_mask,
                active_mask=active_mask,
                held_desired_mask=held_mask,
                pending_mask=pending_mask,
                remaining_delay_support=remaining_support,
            ),
            observation_version=VersionIdentity.from_mapping(
                "th08-native-decision-observation-v1",
                {
                    "active_source": "input_current",
                    "position_precision": "float32",
                },
            ),
            hazard_version=hazard_version,
            policy_version=_corridor_version(
                "th08-corridor-policy-v1",
                corridor_solution,
            ),
            model_version=VersionIdentity.from_mapping(
                "belief-pipeline-model-v1",
                {
                    "pending_capacity": 1,
                    "issue_semantics": "complete-mask-no-write",
                    "observation_merge": True,
                },
            ),
            clock_version=VersionIdentity.from_mapping(
                "th08-manager-frame-clock-boundary-v1",
                {
                    "authority": "shadow_no_reset_authority",
                    "ce0120": "open",
                    "manager_frame_is_physical_clock": False,
                },
            ),
        )

    record: dict[str, object] = {
        "role": PIPELINE_SHADOW_ROLE,
        "active_action": active_action,
        "active_mask": active_mask,
        "held_desired_action": held_action,
        "held_desired_mask": held_mask,
        "pending_action": pending_action,
        "pending_mask": pending_mask,
        "remaining_delay_support": remaining_support,
        "snapshot_age": (
            pending_estimate.snapshot_age
            if pending_estimate is not None
            else None
        ),
        "issue_age": (
            pending_estimate.issue_age
            if pending_estimate is not None
            else None
        ),
        "overdue": (
            pending_estimate.overdue
            if pending_estimate is not None
            else False
        ),
        "estimator_consistent": estimator_consistent,
        "canonical_status": (
            "available"
            if canonical_identity is not None
            else "estimator_inconsistent"
        ),
        "canonical_identity": (
            canonical_identity.record()
            if canonical_identity is not None
            else None
        ),
        "hazard_coverage": hazard_coverage.record(),
        "clock_authority": "shadow_no_reset_authority",
    }
    return PipelineShadowSnapshot(
        local_root=local_root,
        canonical_identity=canonical_identity,
        hazard_coverage=hazard_coverage,
        record=record,
    )


__all__ = [
    "PIPELINE_SHADOW_ROLE",
    "PipelineShadowSnapshot",
    "build_pipeline_shadow_snapshot",
    "corridor_hazard_version",
    "unknown_future_coverage",
]
