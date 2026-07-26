#!/usr/bin/env python3
"""Audit pre-hit winning candidate witnesses without granting authority.

The retained v2 trace does not contain alternate-action issue certificates.
Consequently this audit can recover exact finite-model action labels and
candidate witnesses from the retained capsule, but can establish issue-time
compatibility only when the action actually issued by the controller is also
one of the candidate-best actions.  Every alternate action remains explicitly
unresolved instead of being re-certified from the trace-radius subset.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import statistics
import time
from pathlib import Path

from analysis.belief_upper_certification_audit import (
    Root,
    _read_roots,
)
from analysis.feasibility_first_capsule_audit import _problem
from th08_live_dodge_agent import _action_name_from_mask
from touhou_control.policy_synthesis import (
    CandidateActionWitness,
    evaluate_candidate_policy_portfolio,
    singleton_continuation_candidates,
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
        "frames": int(label.guaranteed_frames),
        "margin": float(label.bottleneck_margin),
    }


def _winning(label, *, horizon: int) -> bool:
    return bool(
        label.guaranteed_frames == horizon
        and label.bottleneck_margin > 0.0
    )


def _witness_record(
    witness: CandidateActionWitness,
) -> dict[str, object]:
    return {
        "root_action": witness.root_action,
        "candidate_policy": witness.candidate_policy,
        "label": _label(witness.label),
    }


def issue_certificate_lower_bound(
    row: dict[str, object],
    *,
    candidate_best_actions: tuple[str, ...],
    issued_action: str,
) -> dict[str, object]:
    """Return only compatibility proved by certificate telemetry in the row.

    The trace retains the final issued action's certificate, not the complete
    fresh per-action map.  Therefore a different candidate action is unknown,
    even though the trace-radius hazards could be replayed heuristically.
    """

    deadline = row.get("deadline_guard")
    deadline_missed = bool(
        isinstance(deadline, dict) and deadline.get("missed")
    )
    robust = row.get("robust_control")
    if issued_action not in candidate_best_actions:
        return {
            "status": "alternate_action_certificate_not_retained",
            "available": False,
            "safe": None,
            "deadline_missed": deadline_missed,
            "issued_action": issued_action,
        }
    if deadline_missed:
        return {
            "status": "deadline_missed",
            "available": False,
            "safe": None,
            "deadline_missed": True,
            "issued_action": issued_action,
        }
    if not isinstance(robust, dict):
        return {
            "status": "issued_certificate_missing",
            "available": False,
            "safe": None,
            "deadline_missed": False,
            "issued_action": issued_action,
        }
    collisions = int(robust.get("worst_collisions", 0))
    clearance = float(robust.get("min_clearance", -math.inf))
    return {
        "status": (
            "issued_candidate_action_safe"
            if collisions == 0 and clearance >= 0.0
            else "issued_candidate_action_unsafe"
        ),
        "available": True,
        "safe": collisions == 0 and clearance >= 0.0,
        "deadline_missed": False,
        "issued_action": issued_action,
        "worst_collisions": collisions,
        "min_clearance": clearance,
        "cvar_risk": float(robust.get("cvar_risk", 0.0)),
        "worst_delay": robust.get("worst_delay"),
    }


def _compact_candidate_row(
    row: dict[str, object],
) -> dict[str, object] | None:
    shadow = row.get("candidate_verifier_shadow")
    if not isinstance(shadow, dict) or shadow.get("status") != "hit":
        return None
    result = shadow.get("result")
    target = shadow.get("target")
    corridor = row.get("corridor")
    if (
        not isinstance(result, dict)
        or result.get("winning") is not True
        or not isinstance(target, dict)
        or not isinstance(corridor, dict)
    ):
        return None
    return {
        "frame": int(row["frame"]),
        "mask": int(row["mask"]),
        "action": str(row["action"]),
        "spell": row.get("spell"),
        "candidate_result": result,
        "candidate_target": target,
        "corridor": {
            "source_frame": corridor.get("source_frame"),
            "audit_capsule": corridor.get("audit_capsule"),
        },
        "robust_control": row.get("robust_control"),
        "deadline_guard": row.get("deadline_guard"),
        "issue_time_enemy_guard": row.get("issue_time_enemy_guard"),
    }


def _read_candidate_rows(
    trace: Path,
) -> tuple[list[dict[str, object]], list[int]]:
    candidates: list[dict[str, object]] = []
    hit_frames: list[int] = []
    with trace.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSON at {trace}:{line_number}: {error}"
                ) from error
            if row.get("kind") != "decision":
                continue
            if row.get("hit_started"):
                hit_frames.append(int(row["frame"]))
            compact = _compact_candidate_row(row)
            if compact is not None:
                candidates.append(compact)
    return candidates, hit_frames


def _next_hit(
    hit_frames: list[int],
    frame: int,
    *,
    pre_hit_window: int,
) -> int | None:
    index = bisect.bisect_right(hit_frames, frame)
    if index >= len(hit_frames):
        return None
    hit = hit_frames[index]
    return hit if 0 < hit - frame <= pre_hit_window else None


def _same_pending(
    target: dict[str, object],
    root: Root,
) -> bool:
    action = (
        root.pending.action if root.pending is not None else None
    )
    remaining = (
        tuple(root.pending.remaining_frames)
        if root.pending is not None
        else ()
    )
    raw_remaining = target.get("pending_remaining_frames", ())
    return bool(
        target.get("pending_action") == action
        and isinstance(raw_remaining, (list, tuple))
        and tuple(int(value) for value in raw_remaining) == remaining
    )


def _audit_root(
    row: dict[str, object],
    *,
    root: Root,
    capsule_dir: Path,
    horizon: int,
    cadence: tuple[int, ...],
    hit_frame: int,
) -> dict[str, object]:
    target = row["candidate_target"]
    trace_result = row["candidate_result"]
    assert isinstance(target, dict)
    assert isinstance(trace_result, dict)
    problem, query, clearance_ms, position_error = _problem(
        root,
        capsule_dir=capsule_dir,
        horizon=horizon,
    )
    expected_relative_frame = root.query_frame - root.source_frame
    root_contract_matches = bool(
        int(target["frame"]) == expected_relative_frame
        and int(target["row"]) == int(query["row"])
        and int(target["column"]) == int(query["column"])
        and str(target["observed_action"]) == root.observed_action
        and _same_pending(target, root)
    )

    candidates_by_name = {
        candidate.name: candidate
        for candidate in singleton_continuation_candidates(problem)
    }
    completed_names = tuple(
        str(name)
        for name in trace_result.get("completed_candidates", ())
    )
    completed_candidates = tuple(
        candidates_by_name[name] for name in completed_names
    )
    if not completed_candidates:
        raise ValueError(
            f"winning frame {row['frame']} retained no completed candidate"
        )

    started = time.perf_counter()
    portfolio = evaluate_candidate_policy_portfolio(
        problem=problem,
        policy_version=(
            "candidate-witness-counterfactual",
            root.capsule,
            root.query_frame,
        ),
        decision_frame_support=cadence,
        candidates=completed_candidates,
        frame=0,
        row=int(target["row"]),
        column=int(target["column"]),
        observed_action=str(target["observed_action"]),
        pending_command=root.pending,
        stop_on_feasibility=False,
    )
    replay_ms = (time.perf_counter() - started) * 1000.0
    result = portfolio.result
    labels = dict(result.action_labels)
    trace_best = tuple(str(value) for value in trace_result["best_actions"])
    trace_frames = int(trace_result["survival_frames"])
    trace_margin = float(trace_result["bottleneck_margin"])
    label_parity = bool(
        result.state_label.guaranteed_frames == trace_frames
        and math.isclose(
            result.state_label.bottleneck_margin,
            trace_margin,
            rel_tol=0.0,
            abs_tol=1e-6,
        )
    )
    best_action_parity = result.best_actions == trace_best
    historical_replay_parity = bool(
        root_contract_matches
        and label_parity
        and best_action_parity
    )

    issued_action = _action_name_from_mask(int(row["mask"]))
    issued_label = labels.get(issued_action)
    replay_issued_winning = bool(
        issued_label is not None
        and _winning(issued_label, horizon=horizon)
    )
    winning_witnesses = tuple(
        witness
        for witness in portfolio.action_witnesses
        if witness.root_action in result.best_actions
    )
    issue_compatibility = (
        issue_certificate_lower_bound(
            row,
            candidate_best_actions=result.best_actions,
            issued_action=issued_action,
        )
        if historical_replay_parity
        else {
            "available": False,
            "safe": None,
            "status": "historical_replay_mismatch",
            "reason": (
                "the current exact replay does not reproduce both the "
                "historical state label and best-action set"
            ),
        }
    )
    return {
        "decision_frame": int(row["frame"]),
        "hit_frame": hit_frame,
        "frames_to_hit": hit_frame - int(row["frame"]),
        "spell": row.get("spell"),
        "capsule": root.capsule,
        "source_frame": root.source_frame,
        "query_frame": root.query_frame,
        "root_contract_matches": root_contract_matches,
        "trace_label_parity": label_parity,
        "trace_best_action_parity": best_action_parity,
        "historical_replay_parity": historical_replay_parity,
        "position_error": position_error,
        "clearance_ms": clearance_ms,
        "candidate_replay_ms": replay_ms,
        "trace_candidate_label": {
            "frames": trace_frames,
            "margin": trace_margin,
        },
        "trace_best_actions": list(trace_best),
        "replay_candidate_label": _label(result.state_label),
        "replay_best_actions": list(result.best_actions),
        "replay_candidate_witnesses": [
            _witness_record(witness)
            for witness in winning_witnesses
        ],
        "issued_action": issued_action,
        "issued_label": (
            _label(issued_label)
            if historical_replay_parity and issued_label is not None
            else None
        ),
        "issued_model_winning": (
            replay_issued_winning if historical_replay_parity else None
        ),
        "candidate_changes_action": (
            issued_action not in result.best_actions
            if historical_replay_parity
            else None
        ),
        "candidate_feasibility_gain": (
            _winning(result.state_label, horizon=horizon)
            and not replay_issued_winning
            if historical_replay_parity
            else None
        ),
        "issue_certificate_lower_bound": issue_compatibility,
        "issue_enemy_changed": bool(
            isinstance(row.get("issue_time_enemy_guard"), dict)
            and row["issue_time_enemy_guard"].get("changes")
        ),
    }


def audit(
    *,
    trace: Path,
    capsule_dir: Path,
    pre_hit_window: int,
    horizon: int,
    cadence: tuple[int, ...],
    max_roots: int,
) -> dict[str, object]:
    roots, _ = _read_roots(trace)
    roots_by_frame = {root.decision_frame: root for root in roots}
    candidate_rows, hit_frames = _read_candidate_rows(trace)
    selected = []
    for row in candidate_rows:
        hit_frame = _next_hit(
            hit_frames,
            int(row["frame"]),
            pre_hit_window=pre_hit_window,
        )
        if hit_frame is None:
            continue
        root = roots_by_frame.get(int(row["frame"]))
        if root is not None:
            selected.append((row, root, hit_frame))
    if max_roots:
        selected = selected[:max_roots]

    observations = []
    for index, (row, root, hit_frame) in enumerate(selected, 1):
        print(
            f"[{index}/{len(selected)}] candidate witness frame "
            f"{row['frame']} -> hit {hit_frame}",
            flush=True,
        )
        observations.append(
            _audit_root(
                row,
                root=root,
                capsule_dir=capsule_dir,
                horizon=horizon,
                cadence=cadence,
                hit_frame=hit_frame,
            )
        )

    closest_by_hit: dict[int, dict[str, object]] = {}
    closest_auditable_by_hit: dict[int, dict[str, object]] = {}
    for item in observations:
        hit_frame = int(item["hit_frame"])
        incumbent = closest_by_hit.get(hit_frame)
        if (
            incumbent is None
            or int(item["frames_to_hit"])
            < int(incumbent["frames_to_hit"])
        ):
            closest_by_hit[hit_frame] = item
        if item["historical_replay_parity"]:
            auditable_incumbent = closest_auditable_by_hit.get(hit_frame)
            if (
                auditable_incumbent is None
                or int(item["frames_to_hit"])
                < int(auditable_incumbent["frames_to_hit"])
            ):
                closest_auditable_by_hit[hit_frame] = item

    compatibility_statuses: dict[str, int] = {}
    for item in observations:
        compatibility = item["issue_certificate_lower_bound"]
        assert isinstance(compatibility, dict)
        status = str(compatibility["status"])
        compatibility_statuses[status] = (
            compatibility_statuses.get(status, 0) + 1
        )

    return {
        "schema": "th08-candidate-witness-counterfactual-audit-v2",
        "scope": {
            "trace": str(trace),
            "capsule_dir": str(capsule_dir),
            "pre_hit_window": pre_hit_window,
            "horizon": horizon,
            "decision_frame_support": list(cadence),
            "selected_root_count": len(selected),
            "covered_hit_count": len(closest_by_hit),
            "auditable_hit_count": len(closest_auditable_by_hit),
            "native_hit_count": len(hit_frames),
            "authority": "offline counterfactual only",
        },
        "contract": {
            "candidate": (
                "counterfactual fields are available only when the current "
                "exact finite-model replay reproduces both the historical "
                "state label and best-action set; mismatches fail closed"
            ),
            "issue_certificate": (
                "exact only when the actually issued action is candidate-best; "
                "alternate-action certificates were not retained and remain "
                "unresolved"
            ),
            "trace_radius": (
                "never used to infer alternate-action hard safety"
            ),
            "hit_interpretation": (
                "a 32-frame witness ending before contact does not prove hit "
                "avoidance or recursive feasibility"
            ),
        },
        "summary": {
            "root_contract_match_count": sum(
                bool(item["root_contract_matches"])
                for item in observations
            ),
            "trace_label_parity_count": sum(
                bool(item["trace_label_parity"])
                for item in observations
            ),
            "trace_best_action_parity_count": sum(
                bool(item["trace_best_action_parity"])
                for item in observations
            ),
            "historical_replay_parity_count": sum(
                bool(item["historical_replay_parity"])
                for item in observations
            ),
            "historical_replay_mismatch_count": sum(
                not bool(item["historical_replay_parity"])
                for item in observations
            ),
            "candidate_changes_action_count": sum(
                bool(item["candidate_changes_action"])
                for item in observations
            ),
            "candidate_feasibility_gain_count": sum(
                bool(item["candidate_feasibility_gain"])
                for item in observations
            ),
            "issued_model_winning_count": sum(
                bool(item["issued_model_winning"])
                for item in observations
            ),
            "issue_certificate_statuses": compatibility_statuses,
            "issue_enemy_changed_count": sum(
                bool(item["issue_enemy_changed"])
                for item in observations
            ),
            "frames_to_hit": _summary(
                [float(item["frames_to_hit"]) for item in observations]
            ),
            "timing_ms": {
                "clearance": _summary(
                    [float(item["clearance_ms"]) for item in observations]
                ),
                "candidate_replay": _summary(
                    [
                        float(item["candidate_replay_ms"])
                        for item in observations
                    ]
                ),
            },
            "closest_root_per_hit": [
                {
                    "hit_frame": hit_frame,
                    "decision_frame": int(item["decision_frame"]),
                    "frames_to_hit": int(item["frames_to_hit"]),
                    "historical_replay_parity": item[
                        "historical_replay_parity"
                    ],
                    "candidate_changes_action": item[
                        "candidate_changes_action"
                    ],
                    "candidate_feasibility_gain": item[
                        "candidate_feasibility_gain"
                    ],
                    "issue_certificate_status": item[
                        "issue_certificate_lower_bound"
                    ]["status"],
                }
                for hit_frame, item in sorted(closest_by_hit.items())
            ],
            "closest_auditable_root_per_hit": [
                {
                    "hit_frame": hit_frame,
                    "decision_frame": int(item["decision_frame"]),
                    "frames_to_hit": int(item["frames_to_hit"]),
                    "candidate_changes_action": item[
                        "candidate_changes_action"
                    ],
                    "candidate_feasibility_gain": item[
                        "candidate_feasibility_gain"
                    ],
                    "issue_certificate_status": item[
                        "issue_certificate_lower_bound"
                    ]["status"],
                }
                for hit_frame, item in sorted(
                    closest_auditable_by_hit.items()
                )
            ],
        },
        "observations": observations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("capsules", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pre-hit-window", type=int, default=120)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--cadence", type=int, nargs="+", default=(4, 5, 6))
    parser.add_argument("--max-roots", type=int, default=0)
    args = parser.parse_args(argv)
    if min(args.pre_hit_window, args.horizon, *args.cadence) <= 0:
        parser.error("window, horizon, and cadence must be positive")
    if args.max_roots < 0:
        parser.error("max roots cannot be negative")
    report = audit(
        trace=args.trace,
        capsule_dir=args.capsules,
        pre_hit_window=args.pre_hit_window,
        horizon=args.horizon,
        cadence=tuple(sorted(set(args.cadence))),
        max_roots=args.max_roots,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
