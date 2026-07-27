"""Deterministic retained physical roots and independent scalar portfolios."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

from analysis.complete_mask_capsule.solve import build_problem
from analysis.complete_mask_capsule.trace import read_complete_mask_roots
from analysis.complete_mask_capsule.types import CompleteMaskCapsuleRoot
from analysis.partial_witness_capsule.serialization import file_sha256
from th08_pipeline_actions import TH08_COMPLETE_MASK_ACTION_SPACE
from touhou_control.partial_survival_witness import (
    StationaryWitnessPortfolio,
    build_stationary_witness_portfolio,
    replay_stationary_worst_branch,
)
from touhou_control.query_survival import SurvivalQueryProblem


SOURCE_RUN = "lunatic_route2_stage4a_unattended_20260728_005108"
SOURCE_TRACE_SHA256 = (
    "93037d9febe609accd44eb150150088c29610443783a4434328478409fee41b0"
)
HIT_FRAMES = (
    4259,
    11726,
    12357,
    13405,
    19017,
    21215,
    22063,
    31161,
    31625,
    42033,
)


@dataclass(frozen=True)
class PreparedWitnessWorkload:
    root: CompleteMaskCapsuleRoot
    problem: SurvivalQueryProblem
    query: dict[str, object]
    expected: StationaryWitnessPortfolio
    capsule_sha256: str
    lowering_ms: float
    oracle_ms: float

    @property
    def identity(self) -> str:
        return self.root.identity.digest


@dataclass(frozen=True)
class PreparedPhysicalReservoir:
    workloads: tuple[PreparedWitnessWorkload, ...]
    trace_sha256: str
    trace_read_ms: float
    accepted_root_count: int
    boolean_empty_root_count: int
    rejected_root_count: int
    rejected_root_samples: tuple[str, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def select_physical_roots(
    roots: list[CompleteMaskCapsuleRoot],
    *,
    hit_frames: tuple[int, ...] = HIT_FRAMES,
) -> tuple[CompleteMaskCapsuleRoot, ...]:
    """Apply the fixed first-eight plus pre-hit reservoir rule."""

    empty = [root for root in roots if not root.trace_state_viable]
    if len(empty) < 8:
        raise ValueError("fewer than eight accepted Boolean-empty roots")
    selected: list[CompleteMaskCapsuleRoot] = []
    selected_digests: set[str] = set()

    def add(root: CompleteMaskCapsuleRoot) -> None:
        if root.identity.digest not in selected_digests:
            selected.append(root)
            selected_digests.add(root.identity.digest)

    for root in empty[:8]:
        add(root)
    for hit_frame in hit_frames:
        prior = [
            root for root in empty if root.decision_frame < hit_frame
        ]
        if not prior:
            raise ValueError(
                f"no accepted Boolean-empty root precedes hit {hit_frame}"
            )
        add(prior[-1])
    if not selected:
        raise ValueError("physical stationary reservoir is empty")
    return tuple(selected)


def prepare_physical_reservoir(
    *,
    trace: Path,
    capsule_dir: Path,
    horizon: int = 32,
    decision_frame_support: tuple[int, ...] = (4, 5, 6),
    verify_trace_sha256: bool = True,
) -> PreparedPhysicalReservoir:
    """Read, select, lower, and independently solve the fixed reservoir."""

    trace_sha256 = _sha256(trace)
    if verify_trace_sha256 and trace_sha256 != SOURCE_TRACE_SHA256:
        raise ValueError(
            "physical trace digest differs from the fixed delivery contract"
        )
    started = time.perf_counter()
    roots, failures = read_complete_mask_roots(trace)
    trace_read_ms = (time.perf_counter() - started) * 1000.0
    selected = select_physical_roots(roots)
    expected_actions = tuple(
        action.name for action in TH08_COMPLETE_MASK_ACTION_SPACE.control_actions
    )
    if len(expected_actions) != 36 or len(set(expected_actions)) != 36:
        raise RuntimeError("complete-mask action space is not exactly 36 actions")

    prepared: list[PreparedWitnessWorkload] = []
    for root in selected:
        capsule_path = capsule_dir / root.capsule
        if not capsule_path.is_file():
            raise FileNotFoundError(
                f"retained capsule is missing: {capsule_path}"
            )
        if root.held_token not in expected_actions:
            raise ValueError("held continuation is outside complete-mask actions")
        lowering_started = time.perf_counter()
        problem, query, _position_error = build_problem(
            root,
            capsule_dir=capsule_dir,
            horizon=horizon,
        )
        lowering_ms = (
            time.perf_counter() - lowering_started
        ) * 1000.0
        if tuple(action.name for action in problem.actions) != expected_actions:
            raise ValueError("lowered problem action order is not canonical")
        oracle_started = time.perf_counter()
        portfolio = build_stationary_witness_portfolio(
            problem=problem,
            decision_frame_support=decision_frame_support,
            continuation_candidates=(root.held_token,),
            unrestricted_status="unresolved",
            **query,
        )
        oracle_ms = (time.perf_counter() - oracle_started) * 1000.0
        if (
            not portfolio.complete
            or portfolio.complete_root_actions != expected_actions
            or len(portfolio.action_witnesses) != 36
        ):
            raise RuntimeError("independent stationary portfolio is incomplete")
        for witness in portfolio.action_witnesses:
            if replay_stationary_worst_branch(witness) != witness.label:
                raise RuntimeError("independent stationary path does not replay")
        prepared.append(
            PreparedWitnessWorkload(
                root=root,
                problem=problem,
                query=query,
                expected=portfolio,
                capsule_sha256=file_sha256(capsule_path),
                lowering_ms=lowering_ms,
                oracle_ms=oracle_ms,
            )
        )
    return PreparedPhysicalReservoir(
        workloads=tuple(prepared),
        trace_sha256=trace_sha256,
        trace_read_ms=trace_read_ms,
        accepted_root_count=len(roots),
        boolean_empty_root_count=sum(
            not root.trace_state_viable for root in roots
        ),
        rejected_root_count=len(failures),
        rejected_root_samples=tuple(failures[:8]),
    )


def preparation_record(
    reservoir: PreparedPhysicalReservoir,
) -> dict[str, object]:
    return {
        "source_run": SOURCE_RUN,
        "trace_sha256": reservoir.trace_sha256,
        "trace_read_ms": reservoir.trace_read_ms,
        "accepted_root_count": reservoir.accepted_root_count,
        "boolean_empty_root_count": reservoir.boolean_empty_root_count,
        "rejected_root_count": reservoir.rejected_root_count,
        "rejected_root_samples": reservoir.rejected_root_samples,
        "selected_root_count": len(reservoir.workloads),
        "selected_roots": [
            {
                "identity": workload.identity,
                "decision_frame": workload.root.decision_frame,
                "query_frame": workload.root.query_frame,
                "source_frame": workload.root.source_frame,
                "capsule": workload.root.capsule,
                "capsule_sha256": workload.capsule_sha256,
                "held_token": workload.root.held_token,
                "lowering_ms": workload.lowering_ms,
                "oracle_ms": workload.oracle_ms,
            }
            for workload in reservoir.workloads
        ],
    }


__all__ = [
    "HIT_FRAMES",
    "PreparedPhysicalReservoir",
    "PreparedWitnessWorkload",
    "SOURCE_RUN",
    "SOURCE_TRACE_SHA256",
    "preparation_record",
    "prepare_physical_reservoir",
    "select_physical_roots",
]
