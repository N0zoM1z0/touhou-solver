#!/usr/bin/env python3
"""Audit Boolean publication, observed input, and the pending pipeline.

This analysis consumes one ignored live JSONL trace plus its ignored viability
capsules.  It first measures the complete trace without rebuilding policies,
then runs the phase-exact query-local oracle on a small deterministic cohort.
The output is compact and may be retained after the raw inputs are removed.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from analysis.viability_differential_audit import (
    BASE,
    _clearance,
    _variant_config,
)
from th08_corridor_adapter import TH08_VIABILITY_ACTIONS
from touhou_control.query_survival import (
    PendingCommand,
    QueryLocalSurvivalResult,
    SurvivalQueryProblem,
)
from touhou_control.viability import ViabilityConfig
from touhou_control.viability_audit_capsule import (
    read_viability_audit_capsule,
)


@dataclass(frozen=True)
class Candidate:
    frame: int
    phase_frames: int
    active_mismatch: bool
    pending: bool
    observed_state_differs: bool
    issued_outside_dense_best: bool
    dense_survival_frames: int


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _timing_summary(values: list[float]) -> dict[str, float | None]:
    return {
        "median": statistics.median(values) if values else None,
        "p95": _p95(values),
        "max": max(values) if values else None,
    }


def _capsule_name(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    return raw.replace("\\", "/").rsplit("/", 1)[-1]


def _pending_command(raw: object) -> PendingCommand | None:
    if not isinstance(raw, dict):
        return None
    action = raw.get("desired_action")
    remaining = raw.get("remaining_frames")
    if not isinstance(action, str) or not isinstance(remaining, list):
        return None
    return PendingCommand(action, tuple(int(value) for value in remaining))


def _scan_trace(
    path: Path,
) -> tuple[dict[str, object], list[Candidate]]:
    counts: Counter[str] = Counter()
    phase_counts: Counter[int] = Counter()
    pending_remaining: Counter[str] = Counter()
    policy_statuses: Counter[str] = Counter()
    first_policy_age: dict[int, float] = {}
    solve_ms: dict[int, float] = {}
    first_label_age: dict[int, float] = {}
    label_ms: dict[int, float] = {}
    parity_failures: set[int] = set()
    policy_query_ages: list[float] = []
    candidates: list[Candidate] = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("kind") != "decision":
                continue
            counts["decisions"] += 1
            corridor = row.get("corridor")
            if not isinstance(corridor, dict):
                continue
            status = corridor.get("policy_status")
            if isinstance(status, str):
                policy_statuses[status] += 1
            source_frame = corridor.get("source_frame")
            corridor_age = corridor.get("age")
            if isinstance(source_frame, int):
                if isinstance(corridor_age, (int, float)):
                    first_policy_age.setdefault(
                        source_frame,
                        float(corridor_age),
                    )
                if isinstance(corridor.get("solve_ms"), (int, float)):
                    solve_ms.setdefault(
                        source_frame,
                        float(corridor["solve_ms"]),
                    )
                if isinstance(
                    corridor.get("postpublished_survival_ms"),
                    (int, float),
                ):
                    label_ms.setdefault(
                        source_frame,
                        float(corridor["postpublished_survival_ms"]),
                    )
                    if isinstance(corridor_age, (int, float)):
                        first_label_age.setdefault(
                            source_frame,
                            float(corridor_age),
                        )
                if corridor.get("postpublished_survival_parity") is False:
                    parity_failures.add(source_frame)
            viability = corridor.get("viability")
            if not isinstance(viability, dict) or not viability.get(
                "available"
            ):
                continue
            counts["viability_queries"] += 1
            if isinstance(viability.get("age"), (int, float)):
                policy_query_ages.append(float(viability["age"]))
            phase = int(viability.get("phase_frames", -1))
            phase_counts[phase] += 1
            active_mismatch = (
                viability.get("active_action")
                != viability.get("observed_input_action")
            )
            counts["active_action_mismatches"] += int(active_mismatch)
            pending_raw = corridor.get("pending_command")
            pending = isinstance(pending_raw, dict)
            counts["pending_commands"] += int(pending)
            if pending:
                remaining = tuple(
                    int(value)
                    for value in pending_raw.get("remaining_frames", ())
                )
                pending_remaining[",".join(map(str, remaining))] += 1
                counts["overdue_pending_commands"] += int(
                    bool(pending_raw.get("overdue"))
                )

            shadow = corridor.get("postpublished_survival_shadow")
            if not isinstance(shadow, dict) or not shadow.get("available"):
                continue
            counts["postpublished_queries"] += 1
            state_differs = bool(viability.get("state_viable")) != bool(
                shadow.get("state_viable")
            )
            counts["observed_state_classification_differences"] += int(
                state_differs
            )
            counts["legacy_false_winning_states"] += int(
                state_differs
                and bool(viability.get("state_viable"))
                and not bool(shadow.get("state_viable"))
            )
            counts["legacy_false_losing_states"] += int(
                state_differs
                and not bool(viability.get("state_viable"))
                and bool(shadow.get("state_viable"))
            )
            best = tuple(shadow.get("survival_best_actions") or ())
            issued_outside = row.get("action") not in best
            if not shadow.get("state_viable"):
                counts["postpublished_losing_queries"] += 1
                counts["issued_outside_dense_losing_best"] += int(
                    issued_outside
                )
            survival_frames = int(shadow.get("survival_frames") or 0)
            if (
                survival_frames <= 0
                or _capsule_name(corridor.get("audit_capsule")) is None
            ):
                continue
            candidates.append(
                Candidate(
                    frame=int(row["frame"]),
                    phase_frames=phase,
                    active_mismatch=active_mismatch,
                    pending=pending,
                    observed_state_differs=state_differs,
                    issued_outside_dense_best=issued_outside,
                    dense_survival_frames=survival_frames,
                )
            )
    return (
        {
            **dict(counts),
            "query_phase_counts": {
                str(key): value for key, value in sorted(phase_counts.items())
            },
            "pending_remaining_support_counts": dict(pending_remaining),
            "delivery": {
                "unique_policy_count": len(first_policy_age),
                "first_observed_policy_age_frames": _timing_summary(
                    list(first_policy_age.values())
                ),
                "query_policy_age_frames": _timing_summary(
                    policy_query_ages
                ),
                "solve_ms": _timing_summary(list(solve_ms.values())),
                "policy_status_counts": dict(policy_statuses),
                "unique_labeled_policy_count": len(label_ms),
                "label_ms": _timing_summary(list(label_ms.values())),
                "first_observed_label_age_frames": _timing_summary(
                    list(first_label_age.values())
                ),
                "parity_failure_policy_count": len(parity_failures),
            },
        },
        candidates,
    )


def _select_candidates(
    candidates: list[Candidate],
    *,
    limit: int,
) -> tuple[Candidate, ...]:
    """Retain classification flips, then cover pending phase offsets."""

    if limit <= 0:
        raise ValueError("query limit must be positive")
    selected: list[Candidate] = []
    selected_frames: set[int] = set()

    def add(candidate: Candidate) -> None:
        if len(selected) < limit and candidate.frame not in selected_frames:
            selected.append(candidate)
            selected_frames.add(candidate.frame)

    for candidate in candidates:
        if candidate.observed_state_differs:
            add(candidate)

    for phase in range(BASE.frames_per_layer):
        cohort = [
            candidate
            for candidate in candidates
            if candidate.phase_frames == phase
            and candidate.pending
            and candidate.active_mismatch
        ]
        if cohort:
            add(
                max(
                    cohort,
                    key=lambda item: (
                        item.issued_outside_dense_best,
                        item.dense_survival_frames,
                        -item.frame,
                    ),
                )
            )

    remainder = [
        candidate
        for candidate in candidates
        if candidate.frame not in selected_frames
    ]
    remainder.sort(
        key=lambda item: (
            not item.pending,
            not item.active_mismatch,
            not item.issued_outside_dense_best,
            -item.dense_survival_frames,
            item.frame,
        )
    )
    for candidate in remainder:
        add(candidate)
    return tuple(selected)


def _read_selected_rows(
    path: Path,
    frames: set[int],
) -> dict[int, dict[str, object]]:
    rows: dict[int, dict[str, object]] = {}
    with path.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("kind") != "decision":
                continue
            frame = int(row["frame"])
            if frame in frames:
                rows[frame] = row
                if len(rows) == len(frames):
                    break
    return rows


def _result_payload(
    result: QueryLocalSurvivalResult,
    *,
    issued_action: str,
    elapsed_ms: float,
) -> dict[str, object]:
    return {
        "survival_frames": result.state_label.guaranteed_frames,
        "bottleneck_margin": result.state_label.bottleneck_margin,
        "remaining_horizon_frames": result.remaining_frames,
        "winning": result.winning,
        "best_actions": result.best_actions,
        "issued_in_best": issued_action in result.best_actions,
        "evaluated_state_count": result.evaluated_state_count,
        "backend": result.backend,
        "elapsed_ms": elapsed_ms,
    }


def _audit_candidate(
    *,
    row: dict[str, object],
    capsule_dir: Path,
) -> dict[str, object]:
    corridor = row["corridor"]
    viability = corridor["viability"]
    capsule_name = _capsule_name(corridor.get("audit_capsule"))
    if capsule_name is None:
        raise ValueError("selected row has no audit capsule")
    capsule_path = capsule_dir / capsule_name
    capsule = read_viability_audit_capsule(capsule_path)
    corridor_config = _variant_config(BASE)
    clearance_started = time.perf_counter()
    x_axis, y_axis, clearance = _clearance(
        capsule,
        corridor_config,
        variant=BASE,
    )
    clearance_ms = (time.perf_counter() - clearance_started) * 1000.0
    start_frame = (
        int(viability["query_frame"])
        - int(capsule.metadata["source_frame"])
    )
    delays = tuple(int(value) for value in row["control_delay_candidates"])
    problem = SurvivalQueryProblem(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance,
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=delays,
        nominal_delay=int(row["control_delay_frames"]),
        config=ViabilityConfig(
            frames_per_layer=BASE.frames_per_layer,
            required_clearance=corridor_config.required_clearance,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        ),
    )
    observed = str(viability["observed_input_action"])
    legacy = str(viability["active_action"])
    pending = _pending_command(corridor.get("pending_command"))
    issued = str(row["action"])
    queries = (
        ("legacy_phase_exact", legacy, None),
        ("observed_phase_exact", observed, None),
        ("pending_pipeline_exact", observed, pending),
    )
    cache: dict[
        tuple[str, PendingCommand | None],
        tuple[QueryLocalSurvivalResult, float],
    ] = {}
    variants = {}
    player = row["player"]
    for name, active, command in queries:
        key = (active, command)
        if key not in cache:
            started = time.perf_counter()
            result = problem.query(
                frame=start_frame,
                x=float(player["projected_x"]),
                y=float(player["projected_y"]),
                observed_action=active,
                pending_command=command,
                backend="native",
            )
            cache[key] = (
                result,
                (time.perf_counter() - started) * 1000.0,
            )
        result, elapsed_ms = cache[key]
        variants[name] = _result_payload(
            result,
            issued_action=issued,
            elapsed_ms=elapsed_ms,
        )
    dense = corridor["postpublished_survival_shadow"]
    dense_best = tuple(dense.get("survival_best_actions") or ())
    return {
        "frame": int(row["frame"]),
        "spell_id": int(row["spell"]["spell_id"]),
        "capsule": capsule_name,
        "capsule_source_frame": int(capsule.metadata["source_frame"]),
        "query_frame": int(viability["query_frame"]),
        "phase_frames": int(viability["phase_frames"]),
        "exact_start_frame": start_frame,
        "position": [
            float(player["projected_x"]),
            float(player["projected_y"]),
        ],
        "legacy_active_action": legacy,
        "observed_active_action": observed,
        "pending_command": (
            {
                "action": pending.action,
                "remaining_frames": pending.remaining_frames,
            }
            if pending is not None
            else None
        ),
        "new_command_delay_support": delays,
        "issued_action": issued,
        "trace_boolean": {
            "state_viable": bool(viability["state_viable"]),
            "safe_actions": tuple(viability.get("safe_actions") or ()),
            "issued_in_safe": issued
            in tuple(viability.get("safe_actions") or ()),
        },
        "dense_postpublished_observed_no_pending": {
            "state_viable": bool(dense["state_viable"]),
            "survival_frames": int(dense["survival_frames"]),
            "bottleneck_margin": float(
                dense["survival_bottleneck_margin"]
            ),
            "best_actions": dense_best,
            "issued_in_best": issued in dense_best,
        },
        "exact_variants": variants,
        "clearance_ms": clearance_ms,
    }


def audit(
    *,
    trace_path: Path,
    capsule_dir: Path,
    query_limit: int,
) -> dict[str, object]:
    aggregate, candidates = _scan_trace(trace_path)
    selected = _select_candidates(candidates, limit=query_limit)
    rows = _read_selected_rows(
        trace_path,
        {candidate.frame for candidate in selected},
    )
    observations = []
    for index, candidate in enumerate(selected, 1):
        print(
            f"[{index}/{len(selected)}] phase-exact frame "
            f"{candidate.frame}",
            flush=True,
        )
        observations.append(
            _audit_candidate(
                row=rows[candidate.frame],
                capsule_dir=capsule_dir,
            )
        )

    summary: Counter[str] = Counter()
    query_times = []
    clearance_times = []
    for observation in observations:
        dense = observation[
            "dense_postpublished_observed_no_pending"
        ]
        variants = observation["exact_variants"]
        legacy = variants["legacy_phase_exact"]
        observed = variants["observed_phase_exact"]
        pipeline = variants["pending_pipeline_exact"]
        summary["selected_queries"] += 1
        summary["legacy_to_observed_best_set_changes"] += int(
            legacy["best_actions"] != observed["best_actions"]
        )
        summary["pending_pipeline_best_set_changes"] += int(
            observed["best_actions"] != pipeline["best_actions"]
        )
        summary["dense_to_pipeline_best_set_changes"] += int(
            dense["best_actions"] != pipeline["best_actions"]
        )
        summary["pending_pipeline_issued_rejections"] += int(
            observed["issued_in_best"] and not pipeline["issued_in_best"]
        )
        summary["pending_pipeline_issued_rescues"] += int(
            not observed["issued_in_best"] and pipeline["issued_in_best"]
        )
        summary["dense_to_pipeline_issued_rejections"] += int(
            dense["issued_in_best"] and not pipeline["issued_in_best"]
        )
        summary["dense_to_pipeline_issued_rescues"] += int(
            not dense["issued_in_best"] and pipeline["issued_in_best"]
        )
        trace_winning = bool(observation["trace_boolean"]["state_viable"])
        dense_winning = bool(dense["state_viable"])
        legacy_winning = bool(legacy["winning"])
        observed_winning = bool(observed["winning"])
        pipeline_winning = bool(pipeline["winning"])
        for prefix, left, right in (
            ("trace_boolean_to_pipeline", trace_winning, pipeline_winning),
            ("dense_to_pipeline", dense_winning, pipeline_winning),
            (
                "legacy_to_observed_phase_exact",
                legacy_winning,
                observed_winning,
            ),
            (
                "observed_to_pending_pipeline",
                observed_winning,
                pipeline_winning,
            ),
        ):
            summary[f"{prefix}_winning_changes"] += int(left != right)
            summary[f"{prefix}_false_winning"] += int(left and not right)
            summary[f"{prefix}_false_losing"] += int(not left and right)
        clearance_times.append(float(observation["clearance_ms"]))
        query_times.extend(
            float(payload["elapsed_ms"])
            for payload in variants.values()
        )
    return {
        "schema": "postpublished-survival-pending-pipeline-audit-v1",
        "scope": {
            "trace": str(trace_path),
            "capsule_dir": str(capsule_dir),
            "query_limit": query_limit,
            "candidate_positive_label_queries": len(candidates),
            "selection": (
                "all observed-vs-issued Boolean classification flips first; "
                "then pending-command phase coverage; then high-survival "
                "issued-outside-label cases"
            ),
        },
        "semantics": {
            "authoritative_policy": "trace Boolean policy",
            "dense_shadow": (
                "source-layer-aligned observed input, no explicit pending "
                "command, policy-wide delay support"
            ),
            "phase_exact_variants": (
                "exact physical query phase and current delay support"
            ),
            "pending_pipeline": (
                "observed active -> older pending -> newly selected command; "
                "robust over remaining pending and new-command delays"
            ),
            "limitation": (
                "The exact cohort is diagnostic and deterministic, not an "
                "estimate of a fresh-run hit rate."
            ),
        },
        "trace_aggregate": aggregate,
        "exact_summary": dict(summary),
        "timing_ms": {
            "clearance": _timing_summary(clearance_times),
            "query_variant": _timing_summary(query_times),
        },
        "observations": observations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("capsules", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--query-limit", type=int, default=16)
    args = parser.parse_args(argv)
    if args.query_limit <= 0:
        parser.error("--query-limit must be positive")
    report = audit(
        trace_path=args.trace,
        capsule_dir=args.capsules,
        query_limit=args.query_limit,
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
