#!/usr/bin/env python3
"""Summarize one retained physical kill-before-saturation gate."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "th08-kill-before-saturation-physical-gate-v1"
BOMB = 0x02


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_report(
    *,
    trace_path: Path,
    session_path: Path,
    summary_path: Path,
    baseline_summary_path: Path,
) -> dict[str, object]:
    session = _read_json(session_path)
    summary = _read_json(summary_path)
    baseline = _read_json(baseline_summary_path)

    decisions = 0
    enabled = 0
    target_observed = 0
    preference_requested = 0
    preference_applied = 0
    deadline_missed_with_preference = 0
    viability_constrained = 0
    global_allowed_available = 0
    bomb_violations: list[int] = []
    applied_frames: list[int] = []
    requested_without_fresh_transaction = 0
    target_pointers: Counter[int] = Counter()
    observation_reasons: Counter[str] = Counter()
    selection_reasons: Counter[str] = Counter()

    with trace_path.open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("kind") != "decision":
                continue
            decisions += 1
            frame = int(row["frame"])
            policy = row.get("kill_before_saturation") or {}
            if policy.get("enabled"):
                enabled += 1
            reason = str(policy.get("observation_reason", "missing"))
            observation_reasons[reason] += 1
            target = policy.get("target")
            if isinstance(target, dict):
                target_observed += 1
                target_pointers[int(target["enemy_pointer"])] += 1
            preferred = policy.get("preferred_action")
            transaction = (
                (row.get("issue_time_enemy_guard") or {}).get("transaction")
            )
            if preferred is not None:
                preference_requested += 1
                if bool((row.get("deadline_guard") or {}).get("missed")):
                    deadline_missed_with_preference += 1
                if transaction is None:
                    requested_without_fresh_transaction += 1
                    selection_reasons["no_fresh_transaction"] += 1
                else:
                    selection_reasons[
                        str(transaction.get("selection_reason"))
                    ] += 1
            if policy.get("preference_applied"):
                preference_applied += 1
                applied_frames.append(frame)
            guidance = row.get("planner_guidance") or {}
            if guidance.get("allowed_first_actions") is not None:
                global_allowed_available += 1
            if (row.get("robust_control") or {}).get(
                "viability_constrained"
            ):
                viability_constrained += 1
            if (
                int(row.get("mask", 0)) & BOMB
                or bool(row.get("bomb"))
                or "bomb" in str(row.get("action", "")).lower()
            ):
                bomb_violations.append(frame)

    hit_frames = [int(frame) for frame in summary["hit_frames"]]
    baseline_hit_frames = [
        int(frame) for frame in baseline["hit_frames"]
    ]
    first_hit = hit_frames[0] if hit_frames else None
    baseline_first_hit = (
        baseline_hit_frames[0] if baseline_hit_frames else None
    )
    replay_save = session.get("post_stage_replay_save") or {}
    current_archive = replay_save.get("current_archive") or {}
    replay_metadata = current_archive.get("metadata") or {}
    replay_stages = replay_metadata.get("stages") or []
    replay_bomb_frames = [
        int(frame)
        for stage in replay_stages
        for frame in stage.get("bomb_press_frames", [])
    ]

    return {
        "schema": SCHEMA,
        "authority": {
            "physical_result": "observed",
            "baseline_comparison": (
                "observational_different_rng_not_causal_ab"
            ),
            "same_root_native_bullet_suppression": (
                "separate_causal_evidence"
            ),
        },
        "source": {
            "run_id": session.get("run_id"),
            "trace": str(trace_path),
            "trace_sha256": _sha256(trace_path),
            "session": str(session_path),
            "session_sha256": _sha256(session_path),
            "summary": str(summary_path),
            "summary_sha256": _sha256(summary_path),
            "baseline_summary": str(baseline_summary_path),
            "baseline_summary_sha256": _sha256(
                baseline_summary_path
            ),
            "executable_sha256": (
                (session.get("target") or {}).get("sha256")
            ),
        },
        "physical_integrity": {
            "trial_accepted": bool(session.get("trial_accepted")),
            "termination_reason": summary.get("termination_reason"),
            "hard_no_bomb": bool(session.get("hard_no_bomb")),
            "decision_bomb_violation_frames": bomb_violations,
            "replay_bomb_press_frames": replay_bomb_frames,
            "game_terminated_after_trial": bool(
                session.get("game_terminated_after_trial")
            ),
            "replay": {
                "slot": replay_save.get("slot"),
                "sha256": replay_metadata.get("sha256"),
                "archive": current_archive.get("archive"),
                "manifest": current_archive.get("manifest"),
            },
        },
        "policy_exercise": {
            "decision_count": decisions,
            "enabled_decision_count": enabled,
            "target_observed_count": target_observed,
            "target_pointer_counts": [
                {"enemy_pointer": pointer, "count": count}
                for pointer, count in sorted(target_pointers.items())
            ],
            "observation_reason_counts": dict(
                sorted(observation_reasons.items())
            ),
            "preference_requested_count": preference_requested,
            "preference_applied_count": preference_applied,
            "requested_without_fresh_transaction_count": (
                requested_without_fresh_transaction
            ),
            "selection_reason_counts": dict(
                sorted(selection_reasons.items())
            ),
            "deadline_missed_with_preference_count": (
                deadline_missed_with_preference
            ),
            "applied_frames": applied_frames,
            "applied_before_first_hit_count": sum(
                first_hit is None or frame < first_hit
                for frame in applied_frames
            ),
        },
        "global_delivery": {
            "decision_with_global_allowed_actions_count": (
                global_allowed_available
            ),
            "viability_constrained_decision_count": (
                viability_constrained
            ),
            "result": (
                "global_policy_unavailable_throughout_physical_gate"
                if (
                    global_allowed_available == 0
                    and viability_constrained == 0
                )
                else "global_policy_partially_exercised"
            ),
        },
        "outcome": {
            "hit_count": len(hit_frames),
            "hit_frames": hit_frames,
            "first_hit": first_hit,
            "baseline_run_id": baseline_summary_path.name.removesuffix(
                ".summary.json"
            ),
            "baseline_hit_count": len(baseline_hit_frames),
            "baseline_first_hit": baseline_first_hit,
            "hit_count_delta": len(hit_frames) - len(baseline_hit_frames),
            "first_hit_frame_delta": (
                first_hit - baseline_first_hit
                if (
                    first_hit is not None
                    and baseline_first_hit is not None
                )
                else None
            ),
            "interpretation": (
                "mixed_physical_observation_first_hit_later_total_hits_worse"
            ),
        },
        "conclusion": {
            "policy_physically_exercised": preference_applied > 0,
            "global_kernel_rescued_in_this_gate": False,
            "idea_falsified": False,
            "reason": (
                "early-kill action authority was exercised without Bomb, "
                "but the global policy remained unavailable and total hits "
                "did not improve; the comparison uses a different RNG root"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--baseline-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(
        trace_path=args.trace,
        session_path=args.session,
        summary_path=args.summary,
        baseline_summary_path=args.baseline_summary,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
