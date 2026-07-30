#!/usr/bin/env python3
"""Join Route-2 source/emission and item/drop atlases into candidate cohorts."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "th08-route2-combat-resource-candidate-board-v1"
SOURCE_SCHEMA = "th08-source-emission-program-atlas-v1"
ITEM_SCHEMA = "th08-route2-item-drop-opportunity-atlas-v1"
EXPECTED_SOURCE_ATLAS_SHA256 = (
    "6ae9494a40ff5a08143564c653b3c2007e1125063a16b1108854db84f74531b5"
)
EXPECTED_ITEM_ATLAS_SHA256 = (
    "0692985c579a3040def4e635115a3399c0e4323a338d5f03427c4930821dc0b0"
)
TASKBOOK_CARDS = ("COMBAT-KILL-01", "POWER-ROUTE-01", "ROUTE-OPT-01")


class CombatResourceCandidateBoardError(ValueError):
    """Raised when an immutable cross-atlas join cannot be preserved."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_pinned_atlas(
    path: Path,
    *,
    expected_sha256: str,
    expected_schema: str,
) -> dict[str, Any]:
    actual_sha256 = _sha256_path(path)
    if actual_sha256 != expected_sha256:
        raise CombatResourceCandidateBoardError(
            f"{path.name} SHA-256 differs from the accepted checkpoint"
        )
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema") != expected_schema:
        raise CombatResourceCandidateBoardError(
            f"{path.name} has an unsupported schema"
        )
    return report


def _index_programs(
    programs: list[dict[str, Any]],
    *,
    field: str,
    source: str,
) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for program in programs:
        root = int(program[field])
        if root in indexed:
            raise CombatResourceCandidateBoardError(
                f"{source} duplicates root subroutine {root}"
            )
        indexed[root] = program
    return indexed


def _positive_values(values: object) -> tuple[int, ...]:
    if not isinstance(values, list):
        raise CombatResourceCandidateBoardError(
            "candidate count set must be a list"
        )
    return tuple(sorted({int(value) for value in values if int(value) > 0}))


def _candidate_families(
    *,
    ordinary_emitter: bool,
    direct_emission: bool,
    child_emitter: bool,
    periodic_control: bool,
    default_small_power: bool,
    configured_extra_power_counts: tuple[int, ...],
    direct_power_bundle_counts: tuple[int, ...],
    ordinary_compatible: bool,
) -> tuple[str, ...]:
    configured_power = bool(configured_extra_power_counts)
    direct_bundle = bool(direct_power_bundle_counts)
    any_power_signal = (
        default_small_power or configured_power or direct_bundle
    )
    families: list[str] = []
    if ordinary_emitter and default_small_power:
        families.append("ordinary_emitter_default_small_power")
    if ordinary_emitter and configured_power:
        families.append("ordinary_emitter_configured_extra_power")
    if ordinary_emitter and direct_bundle:
        families.append("ordinary_emitter_direct_power_bundle")
    if ordinary_emitter and any_power_signal:
        families.append("ordinary_emitter_power_intersection")
        if direct_emission:
            families.append("power_intersection_direct_emission")
        if child_emitter:
            families.append("power_intersection_child_emitter")
        if periodic_control:
            families.append("power_intersection_periodic_control")
    if ordinary_emitter and not any_power_signal:
        families.append("ordinary_emitter_without_static_power_signal")
    if ordinary_compatible and any_power_signal and not ordinary_emitter:
        families.append("ordinary_resource_without_emitter_candidate")
    return tuple(families)


def _joined_program(
    *,
    stage_key: str,
    ecl_name: str,
    ecl_sha256: str,
    source_program: dict[str, Any],
    item_program: dict[str, Any],
) -> dict[str, Any]:
    root = int(source_program["root_subroutine"])
    item_join = item_program.get("source_emission_join_key")
    expected_join = {
        "route_ecl_sha256": ecl_sha256,
        "root_subroutine": root,
    }
    if item_join != expected_join:
        raise CombatResourceCandidateBoardError(
            f"{stage_key} root {root} has an inconsistent item-atlas join key"
        )

    source_class = source_program["classification"]
    item_class = item_program["classification"]
    ordinary_emitter = bool(
        source_class["ordinary_static_emitter_candidate"]
    )
    direct_emission_count = int(source_class["direct_emission_site_count"])
    child_emitter_count = int(source_class["child_emitter_site_count"])
    periodic_control_count = int(source_class["periodic_control_site_count"])
    default_small_power = bool(
        item_class[
            "ordinary_default_small_power_on_eligible_hp_defeat_candidate"
        ]
    )
    configured_counts = _positive_values(
        item_class["configured_extra_power_count_candidates"]
    )
    bundle_counts = _positive_values(
        item_class["direct_power_bundle_count_candidates"]
    )
    families = _candidate_families(
        ordinary_emitter=ordinary_emitter,
        direct_emission=direct_emission_count > 0,
        child_emitter=child_emitter_count > 0,
        periodic_control=periodic_control_count > 0,
        default_small_power=default_small_power,
        configured_extra_power_counts=configured_counts,
        direct_power_bundle_counts=bundle_counts,
        ordinary_compatible=bool(item_class["ordinary_compatible"]),
    )
    return {
        "candidate_id": f"{ecl_name}:root:{root}",
        "stage_key": stage_key,
        "join_key": expected_join,
        "root_subroutine": root,
        "source_metrics": {
            "timeline_spawn_instance_count": len(
                source_program["spawn_instances"]
            ),
            "direct_emission_site_count": direct_emission_count,
            "child_emitter_site_count": child_emitter_count,
            "periodic_control_site_count": periodic_control_count,
            "positive_local_timer_guard_count": int(
                source_class["positive_local_timer_guard_count"]
            ),
            "ordinary_static_emitter_candidate": ordinary_emitter,
            "static_program_coverage": str(
                source_class["static_program_coverage"]
            ),
        },
        "resource_signals": {
            "ordinary_compatible": bool(item_class["ordinary_compatible"]),
            "default_small_power_on_eligible_hp_defeat_candidate": (
                default_small_power
            ),
            "configured_extra_power_count_candidates": list(
                configured_counts
            ),
            "direct_power_bundle_count_candidates": list(bundle_counts),
            "direct_item_site_count": int(
                item_class["direct_item_site_count"]
            ),
            "drop_configuration_site_count": int(
                item_class["drop_configuration_site_count"]
            ),
            "possible_defeat_modes": list(
                item_class["possible_defeat_modes"]
            ),
            "mode3_drop_bypass_possible": bool(
                item_class["mode3_drop_bypass_possible"]
            ),
            "origin_kinds": list(item_program["origin_kinds"]),
        },
        "candidate_families": list(families),
        "runtime_join_required": [
            "exact enemy generation and root ownership",
            "main/aux VM instruction execution",
            "damageability and ordered HP-defeat end reason",
            "prevented hostile births or shortened exposure",
            "item request allocation and pickup identity",
            "survival-feasible action and later Power/combat consequence",
        ],
    }


def _stage_join(
    source_stage: dict[str, Any],
    item_stage: dict[str, Any],
) -> dict[str, Any]:
    if source_stage["key"] != item_stage["key"]:
        raise CombatResourceCandidateBoardError("stage keys do not align")
    if source_stage["route_stage_index"] != item_stage["route_stage_index"]:
        raise CombatResourceCandidateBoardError(
            f"{source_stage['key']} route-stage indices do not align"
        )
    if source_stage["route_ecl"] != item_stage["route_ecl"]:
        raise CombatResourceCandidateBoardError(
            f"{source_stage['key']} ECL identities do not align"
        )

    source_programs = _index_programs(
        source_stage["source_programs"],
        field="root_subroutine",
        source=f"{source_stage['key']} source atlas",
    )
    item_programs = _index_programs(
        item_stage["programs"],
        field="root_subroutine",
        source=f"{item_stage['key']} item atlas",
    )
    missing = sorted(set(source_programs) - set(item_programs))
    if missing:
        raise CombatResourceCandidateBoardError(
            f"{source_stage['key']} source roots missing from item atlas: "
            f"{missing}"
        )

    ecl = source_stage["route_ecl"]
    programs = [
        _joined_program(
            stage_key=str(source_stage["key"]),
            ecl_name=str(ecl["name"]),
            ecl_sha256=str(ecl["sha256"]),
            source_program=source_programs[root],
            item_program=item_programs[root],
        )
        for root in sorted(source_programs)
    ]
    family_counts = Counter(
        family for program in programs for family in program["candidate_families"]
    )
    intersection = [
        program
        for program in programs
        if "ordinary_emitter_power_intersection"
        in program["candidate_families"]
    ]
    return {
        "key": source_stage["key"],
        "label": source_stage["label"],
        "route_stage_index": source_stage["route_stage_index"],
        "route_ecl": ecl,
        "summary": {
            "joined_source_program_count": len(programs),
            "item_only_program_count": len(item_programs)
            - len(source_programs),
            "ordinary_emitter_candidate_count": sum(
                bool(
                    program["source_metrics"][
                        "ordinary_static_emitter_candidate"
                    ]
                )
                for program in programs
            ),
            "ordinary_emitter_power_intersection_count": len(intersection),
            "intersection_timeline_spawn_instance_count": sum(
                int(
                    program["source_metrics"][
                        "timeline_spawn_instance_count"
                    ]
                )
                for program in intersection
            ),
            "candidate_family_counts": dict(sorted(family_counts.items())),
        },
        "programs": programs,
    }


def build_combat_resource_candidate_board(
    *,
    source_atlas_path: Path,
    item_atlas_path: Path,
) -> dict[str, object]:
    source = _load_pinned_atlas(
        source_atlas_path,
        expected_sha256=EXPECTED_SOURCE_ATLAS_SHA256,
        expected_schema=SOURCE_SCHEMA,
    )
    item = _load_pinned_atlas(
        item_atlas_path,
        expected_sha256=EXPECTED_ITEM_ATLAS_SHA256,
        expected_schema=ITEM_SCHEMA,
    )
    if source["immutable_content_manifest"] != item["immutable_content_manifest"]:
        raise CombatResourceCandidateBoardError(
            "input atlases do not share one immutable content manifest"
        )
    if source["route_profile"] != item["route_profile"]:
        raise CombatResourceCandidateBoardError(
            "input atlases do not share one route profile"
        )
    source_stages = source["stages"]
    item_stages = item["stages"]
    if len(source_stages) != len(item_stages):
        raise CombatResourceCandidateBoardError(
            "input atlases have different stage counts"
        )
    stages = [
        _stage_join(source_stage, item_stage)
        for source_stage, item_stage in zip(
            source_stages,
            item_stages,
            strict=True,
        )
    ]
    programs = [
        program for stage in stages for program in stage["programs"]
    ]
    family_rows: dict[str, list[dict[str, object]]] = {}
    for program in programs:
        for family in program["candidate_families"]:
            family_rows.setdefault(str(family), []).append(program)
    cohorts = [
        {
            "family": family,
            "program_count": len(rows),
            "timeline_spawn_instance_count": sum(
                int(row["source_metrics"]["timeline_spawn_instance_count"])
                for row in rows
            ),
            "candidate_ids": sorted(str(row["candidate_id"]) for row in rows),
        }
        for family, rows in sorted(family_rows.items())
    ]
    summary = {
        "joined_source_program_count": len(programs),
        "item_only_program_count": sum(
            int(stage["summary"]["item_only_program_count"]) for stage in stages
        ),
        "ordinary_emitter_candidate_count": sum(
            int(stage["summary"]["ordinary_emitter_candidate_count"])
            for stage in stages
        ),
        "ordinary_emitter_power_intersection_count": sum(
            int(
                stage["summary"][
                    "ordinary_emitter_power_intersection_count"
                ]
            )
            for stage in stages
        ),
        "intersection_timeline_spawn_instance_count": sum(
            int(
                stage["summary"][
                    "intersection_timeline_spawn_instance_count"
                ]
            )
            for stage in stages
        ),
        "candidate_family_counts": dict(
            sorted(
                Counter(
                    family
                    for program in programs
                    for family in program["candidate_families"]
                ).items()
            )
        ),
    }
    result: dict[str, object] = {
        "schema": SCHEMA,
        "taskbook_cards": list(TASKBOOK_CARDS),
        "status": "static_cross_atlas_candidate_board_runtime_join_required",
        "inputs": {
            "source_emission_atlas": {
                "name": source_atlas_path.name,
                "sha256": EXPECTED_SOURCE_ATLAS_SHA256,
                "report_digest": source["report_digest"],
            },
            "item_drop_atlas": {
                "name": item_atlas_path.name,
                "sha256": EXPECTED_ITEM_ATLAS_SHA256,
                "report_digest": item["report_digest"],
            },
            "immutable_content_manifest": source[
                "immutable_content_manifest"
            ],
        },
        "route_profile": source["route_profile"],
        "selection_contract": {
            "method": "exact immutable-key intersection and named cohorts",
            "no_scalar_utility_ranking": True,
            "local_vm_timer_is_not_kill_deadline": True,
            "static_item_signal_is_not_pickup": True,
            "static_emission_site_is_not_prevented_birth": True,
            "consumer_rule": (
                "select more than one immutable root/event family, then run "
                "same-root exact survival versus damage/resource ablations"
            ),
        },
        "summary": summary,
        "cohorts": cohorts,
        "stages": stages,
        "authority": {
            "immutable_cross_atlas_join": True,
            "shipped_static_candidate_cohorts": True,
            "runtime_generation_or_instruction_execution": False,
            "verified_kill_or_prevented_birth": False,
            "verified_item_allocation_or_pickup": False,
            "causal_power_or_survival_benefit": False,
            "phase_option_edge": False,
            "planner_or_action_authority": False,
            "physical_trial_run": False,
        },
        "next_gate": {
            "join_key": (
                "content digest + stage/gameplay epoch + enemy generation + "
                "root subroutine + VM PC + lifecycle event + item allocation/"
                "pickup + hostile births + viable action certificate"
            ),
            "minimum_diversity": (
                "at least two immutable roots from more than one event family"
            ),
            "branch_contract": (
                "pure survival and damage/resource branches start at the "
                "same immutable root and regenerate their causal futures"
            ),
        },
    }
    result["report_digest"] = _sha256_bytes(
        json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-atlas", required=True, type=Path)
    parser.add_argument("--item-atlas", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_combat_resource_candidate_board(
        source_atlas_path=args.source_atlas,
        item_atlas_path=args.item_atlas,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
