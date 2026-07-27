"""Exact-root selection, solving, and validation for the G3 capsule gate."""

from __future__ import annotations

import math

from analysis.belief_upper_certification_audit import Root, _read_roots
from analysis.feasibility_first_capsule_audit import _problem
from touhou_control.partial_survival_witness import (
    StationaryWitnessPortfolio,
    build_stationary_witness_portfolio,
    replay_stationary_worst_branch,
)
from touhou_control.query_survival import PendingCommand

from .serialization import (
    canonical_sha256,
    file_sha256,
    label_record,
    root_record,
    witness_record,
)
from .types import TARGET_MODES, WORKLOADS, Workload


def _validate_native(
    *,
    problem,
    portfolio: StationaryWitnessPortfolio,
    decision_frame_support: tuple[int, ...],
) -> dict[str, object]:
    mismatches: list[dict[str, object]] = []
    margin_errors: list[float] = []
    continuations = tuple(
        dict.fromkeys(
            witness.continuation_action
            for witness in portfolio.action_witnesses
        )
    )
    pending_command = (
        None
        if portfolio.root.pending_action is None
        else PendingCommand(
            portfolio.root.pending_action,
            portfolio.root.remaining_delay_support,
        )
    )
    for continuation in continuations:
        version = (
            "g3-stationary-capsule-audit",
            portfolio.problem_digest,
            continuation,
        )
        with problem.build_belief_pipeline_workspace(
            policy_version=version,
            decision_frame_support=decision_frame_support,
            continuation_actions=(continuation,),
        ) as workspace:
            native = workspace.query_cell(
                policy_version=version,
                frame=portfolio.root.frame,
                row=portfolio.root.row,
                column=portfolio.root.column,
                observed_action=portfolio.root.observed_action,
                pending_command=pending_command,
            )
        for witness in portfolio.action_witnesses:
            if witness.continuation_action != continuation:
                continue
            native_label = native.action_label(witness.root_action)
            margin_error = abs(
                native_label.bottleneck_margin
                - witness.label.bottleneck_margin
            )
            margin_errors.append(margin_error)
            if (
                native_label.guaranteed_frames
                != witness.label.guaranteed_frames
                or not math.isclose(
                    native_label.bottleneck_margin,
                    witness.label.bottleneck_margin,
                    rel_tol=0.0,
                    abs_tol=1e-5,
                )
            ):
                mismatches.append(
                    {
                        "root_action": witness.root_action,
                        "continuation_action": continuation,
                        "scalar": label_record(witness.label),
                        "native": label_record(native_label),
                    }
                )
    return {
        "checked_selected_witness_count": len(portfolio.action_witnesses),
        "checked_continuation_count": len(continuations),
        "margin_absolute_tolerance": 1e-5,
        "max_absolute_margin_error_hex": float(
            max(margin_errors, default=0.0)
        ).hex(),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def _audit_root(
    *,
    root: Root,
    workload: Workload,
    horizon: int,
    decision_frame_support: tuple[int, ...],
) -> tuple[str, dict[str, object]]:
    problem, query, _clearance_ms, position_error = _problem(
        root,
        capsule_dir=workload.capsule_dir,
        horizon=horizon,
    )
    portfolio = build_stationary_witness_portfolio(
        problem=problem,
        decision_frame_support=decision_frame_support,
        continuation_candidates=tuple(
            action.name for action in problem.actions
        ),
        unrestricted_status="unresolved",
        **query,
    )
    if not portfolio.complete:
        raise RuntimeError("stationary root-action portfolio is incomplete")
    expected_actions = tuple(action.name for action in problem.actions)
    if portfolio.complete_root_actions != expected_actions:
        raise RuntimeError("stationary portfolio omitted or reordered actions")
    for witness in portfolio.action_witnesses:
        if replay_stationary_worst_branch(witness) != witness.label:
            raise RuntimeError("stationary worst branch did not replay")
    native = _validate_native(
        problem=problem,
        portfolio=portfolio,
        decision_frame_support=decision_frame_support,
    )
    if native["mismatch_count"]:
        raise RuntimeError("stationary scalar/native capsule mismatch")

    capsule_path = workload.capsule_dir / root.capsule
    pending = query["pending_command"]
    return portfolio.mode, {
        "mode": portfolio.mode,
        "unrestricted_status": portfolio.unrestricted_status,
        "unrestricted_status_reason": (
            "the retained Boolean-empty trace root is not an exact "
            "unrestricted belief losing certificate"
        ),
        "root": root_record(root),
        "query": {
            "frame": query["frame"],
            "row": query["row"],
            "column": query["column"],
            "observed_action": query["observed_action"],
            "pending_action": (
                None if pending is None else pending.action
            ),
            "pending_remaining_support": (
                () if pending is None else pending.remaining_frames
            ),
            "position_error_hex": float(position_error).hex(),
        },
        "capsule": {
            "path": str(capsule_path),
            "bytes": capsule_path.stat().st_size,
            "sha256": file_sha256(capsule_path),
        },
        "problem_digest": portfolio.problem_digest,
        "portfolio_digest": portfolio.portfolio_digest,
        "continuation_candidates": portfolio.continuation_candidates,
        "complete_root_actions": portfolio.complete_root_actions,
        "state_label": label_record(portfolio.state_label),
        "best_actions": portfolio.best_actions,
        "native_selected_witness_parity": native,
        "action_witnesses": [
            witness_record(witness)
            for witness in portfolio.action_witnesses
        ],
    }


def audit_workload(
    workload: Workload,
    *,
    horizon: int,
    decision_frame_support: tuple[int, ...],
    max_scanned_roots: int,
) -> dict[str, object]:
    roots, hit_frames = _read_roots(workload.trace)
    eligible = tuple(
        root
        for root in roots
        if (
            not root.trace_state_viable
            and 0 <= root.query_frame - root.source_frame
            and root.query_frame - root.source_frame + horizon <= 80
        )
    )
    selected: dict[str, dict[str, object]] = {}
    scanned_root_count = 0
    for root in eligible[:max_scanned_roots]:
        scanned_root_count += 1
        mode, record = _audit_root(
            root=root,
            workload=workload,
            horizon=horizon,
            decision_frame_support=decision_frame_support,
        )
        if mode in TARGET_MODES and mode not in selected:
            selected[mode] = record
        if len(selected) == len(TARGET_MODES):
            break

    return {
        "workload": workload.name,
        "stage": workload.stage,
        "physical_interpretation": workload.physical_interpretation,
        "trace": {
            "path": str(workload.trace),
            "bytes": workload.trace.stat().st_size,
            "sha256": file_sha256(workload.trace),
        },
        "read_root_count": len(roots),
        "native_hit_count": len(hit_frames),
        "eligible_boolean_empty_root_count": len(eligible),
        "scanned_root_count": scanned_root_count,
        "requested_modes": TARGET_MODES,
        "retained_modes": tuple(
            mode for mode in TARGET_MODES if mode in selected
        ),
        "missing_modes": tuple(
            mode for mode in TARGET_MODES if mode not in selected
        ),
        "observations": [
            selected[mode] for mode in TARGET_MODES if mode in selected
        ],
    }


def audit(
    *,
    horizon: int,
    decision_frame_support: tuple[int, ...],
    max_scanned_roots: int,
) -> dict[str, object]:
    if not 1 <= horizon <= 80:
        raise ValueError("horizon must be in [1, 80]")
    if max_scanned_roots <= 0:
        raise ValueError("max scanned roots must be positive")
    report = {
        "schema": "th08-g3-stationary-partial-witness-capsule-audit-v1",
        "scope": {
            "authority": "offline restricted attainable lower witness only",
            "horizon_frames": horizon,
            "decision_frame_support": decision_frame_support,
            "root_action_contract": (
                "all 17 historical movement actions, ordered by the retained "
                "capsule problem"
            ),
            "continuation_contract": (
                "best completed singleton stationary continuation per root "
                "action; all 17 stationary candidates evaluated"
            ),
            "unrestricted_contract": (
                "unresolved unless a separate exact unrestricted certificate "
                "is retained; Boolean empty alone is insufficient"
            ),
            "publication": (
                "no live lookup, deadline, issue certificate, or action "
                "authority"
            ),
        },
        "workloads": [
            audit_workload(
                workload,
                horizon=horizon,
                decision_frame_support=decision_frame_support,
                max_scanned_roots=max_scanned_roots,
            )
            for workload in WORKLOADS
        ],
    }
    report["report_digest"] = canonical_sha256(report)
    return report
