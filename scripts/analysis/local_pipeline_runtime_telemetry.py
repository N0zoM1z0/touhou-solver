#!/usr/bin/env python3
"""Summarize live TH08 observe/decode/certify/issue root telemetry."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Iterable


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _p99(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.99 * len(ordered)) - 1)]


def numeric_summary(
    values: Iterable[float],
    *,
    unit: str,
) -> dict[str, float | int] | None:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return None
    return {
        "count": len(finite),
        f"median_{unit}": statistics.median(finite),
        f"p95_{unit}": _p95(finite),
        f"p99_{unit}": _p99(finite),
        f"max_{unit}": max(finite),
        f"mean_{unit}": statistics.fmean(finite),
    }


def timing_summary(values: Iterable[float]) -> dict[str, float | int] | None:
    return numeric_summary(values, unit="ms")


def _nested_float(
    row: dict[str, object],
    *path: str,
) -> float | None:
    value: object = row
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    return converted if math.isfinite(converted) else None


def _timing_field(
    rows: Iterable[dict[str, object]],
    *path: str,
) -> dict[str, float | int] | None:
    return timing_summary(
        value
        for row in rows
        if (value := _nested_float(row, *path)) is not None
    )


def _density(active_bullets: int) -> str:
    if active_bullets < 200:
        return "lt_200"
    if active_bullets < 600:
        return "200_599"
    if active_bullets < 1000:
        return "600_999"
    return "ge_1000"


def _chain_timing(rows: list[dict[str, object]]) -> dict[str, object]:
    fields = {
        "observe": ("timing_ms", "observe"),
        "read_pools": ("timing_ms", "read_pools"),
        "read_enemy_background": (
            "timing_ms",
            "read_enemy_background",
        ),
        "read_enemy_prefix_capture": (
            "timing_ms",
            "read_enemy_prefix_capture",
        ),
        "read_enemy_prefix_merge": (
            "timing_ms",
            "read_enemy_prefix_merge",
        ),
        "read_bullet_pool": ("timing_ms", "read_bullet_pool"),
        "read_laser_pool": ("timing_ms", "read_laser_pool"),
        "read_item_pool": ("timing_ms", "read_item_pool"),
        "read_boss_phase": ("timing_ms", "read_boss_phase"),
        "read_spell_enemy_guard": (
            "timing_ms",
            "read_spell_enemy_guard",
        ),
        "read_ecl_lookahead": (
            "timing_ms",
            "read_ecl_lookahead",
        ),
        "read_hazard_bookkeeping": (
            "timing_ms",
            "read_hazard_bookkeeping",
        ),
        "read_enemy_issue_prefix": (
            "timing_ms",
            "read_enemy_issue_prefix",
        ),
        "decode_pools": ("timing_ms", "decode_pools"),
        "decode_bullets": ("timing_ms", "decode_bullets"),
        "attach_bullet_events": (
            "timing_ms",
            "attach_bullet_events",
        ),
        "decode_lasers": ("timing_ms", "decode_lasers"),
        "decode_items": ("timing_ms", "decode_items"),
        "corridor_bookkeeping": (
            "timing_ms",
            "corridor_bookkeeping",
        ),
        "local_plan_initial": ("timing_ms", "local_plan_initial"),
        "local_shared_laser_projection": (
            "timing_ms",
            "local_shared_laser_projection",
        ),
        "local_certificate_total": (
            "timing_ms",
            "local_certificate_total",
        ),
        "local_certificate_geometry": (
            "timing_ms",
            "local_certificate_geometry",
        ),
        "local_control_prefix": (
            "local_pipeline_timing",
            "planning",
            "control_prefix_ms",
        ),
        "local_planning_bullet_projection": (
            "local_pipeline_timing",
            "planning",
            "planning_bullet_projection_ms",
        ),
        "local_beam_search": (
            "local_pipeline_timing",
            "planning",
            "beam_search_ms",
        ),
        "local_terminal_threat": (
            "local_pipeline_timing",
            "planning",
            "terminal_threat_ms",
        ),
        "local_selection_finalize": (
            "local_pipeline_timing",
            "planning",
            "selection_finalize_ms",
        ),
        "local_certificate_validation": (
            "local_pipeline_timing",
            "planning",
            "validation_ms",
        ),
        "local_certificate_hazard_projection": (
            "local_pipeline_timing",
            "planning",
            "hazard_projection_ms",
        ),
        "local_certificate_branch_setup": (
            "local_pipeline_timing",
            "planning",
            "branch_setup_ms",
        ),
        "local_certificate_reduction": (
            "local_pipeline_timing",
            "planning",
            "reduction_ms",
        ),
        "issue_enemy_recertificate": (
            "timing_ms",
            "issue_enemy_recertificate",
        ),
        "issue_certificate_total": (
            "timing_ms",
            "issue_certificate_total",
        ),
        "issue_path_to_input": (
            "timing_ms",
            "issue_path_to_input",
        ),
        "observe_to_input": ("timing_ms", "observe_to_input"),
        "input": ("timing_ms", "input"),
        "post_issue_root_shadow": (
            "timing_ms",
            "post_issue_root_shadow",
        ),
        "before_trace": ("timing_ms", "before_trace"),
        "previous_iteration": ("timing_ms", "previous_iteration"),
    }
    summaries: dict[str, object] = {
        name: _timing_field(rows, *path)
        for name, path in fields.items()
    }
    local_other = []
    for row in rows:
        local_plan = _nested_float(
            row,
            "timing_ms",
            "local_plan_initial",
        )
        shared = _nested_float(
            row,
            "timing_ms",
            "local_shared_laser_projection",
        )
        certificate = _nested_float(
            row,
            "timing_ms",
            "local_certificate_total",
        )
        if local_plan is None or shared is None or certificate is None:
            continue
        local_other.append(max(0.0, local_plan - shared - certificate))
    summaries["local_search_and_other"] = timing_summary(local_other)
    return summaries


def _root_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    root_rows = [
        row for row in rows
        if isinstance(row.get("local_pipeline_root"), dict)
    ]
    return {
        "rows": len(root_rows),
        "estimator_consistent": sum(
            bool(row["local_pipeline_root"].get("estimator_consistent"))
            for row in root_rows
        ),
        "estimator_inconsistent": sum(
            not bool(row["local_pipeline_root"].get("estimator_consistent"))
            for row in root_rows
        ),
        "active_held_mismatch": sum(
            row["local_pipeline_root"].get("active_action")
            != row["local_pipeline_root"].get("held_desired_action")
            for row in root_rows
        ),
        "pending": sum(
            row["local_pipeline_root"].get("pending_action") is not None
            for row in root_rows
        ),
        "overdue": sum(
            bool(row["local_pipeline_root"].get("overdue"))
            for row in root_rows
        ),
    }


def _shadow_summary(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    shadow_rows = [
        row
        for row in rows
        if isinstance(
            row.get("local_pipeline_certificate_shadow"),
            dict,
        )
    ]
    complete = [
        row
        for row in shadow_rows
        if row["local_pipeline_certificate_shadow"].get("status")
        == "complete"
    ]
    by_density: dict[str, list[dict[str, object]]] = {
        name: [] for name in ("lt_200", "200_599", "600_999", "ge_1000")
    }
    for row in complete:
        by_density[_density(int(row.get("active_bullets", 0)))].append(row)
    segment_names = (
        "validation_ms",
        "hazard_projection_ms",
        "branch_setup_ms",
        "geometry_kernel_ms",
        "reduction_ms",
        "certificate_total_ms",
    )

    def shadow_timing(
        selected: list[dict[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "wall": _timing_field(
                selected,
                "local_pipeline_certificate_shadow",
                "wall_ms",
            )
        }
        for name in segment_names:
            result[name.removesuffix("_ms")] = _timing_field(
                selected,
                "local_pipeline_certificate_shadow",
                "timing",
                name,
            )
        return result

    return {
        "sampled_rows": len(shadow_rows),
        "complete": len(complete),
        "estimator_inconsistent": len(shadow_rows) - len(complete),
        "safe_action_set_changes": sum(
            bool(
                row["local_pipeline_certificate_shadow"].get(
                    "safe_action_set_changed"
                )
            )
            for row in complete
        ),
        "timing": shadow_timing(complete),
        "by_active_bullets": {
            density: {
                "count": len(selected),
                "timing": shadow_timing(selected),
            }
            for density, selected in by_density.items()
        },
    }


def _paired_shadow_contention(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    next_iteration_after_shadow = []
    next_iteration_after_plain = []
    next_frame_delta_after_shadow = []
    next_frame_delta_after_plain = []
    deadline_miss_after_shadow = 0
    deadline_miss_after_plain = 0
    for previous, current in zip(rows, rows[1:]):
        if int(previous.get("gameplay_epoch", 0)) != int(
            current.get("gameplay_epoch", 0)
        ):
            continue
        prior_shadow = isinstance(
            previous.get("local_pipeline_certificate_shadow"),
            dict,
        )
        iteration = _nested_float(
            current,
            "timing_ms",
            "previous_iteration",
        )
        frame_delta = int(current["frame"]) - int(previous["frame"])
        if prior_shadow:
            if iteration is not None:
                next_iteration_after_shadow.append(iteration)
            next_frame_delta_after_shadow.append(float(frame_delta))
            deadline_miss_after_shadow += int(
                bool(
                    (
                        current.get("deadline_guard")
                        if isinstance(
                            current.get("deadline_guard"),
                            dict,
                        )
                        else {}
                    ).get("missed")
                )
            )
        else:
            if iteration is not None:
                next_iteration_after_plain.append(iteration)
            next_frame_delta_after_plain.append(float(frame_delta))
            deadline_miss_after_plain += int(
                bool(
                    (
                        current.get("deadline_guard")
                        if isinstance(
                            current.get("deadline_guard"),
                            dict,
                        )
                        else {}
                    ).get("missed")
                )
            )
    return {
        "warning": (
            "observational comparison only; sampled rows are periodic, not "
            "randomized, and hazard/cadence mix may differ"
        ),
        "next_iteration_ms_after_shadow": timing_summary(
            next_iteration_after_shadow
        ),
        "next_iteration_ms_after_plain": timing_summary(
            next_iteration_after_plain
        ),
        "next_decision_frame_delta_after_shadow": numeric_summary(
            next_frame_delta_after_shadow,
            unit="frames",
        ),
        "next_decision_frame_delta_after_plain": numeric_summary(
            next_frame_delta_after_plain,
            unit="frames",
        ),
        "deadline_miss_after_shadow": deadline_miss_after_shadow,
        "deadline_miss_after_plain": deadline_miss_after_plain,
    }


def summarize_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    decisions = [row for row in rows if row.get("kind") == "decision"]
    prehit = [
        row for row in decisions if int(row.get("hit_count", 0)) == 0
    ]
    deadline_misses = [
        row
        for row in decisions
        if bool(
            (
                row.get("deadline_guard")
                if isinstance(row.get("deadline_guard"), dict)
                else {}
            ).get("missed")
        )
    ]
    return {
        "decision_rows": len(decisions),
        "prehit_decision_rows": len(prehit),
        "first_hit_frame": (
            min(
                int(row["frame"])
                for row in decisions
                if int(row.get("hit_count", 0)) > 0
            )
            if any(int(row.get("hit_count", 0)) > 0 for row in decisions)
            else None
        ),
        "bomb_rows": sum(bool(row.get("bomb")) for row in decisions),
        "deadline_misses": {
            "count": len(deadline_misses),
            "frames": tuple(
                int(row["frame"]) for row in deadline_misses[:32]
            ),
        },
        "issue_recertification_rows": sum(
            (
                _nested_float(
                    row,
                    "timing_ms",
                    "issue_enemy_recertificate",
                )
                or 0.0
            )
            > 0.0
            for row in decisions
        ),
        "root": _root_counts(decisions),
        "full_chain_timing": _chain_timing(decisions),
        "prehit_full_chain_timing": _chain_timing(prehit),
        "explicit_root_shadow": _shadow_summary(decisions),
        "shadow_contention": _paired_shadow_contention(decisions),
    }


def audit_trace(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    rows = [
        json.loads(line)
        for line in payload.decode("utf-8").splitlines()
        if line.strip()
    ]
    return {
        "trace": str(path),
        "trace_sha256": hashlib.sha256(payload).hexdigest(),
        **summarize_rows(rows),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = {
        "schema": "th08-local-pipeline-runtime-telemetry-v1",
        "claim_boundary": {
            "full_chain": (
                "observe_to_input ends immediately after SendInput and excludes "
                "the post-issue explicit-root shadow"
            ),
            "explicit_root_shadow": (
                "computed after SendInput, has no current-action authority, "
                "and can perturb the next cadence"
            ),
            "native_active": (
                "local_pipeline_root.active_action comes from input_current"
            ),
        },
        "traces": [audit_trace(path) for path in args.traces],
    }
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
