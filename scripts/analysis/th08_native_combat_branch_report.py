#!/usr/bin/env python3
"""Lower native snapshot branches into survival-filtered combat comparisons."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "th08-native-combat-branch-comparison-v1"
ROLLING_SCHEMA = "th08-native-snapshot-rolling-trial-v5"
CAUSAL_SEARCH_SCHEMA = "th08-native-snapshot-causal-secondary-search-v3"
ROLLING_ACCEPTED_STATUS = "rolling_native_projection_snapshot_passed"
CAUSAL_ACCEPTED_STATUS = "causal_secondary_search_passed"


class NativeCombatBranchReportError(ValueError):
    """Raised when branch combat evidence cannot be compared exactly."""


def _object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise NativeCombatBranchReportError(f"{field} must be an object")
    return value


def _array(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise NativeCombatBranchReportError(f"{field} must be an array")
    return value


def _combat_summary(value: object, *, field: str) -> dict[str, Any]:
    projection = _object(value, field=field)
    summary = projection.get("summary")
    if not isinstance(summary, dict):
        raise NativeCombatBranchReportError(
            f"{field} omits the native combat summary"
        )
    return summary


def _tick_combat_summary(tick: dict[str, Any], *, field: str) -> dict[str, Any]:
    compact = tick.get("native_combat_summary")
    if isinstance(compact, dict):
        return compact
    return _combat_summary(
        tick.get("native_combat_projection"),
        field=f"{field}.native_combat_projection",
    )


def _integer(summary: dict[str, Any], field: str) -> int:
    value = summary.get(field)
    if type(value) is not int or value < 0:
        raise NativeCombatBranchReportError(
            f"native combat summary {field!r} must be a nonnegative integer"
        )
    return value


def _player_phase(value: object, *, field: str) -> int:
    state = _object(value, field=field)
    phase = state.get("player_phase")
    if type(phase) is not int or phase < 0:
        raise NativeCombatBranchReportError(
            f"{field}.player_phase must be a nonnegative integer"
        )
    return phase


def _summarize_branch(
    *,
    branch_id: str,
    root_summary: dict[str, Any],
    root_player_phase: int,
    branch: dict[str, Any],
    prefix_mask: int | None = None,
    prefix_schedule: list[object] | None = None,
    continuation_mask: int | None = None,
) -> dict[str, object]:
    ticks = _array(branch.get("ticks"), field=f"{branch_id}.ticks")
    if not ticks:
        raise NativeCombatBranchReportError(
            f"{branch_id} has no combat tick history"
        )
    tick_objects = [
        _object(tick, field=f"{branch_id}.ticks[{index}]")
        for index, tick in enumerate(ticks)
    ]
    summaries = [
        _tick_combat_summary(
            tick,
            field=f"{branch_id}.ticks[{index}]",
        )
        for index, tick in enumerate(tick_objects)
    ]
    root_frame = _integer(root_summary, "manager_frame")
    manager_frames = [
        _integer(summary, "manager_frame") for summary in summaries
    ]
    if (
        manager_frames != sorted(manager_frames)
        or len(manager_frames) != len(set(manager_frames))
        or manager_frames[0] <= root_frame
    ):
        raise NativeCombatBranchReportError(
            f"{branch_id} combat frames do not form an ordered future"
        )
    compact_states = [
        _object(tick.get("compact_state"), field=f"{branch_id}.compact_state")
        for tick in tick_objects
    ]
    survived = root_player_phase != 2 and not any(
        _player_phase(state, field=f"{branch_id}.compact_state") == 2
        for state in compact_states
    )
    endpoint = summaries[-1]
    unresolved_target_ticks = sum(
        _integer(summary, "unresolved_overlap_target_count")
        for summary in summaries
    )
    candidate_status = (
        "rejected_hard_survival"
        if not survived
        else (
            "survival_filtered_proxy_only_with_unresolved_overlap"
            if unresolved_target_ticks
            else "survival_filtered_proxy_only"
        )
    )
    return {
        "branch_id": branch_id,
        "prefix_mask": prefix_mask,
        "prefix_action_schedule": prefix_schedule,
        "continuation_mask": continuation_mask,
        "selected_actions": [
            int(tick["selected_action"]) for tick in tick_objects
        ],
        "root_manager_frame": root_frame,
        "root_player_phase": root_player_phase,
        "manager_frames": manager_frames,
        "survived_to_endpoint": survived,
        "candidate_status": candidate_status,
        "metrics": {
            "root_positive_hp_sum": _integer(root_summary, "positive_hp_sum"),
            "endpoint_positive_hp_sum": _integer(endpoint, "positive_hp_sum"),
            "observed_positive_hp_sum_change": (
                _integer(endpoint, "positive_hp_sum")
                - _integer(root_summary, "positive_hp_sum")
            ),
            "published_frame_damage_tick_sum": sum(
                _integer(summary, "published_frame_damage_sum")
                for summary in summaries
            ),
            "supported_primary_contribution_tick_sum": sum(
                _integer(summary, "supported_primary_contribution_sum")
                for summary in summaries
            ),
            "open_gate_supported_primary_contribution_tick_sum": sum(
                _integer(
                    summary,
                    "open_gate_supported_primary_contribution_sum",
                )
                for summary in summaries
            ),
            "supported_alternate_contribution_tick_sum": sum(
                _integer(summary, "supported_alternate_contribution_sum")
                for summary in summaries
            ),
            "open_hp_gate_target_ticks": sum(
                _integer(summary, "open_hp_gate_target_count")
                for summary in summaries
            ),
            "supported_primary_overlap_target_ticks": sum(
                _integer(
                    summary,
                    "supported_primary_overlap_target_count",
                )
                for summary in summaries
            ),
            "unresolved_overlap_target_ticks": unresolved_target_ticks,
            "endpoint_active_shot_count": _integer(
                endpoint,
                "active_shot_count",
            ),
            "endpoint_damage_eligible_shot_count": _integer(
                endpoint,
                "damage_eligible_shot_count",
            ),
            "maximum_hit_state_shot_count": max(
                _integer(summary, "hit_state_shot_count")
                for summary in summaries
            ),
        },
        "authority": {
            "hard_survival_filter": "observed_native_player_phase_over_branch",
            "published_frame_damage": (
                "observed_native_enemy_frame_damage_field_at_endpoint_seams"
            ),
            "supported_contribution": (
                "instantaneous_supported_ordinary_shot_subtotal_proxy"
            ),
            "positive_hp_sum": (
                "cross_slot_aggregate_not_generation_safe_or_birth_normalized"
            ),
            "combat_benefit_authority": False,
            "live_ranking_authority": False,
        },
    }


def _rolling_rows(result: dict[str, Any]) -> list[dict[str, object]]:
    if result.get("status") != ROLLING_ACCEPTED_STATUS:
        raise NativeCombatBranchReportError(
            "rolling source did not pass its deterministic transaction"
        )
    root_summary = _combat_summary(
        result.get("root_native_combat_projection"),
        field="result.root_native_combat_projection",
    )
    root_player_phase = _player_phase(
        result.get("root_compact_state"),
        field="result.root_compact_state",
    )
    branches = _object(result.get("branches"), field="result.branches")
    rows = []
    for branch_id in ("a1", "a2", "b"):
        rows.append(
            _summarize_branch(
                branch_id=branch_id,
                root_summary=root_summary,
                root_player_phase=root_player_phase,
                branch=_object(
                    branches.get(branch_id),
                    field=f"result.branches.{branch_id}",
                ),
            )
        )
    return rows


def _causal_rows(result: dict[str, Any]) -> list[dict[str, object]]:
    if result.get("status") != CAUSAL_ACCEPTED_STATUS:
        raise NativeCombatBranchReportError(
            "causal-search source did not pass its deterministic transaction"
        )
    origin = _object(result.get("origin"), field="result.origin")
    origin_summary = _combat_summary(
        origin.get("native_combat_projection"),
        field="result.origin.native_combat_projection",
    )
    origin_player_phase = _player_phase(
        origin.get("compact_state"),
        field="result.origin.compact_state",
    )
    rows: list[dict[str, object]] = []
    for prefix_index, prefix_value in enumerate(
        _array(result.get("prefixes"), field="result.prefixes")
    ):
        prefix = _object(prefix_value, field=f"result.prefixes[{prefix_index}]")
        prefix_mask_value = prefix.get("prefix_mask")
        prefix_mask = (
            None if prefix_mask_value is None else int(prefix_mask_value)
        )
        prefix_schedule_value = prefix.get("prefix_action_schedule")
        prefix_schedule = (
            None
            if prefix_schedule_value is None
            else _array(
                prefix_schedule_value,
                field=f"result.prefixes[{prefix_index}].prefix_action_schedule",
            )
        )
        rows.append(
            _summarize_branch(
                branch_id=f"prefix-{prefix_index}",
                root_summary=origin_summary,
                root_player_phase=origin_player_phase,
                branch=_object(
                    prefix.get("prefix"),
                    field=f"result.prefixes[{prefix_index}].prefix",
                ),
                prefix_mask=prefix_mask,
                prefix_schedule=prefix_schedule,
            )
        )
        subroot = _object(
            prefix.get("subroot"),
            field=f"result.prefixes[{prefix_index}].subroot",
        )
        subroot_summary = _combat_summary(
            subroot.get("native_combat_projection"),
            field=(
                f"result.prefixes[{prefix_index}].subroot."
                "native_combat_projection"
            ),
        )
        subroot_player_phase = _player_phase(
            subroot.get("compact_state"),
            field=f"result.prefixes[{prefix_index}].subroot.compact_state",
        )
        for continuation_value in _array(
            prefix.get("continuations"),
            field=f"result.prefixes[{prefix_index}].continuations",
        ):
            continuation = _object(
                continuation_value,
                field=f"result.prefixes[{prefix_index}].continuation",
            )
            continuation_mask = int(continuation["complete_mask"])
            rows.append(
                _summarize_branch(
                    branch_id=(
                        f"prefix-{prefix_index}/"
                        f"continuation-{continuation_mask:#04x}"
                    ),
                    root_summary=subroot_summary,
                    root_player_phase=subroot_player_phase,
                    branch=continuation,
                    prefix_mask=prefix_mask,
                    prefix_schedule=prefix_schedule,
                    continuation_mask=continuation_mask,
                )
            )
    return rows


def build_report(
    source: dict[str, Any],
    *,
    source_path: str,
    source_sha256: str,
) -> dict[str, object]:
    source_schema = source.get("schema")
    result = _object(source.get("result"), field="source.result")
    if source_schema == ROLLING_SCHEMA:
        rows = _rolling_rows(result)
    elif source_schema == CAUSAL_SEARCH_SCHEMA:
        rows = _causal_rows(result)
    else:
        raise NativeCombatBranchReportError(
            f"unsupported native combat source schema {source_schema!r}"
        )
    survivors = [
        str(row["branch_id"])
        for row in rows
        if bool(row["survived_to_endpoint"])
    ]
    return {
        "schema": SCHEMA,
        "taskbook_cards": ["COMBAT-FAST-01", "COMBAT-KILL-01"],
        "source": {
            "path": source_path,
            "sha256": source_sha256,
            "schema": source_schema,
            "status": result.get("status"),
        },
        "branch_count": len(rows),
        "survivor_count": len(survivors),
        "survival_filtered_candidate_ids": survivors,
        "branches": rows,
        "result": {
            "status": "combat_branches_lowered_without_benefit_promotion",
            "survival_is_hard_filter": True,
            "combat_metrics_are_proxy_or_observed_state_only": True,
            "verified_generation_safe_hp_transactions": False,
            "verified_prevented_hostile_births": False,
            "candidate_ranking_authority": False,
            "live_authority": False,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source_bytes = args.source.read_bytes()
    source = json.loads(source_bytes)
    if not isinstance(source, dict):
        raise NativeCombatBranchReportError("native combat source is not an object")
    report = build_report(
        source,
        source_path=str(args.source),
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"native combat branch report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
