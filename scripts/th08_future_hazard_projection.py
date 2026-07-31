"""Versioned ordinary-stage future-hazard publication for TH08 policies."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from th08_future_birth_envelope import (
    FUTURE_BIRTH_SECTOR_SEMANTICS_VERSION,
    FutureDirectFire,
    lower_complete_future_birth_sectors,
)
from touhou_control.corridor import (
    AabbTrajectoryHazard,
    AnnularSectorTrajectoryHazard,
)
from touhou_control.hazard_coverage import (
    HazardCoverageAssessment,
    HazardCoverageClass,
    HazardCoverageSlab,
    assess_hazard_coverage,
)
from touhou_control.pipeline_identity import VersionIdentity


ORDINARY_FUTURE_HAZARD_PROJECTION_SCHEMA = (
    "th08-ordinary-future-hazard-projection-v3-annular-sector-and-aabb"
)


def _trajectory_record(
    trajectory: AnnularSectorTrajectoryHazard,
) -> dict[str, object]:
    return {
        "origin": [trajectory.origin_x, trajectory.origin_y],
        "angle": [trajectory.minimum_angle, trajectory.maximum_angle],
        "minimum_radii": trajectory.minimum_radii,
        "maximum_radii": trajectory.maximum_radii,
        "half_extent_radius": trajectory.half_extent_radius,
        "origin_uncertainty": trajectory.origin_uncertainty,
        "base_uncertainty": trajectory.base_uncertainty,
        "uncertainty_per_frame": trajectory.uncertainty_per_frame,
    }


def _aabb_trajectory_record(
    trajectory: AabbTrajectoryHazard,
) -> list[dict[str, float] | None]:
    return [
        (
            None
            if sample is None
            else {
                "x": sample.x,
                "y": sample.y,
                "half_width": sample.half_width,
                "half_height": sample.half_height,
                "base_uncertainty": sample.base_uncertainty,
                "uncertainty_per_frame": sample.uncertainty_per_frame,
            }
        )
        for sample in trajectory.samples
    ]


@dataclass(frozen=True)
class OrdinaryFutureHazardProjection:
    """Complete or fail-closed future hostility rooted at one observation."""

    root_frame: int
    horizon_frames: int
    trajectories: tuple[AnnularSectorTrajectoryHazard, ...]
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...]
    source_closure_complete: bool
    source_closure_reason: str | None
    source_semantics_version: str
    producer_count: int
    digest: str
    version: VersionIdentity
    coverage: HazardCoverageAssessment

    def __post_init__(self) -> None:
        if self.root_frame < 0 or self.horizon_frames < 0:
            raise ValueError("future-hazard projection horizon is invalid")
        if not self.source_semantics_version:
            raise ValueError("source semantics version must not be empty")
        if self.producer_count < 0:
            raise ValueError("producer count cannot be negative")
        if len(self.digest) != 64:
            raise ValueError("future-hazard digest must be SHA-256")
        if self.coverage.root_frame != self.root_frame:
            raise ValueError("future-hazard coverage root disagrees")
        if (
            self.coverage.horizon_frame
            != self.root_frame + self.horizon_frames
        ):
            raise ValueError("future-hazard coverage horizon disagrees")
        if self.source_closure_complete != self.coverage.complete:
            raise ValueError("source closure and coverage completeness disagree")
        if self.source_closure_complete and self.source_closure_reason is not None:
            raise ValueError("complete source closure cannot carry a reason")
        if (
            not self.source_closure_complete
            and not self.source_closure_reason
        ):
            raise ValueError("incomplete source closure requires a reason")

    @property
    def horizon_frame(self) -> int:
        return self.root_frame + self.horizon_frames

    def trajectories_for_policy(
        self,
        *,
        source_frame: int,
        horizon_frames: int,
    ) -> tuple[AnnularSectorTrajectoryHazard, ...]:
        """Rebase root-relative envelopes onto one future policy epoch."""

        if source_frame < self.root_frame:
            raise ValueError("policy source predates future-hazard root")
        if horizon_frames < 0:
            raise ValueError("policy hazard horizon cannot be negative")
        if source_frame + horizon_frames > self.horizon_frame:
            raise ValueError(
                "future-hazard projection does not cover policy horizon"
            )
        offset = source_frame - self.root_frame
        return tuple(
            trajectory.rebase(
                offset=offset,
                horizon_frames=horizon_frames,
            )
            for trajectory in self.trajectories
        )

    def aabb_trajectories_for_policy(
        self,
        *,
        source_frame: int,
        horizon_frames: int,
    ) -> tuple[AabbTrajectoryHazard, ...]:
        if source_frame < self.root_frame:
            raise ValueError("policy source predates future-hazard root")
        if horizon_frames < 0:
            raise ValueError("policy hazard horizon cannot be negative")
        if source_frame + horizon_frames > self.horizon_frame:
            raise ValueError(
                "future-hazard projection does not cover policy horizon"
            )
        offset = source_frame - self.root_frame
        return tuple(
            trajectory.rebase(
                offset=offset,
                horizon_frames=horizon_frames,
            )
            for trajectory in self.aabb_trajectories
        )

    def record(self) -> dict[str, object]:
        return {
            "schema": ORDINARY_FUTURE_HAZARD_PROJECTION_SCHEMA,
            "root_frame": self.root_frame,
            "horizon_frames": self.horizon_frames,
            "source_closure_complete": self.source_closure_complete,
            "source_closure_reason": self.source_closure_reason,
            "source_semantics_version": self.source_semantics_version,
            "producer_count": self.producer_count,
            "trajectory_count": len(self.trajectories),
            "aabb_trajectory_count": len(self.aabb_trajectories),
            "digest": self.digest,
            "version": self.version.record(),
            "coverage": self.coverage.record(),
        }


def _build_projection(
    *,
    root_frame: int,
    horizon_frames: int,
    trajectories: tuple[AnnularSectorTrajectoryHazard, ...],
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...],
    source_closure_complete: bool,
    source_closure_reason: str | None,
    source_semantics_version: str,
    producer_count: int,
) -> OrdinaryFutureHazardProjection:
    identity_payload = {
        "schema": ORDINARY_FUTURE_HAZARD_PROJECTION_SCHEMA,
        "root_frame": root_frame,
        "horizon_frames": horizon_frames,
        "source_closure_complete": source_closure_complete,
        "source_closure_reason": source_closure_reason,
        "source_semantics_version": source_semantics_version,
        "birth_semantics_version": (
            FUTURE_BIRTH_SECTOR_SEMANTICS_VERSION
        ),
        "producer_count": producer_count,
        "trajectories": [
            _trajectory_record(trajectory)
            for trajectory in trajectories
        ],
        "aabb_trajectories": [
            _aabb_trajectory_record(trajectory)
            for trajectory in aabb_trajectories
        ],
    }
    digest = hashlib.sha256(
        json.dumps(
            identity_payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    version = VersionIdentity.from_mapping(
        "th08-ordinary-future-hazard-projection-v3",
        {
            "root_frame": root_frame,
            "horizon_frames": horizon_frames,
            "digest": digest,
            "source_semantics_version": source_semantics_version,
        },
    )
    if horizon_frames == 0:
        slabs: tuple[HazardCoverageSlab, ...] = ()
    else:
        slabs = (
            HazardCoverageSlab(
                start_frame=root_frame + 1,
                end_frame=root_frame + horizon_frames,
                coverage_class=(
                    HazardCoverageClass.BOUNDED_ENVELOPE
                    if source_closure_complete
                    else HazardCoverageClass.UNKNOWN
                ),
                source="th08_ordinary_future_sources",
                version=version,
                rationale=(
                    "all reachable ordinary ECL/timeline producers were "
                    "lowered into consumed continuous annular-sector and "
                    "future hostile-body AABB envelopes"
                    if source_closure_complete
                    else str(source_closure_reason)
                ),
            ),
        )
    coverage = assess_hazard_coverage(
        root_frame=root_frame,
        horizon_frame=root_frame + horizon_frames,
        slabs=slabs,
    )
    return OrdinaryFutureHazardProjection(
        root_frame=root_frame,
        horizon_frames=horizon_frames,
        trajectories=trajectories,
        aabb_trajectories=aabb_trajectories,
        source_closure_complete=source_closure_complete,
        source_closure_reason=source_closure_reason,
        source_semantics_version=source_semantics_version,
        producer_count=producer_count,
        digest=digest,
        version=version,
        coverage=coverage,
    )


def complete_future_hazard_projection(
    *,
    root_frame: int,
    horizon_frames: int,
    events: tuple[FutureDirectFire, ...],
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...] = (),
    source_semantics_version: str,
) -> OrdinaryFutureHazardProjection:
    envelopes = lower_complete_future_birth_sectors(
        events,
        horizon_frames=horizon_frames,
    )
    return _build_projection(
        root_frame=root_frame,
        horizon_frames=horizon_frames,
        trajectories=tuple(
            envelope.trajectory for envelope in envelopes
        ),
        aabb_trajectories=aabb_trajectories,
        source_closure_complete=True,
        source_closure_reason=None,
        source_semantics_version=source_semantics_version,
        producer_count=len(events) + len(aabb_trajectories),
    )


def unknown_future_hazard_projection(
    *,
    root_frame: int,
    horizon_frames: int,
    reason: str,
    source_semantics_version: str,
) -> OrdinaryFutureHazardProjection:
    if not reason:
        raise ValueError("unknown future-hazard projection requires a reason")
    return _build_projection(
        root_frame=root_frame,
        horizon_frames=horizon_frames,
        trajectories=(),
        aabb_trajectories=(),
        source_closure_complete=False,
        source_closure_reason=reason,
        source_semantics_version=source_semantics_version,
        producer_count=0,
    )


__all__ = [
    "ORDINARY_FUTURE_HAZARD_PROJECTION_SCHEMA",
    "OrdinaryFutureHazardProjection",
    "complete_future_hazard_projection",
    "unknown_future_hazard_projection",
]
