#!/usr/bin/env python3
"""Replay verified feasibility-first policies on physical TH08 capsules.

The trace Boolean policy remains authoritative.  A completed candidate policy
is an attainable lower bound for the reconstructed finite model.  Candidate
exhaustion is not called losing until an exact physical-observation threshold
certifies that no unrestricted root action can beat the completed lower.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np

from analysis.belief_upper_certification_audit import (
    Root,
    _read_roots,
    _select_roots,
)
from analysis.viability_differential_audit import (
    BASE,
    _clearance,
    _variant_config,
)
from th08_corridor_adapter import TH08_VIABILITY_ACTIONS
from touhou_control.policy_synthesis import (
    evaluate_candidate_policy_portfolio,
    refine_candidate_policy_gap,
    singleton_continuation_candidates,
)
from touhou_control.query_survival import (
    PipelineWorkspaceDeadlineError,
    SurvivalQueryProblem,
)
from touhou_control.viability import ViabilityConfig
from touhou_control.viability_audit_capsule import (
    read_viability_audit_capsule,
)


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _summary(values: list[float]) -> dict[str, float | None]:
    return {
        "median": statistics.median(values) if values else None,
        "p95": _p95(values),
        "max": max(values) if values else None,
    }


def _label(label) -> dict[str, float | int]:
    return {
        "frames": label.guaranteed_frames,
        "margin": label.bottleneck_margin,
    }


def _problem(
    root: Root,
    *,
    capsule_dir: Path,
    horizon: int,
) -> tuple[SurvivalQueryProblem, dict[str, object], float, float]:
    capsule = read_viability_audit_capsule(capsule_dir / root.capsule)
    start = root.query_frame - root.source_frame
    corridor_config = _variant_config(BASE)
    started = time.perf_counter()
    x_axis, y_axis, source_clearance = _clearance(
        capsule,
        corridor_config,
        variant=BASE,
    )
    clearance_ms = (time.perf_counter() - started) * 1000.0
    clearance = np.ascontiguousarray(
        source_clearance[start : start + horizon + 1],
        dtype=np.float32,
    )
    row = int(np.argmin(np.abs(y_axis - root.y)))
    column = int(np.argmin(np.abs(x_axis - root.x)))
    position_error = float(
        np.hypot(
            float(x_axis[column]) - root.x,
            float(y_axis[row]) - root.y,
        )
    )
    problem = SurvivalQueryProblem(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance,
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=root.delay_frames,
        nominal_delay=root.nominal_delay,
        config=ViabilityConfig(
            frames_per_layer=BASE.frames_per_layer,
            required_clearance=corridor_config.required_clearance,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        ),
    )
    query: dict[str, object] = {
        "frame": 0,
        "row": row,
        "column": column,
        "observed_action": root.observed_action,
        "pending_command": root.pending,
    }
    return problem, query, clearance_ms, position_error


def _audit_root(
    root: Root,
    *,
    capsule_dir: Path,
    horizon: int,
    cadence: tuple[int, ...],
    candidate_timeout_ms: int,
    candidate_total_timeout_ms: int,
    threshold_timeout_ms: int,
    refinement_timeout_ms: int,
    max_columns: int,
    candidate_only: bool,
    hit_frame: int | None,
) -> dict[str, object]:
    problem, query, clearance_ms, position_error = _problem(
        root,
        capsule_dir=capsule_dir,
        horizon=horizon,
    )
    candidates = singleton_continuation_candidates(problem)
    version = (
        root.capsule,
        root.query_frame,
        root.x,
        root.y,
        root.observed_action,
        root.pending,
        root.delay_frames,
        horizon,
        cadence,
    )
    started = time.perf_counter()
    try:
        portfolio = evaluate_candidate_policy_portfolio(
            problem=problem,
            policy_version=("portfolio", version),
            decision_frame_support=cadence,
            candidates=candidates,
            timeout_ms_per_candidate=candidate_timeout_ms,
            total_timeout_ms=candidate_total_timeout_ms,
            stop_on_feasibility=True,
            **query,
        )
    except PipelineWorkspaceDeadlineError:
        return {
            "status": "candidate_timeout",
            "decision_frame": root.decision_frame,
            "query_frame": root.query_frame,
            "hit_frame": hit_frame,
            "capsule": root.capsule,
            "clearance_ms": clearance_ms,
            "candidate_ms": (time.perf_counter() - started) * 1000.0,
        }
    candidate_ms = (time.perf_counter() - started) * 1000.0
    classification = (
        "candidate_feasible"
        if portfolio.feasibility_sufficient
        else "candidate_exhausted"
    )
    threshold = None
    threshold_ms = None
    refinement = None
    refinement_ms = None
    exact_label = None

    if not portfolio.feasibility_sufficient and candidate_only:
        classification = (
            "candidate_budget_exhausted"
            if portfolio.budget_exhausted
            else "candidate_exhausted"
        )
    elif not portfolio.feasibility_sufficient:
        threshold_version = ("physical-threshold", version)
        with problem.build_belief_pipeline_workspace(
            policy_version=threshold_version,
            decision_frame_support=cadence,
            # All admitted positive remaining delays map to one bucket.
            # Since pending action is already public, this is exactly the
            # physical observation partition rather than a clairvoyant upper.
            remaining_delay_bucket_size=62,
        ) as workspace:
            started = time.perf_counter()
            threshold = workspace.certify_upper_bound(
                policy_version=threshold_version,
                lower_bound=portfolio.result.state_label,
                timeout_ms=threshold_timeout_ms,
                **query,
            )
            threshold_ms = (time.perf_counter() - started) * 1000.0
        if threshold.certified:
            classification = "exact_losing"
            exact_label = portfolio.result.state_label
        elif not threshold.deadline_expired:
            started = time.perf_counter()
            try:
                refinement = refine_candidate_policy_gap(
                    problem=problem,
                    policy_version=("refinement", version),
                    decision_frame_support=cadence,
                    candidates=candidates,
                    timeout_ms_per_lower=refinement_timeout_ms,
                    timeout_ms_upper=refinement_timeout_ms,
                    max_columns=max_columns,
                    **query,
                )
            except PipelineWorkspaceDeadlineError:
                classification = "refinement_timeout"
            else:
                refinement_ms = (
                    time.perf_counter() - started
                ) * 1000.0
                if refinement.feasibility_sufficient:
                    classification = "refined_feasible"
                    exact_label = refinement.final_lower_result.state_label
                elif refinement.optimality_certified:
                    classification = "exact_losing"
                    exact_label = refinement.final_lower_result.state_label
                else:
                    classification = "unresolved"
        else:
            classification = "threshold_timeout"

    return {
        "status": "completed",
        "classification": classification,
        "decision_frame": root.decision_frame,
        "query_frame": root.query_frame,
        "source_frame": root.source_frame,
        "hit_frame": hit_frame,
        "frames_to_hit": (
            hit_frame - root.query_frame
            if hit_frame is not None
            else None
        ),
        "spell_id": root.spell_id,
        "capsule": root.capsule,
        "trace_state_viable": root.trace_state_viable,
        "issued_action": root.issued_action,
        "observed_action": root.observed_action,
        "pending_command": (
            {
                "action": root.pending.action,
                "remaining_frames": list(root.pending.remaining_frames),
            }
            if root.pending is not None
            else None
        ),
        "delay_frames": list(root.delay_frames),
        "position_error": position_error,
        "clearance_ms": clearance_ms,
        "candidate_ms": candidate_ms,
        "candidate_label": _label(portfolio.result.state_label),
        "candidate_best_actions": list(portfolio.result.best_actions),
        "completed_candidates": list(portfolio.completed_candidates),
        "timed_out_candidates": list(portfolio.timed_out_candidates),
        "unvisited_candidates": list(
            portfolio.unvisited_candidates
        ),
        "candidate_budget_exhausted": portfolio.budget_exhausted,
        "candidate_witnesses": {
            witness.root_action: witness.candidate_policy
            for witness in portfolio.action_witnesses
            if witness.root_action in portfolio.result.best_actions
        },
        "threshold_ms": threshold_ms,
        "physical_threshold": (
            {
                "certified": threshold.certified,
                "deadline_expired": threshold.deadline_expired,
                "unresolved_actions": list(
                    threshold.unresolved_actions
                ),
                "stats": {
                    field: int(value)
                    for field, value in vars(
                        threshold.workspace_stats
                    ).items()
                },
            }
            if threshold is not None
            else None
        ),
        "refinement_ms": refinement_ms,
        "refinement": (
            {
                "label": _label(refinement.final_lower_result.state_label),
                "continuation_actions": list(
                    refinement.final_continuation_actions
                ),
                "optimality_certified": refinement.optimality_certified,
                "unresolved_actions": list(
                    refinement.final_upper_certification.unresolved_actions
                ),
            }
            if refinement is not None
            else None
        ),
        "exact_label": (
            _label(exact_label) if exact_label is not None else None
        ),
    }


def audit(
    *,
    trace: Path,
    capsule_dir: Path,
    query_limit: int,
    pre_hit_lead: int,
    horizon: int,
    cadence: tuple[int, ...],
    candidate_timeout_ms: int,
    candidate_total_timeout_ms: int,
    threshold_timeout_ms: int,
    refinement_timeout_ms: int,
    max_columns: int,
    trace_losing_only: bool,
    candidate_only: bool,
) -> dict[str, object]:
    roots, hit_frames = _read_roots(trace)
    selection_roots = (
        [root for root in roots if not root.trace_state_viable]
        if trace_losing_only
        else roots
    )
    selected = _select_roots(
        selection_roots,
        hit_frames,
        limit=query_limit,
        pre_hit_lead=pre_hit_lead,
        horizon=horizon,
    )
    observations = []
    for index, (root, hit_frame) in enumerate(selected, 1):
        print(
            f"[{index}/{len(selected)}] feasibility frame "
            f"{root.query_frame}",
            flush=True,
        )
        observations.append(
            _audit_root(
                root,
                capsule_dir=capsule_dir,
                horizon=horizon,
                cadence=cadence,
                candidate_timeout_ms=candidate_timeout_ms,
                candidate_total_timeout_ms=(
                    candidate_total_timeout_ms
                ),
                threshold_timeout_ms=threshold_timeout_ms,
                refinement_timeout_ms=refinement_timeout_ms,
                max_columns=max_columns,
                candidate_only=candidate_only,
                hit_frame=hit_frame,
            )
        )

    completed = [
        item for item in observations if item["status"] == "completed"
    ]
    classifications: dict[str, int] = {}
    for item in completed:
        classification = str(item["classification"])
        classifications[classification] = (
            classifications.get(classification, 0) + 1
        )
    pre_hit = [
        item for item in completed if item["hit_frame"] is not None
    ]
    candidate_times = [
        float(item["candidate_ms"]) for item in completed
    ]
    threshold_times = [
        float(item["threshold_ms"])
        for item in completed
        if item["threshold_ms"] is not None
    ]
    capsule_paths = tuple(sorted(capsule_dir.glob("*.npz")))
    return {
        "schema": "th08-feasibility-first-capsule-audit-v1",
        "scope": {
            "trace": str(trace),
            "capsule_dir": str(capsule_dir),
            "raw_trace_bytes": trace.stat().st_size,
            "raw_capsule_count": len(capsule_paths),
            "raw_capsule_bytes": sum(
                path.stat().st_size for path in capsule_paths
            ),
            "available_root_count": len(roots),
            "native_hit_count": len(hit_frames),
            "selected_root_count": len(selected),
            "query_limit": query_limit,
            "pre_hit_lead": pre_hit_lead,
            "horizon": horizon,
            "decision_frame_support": list(cadence),
            "candidate_timeout_ms": candidate_timeout_ms,
            "candidate_total_timeout_ms": (
                candidate_total_timeout_ms
            ),
            "threshold_timeout_ms": threshold_timeout_ms,
            "refinement_timeout_ms": refinement_timeout_ms,
            "max_columns": max_columns,
            "trace_losing_only": trace_losing_only,
            "candidate_only": candidate_only,
            "authority": "offline/shadow only",
        },
        "contract": {
            "candidate": (
                "exact causal restricted-policy lower; stop on completed "
                "full-horizon positive label"
            ),
            "exact_losing": (
                "physical-observation threshold certifies no unrestricted "
                "action can strictly beat the completed losing lower"
            ),
            "timeout": "unfinished work remains unresolved",
            "aggregate_budget": (
                "completed candidate lowers remain exact; unvisited "
                "candidates remain unresolved"
            ),
        },
        "summary": {
            "completed_count": len(completed),
            "timeout_count": len(observations) - len(completed),
            "classifications": classifications,
            "pre_hit_classifications": {
                name: sum(
                    item["classification"] == name for item in pre_hit
                )
                for name in sorted(classifications)
            },
            "candidate_completed_count": _summary(
                [
                    float(len(item["completed_candidates"]))
                    for item in completed
                ]
            ),
            "timing_ms": {
                "clearance": _summary(
                    [float(item["clearance_ms"]) for item in completed]
                ),
                "candidate": _summary(candidate_times),
                "physical_threshold": _summary(threshold_times),
            },
        },
        "observations": observations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("capsules", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--query-limit", type=int, default=32)
    parser.add_argument("--pre-hit-lead", type=int, default=30)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--cadence", type=int, nargs="+", default=(4, 5, 6))
    parser.add_argument("--candidate-timeout-ms", type=int, default=3000)
    parser.add_argument("--candidate-total-timeout-ms", type=int, default=0)
    parser.add_argument("--threshold-timeout-ms", type=int, default=3000)
    parser.add_argument("--refinement-timeout-ms", type=int, default=3000)
    parser.add_argument("--max-columns", type=int, default=6)
    parser.add_argument("--trace-losing-only", action="store_true")
    parser.add_argument("--candidate-only", action="store_true")
    args = parser.parse_args(argv)
    if min(
        args.query_limit,
        args.pre_hit_lead,
        args.horizon,
        args.candidate_timeout_ms,
        args.threshold_timeout_ms,
        args.refinement_timeout_ms,
        args.max_columns,
        *args.cadence,
    ) <= 0:
        parser.error("limits, horizons, timeouts, and cadence must be positive")
    if args.candidate_total_timeout_ms < 0:
        parser.error("candidate total timeout cannot be negative")
    report = audit(
        trace=args.trace,
        capsule_dir=args.capsules,
        query_limit=args.query_limit,
        pre_hit_lead=args.pre_hit_lead,
        horizon=args.horizon,
        cadence=tuple(sorted(set(args.cadence))),
        candidate_timeout_ms=args.candidate_timeout_ms,
        candidate_total_timeout_ms=args.candidate_total_timeout_ms,
        threshold_timeout_ms=args.threshold_timeout_ms,
        refinement_timeout_ms=args.refinement_timeout_ms,
        max_columns=args.max_columns,
        trace_losing_only=args.trace_losing_only,
        candidate_only=args.candidate_only,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
