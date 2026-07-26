#!/usr/bin/env python3
"""Audit local certificates against active/held/pending actuator semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

from th08_live_dodge_agent import (
    SUPPORTED_INPUT_MASK,
    _PLANNER_ACTIONS,
    _action_name_from_mask,
    _legacy_robust_action_certificates,
    _local_pipeline_action_from_mask,
    _robust_action_certificates,
)
from th08_trace_replay import hazards_from_trace
from touhou_control.local_pipeline_oracle import LocalPipelineRoot


PREHIT_WINDOW_FRAMES = 240


@dataclass(frozen=True)
class ReconstructedRoot:
    row: dict[str, object]
    root: LocalPipelineRoot
    held_mask: int
    source_frame: int
    issue_age: int
    overdue: bool
    prehit: bool
    root_source: str = "inferred_previous_write"


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _timing_summary(values: list[float]) -> dict[str, float]:
    return {
        "median_ms": statistics.median(values),
        "p95_ms": _p95(values),
        "max_ms": max(values),
    }


def _density_bin(active_bullets: int) -> str:
    if active_bullets < 200:
        return "lt_200"
    if active_bullets < 600:
        return "200_599"
    if active_bullets < 1000:
        return "600_999"
    return "ge_1000"


def _certificate_record(certificate) -> dict[str, object]:
    return {
        "worst_collisions": certificate.worst_collisions,
        "min_clearance": certificate.min_clearance,
        "cvar_risk": certificate.cvar_risk,
        "worst_delay": certificate.worst_delay,
        "write_required": certificate.write_required,
        "pipeline_branch_count": certificate.pipeline_branch_count,
        "worst_pending_remaining": (
            certificate.worst_pending_remaining
        ),
    }


def _safe_actions(certificates) -> tuple[str, ...]:
    return tuple(
        action.name
        for action in _PLANNER_ACTIONS
        if (
            certificates[action.name].worst_collisions == 0
            and certificates[action.name].min_clearance >= 0.0
        )
    )


def _ranked_action(certificates) -> str:
    return min(
        _PLANNER_ACTIONS,
        key=lambda action: (
            certificates[action.name].worst_collisions,
            max(-certificates[action.name].min_clearance, 0.0),
            certificates[action.name].cvar_risk,
            -certificates[action.name].min_clearance,
            action.name,
        ),
    ).name


def _read_decisions(
    trace: Path,
) -> tuple[list[dict[str, object]], str]:
    rows = []
    digest = hashlib.sha256()
    with trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if row.get("kind") == "decision":
                rows.append(row)
    return rows, digest.hexdigest()


def _direct_root_from_trace(
    row: dict[str, object],
) -> tuple[LocalPipelineRoot, int, int, bool]:
    """Parse and cross-check one new-schema shadow root, failing closed."""

    record = row.get("local_pipeline_root")
    if not isinstance(record, dict):
        raise ValueError("local pipeline root record is not an object")
    if record.get("role") != "shadow_no_action_authority":
        raise ValueError("local pipeline root has unexpected authority role")
    if record.get("estimator_consistent") is not True:
        raise ValueError("local pipeline root estimator is inconsistent")

    active_action = record.get("active_action")
    held_action = record.get("held_desired_action")
    pending_action = record.get("pending_action")
    active_mask = record.get("active_mask")
    held_mask = record.get("held_desired_mask")
    pending_mask = record.get("pending_mask")
    if not isinstance(active_action, str) or not isinstance(held_action, str):
        raise ValueError("local pipeline root action names are invalid")
    if pending_action is not None and not isinstance(pending_action, str):
        raise ValueError("local pipeline pending action is invalid")
    if type(active_mask) is not int or type(held_mask) is not int:
        raise ValueError("local pipeline root masks are invalid")
    if (
        active_mask != active_mask & SUPPORTED_INPUT_MASK
        or held_mask != held_mask & SUPPORTED_INPUT_MASK
    ):
        raise ValueError("local pipeline root contains unsupported mask bits")
    input_snapshot = row.get("input_snapshot")
    if (
        not isinstance(input_snapshot, dict)
        or type(input_snapshot.get("current")) is not int
        or (
            int(input_snapshot["current"]) & SUPPORTED_INPUT_MASK
            != active_mask
        )
    ):
        raise ValueError("direct active mask disagrees with trace snapshot")
    if _local_pipeline_action_from_mask(active_mask) != active_action:
        raise ValueError("direct active mask/action disagree")
    if _local_pipeline_action_from_mask(held_mask) != held_action:
        raise ValueError("direct held mask/action disagree")

    remaining_raw = record.get("remaining_delay_support", ())
    if not isinstance(remaining_raw, (list, tuple)) or any(
        type(value) is not int for value in remaining_raw
    ):
        raise ValueError("direct remaining-delay support is invalid")
    remaining = tuple(int(value) for value in remaining_raw)
    if pending_action is None:
        if pending_mask is not None:
            raise ValueError("direct root has a mask without pending action")
        if active_mask != held_mask:
            raise ValueError(
                "direct no-pending root has different active/held masks"
            )
    else:
        if (
            type(pending_mask) is not int
            or pending_mask != pending_mask & SUPPORTED_INPUT_MASK
            or pending_mask != held_mask
            or _local_pipeline_action_from_mask(pending_mask)
            != pending_action
        ):
            raise ValueError("direct pending mask/action disagree")

    root = LocalPipelineRoot(
        active_action=active_action,
        held_desired_action=held_action,
        pending_action=pending_action,
        remaining_delay_support=remaining,
    )
    issue_age_raw = record.get("issue_age")
    if issue_age_raw is None:
        issue_age = 0
    elif type(issue_age_raw) is int and issue_age_raw >= 0:
        issue_age = int(issue_age_raw)
    else:
        raise ValueError("direct issue age is invalid")
    overdue = record.get("overdue", False)
    if not isinstance(overdue, bool):
        raise ValueError("direct overdue flag is invalid")
    return root, held_mask, issue_age, overdue


def _reconstruct_roots(
    rows: list[dict[str, object]],
) -> tuple[list[ReconstructedRoot], dict[str, int]]:
    hit_frames_by_epoch: dict[int, list[int]] = {}
    for row in rows:
        if row.get("hit_started"):
            hit_frames_by_epoch.setdefault(
                int(row.get("gameplay_epoch", 0)),
                [],
            ).append(int(row["frame"]))

    reconstructed = []
    held_mask: int | None = None
    last_write_source: int | None = None
    last_write_issue: int | None = None
    last_write_support: tuple[int, ...] = ()
    prior_epoch: int | None = None
    prior_frame: int | None = None
    counters = {
        "decision_count": len(rows),
        "action_eligible_count": 0,
        "reconstructed_count": 0,
        "active_held_mismatch_count": 0,
        "overdue_count": 0,
        "inconsistent_or_uninitialized_count": 0,
        "direct_root_count": 0,
        "inferred_root_count": 0,
        "invalid_direct_root_count": 0,
    }
    for row in rows:
        frame = int(row["frame"])
        epoch = int(row.get("gameplay_epoch", 0))
        action_lag = int(row.get("action_lag", 0))
        source_frame = frame - action_lag
        if (
            prior_epoch is not None
            and (epoch != prior_epoch or (prior_frame is not None and frame <= prior_frame))
        ):
            held_mask = None
            last_write_source = None
            last_write_issue = None
            last_write_support = ()
        prior_epoch = epoch
        prior_frame = frame

        phase = int(row.get("player", {}).get("phase_at_action", 0))
        deadline = row.get("deadline_guard", {})
        action_eligible = (
            phase != 2
            and not bool(row.get("bomb"))
            and not bool(deadline.get("input_suppressed"))
        )
        if action_eligible:
            counters["action_eligible_count"] += 1

        current_mask = int(row["input_snapshot"]["current"])
        if action_eligible:
            root = None
            root_held_mask = held_mask
            root_source = "inferred_previous_write"
            overdue = False
            issue_age = 0
            if "local_pipeline_root" in row:
                try:
                    (
                        root,
                        root_held_mask,
                        issue_age,
                        overdue,
                    ) = _direct_root_from_trace(row)
                    if (
                        held_mask is not None
                        and root_held_mask
                        != held_mask & SUPPORTED_INPUT_MASK
                    ):
                        raise ValueError(
                            "direct held mask disagrees with prior trace write"
                        )
                    root_source = "direct_trace"
                    counters["direct_root_count"] += 1
                except ValueError:
                    root = None
                    counters["invalid_direct_root_count"] += 1
                    counters[
                        "inconsistent_or_uninitialized_count"
                    ] += 1
            elif held_mask is not None:
                active_action = _local_pipeline_action_from_mask(
                    current_mask
                )
                held_action = _local_pipeline_action_from_mask(held_mask)
                issue_age = (
                    0
                    if last_write_issue is None
                    else max(0, source_frame - last_write_issue)
                )
                if active_action == held_action:
                    root = LocalPipelineRoot(
                        active_action=active_action,
                        held_desired_action=active_action,
                    )
                elif last_write_source is not None and last_write_support:
                    snapshot_age = max(
                        0,
                        source_frame - last_write_source,
                    )
                    remaining = tuple(
                        delay - snapshot_age
                        for delay in last_write_support
                        if delay > snapshot_age
                    )
                    if not remaining:
                        remaining = (1,)
                        overdue = True
                    root = LocalPipelineRoot(
                        active_action=active_action,
                        held_desired_action=held_action,
                        pending_action=held_action,
                        remaining_delay_support=remaining,
                    )
                else:
                    counters[
                        "inconsistent_or_uninitialized_count"
                    ] += 1
                if root is not None:
                    counters["inferred_root_count"] += 1
            else:
                counters["inconsistent_or_uninitialized_count"] += 1
            if root is not None:
                if root.active_action != root.held_desired_action:
                    counters["active_held_mismatch_count"] += 1
                counters["overdue_count"] += int(overdue)
                next_hits = [
                    hit_frame
                    for hit_frame in hit_frames_by_epoch.get(epoch, ())
                    if frame <= hit_frame <= frame + PREHIT_WINDOW_FRAMES
                ]
                reconstructed.append(
                    ReconstructedRoot(
                        row=row,
                        root=root,
                        held_mask=int(root_held_mask),
                        source_frame=source_frame,
                        issue_age=issue_age,
                        overdue=overdue,
                        prehit=bool(next_hits),
                        root_source=root_source,
                    )
                )
                counters["reconstructed_count"] += 1

        issued_mask = int(row["mask"]) & SUPPORTED_INPUT_MASK
        if held_mask is None or issued_mask != held_mask & SUPPORTED_INPUT_MASK:
            held_mask = issued_mask
            last_write_source = source_frame
            last_write_issue = frame
            last_write_support = tuple(
                int(value)
                for value in row["control_delay_candidates"]
            )
    return reconstructed, counters


def _sample_roots(
    roots: list[ReconstructedRoot],
    sample_count: int,
) -> list[ReconstructedRoot]:
    pending = [
        root for root in roots if root.root.pending_action is not None
    ]
    if len(pending) <= sample_count:
        return pending
    selected_indices = {
        round(index * (len(pending) - 1) / (sample_count - 1))
        for index in range(sample_count)
    }
    selected = [pending[index] for index in sorted(selected_indices)]
    forced = [
        root
        for root in pending
        if root.prehit
    ]
    if forced:
        stride = max(1, len(forced) // max(1, sample_count // 4))
        selected.extend(forced[::stride][: max(1, sample_count // 4)])
    unique = {
        (
            int(root.row["gameplay_epoch"]),
            int(root.row["frame"]),
        ): root
        for root in selected
    }
    return [
        unique[key]
        for key in sorted(unique)
    ]


def _audit_trace(
    trace: Path,
    *,
    sample_count: int,
) -> dict[str, object]:
    rows, digest = _read_decisions(trace)
    roots, population = _reconstruct_roots(rows)
    sampled = _sample_roots(roots, sample_count)
    legacy_ms: list[float] = []
    packed_equivalent_ms: list[float] = []
    pipeline_ms: list[float] = []
    timing_by_density = {
        density: {
            "legacy": [],
            "packed": [],
            "pipeline": [],
        }
        for density in ("lt_200", "200_599", "600_999", "ge_1000")
    }
    safe_set_changes = 0
    ranked_action_changes = 0
    recorded_optimistic = 0
    recorded_conservative = 0
    recorded_label_changes = 0
    no_write_label_changes = 0
    packed_hard_parity_failures = 0
    examples = []
    subgroup_metrics = {
        name: {
            "count": 0,
            "safe_action_set_changes": 0,
            "ranked_action_changes": 0,
            "recorded_action_label_changes": 0,
            "recorded_legacy_safe_pipeline_unsafe": 0,
            "recorded_legacy_unsafe_pipeline_safe": 0,
            "held_no_write_label_changes": 0,
        }
        for name in ("prehit_240f", "outside_prehit_240f", "non_overdue")
    }

    for index, reconstructed in enumerate(sampled):
        row = reconstructed.row
        bullets, lasers, enemy_bodies = hazards_from_trace(row)
        common = {
            "player_x": float(row["player"]["x"]),
            "player_y": float(row["player"]["y"]),
            "previous_mask": reconstructed.held_mask,
            "actions": _PLANNER_ACTIONS,
            "delay_frames": tuple(
                int(value) for value in row["control_delay_candidates"]
            ),
            "action_hold_frames": int(row["action_hold_frames"]),
            "bullets": bullets,
            "lasers": lasers,
            "enemy_bodies": enemy_bodies,
            "snapshot_lag": int(row["snapshot_lag"]),
        }
        order = (
            ("legacy", "packed", "pipeline")
            if index % 2 == 0
            else ("pipeline", "packed", "legacy")
        )
        outputs = {}
        density = _density_bin(int(row.get("active_bullets", 0)))
        for variant in order:
            started = time.perf_counter()
            if variant == "legacy":
                outputs[variant] = _legacy_robust_action_certificates(
                    **common
                )
                timings = legacy_ms
            elif variant == "packed":
                outputs[variant] = _robust_action_certificates(**common)
                timings = packed_equivalent_ms
            else:
                outputs[variant] = _robust_action_certificates(
                    **common,
                    pipeline_root=reconstructed.root,
                )
                timings = pipeline_ms
            duration_ms = (time.perf_counter() - started) * 1000.0
            timings.append(duration_ms)
            timing_by_density[density][variant].append(duration_ms)
        legacy = outputs["legacy"]
        packed = outputs["packed"]
        pipeline = outputs["pipeline"]

        packed_hard_parity_failures += any(
            (
                legacy[action.name].worst_collisions
                != packed[action.name].worst_collisions
                or abs(
                    legacy[action.name].min_clearance
                    - packed[action.name].min_clearance
                )
                > 1e-3
            )
            for action in _PLANNER_ACTIONS
        )
        legacy_safe = _safe_actions(legacy)
        pipeline_safe = _safe_actions(pipeline)
        safe_changed = legacy_safe != pipeline_safe
        safe_set_changes += int(safe_changed)
        legacy_ranked = _ranked_action(legacy)
        pipeline_ranked = _ranked_action(pipeline)
        ranked_changed = legacy_ranked != pipeline_ranked
        ranked_action_changes += int(ranked_changed)

        recorded_action = _action_name_from_mask(int(row["mask"]))
        old = legacy[recorded_action]
        new = pipeline[recorded_action]
        old_safe = (
            old.worst_collisions == 0 and old.min_clearance >= 0.0
        )
        new_safe = (
            new.worst_collisions == 0 and new.min_clearance >= 0.0
        )
        recorded_optimistic += int(old_safe and not new_safe)
        recorded_conservative += int(not old_safe and new_safe)
        label_changed = (
            old.worst_collisions != new.worst_collisions
            or abs(old.min_clearance - new.min_clearance) > 1e-3
            or abs(old.cvar_risk - new.cvar_risk) > 1e-3
        )
        recorded_label_changes += int(label_changed)

        held_action = reconstructed.root.held_desired_action
        held_old = legacy[held_action]
        held_new = pipeline[held_action]
        no_write_changed = (
            held_old.worst_collisions != held_new.worst_collisions
            or abs(held_old.min_clearance - held_new.min_clearance) > 1e-3
            or abs(held_old.cvar_risk - held_new.cvar_risk) > 1e-3
        )
        no_write_label_changes += int(no_write_changed)
        subgroup_names = [
            (
                "prehit_240f"
                if reconstructed.prehit
                else "outside_prehit_240f"
            )
        ]
        if not reconstructed.overdue:
            subgroup_names.append("non_overdue")
        for subgroup_name in subgroup_names:
            subgroup = subgroup_metrics[subgroup_name]
            subgroup["count"] += 1
            subgroup["safe_action_set_changes"] += int(safe_changed)
            subgroup["ranked_action_changes"] += int(ranked_changed)
            subgroup["recorded_action_label_changes"] += int(
                label_changed
            )
            subgroup[
                "recorded_legacy_safe_pipeline_unsafe"
            ] += int(old_safe and not new_safe)
            subgroup[
                "recorded_legacy_unsafe_pipeline_safe"
            ] += int(not old_safe and new_safe)
            subgroup["held_no_write_label_changes"] += int(
                no_write_changed
            )

        if (
            old_safe != new_safe
            or ranked_changed
            or (reconstructed.prehit and label_changed)
        ) and len(examples) < 16:
            examples.append(
                {
                    "frame": int(row["frame"]),
                    "gameplay_epoch": int(row.get("gameplay_epoch", 0)),
                    "spell": row.get("spell"),
                    "active_bullets": int(row.get("active_bullets", 0)),
                    "prehit_240f": reconstructed.prehit,
                    "overdue": reconstructed.overdue,
                    "issue_age": reconstructed.issue_age,
                    "root_source": reconstructed.root_source,
                    "root": {
                        "active_action": reconstructed.root.active_action,
                        "held_desired_action": (
                            reconstructed.root.held_desired_action
                        ),
                        "pending_action": reconstructed.root.pending_action,
                        "remaining_delay_support": (
                            reconstructed.root.remaining_delay_support
                        ),
                    },
                    "recorded_action": recorded_action,
                    "legacy_recorded": _certificate_record(old),
                    "pipeline_recorded": _certificate_record(new),
                    "legacy_ranked_action": legacy_ranked,
                    "pipeline_ranked_action": pipeline_ranked,
                    "legacy_safe_actions": legacy_safe,
                    "pipeline_safe_actions": pipeline_safe,
                }
            )

    count = len(sampled)
    return {
        "trace": str(trace),
        "trace_sha256": digest,
        "population": population,
        "sample": {
            "method": (
                "evenly spaced active/held mismatch roots plus a bounded "
                "240-frame pre-hit supplement"
            ),
            "count": count,
            "prehit_240f_count": sum(root.prehit for root in sampled),
            "overdue_count": sum(root.overdue for root in sampled),
        },
        "differential": {
            "safe_action_set_changes": safe_set_changes,
            "ranked_action_changes": ranked_action_changes,
            "recorded_action_label_changes": recorded_label_changes,
            "recorded_legacy_safe_pipeline_unsafe": recorded_optimistic,
            "recorded_legacy_unsafe_pipeline_safe": recorded_conservative,
            "held_no_write_label_changes": no_write_label_changes,
            "legacy_vs_packed_hard_parity_failures": (
                packed_hard_parity_failures
            ),
            "by_context": subgroup_metrics,
        },
        "timing": {
            "legacy_semantics_fixed_batch": _timing_summary(legacy_ms),
            "packed_equivalent_root": _timing_summary(
                packed_equivalent_ms
            ),
            "packed_pipeline_root": _timing_summary(pipeline_ms),
            "by_active_bullets": {
                density: {
                    "count": len(values["pipeline"]),
                    "legacy_semantics_fixed_batch": (
                        _timing_summary(values["legacy"])
                        if values["legacy"]
                        else None
                    ),
                    "packed_equivalent_root": (
                        _timing_summary(values["packed"])
                        if values["packed"]
                        else None
                    ),
                    "packed_pipeline_root": (
                        _timing_summary(values["pipeline"])
                        if values["pipeline"]
                        else None
                    ),
                }
                for density, values in timing_by_density.items()
            },
        },
        "examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples-per-trace", type=int, default=128)
    args = parser.parse_args()
    if args.samples_per_trace < 2:
        raise SystemExit("--samples-per-trace must be at least two")

    results = [
        _audit_trace(
            trace,
            sample_count=args.samples_per_trace,
        )
        for trace in args.traces
    ]
    artifact = {
        "schema": "th08-local-pipeline-certificate-audit-v1",
        "generated_at": "2026-07-26",
        "evidence_labels": {
            "observed": (
                "trace fields, replayed geometry, scalar/native-independent "
                "unit differentials, and measured replay timing"
            ),
            "inferred": (
                "remaining pending support is reconstructed from the last "
                "trace write only when direct local-pipeline-root telemetry "
                "is absent"
            ),
            "hypothesized": (
                "physical survival or live-authority benefit; neither is "
                "claimed by this offline artifact"
            ),
        },
        "contract": {
            "horizon": "action_hold_frames + max(new_delay_support)",
            "root": (
                "native active action, controller-held desired action, and "
                "one pending command with conditioned remaining support; "
                "direct trace roots are preferred and cross-checked"
            ),
            "write": (
                "selected != held samples new delay; selected == held is "
                "no-write and preserves the older pending command"
            ),
            "scope": (
                "finite local lease only; no recursive cadence, future "
                "observation maximization, frozen-manager authority, or "
                "physical survival claim"
            ),
        },
        "traces": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(artifact, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
