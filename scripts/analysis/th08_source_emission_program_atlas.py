#!/usr/bin/env python3
"""Build a route-wide static source-lifetime to emission-program atlas."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from th08_ecl import TIMELINE_OPCODE_NAMES, EclFile, SubInstruction, parse_ecl
from th08_ecl_birth import (
    ECL_OP_DISABLE_DEFERRED_FIRE,
    ECL_OP_EMIT_CURRENT_PATTERN,
    ECL_OP_ENABLE_DEFERRED_FIRE,
    ECL_OP_FIRST_CHILD_SOURCE,
    ECL_OP_FIRST_DIRECT_FIRE,
    ECL_OP_LAST_CHILD_SOURCE,
    ECL_OP_LAST_DIRECT_FIRE,
    ECL_OP_SET_FIRE_DELAY,
    ECL_OP_SET_FIRE_DELAY_RANDOM_PHASE,
)
from th08_ecl_callback_model import CALLBACK_SPECS
from th08_ecl_flow import (
    TIMELINE_SPAWN_OPCODES,
    FlowConfig,
    SubEdge,
    analyze_flow,
)
from th08_ecl_opcodes import opcode_spec


SCHEMA = "th08-source-emission-program-atlas-v1"
TASKBOOK_CARD = "COMBAT-KILL-01"
EXPECTED_CONTENT_MANIFEST_SHA256 = (
    "3a52b6f485ada63c833f77ae8cd1653f469ae4fadeef3c38336a737c7e753ae1"
)
ROUTE_ID = 2
DIFFICULTY_INDEX = 3
DIFFICULTY_MASK = 0x08

SAME_SOURCE_EDGE_KINDS = frozenset({"call", "interrupt_slot", "aux_vm"})
CROSS_SOURCE_EDGE_KINDS = frozenset({"call_with_enemy", "child_spawn"})
PHASE_EXIT_EDGE_KINDS = frozenset(
    {"enemy_end", "health_phase", "timeout_phase"}
)
BOSS_CONTROL_OPCODES = frozenset({0x53, 0x7A, 0x83, 0x85, 0x86, 0xB0, 0xB1})
DIRECT_EMISSION_OPCODES = frozenset(
    {
        *range(ECL_OP_FIRST_DIRECT_FIRE, ECL_OP_LAST_DIRECT_FIRE + 1),
        ECL_OP_EMIT_CURRENT_PATTERN,
        0x72,
        0x73,
    }
)
PERIODIC_CONTROL_OPCODES = frozenset(
    {
        ECL_OP_SET_FIRE_DELAY,
        ECL_OP_SET_FIRE_DELAY_RANDOM_PHASE,
        ECL_OP_ENABLE_DEFERRED_FIRE,
        ECL_OP_DISABLE_DEFERRED_FIRE,
    }
)
CALLBACK_OPCODES = frozenset({0x88, 0x89})


@dataclass(frozen=True)
class StageSpec:
    key: str
    label: str
    route_stage_index: int
    ecl_name: str


STAGES = (
    StageSpec("stage1", "Stage 1", 0, "ecldata1.ecl"),
    StageSpec("stage2", "Stage 2", 1, "ecldata2.ecl"),
    StageSpec("stage3", "Stage 3", 2, "ecldata3.ecl"),
    StageSpec("stage4a", "Stage 4A / Reimu", 3, "ecldata4a.ecl"),
    StageSpec("stage5", "Stage 5", 5, "ecldata5.ecl"),
    StageSpec("final_b", "Final B / Kaguya", 7, "ecldata7.ecl"),
)


class SourceEmissionAtlasError(ValueError):
    """Raised when immutable or structural authority cannot be preserved."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def _eligible(instruction: SubInstruction) -> bool:
    return bool(instruction.difficulty_mask & DIFFICULTY_MASK)


def _source_owned_subroutines(
    root_subroutine: int,
    edges: Iterable[SubEdge],
) -> tuple[int, ...]:
    adjacency: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if edge.kind in SAME_SOURCE_EDGE_KINDS:
            adjacency[edge.source_subroutine].add(edge.target_subroutine)
    visited: set[int] = set()
    pending = deque((root_subroutine,))
    while pending:
        current = pending.popleft()
        if current in visited:
            continue
        visited.add(current)
        pending.extend(sorted(adjacency.get(current, ())))
    return tuple(sorted(visited))


def _component_instructions(
    ecl: EclFile,
    component: tuple[int, ...],
    reachable_offsets: set[int],
) -> tuple[tuple[int, SubInstruction], ...]:
    rows: list[tuple[int, SubInstruction]] = []
    for subroutine_index in component:
        for instruction in ecl.subroutines[subroutine_index].instructions:
            if instruction.offset in reachable_offsets and _eligible(instruction):
                rows.append((subroutine_index, instruction))
    return tuple(sorted(rows, key=lambda row: (row[0], row[1].offset)))


def _instruction_site(
    ecl: EclFile,
    subroutine_index: int,
    instruction: SubInstruction,
) -> dict[str, object]:
    spec = opcode_spec(instruction.opcode)
    return {
        "symbolic_id": (
            f"{ecl.path.name}:sub:{subroutine_index}:"
            f"0x{instruction.offset:08x}"
        ),
        "subroutine": subroutine_index,
        "file_offset": instruction.offset,
        "local_vm_timer_guard": instruction.time,
        "opcode": instruction.opcode,
        "opcode_hex": f"0x{instruction.opcode:02x}",
        "opcode_name": spec.name,
        "semantic_confidence": spec.confidence,
        "difficulty_mask": instruction.difficulty_mask,
        "parameter_mask": instruction.parameter_mask,
        "argument_words": [
            f"0x{argument:08x}" for argument in instruction.arguments
        ],
        "timer_guard_authority": (
            "local_vm_timer_value_not_source_age_or_manager_frame_deadline"
        ),
    }


def _callback_residual(instruction: SubInstruction) -> dict[str, object]:
    dynamic = bool(instruction.parameter_mask & 0x01)
    index = None if dynamic else _signed(instruction.arguments[0])
    result: dict[str, object] = {
        "dynamic_index": dynamic,
        "callback_index": index,
        "action": (
            "invoke"
            if instruction.opcode == 0x88
            else "clear"
            if index is not None and index < 0
            else "install"
        ),
    }
    if index is not None and index >= 0:
        if index >= len(CALLBACK_SPECS):
            raise SourceEmissionAtlasError(
                f"callback index {index} exceeds native callback table"
            )
        callback = CALLBACK_SPECS[index]
        result.update(
            {
                "callback_name": callback.name,
                "callback_confidence": callback.confidence,
            }
        )
    return result


def _edges_from_component(
    component: tuple[int, ...],
    edges: tuple[SubEdge, ...],
) -> tuple[SubEdge, ...]:
    component_set = set(component)
    return tuple(
        edge for edge in edges if edge.source_subroutine in component_set
    )


def _program_report(
    *,
    ecl: EclFile,
    root_subroutine: int,
    flow,
    spawn_instances: list[dict[str, object]],
    component_cache: dict[int, tuple[int, ...]],
) -> dict[str, object]:
    reachable_offsets = set(flow.reachable_instruction_offsets)

    def component(root: int) -> tuple[int, ...]:
        cached = component_cache.get(root)
        if cached is None:
            cached = _source_owned_subroutines(root, flow.edges)
            component_cache[root] = cached
        return cached

    source_component = component(root_subroutine)
    source_instructions = _component_instructions(
        ecl,
        source_component,
        reachable_offsets,
    )
    component_edges = _edges_from_component(source_component, flow.edges)
    edge_by_offset = {edge.source_offset: edge for edge in component_edges}

    direct_sites = [
        _instruction_site(ecl, subroutine, instruction)
        for subroutine, instruction in source_instructions
        if instruction.opcode in DIRECT_EMISSION_OPCODES
    ]
    periodic_sites = [
        _instruction_site(ecl, subroutine, instruction)
        for subroutine, instruction in source_instructions
        if instruction.opcode in PERIODIC_CONTROL_OPCODES
    ]
    callback_sites: list[dict[str, object]] = []
    callback_unknown = False
    for subroutine, instruction in source_instructions:
        if instruction.opcode not in CALLBACK_OPCODES:
            continue
        site = _instruction_site(ecl, subroutine, instruction)
        residual = _callback_residual(instruction)
        site["callback"] = residual
        callback_sites.append(site)
        callback_unknown = callback_unknown or bool(
            residual["dynamic_index"]
            or residual.get("callback_confidence") == "unknown"
        )

    child_sites: list[dict[str, object]] = []
    for subroutine, instruction in source_instructions:
        if not (
            ECL_OP_FIRST_CHILD_SOURCE
            <= instruction.opcode
            <= ECL_OP_LAST_CHILD_SOURCE
        ):
            continue
        edge = edge_by_offset.get(instruction.offset)
        target = edge.target_subroutine if edge is not None else None
        site = _instruction_site(ecl, subroutine, instruction)
        site["target_subroutine"] = target
        if target is not None:
            child_component = component(target)
            child_instructions = _component_instructions(
                ecl,
                child_component,
                reachable_offsets,
            )
            child_direct = sum(
                instruction.opcode in DIRECT_EMISSION_OPCODES
                for _, instruction in child_instructions
            )
            child_periodic = sum(
                instruction.opcode in PERIODIC_CONTROL_OPCODES
                for _, instruction in child_instructions
            )
            child_boss = any(
                instruction.opcode in BOSS_CONTROL_OPCODES
                for _, instruction in child_instructions
            )
            site["target_program"] = {
                "source_owned_subroutines": list(child_component),
                "direct_emission_site_count": child_direct,
                "periodic_control_site_count": child_periodic,
                "boss_control_possible": child_boss,
                "emitter_candidate": bool(child_direct),
            }
        child_sites.append(site)

    boss_sites = [
        _instruction_site(ecl, subroutine, instruction)
        for subroutine, instruction in source_instructions
        if instruction.opcode in BOSS_CONTROL_OPCODES
    ]
    unknown_sites = [
        _instruction_site(ecl, subroutine, instruction)
        for subroutine, instruction in source_instructions
        if opcode_spec(instruction.opcode).confidence == "unknown"
    ]
    cross_source_edges = [
        {
            "source_subroutine": edge.source_subroutine,
            "source_offset": edge.source_offset,
            "target_subroutine": edge.target_subroutine,
            "kind": edge.kind,
        }
        for edge in component_edges
        if edge.kind in CROSS_SOURCE_EDGE_KINDS
    ]
    phase_exit_edges = [
        {
            "source_subroutine": edge.source_subroutine,
            "source_offset": edge.source_offset,
            "target_subroutine": edge.target_subroutine,
            "kind": edge.kind,
        }
        for edge in component_edges
        if edge.kind in PHASE_EXIT_EDGE_KINDS
    ]
    unresolved_edges = [
        {
            "source_subroutine": subroutine,
            "source_offset": offset,
            "opcode": opcode,
        }
        for subroutine, offset, opcode in flow.unresolved_dynamic_subroutine_edges
        if subroutine in source_component
    ]
    child_emitter_site_count = sum(
        bool(site.get("target_program", {}).get("emitter_candidate"))
        for site in child_sites
    )
    boss_possible = bool(boss_sites)
    direct_or_child_emitter = bool(direct_sites or child_emitter_site_count)
    ordinary_compatible_candidate = not boss_possible and direct_or_child_emitter
    positive_timer_guard_count = sum(
        int(site["local_vm_timer_guard"]) > 0
        for site in (*direct_sites, *child_sites)
    )
    residual_reasons = []
    if callback_unknown:
        residual_reasons.append("unknown_or_dynamic_callback")
    if unknown_sites:
        residual_reasons.append("unknown_opcode_in_source_component")
    if unresolved_edges:
        residual_reasons.append("dynamic_subroutine_edge")
    if any(edge["kind"] == "call_with_enemy" for edge in cross_source_edges):
        residual_reasons.append("cross_enemy_call")
    if periodic_sites:
        residual_reasons.append("runtime_deferred_periodic_state_required")
    residual_reasons.extend(
        (
            "runtime_branch_and_vm_timer_state_required",
            "runtime_generation_hp_damageability_and_end_reason_required",
            "existing_projectiles_persist_without_explicit_cancel",
        )
    )

    return {
        "root_subroutine": root_subroutine,
        "spawn_instances": spawn_instances,
        "source_owned_subroutines": list(source_component),
        "source_ownership": {
            "included_edges": sorted(SAME_SOURCE_EDGE_KINDS),
            "excluded_cross_source_edges": sorted(CROSS_SOURCE_EDGE_KINDS),
            "phase_exit_edges_not_traversed": sorted(PHASE_EXIT_EDGE_KINDS),
        },
        "direct_emission_sites": direct_sites,
        "periodic_control_sites": periodic_sites,
        "child_spawn_sites": child_sites,
        "callback_sites": callback_sites,
        "boss_control_sites": boss_sites,
        "unknown_semantic_sites": unknown_sites,
        "cross_source_edges": cross_source_edges,
        "phase_exit_edges": phase_exit_edges,
        "unresolved_dynamic_edges": unresolved_edges,
        "classification": {
            "boss_control_possible": boss_possible,
            "ordinary_compatible": not boss_possible,
            "direct_emission_site_count": len(direct_sites),
            "periodic_control_site_count": len(periodic_sites),
            "child_emitter_site_count": child_emitter_site_count,
            "positive_local_timer_guard_count": positive_timer_guard_count,
            "ordinary_static_emitter_candidate": ordinary_compatible_candidate,
            "deadline_status": "runtime_join_required",
            "static_program_coverage": (
                "partial_with_semantic_residuals"
                if residual_reasons
                else "conservative_cfg_site_inventory"
            ),
        },
        "residual_reasons": sorted(set(residual_reasons)),
    }


def _asset_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise SourceEmissionAtlasError("content manifest assets are missing")
    return {
        str(asset["name"]): asset
        for asset in assets
        if isinstance(asset, dict) and "name" in asset
    }


def _validate_ecl(ecl: EclFile, assets: dict[str, dict[str, Any]]) -> None:
    asset = assets.get(ecl.path.name)
    if asset is None:
        raise SourceEmissionAtlasError(
            f"{ecl.path.name} is absent from immutable content manifest"
        )
    if asset.get("decoded_sha256") != ecl.sha256:
        raise SourceEmissionAtlasError(
            f"{ecl.path.name} decoded SHA differs from immutable manifest"
        )


def _stage_report(
    *,
    decoded_dir: Path,
    stage: StageSpec,
    assets: dict[str, dict[str, Any]],
) -> dict[str, object]:
    ecl = parse_ecl(decoded_dir / stage.ecl_name)
    _validate_ecl(ecl, assets)
    flow = analyze_flow(
        ecl,
        FlowConfig(
            difficulty_index=DIFFICULTY_INDEX,
            difficulty_mask=DIFFICULTY_MASK,
            route_id=ROUTE_ID,
        ),
    )
    spawns_by_root: dict[int, list[dict[str, object]]] = defaultdict(list)
    for timeline in ecl.timelines:
        for instruction in timeline.instructions:
            if (
                instruction.opcode not in TIMELINE_SPAWN_OPCODES
                or not instruction.difficulty_mask & DIFFICULTY_MASK
            ):
                continue
            root = _signed(instruction.arguments[0])
            spawns_by_root[root].append(
                {
                    "symbolic_id": (
                        f"{ecl.path.name}:timeline:{timeline.index}:"
                        f"0x{instruction.offset:08x}"
                    ),
                    "timeline": timeline.index,
                    "file_offset": instruction.offset,
                    "timeline_time": instruction.time,
                    "opcode": instruction.opcode,
                    "opcode_name": TIMELINE_OPCODE_NAMES.get(
                        instruction.opcode,
                        f"timeline_{instruction.opcode:02x}",
                    ),
                    "difficulty_mask": instruction.difficulty_mask,
                    "root_subroutine": root,
                }
            )
    component_cache: dict[int, tuple[int, ...]] = {}
    programs = [
        _program_report(
            ecl=ecl,
            root_subroutine=root,
            flow=flow,
            spawn_instances=sorted(
                instances,
                key=lambda row: (
                    int(row["timeline"]),
                    int(row["file_offset"]),
                ),
            ),
            component_cache=component_cache,
        )
        for root, instances in sorted(spawns_by_root.items())
    ]
    classifications = [program["classification"] for program in programs]
    candidate_programs = [
        program
        for program in programs
        if bool(program["classification"]["ordinary_static_emitter_candidate"])
    ]
    candidate_spawns = sum(
        len(program["spawn_instances"]) for program in candidate_programs
    )
    return {
        "key": stage.key,
        "label": stage.label,
        "route_stage_index": stage.route_stage_index,
        "route_ecl": {
            "name": ecl.path.name,
            "sha256": ecl.sha256,
            "subroutine_count": len(ecl.subroutines),
            "timeline_count": len(ecl.timelines),
        },
        "flow": {
            "root_subroutines": list(flow.root_subroutines),
            "reachable_subroutine_count": len(flow.reachable_subroutines),
            "reachable_instruction_count": len(flow.reachable_instruction_offsets),
            "folded_branch_count": flow.folded_branch_count,
            "conservative_branch_count": flow.conservative_branch_count,
            "unresolved_dynamic_subroutine_edges": [
                list(row) for row in flow.unresolved_dynamic_subroutine_edges
            ],
        },
        "summary": {
            "spawn_instance_count": sum(len(rows) for rows in spawns_by_root.values()),
            "unique_source_program_count": len(programs),
            "boss_possible_program_count": sum(
                bool(row["boss_control_possible"]) for row in classifications
            ),
            "ordinary_compatible_program_count": sum(
                bool(row["ordinary_compatible"]) for row in classifications
            ),
            "ordinary_static_emitter_candidate_program_count": len(
                candidate_programs
            ),
            "ordinary_static_emitter_candidate_spawn_count": candidate_spawns,
            "ordinary_candidate_direct_emission_site_count": sum(
                int(program["classification"]["direct_emission_site_count"])
                for program in candidate_programs
            ),
            "ordinary_candidate_child_emitter_site_count": sum(
                int(program["classification"]["child_emitter_site_count"])
                for program in candidate_programs
            ),
            "ordinary_candidate_periodic_control_site_count": sum(
                int(program["classification"]["periodic_control_site_count"])
                for program in candidate_programs
            ),
            "direct_emission_site_count": sum(
                int(row["direct_emission_site_count"]) for row in classifications
            ),
            "child_emitter_site_count": sum(
                int(row["child_emitter_site_count"]) for row in classifications
            ),
            "periodic_control_site_count": sum(
                int(row["periodic_control_site_count"]) for row in classifications
            ),
        },
        "source_programs": programs,
    }


def build_source_emission_atlas(
    *,
    decoded_dir: Path,
    content_manifest_path: Path,
) -> dict[str, object]:
    manifest_sha256 = _sha256_path(content_manifest_path)
    if manifest_sha256 != EXPECTED_CONTENT_MANIFEST_SHA256:
        raise SourceEmissionAtlasError(
            "immutable content manifest SHA differs from accepted checkpoint"
        )
    manifest = json.loads(content_manifest_path.read_text(encoding="utf-8"))
    assets = _asset_index(manifest)
    stages = [
        _stage_report(decoded_dir=decoded_dir, stage=stage, assets=assets)
        for stage in STAGES
    ]
    stage_summaries = [stage["summary"] for stage in stages]
    aggregate_keys = (
        "spawn_instance_count",
        "unique_source_program_count",
        "boss_possible_program_count",
        "ordinary_compatible_program_count",
        "ordinary_static_emitter_candidate_program_count",
        "ordinary_static_emitter_candidate_spawn_count",
        "ordinary_candidate_direct_emission_site_count",
        "ordinary_candidate_child_emitter_site_count",
        "ordinary_candidate_periodic_control_site_count",
        "direct_emission_site_count",
        "child_emitter_site_count",
        "periodic_control_site_count",
    )
    result: dict[str, object] = {
        "schema": SCHEMA,
        "taskbook_card": TASKBOOK_CARD,
        "status": "static_candidate_index_runtime_join_required",
        "route_profile": {
            "route_id": ROUTE_ID,
            "difficulty": "Lunatic",
            "difficulty_index": DIFFICULTY_INDEX,
            "difficulty_mask": DIFFICULTY_MASK,
            "route": "Sakuya/Remilia Final B",
            "stage_keys": [stage.key for stage in STAGES],
        },
        "immutable_content_manifest": {
            "name": content_manifest_path.name,
            "sha256": manifest_sha256,
            "content_set_sha256": manifest["content_scope"]["content_set_sha256"],
            "executable_sha256": manifest["shipped_identity"]["executable_sha256"],
        },
        "summary": {
            key: sum(int(summary[key]) for summary in stage_summaries)
            for key in aggregate_keys
        },
        "stages": stages,
        "native_order": {
            "same_update": (
                "enemy main/aux ECL and staged periodic emission run before "
                "player-shot HP subtraction"
            ),
            "kill_effect": (
                "a player-shot kill cannot undo births already produced in "
                "that update; inactive retirement prevents later source VM "
                "updates"
            ),
            "projectile_persistence": (
                "ordinary source death does not imply cancellation of bullets "
                "or lasers already active"
            ),
        },
        "authority": {
            "shipped_content_identity": True,
            "route_difficulty_cfg_overapproximation": True,
            "source_owned_direct_site_inventory": True,
            "runtime_instruction_execution": False,
            "runtime_generation_or_kill_reason": False,
            "absolute_kill_deadline": False,
            "prevented_birth_count": False,
            "planner_or_action_authority": False,
            "physical_trial_run": False,
        },
        "next_gate": {
            "join_key": (
                "content digest + stage + gameplay epoch + enemy generation + "
                "main/aux VM instruction pointer + periodic descriptor/timer"
            ),
            "required_measurements": [
                "exact pre/post HP and frame damage",
                "damageability and end reason",
                "birth ownership and post-death projectile persistence",
                "viable action and issue certificate",
            ],
            "deadline_rule": (
                "local VM timer guards are candidate labels only; derive a "
                "manager-frame kill deadline from an immutable runtime root"
            ),
        },
    }
    digest_payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    result["report_digest"] = _sha256_bytes(digest_payload)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoded-dir", type=Path, required=True)
    parser.add_argument("--content-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    report = build_source_emission_atlas(
        decoded_dir=arguments.decoded_dir,
        content_manifest_path=arguments.content_manifest,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
