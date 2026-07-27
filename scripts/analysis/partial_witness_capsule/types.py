"""Workload declarations for the retained G3 capsule gate."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from touhou_control.partial_survival_witness import (
    FINITE_MODEL_FEASIBILITY_WITNESS,
    NO_POSITIVE_ATTAINABLE_WITNESS,
    PARTIAL_WITNESS_ON_UNRESOLVED,
)


TARGET_MODES = (
    FINITE_MODEL_FEASIBILITY_WITNESS,
    PARTIAL_WITNESS_ON_UNRESOLVED,
    NO_POSITIVE_ATTAINABLE_WITNESS,
)


@dataclass(frozen=True)
class Workload:
    name: str
    stage: str
    trace: Path
    capsule_dir: Path
    physical_interpretation: str


WORKLOADS = (
    Workload(
        name="lunatic_stage4a_20260726_103856",
        stage="4A",
        trace=Path(
            "artifacts/runtime_reports/"
            "lunatic_route2_stage4a_unattended_20260726_103856.jsonl"
        ),
        capsule_dir=Path(
            "artifacts/viability_audit/raw/"
            "lunatic_route2_stage4a_unattended_20260726_103856"
        ),
        physical_interpretation=(
            "finite-model capsule evidence only; the physical run used the "
            "rejected repeated-counter manager-frame guard"
        ),
    ),
    Workload(
        name="lunatic_stage6b_20260726_011639",
        stage="6B",
        trace=Path(
            "artifacts/runtime_reports/"
            "lunatic_route2_stage6b_unattended_20260726_011639.jsonl"
        ),
        capsule_dir=Path(
            "artifacts/viability_audit/raw/"
            "lunatic_route2_stage6b_unattended_20260726_011639"
        ),
        physical_interpretation=(
            "offline finite-model replay; no alternate-action issue "
            "certificate or live authority is inferred"
        ),
    ),
)
