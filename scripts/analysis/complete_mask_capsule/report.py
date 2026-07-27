"""Compact retained report construction."""

from __future__ import annotations

from collections import Counter

from analysis.partial_witness_capsule.serialization import (
    canonical_sha256,
    file_sha256,
)

from .solve import audit_root
from .trace import read_complete_mask_roots
from .types import CompleteMaskWorkload


def _failure_reason(failure: str) -> str:
    parts = failure.split(": ", 2)
    return parts[-1] if len(parts) == 3 else failure


def _failure_samples(failures: list[str]) -> tuple[str, ...]:
    if len(failures) <= 6:
        return tuple(failures)
    return (*failures[:5], failures[-1])


def audit(
    *,
    workloads: tuple[CompleteMaskWorkload, ...],
    horizon: int,
    decision_frame_support: tuple[int, ...],
    root_limit: int,
) -> dict[str, object]:
    if not 1 <= horizon <= 80:
        raise ValueError("horizon must be in [1, 80]")
    if root_limit <= 0:
        raise ValueError("root limit must be positive")
    records = []
    for workload in workloads:
        roots, failures = read_complete_mask_roots(workload.trace)
        missing_capsules = tuple(
            root
            for root in roots
            if not (workload.capsule_dir / root.capsule).is_file()
        )
        failures.extend(
            f"frame {root.decision_frame}: FileNotFoundError: "
            f"joined capsule is absent: {root.capsule}"
            for root in missing_capsules
        )
        failure_counts = Counter(
            _failure_reason(failure)
            for failure in failures
        )
        eligible = tuple(
            root
            for root in roots
            if (
                not root.trace_state_viable
                and root.query_frame >= root.source_frame
                and root.query_frame - root.source_frame + horizon <= 80
                and (workload.capsule_dir / root.capsule).is_file()
            )
        )
        selected = eligible[:root_limit]
        records.append(
            {
                "workload": workload.name,
                "stage": workload.stage,
                "physical_interpretation": (
                    workload.physical_interpretation
                ),
                "trace": {
                    "path": str(workload.trace),
                    "bytes": workload.trace.stat().st_size,
                    "sha256": file_sha256(workload.trace),
                },
                "read_joined_root_count": len(roots),
                "root_validation_failure_count": len(failures),
                "root_validation_failure_counts": dict(
                    sorted(failure_counts.items())
                ),
                "root_validation_failure_samples": (
                    _failure_samples(failures)
                ),
                "missing_capsule_count": len(missing_capsules),
                "eligible_boolean_empty_root_count": len(eligible),
                "audited_root_count": len(selected),
                "observations": [
                    audit_root(
                        root,
                        capsule_dir=workload.capsule_dir,
                        horizon=horizon,
                        decision_frame_support=decision_frame_support,
                    )
                    for root in selected
                ],
            }
        )
    report = {
        "schema": "th08-g5-complete-mask-capsule-audit-v2",
        "scope": {
            "authority": (
                "offline exact restricted finite-model witness; "
                "no physical or action authority"
            ),
            "action_alphabet": (
                "all 36 canonical no-Bomb complete-mask root actions"
            ),
            "continuation_contract": (
                "stationary exact held complete-mask token"
            ),
            "horizon_frames": horizon,
            "decision_frame_support": decision_frame_support,
            "coverage_contract": (
                "UNKNOWN or missing future-event slabs block physical "
                "interpretation even when the finite model is feasible"
            ),
        },
        "workloads": records,
    }
    report["report_digest"] = canonical_sha256(report)
    return report


__all__ = ["audit"]
