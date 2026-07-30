#!/usr/bin/env python3
"""Lower native snapshot branches into survival-filtered combat comparisons."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCHEMA = "th08-native-combat-branch-comparison-v3"
ROLLING_SCHEMA = "th08-native-snapshot-rolling-trial-v10"
CAUSAL_SEARCH_SCHEMA = "th08-native-snapshot-causal-secondary-search-v8"
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


def _boolean(summary: dict[str, Any], field: str) -> bool:
    value = summary.get(field)
    if type(value) is not bool:
        raise NativeCombatBranchReportError(f"{field} is not a Boolean")
    return value


def _byte(summary: dict[str, Any], field: str) -> int:
    value = _integer(summary, field)
    if value > 0xFF:
        raise NativeCombatBranchReportError(
            f"native combat summary {field!r} must be a byte integer"
        )
    return value


def _action_mask(tick: dict[str, Any], *, field: str) -> int:
    value = tick.get("selected_action")
    if type(value) is not int or not 0 <= value <= 0xFF:
        raise NativeCombatBranchReportError(
            f"{field}.selected_action is not a byte integer"
        )
    return value


def _optional_action_mask(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not 0 <= value <= 0xFF:
        raise NativeCombatBranchReportError(f"{field} is not a byte integer")
    return value


def _player_phase(value: object, *, field: str) -> int:
    state = _object(value, field=field)
    phase = state.get("player_phase")
    if type(phase) is not int or phase < 0:
        raise NativeCombatBranchReportError(
            f"{field}.player_phase must be a nonnegative integer"
        )
    return phase


def _resources(value: object, *, field: str) -> dict[str, float]:
    state = _object(value, field=field)
    resources = _object(state.get("resources"), field=f"{field}.resources")
    result: dict[str, float] = {}
    for name in ("lives", "bombs", "power"):
        raw = resources.get(name)
        if (
            type(raw) not in (int, float)
            or not math.isfinite(float(raw))
            or float(raw) < 0.0
        ):
            raise NativeCombatBranchReportError(
                f"{field}.resources.{name} must be finite and nonnegative"
            )
        result[name] = float(raw)
    return result


def _summarize_branch(
    *,
    branch_id: str,
    root_summary: dict[str, Any],
    root_player_phase: int,
    root_resources: dict[str, float],
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
    player_phase_survived = root_player_phase != 2 and not any(
        _player_phase(state, field=f"{branch_id}.compact_state") == 2
        for state in compact_states
    )
    resource_trajectory = [
        root_resources,
        *[
            _resources(
                state,
                field=f"{branch_id}.ticks[{index}].compact_state",
            )
            for index, state in enumerate(compact_states)
        ],
    ]
    life_decrease_tick_indices = [
        index
        for index, (previous, current) in enumerate(
            zip(
                resource_trajectory[:-1],
                resource_trajectory[1:],
                strict=True,
            )
        )
        if current["lives"] < previous["lives"]
    ]
    bomb_resource_decrease_tick_indices = [
        index
        for index, (previous, current) in enumerate(
            zip(
                resource_trajectory[:-1],
                resource_trajectory[1:],
                strict=True,
            )
        )
        if current["bombs"] < previous["bombs"]
    ]
    survived = player_phase_survived and not life_decrease_tick_indices
    selected_actions = [
        _action_mask(tick, field=f"{branch_id}.ticks[{index}]")
        for index, tick in enumerate(tick_objects)
    ]
    route_ids = [
        _byte(summary, "route_id")
        for summary in (root_summary, *summaries)
    ]
    route2_scope = all(route_id == 2 for route_id in route_ids)
    bomb_active_frames = [
        _integer(summary, "manager_frame")
        for summary in (root_summary, *summaries)
        if _boolean(summary, "bomb_active")
    ]
    bomb_active_input_frames = [
        _integer(summary, "manager_frame")
        for summary in (root_summary, *summaries)
        if _byte(summary, "active_input") & 0x02
    ]
    bomb_action_indices = [
        index for index, action in enumerate(selected_actions) if action & 0x02
    ]
    bomb_declared_action_fields: list[str] = []
    checked_prefix_mask = _optional_action_mask(
        prefix_mask,
        field=f"{branch_id}.prefix_mask",
    )
    if checked_prefix_mask is not None and checked_prefix_mask & 0x02:
        bomb_declared_action_fields.append("prefix_mask")
    checked_prefix_schedule: list[int | None] | None = None
    if prefix_schedule is not None:
        checked_prefix_schedule = []
        for index, value in enumerate(prefix_schedule):
            mask = _optional_action_mask(
                value,
                field=f"{branch_id}.prefix_action_schedule[{index}]",
            )
            checked_prefix_schedule.append(mask)
            if mask is not None and mask & 0x02:
                bomb_declared_action_fields.append(
                    f"prefix_action_schedule[{index}]"
                )
    checked_continuation_mask = _optional_action_mask(
        continuation_mask,
        field=f"{branch_id}.continuation_mask",
    )
    if (
        checked_continuation_mask is not None
        and checked_continuation_mask & 0x02
    ):
        bomb_declared_action_fields.append("continuation_mask")
    no_bomb = (
        not bomb_active_frames
        and not bomb_active_input_frames
        and not bomb_action_indices
        and not bomb_declared_action_fields
        and not bomb_resource_decrease_tick_indices
    )
    route2_nmnb_eligible = survived and no_bomb and route2_scope
    endpoint = summaries[-1]
    unresolved_target_ticks = sum(
        _integer(summary, "unresolved_overlap_target_count")
        for summary in summaries
    )
    route2_normal_incompatible_active_shot_ticks = sum(
        _integer(
            summary,
            "route2_normal_damage_path_incompatible_active_shot_count",
        )
        for summary in (root_summary, *summaries)
    )
    route2_non_normal_or_unknown_source_active_shot_ticks = sum(
        _integer(
            summary,
            "route2_non_normal_or_unknown_source_active_shot_count",
        )
        for summary in (root_summary, *summaries)
    )
    candidate_status = (
        "rejected_hard_survival"
        if not survived
        else (
            "rejected_hard_no_bomb"
            if not no_bomb
            else (
                "out_of_scope_non_route2"
                if not route2_scope
                else (
                    "survival_filtered_proxy_only_with_unresolved_overlap"
                    if unresolved_target_ticks
                    else (
                        "survival_filtered_proxy_only_"
                        "non_normal_or_unknown_shot_source"
                        if route2_non_normal_or_unknown_source_active_shot_ticks
                        else (
                            "survival_filtered_proxy_only_"
                            "non_normal_shot_content"
                            if route2_normal_incompatible_active_shot_ticks
                            else "survival_filtered_proxy_only"
                        )
                    )
                )
            )
        )
    )
    return {
        "branch_id": branch_id,
        "prefix_mask": checked_prefix_mask,
        "prefix_action_schedule": checked_prefix_schedule,
        "continuation_mask": checked_continuation_mask,
        "selected_actions": selected_actions,
        "root_manager_frame": root_frame,
        "root_player_phase": root_player_phase,
        "manager_frames": manager_frames,
        "player_phase_survived_to_endpoint": player_phase_survived,
        "survived_to_endpoint": survived,
        "no_bomb_to_endpoint": no_bomb,
        "route2_scope": route2_scope,
        "route2_nmnb_eligible": route2_nmnb_eligible,
        "bomb_active_manager_frames": bomb_active_frames,
        "bomb_active_input_manager_frames": bomb_active_input_frames,
        "bomb_action_tick_indices": bomb_action_indices,
        "bomb_declared_action_fields": bomb_declared_action_fields,
        "life_decrease_tick_indices": life_decrease_tick_indices,
        "bomb_resource_decrease_tick_indices": (
            bomb_resource_decrease_tick_indices
        ),
        "candidate_status": candidate_status,
        "metrics": {
            "root_resources": resource_trajectory[0],
            "endpoint_resources": resource_trajectory[-1],
            "resource_delta": {
                name: (
                    resource_trajectory[-1][name]
                    - resource_trajectory[0][name]
                )
                for name in ("lives", "bombs", "power")
            },
            "resource_trajectory": resource_trajectory,
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
            "supported_primary_damage_region_contribution_tick_sum": sum(
                _integer(
                    summary,
                    "supported_primary_damage_region_contribution_sum",
                )
                for summary in summaries
            ),
            "supported_alternate_damage_region_contribution_tick_sum": sum(
                _integer(
                    summary,
                    "supported_alternate_damage_region_contribution_sum",
                )
                for summary in summaries
            ),
            "supported_resolved_hp_damage_tick_sum": sum(
                _integer(summary, "supported_resolved_hp_damage_sum")
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
            "route2_normal_damage_path_incompatible_active_shot_ticks": (
                route2_normal_incompatible_active_shot_ticks
            ),
            "route2_non_normal_or_unknown_source_active_shot_ticks": (
                route2_non_normal_or_unknown_source_active_shot_ticks
            ),
        },
        "authority": {
            "hard_survival_filter": (
                "observed_native_player_phase_and_lives_over_branch"
            ),
            "hard_no_bomb_filter": (
                "declared_and_selected_complete_masks_native_active_input_"
                "observed_native_bomb_state_and_bomb_stock_non_decrease"
            ),
            "resource_trajectory": (
                "observed_native_float32_seam_values_no_benefit_inference"
            ),
            "route2_scope_filter": (
                "exact_root_and_tick_native_route_id_equals_2"
            ),
            "published_frame_damage": (
                "observed_native_enemy_frame_damage_field_at_endpoint_seams"
            ),
            "supported_contribution": (
                "instantaneous_supported_ordinary_shot_and_damage_region_"
                "pass_subtotals_before_late_enemy_scaling"
            ),
            "supported_resolved_hp_damage": (
                "manager_ordered_supported_slots_plus_exact_root_raw_"
                "predicate_arithmetic_synthetic_not_observed_transaction"
            ),
            "positive_hp_sum": (
                "cross_slot_aggregate_not_generation_safe_or_birth_normalized"
            ),
            "route2_normal_damage_path_content_compatible": (
                route2_normal_incompatible_active_shot_ticks == 0
            ),
            "route2_exact_normal_source_provenance": (
                route2_non_normal_or_unknown_source_active_shot_ticks == 0
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
    root_resources = _resources(
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
                root_resources=root_resources,
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
    origin_resources = _resources(
        origin.get("compact_state"),
        field="result.origin.compact_state",
    )
    rows: list[dict[str, object]] = []
    for prefix_index, prefix_value in enumerate(
        _array(result.get("prefixes"), field="result.prefixes")
    ):
        prefix = _object(prefix_value, field=f"result.prefixes[{prefix_index}]")
        prefix_mask_value = prefix.get("prefix_mask")
        prefix_mask = _optional_action_mask(
            prefix_mask_value,
            field=f"result.prefixes[{prefix_index}].prefix_mask",
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
                root_resources=origin_resources,
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
        subroot_resources = _resources(
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
            continuation_mask = _optional_action_mask(
                continuation.get("complete_mask"),
                field=(
                    f"result.prefixes[{prefix_index}].continuation."
                    "complete_mask"
                ),
            )
            if continuation_mask is None:
                raise NativeCombatBranchReportError(
                    "continuation complete_mask cannot be null"
                )
            rows.append(
                _summarize_branch(
                    branch_id=(
                        f"prefix-{prefix_index}/"
                        f"continuation-{continuation_mask:#04x}"
                    ),
                    root_summary=subroot_summary,
                    root_player_phase=subroot_player_phase,
                    root_resources=subroot_resources,
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
    route2_nmnb_eligible = [
        str(row["branch_id"])
        for row in rows
        if bool(row["route2_nmnb_eligible"])
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
        "route2_nmnb_eligible_count": len(route2_nmnb_eligible),
        "route2_nmnb_filtered_candidate_ids": route2_nmnb_eligible,
        "branches": rows,
        "result": {
            "status": "combat_branches_lowered_without_benefit_promotion",
            "survival_is_hard_filter": True,
            "hard_survival_uses_player_phase_and_lives": True,
            "no_bomb_is_hard_filter": True,
            "hard_no_bomb_uses_bomb_stock_non_decrease": True,
            "route2_scope_is_required_for_combat_proxy": True,
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
