#!/usr/bin/env python3
"""Build compact causal-policy evidence from rolling Native snapshot trials."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA = "th08-native-snapshot-causal-policy-evidence-v1"
DEFAULT_H8_ALL36 = Path(
    "artifacts/native_snapshot_rolling/raw/th08_h8_all36_v2_20260730.json"
)
DEFAULT_SECONDARY_PREFIX14 = Path(
    "artifacts/native_snapshot_rolling/raw/th08_secondary_prefix14_h8_20260730.json"
)
DEFAULT_SECONDARY_REMAINING5 = Path(
    "artifacts/native_snapshot_rolling/raw/th08_secondary_remaining5_h8_20260730.json"
)
DEFAULT_TERTIARY = Path(
    "artifacts/native_snapshot_rolling/raw/th08_tertiary_94_44_all36_h8_20260730.json"
)
DEFAULT_QUATERNARY = Path(
    "artifacts/native_snapshot_rolling/raw/"
    "th08_quaternary_94_44_10_all36_h8_20260730.json"
)
DEFAULT_WITNESS = Path(
    "artifacts/native_snapshot_rolling/raw/"
    "th08_schedule_94_44_10_a4_h32_natural_20260730.json"
)
DEFAULT_OUTPUT = Path(
    "artifacts/runtime_reports/"
    "th08_native_snapshot_causal_policy_root2129_h32_20260730.json"
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _content_artifact(kind: str, payload: dict[str, object]) -> dict[str, object]:
    body = {
        "kind": kind,
        "payload": payload,
    }
    return {
        "artifact_id": f"sha256:{hashlib.sha256(_canonical_bytes(body)).hexdigest()}",
        **body,
    }


def _load_source(path: Path) -> tuple[dict[str, Any], dict[str, object]]:
    data = path.read_bytes()
    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise ValueError(f"native snapshot source is not an object: {path}")
    return payload, {
        "path": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def _collision_summary(tick: dict[str, Any]) -> dict[str, Any]:
    compact = tick.get("collision_control_summary")
    if isinstance(compact, dict):
        return compact
    projection = tick.get("collision_control_projection")
    if isinstance(projection, dict) and isinstance(projection.get("summary"), dict):
        return projection["summary"]
    raise ValueError("native tick has no collision/control summary")


def _collision_sha(tick: dict[str, Any]) -> str:
    compact = tick.get("collision_control_projection_sha256")
    if isinstance(compact, str):
        return compact
    projection = tick.get("collision_control_projection")
    if isinstance(projection, dict) and isinstance(projection.get("sha256"), str):
        return projection["sha256"]
    raise ValueError("native tick has no collision/control digest")


def _native_sha(tick: dict[str, Any]) -> str:
    compact = tick.get("native_projection_sha256")
    if isinstance(compact, str):
        return compact
    projection = tick.get("native_projection")
    if isinstance(projection, dict) and isinstance(projection.get("sha256"), str):
        return projection["sha256"]
    raise ValueError("native tick has no native projection digest")


def _first_hit(ticks: list[dict[str, Any]]) -> int | None:
    return next(
        (
            int(tick["compact_state"]["manager_frame"])
            for tick in ticks
            if int(tick["compact_state"]["player_phase"]) == 2
        ),
        None,
    )


def _minimum_clearance(ticks: list[dict[str, Any]]) -> dict[str, object]:
    samples = []
    for tick in ticks:
        nearest = _collision_summary(tick)["nearest_bullets"][0]
        state = tick["compact_state"]
        samples.append(
            {
                "manager_frame": int(state["manager_frame"]),
                "slot": int(nearest["slot"]),
                "signed_box_separation": float(nearest["signed_box_separation"]),
                "player_x": float(state["player_x"]),
                "player_y": float(state["player_y"]),
            }
        )
    return min(samples, key=lambda sample: sample["signed_box_separation"])


def _choose_maximin(
    branches: list[dict[str, Any]],
    *,
    mask_field: str,
) -> dict[str, object]:
    candidates = []
    for branch in branches:
        ticks = branch["ticks"]
        if branch.get("first_hit_manager_frame", _first_hit(ticks)) is not None:
            continue
        minimum = _minimum_clearance(ticks)
        endpoint_nearest = _collision_summary(ticks[-1])["nearest_bullets"][0]
        candidates.append(
            {
                "complete_mask": int(branch[mask_field]),
                "minimum_clearance": minimum,
                "endpoint_clearance": float(endpoint_nearest["signed_box_separation"]),
            }
        )
    if not candidates:
        raise ValueError("native action portfolio has no surviving branch")
    return max(
        candidates,
        key=lambda candidate: (
            candidate["minimum_clearance"]["signed_box_separation"],
            candidate["endpoint_clearance"],
            -candidate["complete_mask"],
        ),
    )


def _hit_histogram(branches: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(
        (
            branch.get("first_hit_manager_frame")
            if "first_hit_manager_frame" in branch
            else _first_hit(branch["ticks"])
        )
        for branch in branches
    )
    return {
        ("survived" if frame is None else str(frame)): count
        for frame, count in sorted(
            counts.items(),
            key=lambda item: (
                item[0] is None,
                -1 if item[0] is None else int(item[0]),
            ),
        )
    }


def _portfolio_artifact(
    *,
    name: str,
    root_frame: int,
    prefix_schedule: list[int | None],
    branches: list[dict[str, Any]],
    mask_field: str,
    parent_repeat_exact: bool,
    timing_ms: float,
) -> tuple[dict[str, object], dict[str, object]]:
    selected = _choose_maximin(branches, mask_field=mask_field)
    survivors = sorted(
        int(branch[mask_field])
        for branch in branches
        if branch.get("first_hit_manager_frame", _first_hit(branch["ticks"])) is None
    )
    artifact = _content_artifact(
        "ActionPortfolio",
        {
            "name": name,
            "root_manager_frame": root_frame,
            "prefix_action_schedule": prefix_schedule,
            "branch_horizon": len(branches[0]["ticks"]),
            "branch_count": len(branches),
            "survivor_masks": survivors,
            "survivor_masks_hex": [f"0x{mask:02X}" for mask in survivors],
            "hit_histogram": _hit_histogram(branches),
            "selected_by": (
                "maximize whole-segment minimum signed clearance, then endpoint "
                "clearance, then lower equivalent Shot mask"
            ),
            "selected": selected,
            "parent_root_repeat_exact": parent_repeat_exact,
            "portfolio_timing_ms": timing_ms,
        },
    )
    return artifact, selected


def _find_slot(
    tick: dict[str, Any],
    slot: int,
) -> dict[str, Any]:
    return next(
        bullet
        for bullet in _collision_summary(tick)["nearest_bullets"]
        if int(bullet["slot"]) == slot
    )


def _compact_trajectory_tick(tick: dict[str, Any]) -> dict[str, object]:
    state = tick["compact_state"]
    nearest = _collision_summary(tick)["nearest_bullets"][0]
    return {
        "manager_frame": int(state["manager_frame"]),
        "selected_action": int(tick["selected_action"]),
        "recorded_action": int(tick["recorded_action"]),
        "player_phase": int(state["player_phase"]),
        "player_x": float(state["player_x"]),
        "player_y": float(state["player_y"]),
        "nearest_bullet_slot": int(nearest["slot"]),
        "nearest_signed_box_separation": float(nearest["signed_box_separation"]),
        "native_projection_sha256": _native_sha(tick),
        "collision_control_projection_sha256": _collision_sha(tick),
    }


def build_report(
    *,
    h8_all36: Path,
    secondary_prefix14: Path,
    secondary_remaining5: Path,
    tertiary: Path,
    quaternary: Path,
    witness: Path,
) -> dict[str, object]:
    source_paths = (
        h8_all36,
        secondary_prefix14,
        secondary_remaining5,
        tertiary,
        quaternary,
        witness,
    )
    loaded = [_load_source(path) for path in source_paths]
    (
        initial,
        secondary14,
        secondary5,
        tertiary_raw,
        quaternary_raw,
        witness_raw,
    ) = (entry[0] for entry in loaded)
    sources = [entry[1] for entry in loaded]

    if initial["result"]["status"] != "rolling_native_all36_outcome_portfolio_passed":
        raise ValueError("initial H8 all-36 source did not pass")
    for source in (secondary14, secondary5, tertiary_raw, quaternary_raw):
        result = source["result"]
        if (
            result["status"] != "causal_secondary_search_passed"
            or not result["parent_root_repeat"]["exact"]
        ):
            raise ValueError("causal portfolio source did not pass exact parent repeat")
    witness_result = witness_raw["result"]
    natural = witness_result.get("natural_reference")
    if (
        witness_result["status"] != "rolling_native_projection_snapshot_passed"
        or not isinstance(natural, dict)
        or natural["status"] != "natural_frame_differential_passed"
    ):
        raise ValueError("H32 witness did not pass the natural differential")

    initial_branches = initial["result"]["branches"]
    initial_portfolio, selected0 = _portfolio_artifact(
        name="root2129_h8_all36",
        root_frame=2129,
        prefix_schedule=[],
        branches=initial_branches,
        mask_field="complete_mask",
        parent_repeat_exact=bool(initial["result"]["recorded_action_repeat_exact"]),
        timing_ms=float(initial["result"]["timing_ms"]["portfolio_36_branches"]),
    )

    secondary_prefixes = [
        *secondary14["result"]["prefixes"],
        *secondary5["result"]["prefixes"],
    ]
    if sorted(prefix["prefix_mask"] for prefix in secondary_prefixes) != [
        0x14,
        0x15,
        0x90,
        0x91,
        0x94,
        0x95,
    ]:
        raise ValueError("secondary portfolio does not cover the six H8 survivors")
    selected_prefix = next(
        prefix
        for prefix in secondary_prefixes
        if int(prefix["prefix_mask"]) == int(selected0["complete_mask"])
    )
    selected_prefix_portfolio, selected1 = _portfolio_artifact(
        name="root2137_h8_all36_after_0x94",
        root_frame=2137,
        prefix_schedule=selected_prefix["prefix"]["action_schedule"],
        branches=selected_prefix["continuations"],
        mask_field="complete_mask",
        parent_repeat_exact=bool(
            secondary14["result"]["parent_root_repeat"]["exact"]
            and secondary5["result"]["parent_root_repeat"]["exact"]
        ),
        timing_ms=float(
            secondary14["result"]["timing_ms"]["secondary_search"]
            + secondary5["result"]["timing_ms"]["secondary_search"]
        ),
    )
    secondary_entries = []
    for prefix in sorted(
        secondary_prefixes,
        key=lambda entry: int(entry["prefix_mask"]),
    ):
        selected_continuation = _choose_maximin(
            prefix["continuations"],
            mask_field="complete_mask",
        )
        prefix_minimum = _minimum_clearance(prefix["prefix"]["ticks"])
        secondary_entries.append(
            {
                "prefix_mask": int(prefix["prefix_mask"]),
                "prefix_mask_hex": f"0x{int(prefix['prefix_mask']):02X}",
                "prefix_minimum_clearance": prefix_minimum,
                "continuation_survivor_masks": prefix["survivor_masks"],
                "continuation_survivor_masks_hex": [
                    f"0x{int(mask):02X}" for mask in prefix["survivor_masks"]
                ],
                "continuation_hit_histogram": _hit_histogram(prefix["continuations"]),
                "selected_continuation": selected_continuation,
                "whole_h16_minimum_clearance": min(
                    float(prefix_minimum["signed_box_separation"]),
                    float(
                        selected_continuation["minimum_clearance"][
                            "signed_box_separation"
                        ]
                    ),
                ),
            }
        )
    selected_pair = max(
        secondary_entries,
        key=lambda entry: (
            entry["whole_h16_minimum_clearance"],
            entry["selected_continuation"]["minimum_clearance"][
                "signed_box_separation"
            ],
            entry["selected_continuation"]["endpoint_clearance"],
            -entry["prefix_mask"],
            -entry["selected_continuation"]["complete_mask"],
        ),
    )
    if (
        selected_pair["prefix_mask"],
        selected_pair["selected_continuation"]["complete_mask"],
    ) != (0x94, 0x44):
        raise ValueError("unexpected global H16 maximin pair")
    secondary_matrix = _content_artifact(
        "ActionPortfolio",
        {
            "name": "root2129_to_2137_six_prefix_secondary_all36",
            "root_manager_frame": 2129,
            "subroot_manager_frame": 2137,
            "endpoint_manager_frame": 2145,
            "prefix_count": 6,
            "continuations_per_prefix": 36,
            "branch_count": 216,
            "entries": secondary_entries,
            "selected_pair": selected_pair,
            "selected_prefix_detail_artifact_id": selected_prefix_portfolio[
                "artifact_id"
            ],
            "parent_root_repeat_exact": bool(
                secondary14["result"]["parent_root_repeat"]["exact"]
                and secondary5["result"]["parent_root_repeat"]["exact"]
            ),
            "portfolio_timing_ms": float(
                secondary14["result"]["timing_ms"]["secondary_search"]
                + secondary5["result"]["timing_ms"]["secondary_search"]
            ),
        },
    )

    tertiary_prefix = tertiary_raw["result"]["prefixes"][0]
    tertiary_portfolio, selected2 = _portfolio_artifact(
        name="root2145_h8_all36_after_0x94_0x44",
        root_frame=2145,
        prefix_schedule=tertiary_prefix["prefix_action_schedule"],
        branches=tertiary_prefix["continuations"],
        mask_field="complete_mask",
        parent_repeat_exact=bool(tertiary_raw["result"]["parent_root_repeat"]["exact"]),
        timing_ms=float(tertiary_raw["result"]["timing_ms"]["secondary_search"]),
    )

    quaternary_prefix = quaternary_raw["result"]["prefixes"][0]
    quaternary_portfolio, selected3 = _portfolio_artifact(
        name="root2153_h8_all36_after_0x94_0x44_0x10",
        root_frame=2153,
        prefix_schedule=quaternary_prefix["prefix_action_schedule"],
        branches=quaternary_prefix["continuations"],
        mask_field="complete_mask",
        parent_repeat_exact=bool(
            quaternary_raw["result"]["parent_root_repeat"]["exact"]
        ),
        timing_ms=float(quaternary_raw["result"]["timing_ms"]["secondary_search"]),
    )

    selected_masks = [
        int(selected0["complete_mask"]),
        int(selected1["complete_mask"]),
        int(selected2["complete_mask"]),
        int(selected3["complete_mask"]),
    ]
    if selected_masks != [0x94, 0x44, 0x10, 0xA4]:
        raise ValueError(f"unexpected maximin causal chain: {selected_masks!r}")

    branch_a = witness_result["branches"]["a1"]
    branch_b = witness_result["branches"]["b"]
    recorded_ticks = branch_a["ticks"]
    witness_ticks = branch_b["ticks"]
    schedule = witness_result["actions"]["b_schedule"]
    if len(witness_ticks) != 32 or schedule is None:
        raise ValueError("exact witness does not cover 32 scheduled ticks")
    recorded_hit = _first_hit(recorded_ticks)
    witness_hit = _first_hit(witness_ticks)
    if recorded_hit != 2136 or witness_hit is not None:
        raise ValueError("recorded/witness hit outcomes changed")

    natural_exact_ticks = sum(
        bool(tick["headless_collision_control_projection_exact"])
        and bool(tick["headless_compact_exact"])
        for tick in natural["ticks"]
    )
    if natural_exact_ticks != 32:
        raise ValueError("natural witness is not exact at every tick")

    first_action_tick = next(
        index
        for index, tick in enumerate(witness_ticks)
        if int(tick["selected_action"]) != int(tick["recorded_action"])
    )
    first_collision_tick = next(
        index
        for index, (left, right) in enumerate(
            zip(recorded_ticks, witness_ticks, strict=True)
        )
        if _collision_sha(left) != _collision_sha(right)
    )
    recorded_hit_tick = next(
        tick
        for tick in recorded_ticks
        if int(tick["compact_state"]["manager_frame"]) == recorded_hit
    )
    witness_same_frame_tick = next(
        tick
        for tick in witness_ticks
        if int(tick["compact_state"]["manager_frame"]) == recorded_hit
    )
    recorded_slot45 = _find_slot(recorded_hit_tick, 45)
    witness_slot45 = _find_slot(witness_same_frame_tick, 45)
    minimum = _minimum_clearance(witness_ticks)

    root_capsule = _content_artifact(
        "NativeRootCapsule",
        {
            "manager_frame": 2129,
            "source_replay_sha256": initial["replay_contract"]["sha256"],
            "executable_sha256": witness_raw["executable_identity"]["sha256"],
            "same_session_snapshot_sha256": witness_result["baseline_root"]["sha256"],
            "native_projection_sha256": witness_result["root_native_projection"][
                "sha256"
            ],
            "collision_control_projection_sha256": witness_result[
                "root_collision_control_projection"
            ]["sha256"],
            "root_compact_state": witness_result["root_compact_state"],
            "process_bound": True,
            "cross_session_use": "evidence_only",
        },
    )
    native_trajectory = _content_artifact(
        "NativeTrajectory",
        {
            "root_artifact_id": root_capsule["artifact_id"],
            "action_schedule": schedule,
            "ticks": [_compact_trajectory_tick(tick) for tick in witness_ticks],
            "first_hit_manager_frame": witness_hit,
        },
    )
    model_trajectory = _content_artifact(
        "ModelTrajectory",
        {
            "status": "not_generated",
            "reason": (
                "the rebuilt solver is not yet bound to this content-addressed "
                "native root/action schedule; no synthetic parity claim is made"
            ),
            "next_gate": (
                "run the rebuilt model on the exact root/action schedule and "
                "compare at the first per-field/event divergence"
            ),
        },
    )
    first_mismatch = _content_artifact(
        "FirstMismatchReport",
        {
            "headless_native_vs_natural_frame_pump": {
                "status": "no_mismatch_through_declared_horizon",
                "root_manager_frame": 2129,
                "endpoint_manager_frame": 2161,
                "exact_tick_count": natural_exact_ticks,
                "first_mismatch_manager_frame": None,
            },
            "recorded_loss_vs_causal_witness": {
                "first_action_difference": {
                    "tick_index": first_action_tick,
                    "manager_frame": int(
                        witness_ticks[first_action_tick]["compact_state"][
                            "manager_frame"
                        ]
                    ),
                    "recorded_action": int(
                        witness_ticks[first_action_tick]["recorded_action"]
                    ),
                    "witness_action": int(
                        witness_ticks[first_action_tick]["selected_action"]
                    ),
                },
                "first_collision_control_difference": {
                    "tick_index": first_collision_tick,
                    "manager_frame": int(
                        witness_ticks[first_collision_tick]["compact_state"][
                            "manager_frame"
                        ]
                    ),
                },
                "recorded_first_hit_manager_frame": recorded_hit,
                "witness_first_hit_manager_frame": witness_hit,
                "frame_2136_slot_45": {
                    "world_position_exact": (
                        float(recorded_slot45["x"]) == float(witness_slot45["x"])
                        and float(recorded_slot45["y"]) == float(witness_slot45["y"])
                    ),
                    "recorded_signed_box_separation": float(
                        recorded_slot45["signed_box_separation"]
                    ),
                    "witness_signed_box_separation": float(
                        witness_slot45["signed_box_separation"]
                    ),
                    "recorded_player": recorded_hit_tick["compact_state"],
                    "witness_player": witness_same_frame_tick["compact_state"],
                },
            },
            "model_vs_native": {
                "status": "pending_model_trajectory",
                "first_mismatch_manager_frame": None,
            },
        },
    )
    exact_witness = _content_artifact(
        "ExactWitness",
        {
            "root_artifact_id": root_capsule["artifact_id"],
            "native_trajectory_artifact_id": native_trajectory["artifact_id"],
            "root_manager_frame": 2129,
            "endpoint_manager_frame": 2161,
            "horizon": 32,
            "decision_masks": selected_masks,
            "decision_masks_hex": [f"0x{mask:02X}" for mask in selected_masks],
            "decision_frames": [2129, 2137, 2145, 2153],
            "action_schedule": schedule,
            "no_bomb": all(
                action is None or int(action) & 0x02 == 0 for action in schedule
            ),
            "first_hit_manager_frame": None,
            "minimum_signed_clearance": minimum,
            "natural_frame_differential": {
                "status": natural["status"],
                "exact_tick_count": natural_exact_ticks,
                "first_mismatch_manager_frame": None,
            },
            "authority": (
                "fixed_replay_root_original-engine causal witness through "
                "manager frame 2161 only"
            ),
        },
    )
    counterexamples = _content_artifact(
        "CounterexampleCorpus",
        {
            "entries": [
                {
                    "id": "CE-0207",
                    "prior_failure": (
                        "six three-frame masks merely delayed the hit to 2140..2142"
                    ),
                    "correction": (
                        "observation-compatible causal continuation at 2137/2145/2153"
                    ),
                    "status": "corrected_through_declared_h32_horizon",
                },
                {
                    "id": "CE-0209",
                    "failure": "unbracketed replay polling tore endpoint state",
                    "correction": "calculation-seam snapshot plus natural differential",
                    "status": "fixed_for_declared_collision_control_projection",
                },
                {
                    "id": "CE-0210",
                    "failure": (
                        "one 216-branch attempt detected a committed-map epoch "
                        "change after 14 continuations"
                    ),
                    "correction": (
                        "poison the session, clean up, rebootstrap, and report "
                        "removed/added region identities on recurrence"
                    ),
                    "status": "intermittent_observed_root_cause_unknown",
                },
            ]
        },
    )

    portfolios = [
        initial_portfolio,
        secondary_matrix,
        tertiary_portfolio,
        quaternary_portfolio,
    ]
    total_portfolio_branches = 36 + 216 + 36 + 36
    return {
        "schema": SCHEMA,
        "status": "accepted_fixed_root_causal_iteration_evidence",
        "root_manager_frame": 2129,
        "endpoint_manager_frame": 2161,
        "sources": sources,
        "artifacts": {
            "native_root_capsule": root_capsule,
            "native_trajectory": native_trajectory,
            "model_trajectory": model_trajectory,
            "first_mismatch_report": first_mismatch,
            "action_portfolios": portfolios,
            "counterexample_corpus": counterexamples,
            "exact_witness": exact_witness,
        },
        "effectiveness": {
            "recorded_first_hit_manager_frame": recorded_hit,
            "witness_first_hit_manager_frame": witness_hit,
            "verified_survival_extension_past_recorded_hit_frames": 2161 - recorded_hit,
            "total_native_portfolio_branches": total_portfolio_branches,
            "secondary_two_decision_branches": 216,
            "largest_single_warm_session_branch_count": 180,
            "largest_single_warm_session_search_ms": float(
                secondary5["result"]["timing_ms"]["secondary_search"]
            ),
            "largest_single_warm_session_parent_repeat_exact": bool(
                secondary5["result"]["parent_root_repeat"]["exact"]
            ),
            "cause_localized_to": (
                "frame 2136 hostile bullet slot 45 versus changed player path"
            ),
            "improvement_found": (
                "four-decision no-Bomb causal schedule remains unhit through 2161"
            ),
        },
        "authority": {
            "accepted_for": (
                "same-replay fixed-root cause isolation, causal candidate "
                "ranking, and exact native witness validation"
            ),
            "not_accepted_for": (
                "rebuilt-model parity, other event-class roots, live action "
                "authority, or physical Lunatic/Extra promotion"
            ),
            "next_gate": (
                "bind the rebuilt solver to the NativeRootCapsule and produce "
                "ModelTrajectory/FirstMismatch; then exercise distinct event "
                "classes before one named physical delivery falsifier"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h8-all36", type=Path, default=DEFAULT_H8_ALL36)
    parser.add_argument(
        "--secondary-prefix14",
        type=Path,
        default=DEFAULT_SECONDARY_PREFIX14,
    )
    parser.add_argument(
        "--secondary-remaining5",
        type=Path,
        default=DEFAULT_SECONDARY_REMAINING5,
    )
    parser.add_argument("--tertiary", type=Path, default=DEFAULT_TERTIARY)
    parser.add_argument("--quaternary", type=Path, default=DEFAULT_QUATERNARY)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(
        h8_all36=args.h8_all36,
        secondary_prefix14=args.secondary_prefix14,
        secondary_remaining5=args.secondary_remaining5,
        tertiary=args.tertiary,
        quaternary=args.quaternary,
        witness=args.witness,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
