"""Fail-closed coverage contracts for finite-horizon hazard slabs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .pipeline_identity import VersionIdentity


class HazardCoverageClass(str, Enum):
    """How completely one physical hazard slab is represented."""

    DETERMINISTIC = "DETERMINISTIC"
    FINITE_SUPPORT = "FINITE_SUPPORT"
    BOUNDED_ENVELOPE = "BOUNDED_ENVELOPE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class HazardCoverageSlab:
    """Inclusive physical-frame coverage for the complete hazard set."""

    start_frame: int
    end_frame: int
    coverage_class: HazardCoverageClass
    source: str
    version: VersionIdentity
    rationale: str

    def __post_init__(self) -> None:
        if (
            type(self.start_frame) is not int
            or type(self.end_frame) is not int
            or self.start_frame < 0
            or self.end_frame < self.start_frame
        ):
            raise ValueError("hazard slab frame range is invalid")
        if not self.source:
            raise ValueError("hazard slab source must not be empty")
        if not self.rationale:
            raise ValueError("hazard slab rationale must not be empty")

    @property
    def authority_eligible(self) -> bool:
        """Known classes declare exhaustive or conservative physical cover."""

        return self.coverage_class is not HazardCoverageClass.UNKNOWN

    def record(self) -> dict[str, object]:
        return {
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "coverage_class": self.coverage_class.value,
            "authority_eligible": self.authority_eligible,
            "source": self.source,
            "version": self.version.record(),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class HazardCoverageAssessment:
    """Coverage of all physical transitions after one observable root."""

    root_frame: int
    horizon_frame: int
    covered_through_frame: int
    unknown_from_frame: int | None
    reason: str | None
    slabs: tuple[HazardCoverageSlab, ...]

    @property
    def model_unknown(self) -> bool:
        return self.unknown_from_frame is not None

    @property
    def complete(self) -> bool:
        return not self.model_unknown

    def record(self) -> dict[str, object]:
        return {
            "role": "shadow_no_action_authority",
            "root_frame": self.root_frame,
            "horizon_frame": self.horizon_frame,
            "covered_through_frame": self.covered_through_frame,
            "unknown_from_frame": self.unknown_from_frame,
            "status": "model_unknown" if self.model_unknown else "complete",
            "reason": self.reason,
            "slabs": [slab.record() for slab in self.slabs],
        }


def assess_hazard_coverage(
    *,
    root_frame: int,
    horizon_frame: int,
    slabs: tuple[HazardCoverageSlab, ...],
) -> HazardCoverageAssessment:
    """Cover every root-reachable transition or truncate at the first unknown.

    Frames are inclusive.  The root state itself is already observed, so the
    first hazard transition requiring coverage is ``root_frame + 1``.  A
    missing slab is semantically identical to explicit ``UNKNOWN`` coverage;
    neither may be interpreted as free space.
    """

    if (
        type(root_frame) is not int
        or type(horizon_frame) is not int
        or root_frame < 0
        or horizon_frame < root_frame
    ):
        raise ValueError("coverage horizon is invalid")
    ordered = tuple(sorted(slabs, key=lambda slab: slab.start_frame))
    for previous, current in zip(ordered, ordered[1:]):
        if current.start_frame <= previous.end_frame:
            raise ValueError("hazard coverage slabs must not overlap")

    required = root_frame + 1
    if required > horizon_frame:
        return HazardCoverageAssessment(
            root_frame=root_frame,
            horizon_frame=horizon_frame,
            covered_through_frame=root_frame,
            unknown_from_frame=None,
            reason=None,
            slabs=(),
        )

    used: list[HazardCoverageSlab] = []
    cursor = required
    for slab in ordered:
        if slab.end_frame < cursor:
            continue
        if slab.start_frame > cursor:
            return HazardCoverageAssessment(
                root_frame=root_frame,
                horizon_frame=horizon_frame,
                covered_through_frame=cursor - 1,
                unknown_from_frame=cursor,
                reason="missing_hazard_coverage_slab",
                slabs=tuple(used),
            )
        used.append(slab)
        if not slab.authority_eligible:
            return HazardCoverageAssessment(
                root_frame=root_frame,
                horizon_frame=horizon_frame,
                covered_through_frame=cursor - 1,
                unknown_from_frame=cursor,
                reason=f"unknown_hazard_coverage:{slab.source}",
                slabs=tuple(used),
            )
        cursor = min(slab.end_frame, horizon_frame) + 1
        if cursor > horizon_frame:
            return HazardCoverageAssessment(
                root_frame=root_frame,
                horizon_frame=horizon_frame,
                covered_through_frame=horizon_frame,
                unknown_from_frame=None,
                reason=None,
                slabs=tuple(used),
            )

    return HazardCoverageAssessment(
        root_frame=root_frame,
        horizon_frame=horizon_frame,
        covered_through_frame=cursor - 1,
        unknown_from_frame=cursor,
        reason="missing_hazard_coverage_slab",
        slabs=tuple(used),
    )


def rebase_hazard_coverage(
    coverage: HazardCoverageAssessment,
    *,
    root_frame: int,
    horizon_frame: int,
) -> HazardCoverageAssessment:
    """Restrict an older exhaustive envelope to a later observable root.

    This never extrapolates.  It only intersects already-covered physical
    slabs with ``root+1..horizon`` and then re-runs the ordinary fail-closed
    coverage assessment.
    """

    if root_frame < coverage.root_frame:
        raise ValueError("rebased hazard root predates captured coverage")
    if horizon_frame < root_frame:
        raise ValueError("rebased hazard horizon is invalid")
    if horizon_frame > coverage.horizon_frame:
        raise ValueError("rebased hazard horizon exceeds captured coverage")
    start = root_frame + 1
    slabs = tuple(
        HazardCoverageSlab(
            start_frame=max(start, slab.start_frame),
            end_frame=min(horizon_frame, slab.end_frame),
            coverage_class=slab.coverage_class,
            source=slab.source,
            version=slab.version,
            rationale=slab.rationale,
        )
        for slab in coverage.slabs
        if slab.end_frame >= start and slab.start_frame <= horizon_frame
    )
    return assess_hazard_coverage(
        root_frame=root_frame,
        horizon_frame=horizon_frame,
        slabs=slabs,
    )


__all__ = [
    "HazardCoverageAssessment",
    "HazardCoverageClass",
    "HazardCoverageSlab",
    "assess_hazard_coverage",
    "rebase_hazard_coverage",
]
