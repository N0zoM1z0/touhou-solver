#!/usr/bin/env python3
"""Retain compact evidence for the fixed-root Native snapshot iteration loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "artifacts" / "native_snapshot_rolling" / "raw"
DEFAULT_OUTPUT = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_native_snapshot_fast_iteration_root2129_h8_20260730.json"
)


def _load(path: Path) -> tuple[dict[str, object], str]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: JSON root is not an object")
    return payload, hashlib.sha256(raw).hexdigest()


def _result(payload: dict[str, object]) -> dict[str, object]:
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("artifact has no result object")
    return result


def _branch(
    result: dict[str, object],
    name: str,
) -> dict[str, object]:
    branches = result.get("branches")
    if not isinstance(branches, dict):
        raise ValueError("artifact has no named branches")
    branch = branches.get(name)
    if not isinstance(branch, dict):
        raise ValueError(f"artifact has no branch {name}")
    return branch


def _ticks(branch: dict[str, object]) -> list[dict[str, object]]:
    ticks = branch.get("ticks")
    if not isinstance(ticks, list) or not ticks:
        raise ValueError("branch has no tick records")
    if not all(isinstance(tick, dict) for tick in ticks):
        raise ValueError("branch tick record is malformed")
    return ticks


def _first_hit_frame(branch: dict[str, object]) -> int | None:
    for tick in _ticks(branch):
        state = tick.get("compact_state")
        if not isinstance(state, dict):
            raise ValueError("tick has no compact state")
        if int(state.get("player_phase", -1)) == 2:
            return int(state["manager_frame"])
    return None


def _tick_at(
    branch: dict[str, object],
    manager_frame: int,
) -> dict[str, object]:
    for tick in _ticks(branch):
        state = tick.get("compact_state")
        if (
            isinstance(state, dict)
            and int(state.get("manager_frame", -1)) == manager_frame
        ):
            return tick
    raise ValueError(f"branch has no tick at manager frame {manager_frame}")


def _nearest_bullets(tick: dict[str, object]) -> list[dict[str, object]]:
    projection = tick.get("collision_control_projection")
    if not isinstance(projection, dict):
        raise ValueError("tick has no collision/control projection")
    summary = projection.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("collision/control projection has no summary")
    bullets = summary.get("nearest_bullets")
    if not isinstance(bullets, list):
        raise ValueError("collision/control summary has no nearest bullets")
    if not all(isinstance(bullet, dict) for bullet in bullets):
        raise ValueError("nearest-bullet record is malformed")
    return bullets


def _bullet(
    tick: dict[str, object],
    slot: int,
) -> dict[str, object]:
    for bullet in _nearest_bullets(tick):
        if int(bullet.get("slot", -1)) == slot:
            return bullet
    raise ValueError(f"slot {slot} is absent from the nearest-bullet set")


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("cannot summarize an empty timing set")
    ordered = sorted(values)
    rank = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[rank]


def _timing_summary(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "minimum": min(values),
        "median": statistics.median(values),
        "p95_nearest_rank": _percentile(values, 0.95),
        "maximum": max(values),
    }


def _artifact_gate(
    path: Path,
    payload: dict[str, object],
    digest: str,
    *,
    expected_action_b: int,
    expected_horizon: int,
) -> dict[str, object]:
    result = _result(payload)
    if result.get("status") != "rolling_native_projection_snapshot_passed":
        raise ValueError(f"{path}: rolling snapshot gate did not pass")
    actions = result.get("actions")
    if not isinstance(actions, dict) or int(actions.get("b", -1)) != expected_action_b:
        raise ValueError(f"{path}: unexpected action B")
    if int(payload.get("horizon", -1)) != expected_horizon:
        raise ValueError(f"{path}: unexpected horizon")
    corpus = result.get("recorded_action_compact_corpus")
    natural = result.get("natural_reference")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "horizon": expected_horizon,
        "action_b": expected_action_b,
        "status": result["status"],
        "recorded_2130_2131_corpus_exact": (
            isinstance(corpus, dict) and corpus.get("exact") is True
        ),
        "natural_reference_status": (
            natural.get("status") if isinstance(natural, dict) else None
        ),
    }


def build_report(args: argparse.Namespace) -> dict[str, object]:
    named_paths = {
        "h2_recorded": args.h2_recorded,
        "h2_movement": args.h2_movement,
        "h2_focus": args.h2_focus,
        "h2_fence": args.h2_fence,
        "h4_fence": args.h4_fence,
        "h8_fence": args.h8_fence,
        "h8_early_hit": args.h8_early_hit,
        "h8_late_hit": args.h8_late_hit,
        "all36": args.all36,
        "legacy_all36": args.legacy_all36,
    }
    loaded = {
        name: (*_load(path.resolve()), path.resolve())
        for name, path in named_paths.items()
    }

    gate_specs = (
        ("h2_recorded", 0x15, 2),
        ("h2_movement", 0x15, 2),
        ("h2_focus", 0x01, 2),
        ("h2_fence", 0x14, 2),
        ("h4_fence", 0x14, 4),
        ("h8_fence", 0x14, 8),
        ("h8_early_hit", 0x61, 8),
        ("h8_late_hit", 0x44, 8),
    )
    gates = []
    for name, action, horizon in gate_specs:
        payload, digest, path = loaded[name]
        gates.append(
            {
                "name": name,
                **_artifact_gate(
                    path,
                    payload,
                    digest,
                    expected_action_b=action,
                    expected_horizon=horizon,
                ),
            }
        )

    h8_payload, h8_digest, h8_path = loaded["h8_fence"]
    h8_result = _result(h8_payload)
    recorded_branch = _branch(h8_result, "a1")
    candidate_branch = _branch(h8_result, "b")
    recorded_hit = _first_hit_frame(recorded_branch)
    candidate_hit = _first_hit_frame(candidate_branch)
    if recorded_hit != 2136 or candidate_hit is not None:
        raise ValueError("H8 causal witness does not have the retained outcome")
    recorded_tick = _tick_at(recorded_branch, 2136)
    candidate_tick = _tick_at(candidate_branch, 2136)
    recorded_state = recorded_tick["compact_state"]
    candidate_state = candidate_tick["compact_state"]
    if not isinstance(recorded_state, dict) or not isinstance(
        candidate_state,
        dict,
    ):
        raise ValueError("H8 causal witness has no compact state")
    recorded_bullet = _bullet(recorded_tick, 45)
    candidate_bullet = _bullet(candidate_tick, 45)
    candidate_closest = _nearest_bullets(candidate_tick)[0]

    all36_payload, all36_digest, all36_path = loaded["all36"]
    all36_result = _result(all36_payload)
    if (
        all36_result.get("status") != "rolling_native_all36_outcome_portfolio_passed"
        or int(all36_result.get("branch_count", -1)) != 36
        or int(
            all36_result.get(
                "legacy_corpus_outcome_class_exact_count",
                -1,
            )
        )
        != 36
        or all36_result.get("recorded_action_repeat_exact") is not True
    ):
        raise ValueError("all-36 rolling portfolio did not pass")
    all36_branches = all36_result.get("branches")
    if not isinstance(all36_branches, list):
        raise ValueError("all-36 result has no branch list")
    survivor_masks = [int(mask) for mask in all36_result.get("no_hit_masks", [])]
    if survivor_masks != [0x14, 0x15, 0x90, 0x91, 0x94, 0x95]:
        raise ValueError("all-36 survivor mask set drifted")

    hit_histogram: Counter[int] = Counter()
    legacy_differences: list[dict[str, object]] = []
    branch_elapsed: list[float] = []
    for branch in all36_branches:
        if not isinstance(branch, dict):
            raise ValueError("all-36 branch is malformed")
        comparison = branch.get("corpus_comparison")
        if not isinstance(comparison, dict):
            raise ValueError("all-36 branch has no corpus comparison")
        hit = comparison.get("observed_first_hit_manager_frame")
        if hit is not None:
            hit_histogram[int(hit)] += 1
        if comparison.get("exact") is not True:
            changes = comparison.get("field_changes")
            if not isinstance(changes, list):
                raise ValueError("legacy mismatch has no field changes")
            legacy_differences.append(
                {
                    "complete_mask": int(branch["complete_mask"]),
                    "expected_first_hit_manager_frame": comparison.get(
                        "expected_first_hit_manager_frame"
                    ),
                    "observed_first_hit_manager_frame": hit,
                    "first_hit_frame_delta": comparison.get("first_hit_frame_delta"),
                    "differing_fields": [
                        change["field"]
                        for change in changes
                        if isinstance(change, dict)
                    ],
                }
            )
        branch_elapsed.append(float(branch["branch_and_restore_elapsed_ms"]))
    if [item["complete_mask"] for item in legacy_differences] != [
        0x14,
        0x15,
        0x44,
        0x61,
        0xA5,
    ]:
        raise ValueError("legacy all-36 mismatch set drifted")

    natural_resolutions = []
    for name, mask in (
        ("h8_fence", 0x14),
        ("h8_early_hit", 0x61),
        ("h8_late_hit", 0x44),
    ):
        payload, digest, path = loaded[name]
        result = _result(payload)
        natural = result.get("natural_reference")
        if (
            not isinstance(natural, dict)
            or natural.get("status") != "natural_frame_differential_passed"
        ):
            raise ValueError(f"{path}: natural-frame validation did not pass")
        natural_ticks = natural.get("ticks")
        if not isinstance(natural_ticks, list):
            raise ValueError(f"{path}: natural-frame history is absent")
        natural_hit = next(
            (
                int(state["manager_frame"])
                for tick in natural_ticks
                if isinstance(tick, dict)
                and isinstance(
                    state := tick.get("compact_state"),
                    dict,
                )
                and int(state.get("player_phase", -1)) == 2
            ),
            None,
        )
        natural_resolutions.append(
            {
                "complete_mask": mask,
                "path": str(path.relative_to(ROOT)),
                "sha256": digest,
                "headless_first_hit_manager_frame": _first_hit_frame(
                    _branch(result, "b")
                ),
                "natural_first_hit_manager_frame": natural_hit,
                "collision_control_exact_every_tick": True,
            }
        )

    step_wait: list[float] = []
    broad_capture: list[float] = []
    collision_capture: list[float] = []
    for branch_name in ("a1", "a2", "b"):
        for tick in _ticks(_branch(h8_result, branch_name)):
            timing = tick.get("timing_ms")
            if not isinstance(timing, dict):
                raise ValueError("H8 tick has no timing record")
            step_wait.append(float(timing["step_wait"]))
            broad_capture.append(float(timing["native_projection_capture"]))
            collision_capture.append(
                float(timing["collision_control_projection_capture"])
            )

    legacy_payload, legacy_digest, legacy_path = loaded["legacy_all36"]
    legacy_started = datetime.fromisoformat(str(legacy_payload["started_at"]))
    legacy_finished = datetime.fromisoformat(str(legacy_payload["finished_at"]))
    all36_started = datetime.fromisoformat(str(all36_payload["started_at"]))
    all36_finished = datetime.fromisoformat(str(all36_payload["finished_at"]))
    all36_timing = all36_result.get("timing_ms")
    if not isinstance(all36_timing, dict):
        raise ValueError("all-36 result has no timing record")

    return {
        "schema": "th08-native-snapshot-fast-iteration-evidence-v1",
        "evidence_finished_at": all36_payload["finished_at"],
        "status": "accepted_fixed_root_fast_iteration_evidence",
        "root": {
            "manager_frame": 2129,
            "rolling_horizon": 8,
            "action_hold_frames": 3,
            "recorded_action": 0x05,
            "source_replay_sha256": h8_payload["replay_contract"]["sha256"],
        },
        "progressive_gates": gates,
        "causal_hit_localization": {
            "classification": "observed",
            "recorded": {
                "first_hit_manager_frame": recorded_hit,
                "player": {
                    "x": recorded_state["player_x"],
                    "y": recorded_state["player_y"],
                    "phase": recorded_state["player_phase"],
                    "predeath_counter": recorded_state["predeath_counter"],
                },
                "hostile_bullet": {
                    "slot": recorded_bullet["slot"],
                    "x": recorded_bullet["x"],
                    "y": recorded_bullet["y"],
                    "signed_box_separation": recorded_bullet["signed_box_separation"],
                },
            },
            "candidate_0x14": {
                "first_hit_through_manager_frame_2137": candidate_hit,
                "player_at_2136": {
                    "x": candidate_state["player_x"],
                    "y": candidate_state["player_y"],
                    "phase": candidate_state["player_phase"],
                    "predeath_counter": candidate_state["predeath_counter"],
                },
                "player_y_delta_from_recorded_at_2136": (
                    float(candidate_state["player_y"])
                    - float(recorded_state["player_y"])
                ),
                "same_slot_45_signed_box_separation_at_2136": (
                    candidate_bullet["signed_box_separation"]
                ),
                "closest_hostile_bullet_at_2136": candidate_closest,
            },
            "same_world_slot_45_position_exact_at_2136": (
                recorded_bullet["x"] == candidate_bullet["x"]
                and recorded_bullet["y"] == candidate_bullet["y"]
            ),
            "source": {
                "path": str(h8_path.relative_to(ROOT)),
                "sha256": h8_digest,
            },
        },
        "all36_candidate_search": {
            "classification": "observed",
            "status": all36_result["status"],
            "branch_count": 36,
            "legacy_outcome_class_exact_count": all36_result[
                "legacy_corpus_outcome_class_exact_count"
            ],
            "legacy_full_endpoint_exact_count": all36_result[
                "legacy_corpus_exact_count"
            ],
            "recorded_action_repeat_exact": all36_result[
                "recorded_action_repeat_exact"
            ],
            "survivor_masks": survivor_masks,
            "survivor_masks_hex": [f"0x{mask:02x}" for mask in survivor_masks],
            "first_hit_frame_histogram": {
                str(frame): hit_histogram[frame] for frame in sorted(hit_histogram)
            },
            "source": {
                "path": str(all36_path.relative_to(ROOT)),
                "sha256": all36_digest,
            },
        },
        "legacy_observer_differences": {
            "classification": "observed_and_source_explained",
            "legacy_capture_model": (
                "observe_state fields were polled without a manager-frame "
                "bracket; the game could advance between field reads"
            ),
            "full_endpoint_exact_count": all36_result["legacy_corpus_exact_count"],
            "outcome_class_exact_count": all36_result[
                "legacy_corpus_outcome_class_exact_count"
            ],
            "differences": legacy_differences,
            "same_seam_natural_resolutions": natural_resolutions,
            "legacy_source": {
                "path": str(legacy_path.relative_to(ROOT)),
                "sha256": legacy_digest,
            },
        },
        "timing": {
            "boundary": (
                "portfolio timing includes eight native calculation ticks, "
                "per-tick broad and collision/control capture, full endpoint "
                "recapture, dirty-page restore, and verification for each "
                "branch; replay startup/root fast-forward is excluded from "
                "the 36-branch subtotal"
            ),
            "native_calculation_step_wait_ms": _timing_summary(step_wait),
            "broad_native_projection_capture_ms": _timing_summary(broad_capture),
            "collision_control_capture_ms": _timing_summary(collision_capture),
            "all36_branch_and_restore_ms": _timing_summary(branch_elapsed),
            "all36_portfolio_subtotal_ms": all36_timing["portfolio_36_branches"],
            "all36_transaction_including_root_and_canary_ms": all36_timing[
                "transaction_including_root_and_canary"
            ],
            "all36_process_wall_ms": (all36_finished - all36_started).total_seconds()
            * 1000.0,
            "legacy_all36_report_wall_ms": (
                legacy_finished - legacy_started
            ).total_seconds()
            * 1000.0,
            "timing_comparison_claim": (
                "the retained clocks have different capture boundaries and "
                "are reported separately; no direct speedup ratio is claimed"
            ),
        },
        "claims": [
            {
                "classification": "observed",
                "claim": (
                    "one immutable native root produced 36 restored H8 "
                    "counterfactuals with deterministic recorded-action repeat"
                ),
            },
            {
                "classification": "observed",
                "claim": (
                    "the recorded 0x05 branch hits at 2136 on hostile bullet "
                    "slot 45; holding 0x14 for three ticks moves the player "
                    "upward and preserves positive clearance through 2137"
                ),
            },
            {
                "classification": "inferred",
                "claim": (
                    "the fixed-root loop is suitable for rapid local cause "
                    "isolation and candidate ranking at this replay seam"
                ),
            },
        ],
        "authority": {
            "accepted_for": (
                "fixed-replay-root offline counterfactual diagnosis and "
                "candidate search"
            ),
            "not_accepted_for": (
                "live predictive authority, event-class generalization, or "
                "physical Lunatic/Extra promotion"
            ),
            "next_gate": (
                "repeat on event-class roots, then use a named physical "
                "falsifier only for promoted immutable behavior"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--h2-recorded",
        type=Path,
        default=RAW / "th08_h2_a_ref_v4_20260730.json",
    )
    parser.add_argument(
        "--h2-movement",
        type=Path,
        default=RAW / "th08_h2_b15_ref_20260730.json",
    )
    parser.add_argument(
        "--h2-focus",
        type=Path,
        default=RAW / "th08_h2_b01_ref_20260730.json",
    )
    parser.add_argument(
        "--h2-fence",
        type=Path,
        default=RAW / "th08_h2_b14_ref_20260730.json",
    )
    parser.add_argument(
        "--h4-fence",
        type=Path,
        default=RAW / "th08_h4_b14_ref_v2_20260730.json",
    )
    parser.add_argument(
        "--h8-fence",
        type=Path,
        default=RAW / "th08_h8_b14_ref_20260730.json",
    )
    parser.add_argument(
        "--h8-early-hit",
        type=Path,
        default=RAW / "th08_h8_b61_ref_20260730.json",
    )
    parser.add_argument(
        "--h8-late-hit",
        type=Path,
        default=RAW / "th08_h8_b44_ref_20260730.json",
    )
    parser.add_argument(
        "--all36",
        type=Path,
        default=RAW / "th08_h8_all36_v2_20260730.json",
    )
    parser.add_argument(
        "--legacy-all36",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "runtime_reports"
            / "th08_native_branch_trials_latest_root2129_fence2137_all36_20260730.json"
        ),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"native snapshot compact report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
