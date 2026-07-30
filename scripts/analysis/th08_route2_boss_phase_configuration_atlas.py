#!/usr/bin/env python3
"""Build a pinned Route-2 Boss HP/timeout configuration graph."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from th08_ecl import EclFile, SubInstruction, parse_ecl
from th08_ecl_flow import (
    TIMELINE_SPAWN_OPCODES,
    FlowConfig,
    SubEdge,
    analyze_flow,
)
from th08_ecl_opcodes import opcode_spec


SCHEMA = "th08-route2-boss-phase-configuration-atlas-v1"
TASKBOOK_CARD = "WS-H"
EXPECTED_CONTENT_MANIFEST_SHA256 = (
    "3a52b6f485ada63c833f77ae8cd1653f469ae4fadeef3c38336a737c7e753ae1"
)
ROUTE_ID = 2
DIFFICULTY_INDEX = 3
DIFFICULTY_MASK = 0x08
PHASE_CONTROL_OPCODES = frozenset({0x83, 0x84, 0x85, 0x86})
BOSS_REGISTRATION_OPCODE = 0x7F
SPELL_START_OPCODE = 0x7A
SUCCESSOR_WRITE_GATE = (
    "engine_flags_bit14_clear_or_mode_bits7_8_zero"
)
SAME_ENEMY_PROGRAM_EDGES = frozenset(
    {
        "call",
        "interrupt_slot",
        "aux_vm",
        "enemy_end",
        "health_phase",
        "timeout_phase",
    }
)


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


class BossPhaseConfigurationAtlasError(ValueError):
    """Raised when immutable or structural authority cannot be preserved."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def _eligible(instruction: SubInstruction) -> bool:
    return bool(instruction.difficulty_mask & DIFFICULTY_MASK)


def _asset_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise BossPhaseConfigurationAtlasError(
            "content manifest assets are missing"
        )
    return {
        str(asset["name"]): asset
        for asset in assets
        if isinstance(asset, dict) and "name" in asset
    }


def _validate_ecl(ecl: EclFile, assets: dict[str, dict[str, Any]]) -> None:
    asset = assets.get(ecl.path.name)
    if asset is None:
        raise BossPhaseConfigurationAtlasError(
            f"{ecl.path.name} is absent from immutable content manifest"
        )
    if asset.get("decoded_sha256") != ecl.sha256:
        raise BossPhaseConfigurationAtlasError(
            f"{ecl.path.name} decoded SHA differs from immutable manifest"
        )


def _operand(
    instruction: SubInstruction,
    index: int,
    name: str,
) -> dict[str, object]:
    if index >= len(instruction.arguments):
        raise BossPhaseConfigurationAtlasError(
            f"opcode {instruction.opcode:#x} at {instruction.offset:#x} "
            f"omits {name}"
        )
    dynamic = bool(instruction.parameter_mask & (1 << index))
    raw_signed = _signed(instruction.arguments[index])
    return {
        "name": name,
        "index": index,
        "dynamic": dynamic,
        "raw_signed": raw_signed,
        "literal_value": None if dynamic else raw_signed,
    }


def _phase_site(
    ecl: EclFile,
    subroutine_index: int,
    instruction: SubInstruction,
) -> dict[str, object]:
    specification = opcode_spec(instruction.opcode)
    site: dict[str, object] = {
        "symbolic_id": (
            f"{ecl.path.name}:sub:{subroutine_index}:"
            f"offset:{instruction.offset:#x}"
        ),
        "subroutine": subroutine_index,
        "offset": instruction.offset,
        "offset_hex": f"{instruction.offset:#x}",
        "local_vm_time": instruction.time,
        "opcode": instruction.opcode,
        "opcode_hex": f"{instruction.opcode:#04x}",
        "opcode_name": specification.name,
        "difficulty_mask": instruction.difficulty_mask,
        "parameter_mask": instruction.parameter_mask,
        "argument_words_signed": [
            _signed(argument) for argument in instruction.arguments
        ],
    }
    if instruction.opcode == 0x83:
        health = _operand(instruction, 0, "health")
        value = health["literal_value"]
        if value is not None and int(value) <= 0:
            raise BossPhaseConfigurationAtlasError(
                "literal set-health value must be positive"
            )
        site["effect"] = {
            "kind": "set_health",
            "health": health,
        }
    elif instruction.opcode == 0x84:
        timer = _operand(instruction, 0, "timer_current")
        site["effect"] = {
            "kind": "set_timer_current",
            "timer_current": timer,
        }
    elif instruction.opcode == 0x85:
        slot = _operand(instruction, 0, "health_transition_slot")
        threshold = _operand(instruction, 1, "health_threshold")
        target = _operand(instruction, 2, "successor_subroutine")
        slot_value = slot["literal_value"]
        threshold_value = threshold["literal_value"]
        if slot_value is not None and not 0 <= int(slot_value) < 4:
            raise BossPhaseConfigurationAtlasError(
                "literal health-transition slot is outside 0..3"
            )
        if threshold_value is not None and int(threshold_value) <= 0:
            raise BossPhaseConfigurationAtlasError(
                "literal health threshold must be positive"
            )
        site["effect"] = {
            "kind": "set_health_phase_transition",
            "slot": slot,
            "threshold": threshold,
            "successor_subroutine": target,
        }
    elif instruction.opcode == 0x86:
        timeout = _operand(instruction, 0, "timeout_frame")
        target = _operand(instruction, 1, "successor_subroutine")
        timeout_value = timeout["literal_value"]
        if timeout_value is not None and int(timeout_value) <= 0:
            raise BossPhaseConfigurationAtlasError(
                "literal timeout must be positive"
            )
        site["effect"] = {
            "kind": "set_timeout_phase_transition",
            "timeout_frame": timeout,
            "successor_subroutine": target,
        }
    else:
        raise BossPhaseConfigurationAtlasError(
            f"unsupported phase-control opcode {instruction.opcode:#x}"
        )
    return site


def _program_subroutines(
    root_subroutine: int,
    edges: Iterable[SubEdge],
) -> tuple[int, ...]:
    outgoing: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if edge.kind in SAME_ENEMY_PROGRAM_EDGES:
            outgoing[edge.source_subroutine].add(edge.target_subroutine)
    seen: set[int] = set()
    pending = deque((root_subroutine,))
    while pending:
        current = pending.popleft()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(sorted(outgoing.get(current, ())))
    return tuple(sorted(seen))


def _spawn_instances(ecl: EclFile) -> dict[int, list[dict[str, object]]]:
    instances: dict[int, list[dict[str, object]]] = defaultdict(list)
    for timeline in ecl.timelines:
        for instruction in timeline.instructions:
            if (
                instruction.opcode not in TIMELINE_SPAWN_OPCODES
                or not instruction.difficulty_mask & DIFFICULTY_MASK
            ):
                continue
            if not instruction.arguments:
                raise BossPhaseConfigurationAtlasError(
                    f"timeline spawn at {instruction.offset:#x} has no root"
                )
            root = _signed(instruction.arguments[0])
            instances[root].append(
                {
                    "symbolic_id": (
                        f"{ecl.path.name}:timeline:{timeline.index}:"
                        f"offset:{instruction.offset:#x}"
                    ),
                    "timeline": timeline.index,
                    "offset": instruction.offset,
                    "offset_hex": f"{instruction.offset:#x}",
                    "timeline_time": instruction.time,
                    "opcode": instruction.opcode,
                    "difficulty_mask": instruction.difficulty_mask,
                }
            )
    return instances


def _relation(
    health_targets: set[int],
    timeout_targets: set[int],
) -> str:
    if not health_targets:
        return "timeout_only"
    if not timeout_targets:
        return "health_only"
    if health_targets == timeout_targets:
        return "same_successor_set"
    if health_targets & timeout_targets:
        return "partially_shared_successors"
    return "disjoint_successors"


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
    reachable_offsets = set(flow.reachable_instruction_offsets)
    reachable_subroutines = set(flow.reachable_subroutines)
    eligible_phase_instructions: list[tuple[int, SubInstruction]] = []
    reachable_phase_instructions: list[tuple[int, SubInstruction]] = []
    boss_registration_subroutines: set[int] = set()
    spell_start_subroutines: set[int] = set()
    for subroutine in ecl.subroutines:
        for instruction in subroutine.instructions:
            if not _eligible(instruction):
                continue
            if (
                instruction.opcode == BOSS_REGISTRATION_OPCODE
                and instruction.offset in reachable_offsets
            ):
                boss_registration_subroutines.add(subroutine.index)
            if (
                instruction.opcode == SPELL_START_OPCODE
                and instruction.offset in reachable_offsets
            ):
                spell_start_subroutines.add(subroutine.index)
            if instruction.opcode not in PHASE_CONTROL_OPCODES:
                continue
            eligible_phase_instructions.append((subroutine.index, instruction))
            if instruction.offset in reachable_offsets:
                reachable_phase_instructions.append(
                    (subroutine.index, instruction)
                )

    sites = [
        _phase_site(ecl, subroutine_index, instruction)
        for subroutine_index, instruction in reachable_phase_instructions
    ]
    sites_by_subroutine: dict[int, list[dict[str, object]]] = defaultdict(list)
    for site in sites:
        sites_by_subroutine[int(site["subroutine"])].append(site)

    phase_subroutines: list[dict[str, object]] = []
    transition_edges: list[dict[str, object]] = []
    relation_counts: Counter[str] = Counter()
    for subroutine_index in sorted(sites_by_subroutine):
        sub_sites = sorted(
            sites_by_subroutine[subroutine_index],
            key=lambda site: int(site["offset"]),
        )
        health_targets: set[int] = set()
        timeout_targets: set[int] = set()
        for site in sub_sites:
            effect = site["effect"]
            assert isinstance(effect, dict)
            kind = effect["kind"]
            if kind == "set_health_phase_transition":
                target_operand = effect["successor_subroutine"]
                assert isinstance(target_operand, dict)
                target = target_operand["literal_value"]
                if target is not None:
                    health_targets.add(int(target))
                    transition_edges.append(
                        {
                            "kind": "health_phase",
                            "source_subroutine": subroutine_index,
                            "source_site": site["symbolic_id"],
                            "slot": effect["slot"],
                            "threshold": effect["threshold"],
                            "target_subroutine": int(target),
                            "successor_write_requires": (
                                SUCCESSOR_WRITE_GATE
                            ),
                        }
                    )
            elif kind == "set_timeout_phase_transition":
                target_operand = effect["successor_subroutine"]
                assert isinstance(target_operand, dict)
                target = target_operand["literal_value"]
                if target is not None:
                    timeout_targets.add(int(target))
                    transition_edges.append(
                        {
                            "kind": "timeout_phase",
                            "source_subroutine": subroutine_index,
                            "source_site": site["symbolic_id"],
                            "timeout_frame": effect["timeout_frame"],
                            "target_subroutine": int(target),
                            "successor_write_requires": (
                                SUCCESSOR_WRITE_GATE
                            ),
                        }
                    )
        relation = _relation(health_targets, timeout_targets)
        if health_targets or timeout_targets:
            relation_counts[relation] += 1
        phase_subroutines.append(
            {
                "subroutine": subroutine_index,
                "sites": sub_sites,
                "health_successor_subroutines": sorted(health_targets),
                "timeout_successor_subroutines": sorted(timeout_targets),
                "health_timeout_successor_relation": relation,
                "boss_registration_reachable": (
                    subroutine_index in boss_registration_subroutines
                ),
                "spell_start_reachable": (
                    subroutine_index in spell_start_subroutines
                ),
            }
        )

    spawns_by_root = _spawn_instances(ecl)
    root_programs: list[dict[str, object]] = []
    for root in flow.root_subroutines:
        component = _program_subroutines(root, flow.edges)
        component_sites = [
            site
            for subroutine_index in component
            for site in sites_by_subroutine.get(subroutine_index, ())
        ]
        if not component_sites:
            continue
        component_set = set(component)
        root_programs.append(
            {
                "root_subroutine": root,
                "spawn_instances": spawns_by_root.get(root, []),
                "same_enemy_phase_program_subroutines": list(component),
                "phase_control_site_count": len(component_sites),
                "phase_subroutines": sorted(
                    {
                        int(site["subroutine"])
                        for site in component_sites
                    }
                ),
                "boss_registration_possible": bool(
                    component_set & boss_registration_subroutines
                ),
                "spell_start_possible": bool(
                    component_set & spell_start_subroutines
                ),
            }
        )

    dynamic_sites = [
        site for site in sites if int(site["parameter_mask"]) != 0
    ]
    effect_counts = Counter(
        str(site["effect"]["kind"])
        for site in sites
        if isinstance(site["effect"], dict)
    )
    return {
        "key": stage.key,
        "label": stage.label,
        "route_stage_index": stage.route_stage_index,
        "ecl": {
            "name": ecl.path.name,
            "sha256": ecl.sha256,
            "subroutine_count": len(ecl.subroutines),
            "timeline_count": len(ecl.timelines),
        },
        "flow": {
            "root_subroutine_count": len(flow.root_subroutines),
            "reachable_subroutine_count": len(reachable_subroutines),
            "unresolved_dynamic_subroutine_edges": [
                {
                    "source_subroutine": source,
                    "source_offset": offset,
                    "opcode": opcode,
                }
                for source, offset, opcode in (
                    flow.unresolved_dynamic_subroutine_edges
                )
            ],
            "folded_branch_count": flow.folded_branch_count,
            "conservative_branch_count": flow.conservative_branch_count,
        },
        "phase_subroutines": phase_subroutines,
        "transition_edges": sorted(
            transition_edges,
            key=lambda edge: (
                int(edge["source_subroutine"]),
                str(edge["kind"]),
                int(edge["target_subroutine"]),
                str(edge["source_site"]),
            ),
        ),
        "root_programs": root_programs,
        "summary": {
            "eligible_phase_control_site_count": len(
                eligible_phase_instructions
            ),
            "reachable_phase_control_site_count": len(sites),
            "eligible_unreachable_phase_control_site_count": (
                len(eligible_phase_instructions) - len(sites)
            ),
            "phase_subroutine_count": len(phase_subroutines),
            "transition_edge_count": len(transition_edges),
            "boss_root_program_count": len(root_programs),
            "boss_root_spawn_instance_count": sum(
                len(program["spawn_instances"]) for program in root_programs
            ),
            "dynamic_phase_control_site_count": len(dynamic_sites),
            "health_timeout_relation_counts": dict(
                sorted(relation_counts.items())
            ),
            "effect_counts": dict(sorted(effect_counts.items())),
        },
    }


def build_boss_phase_configuration_atlas(
    *,
    decoded_dir: Path,
    content_manifest_path: Path,
) -> dict[str, object]:
    manifest_sha256 = _sha256_path(content_manifest_path)
    if manifest_sha256 != EXPECTED_CONTENT_MANIFEST_SHA256:
        raise BossPhaseConfigurationAtlasError(
            "immutable content manifest SHA differs from accepted checkpoint"
        )
    manifest = json.loads(content_manifest_path.read_text(encoding="utf-8"))
    assets = _asset_index(manifest)
    stages = [
        _stage_report(decoded_dir=decoded_dir, stage=stage, assets=assets)
        for stage in STAGES
    ]
    summaries = [stage["summary"] for stage in stages]
    effect_counts: Counter[str] = Counter()
    relation_counts: Counter[str] = Counter()
    for summary in summaries:
        effect_counts.update(summary["effect_counts"])
        relation_counts.update(summary["health_timeout_relation_counts"])
    aggregate_keys = (
        "eligible_phase_control_site_count",
        "reachable_phase_control_site_count",
        "eligible_unreachable_phase_control_site_count",
        "phase_subroutine_count",
        "transition_edge_count",
        "boss_root_program_count",
        "boss_root_spawn_instance_count",
        "dynamic_phase_control_site_count",
    )
    result: dict[str, object] = {
        "schema": SCHEMA,
        "taskbook_card": TASKBOOK_CARD,
        "status": "static_route_configuration_runtime_execution_required",
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
            "content_set_sha256": manifest["content_scope"][
                "content_set_sha256"
            ],
            "executable_sha256": manifest["shipped_identity"][
                "executable_sha256"
            ],
        },
        "summary": {
            **{
                key: sum(int(summary[key]) for summary in summaries)
                for key in aggregate_keys
            },
            "effect_counts": dict(sorted(effect_counts.items())),
            "health_timeout_relation_counts": dict(
                sorted(relation_counts.items())
            ),
        },
        "stages": stages,
        "native_transition_order": {
            "manager_order": (
                "strict current_hp < threshold and integer timeout checks run "
                "before later same-update player-shot HP subtraction"
            ),
            "health_priority": (
                "health transitions scan slots 0..3 and win over timeout; "
                "multiple crossed slots may be consumed in one update"
            ),
            "timeout_restore": (
                "timeout restores the greatest positive retained health "
                "threshold before starting its configured successor"
            ),
            "pending_overshoot": (
                "post-damage HP may sit below a retained threshold until the "
                "next eligible manager update"
            ),
        },
        "native_ecl_write_semantics": {
            "opcode_0x83": (
                "arg0 writes max HP +0x2e00, current HP +0x2dfc, and "
                "phase-start HP +0x2e04; other conditional side effects are "
                "outside this atlas"
            ),
            "opcode_0x84": (
                "arg0 calls timer_set_elapsed on phase timer +0x2e14"
            ),
            "opcode_0x85": (
                "arg0 selects slot; arg1 always writes threshold "
                "+0x3358[slot]; arg2 writes successor +0x3368[slot] only "
                "on the full-configuration engine-mode branch"
            ),
            "opcode_0x86": (
                "arg0 always writes timeout +0x3378 and resets phase timer "
                "+0x2e14; arg1 writes successor +0x337c only on the "
                "full-configuration engine-mode branch"
            ),
            "successor_write_gate": {
                "symbolic_name": SUCCESSOR_WRITE_GATE,
                "full_configuration_when": (
                    "(engine_flags & 0x4000) == 0 or "
                    "((engine_flags >> 7) & 0x3) == 0"
                ),
                "retained_successor_when_suppressed": (
                    "(engine_flags & 0x4000) != 0 and "
                    "((engine_flags >> 7) & 0x3) != 0"
                ),
            },
        },
        "static_limit": {
            "local_vm_time": (
                "instruction-local time is not an absolute manager-frame "
                "phase deadline"
            ),
            "control_flow": (
                "reachable sites and literal transition edges are a "
                "route/difficulty, full-configuration-mode CFG "
                "overapproximation; branch alternatives are not simultaneous "
                "runtime writes"
            ),
            "engine_mode": (
                "when the successor-write gate is false, opcodes 0x85 and "
                "0x86 retain the previous successor register; ECL content "
                "alone cannot identify that runtime successor"
            ),
            "successor_effect": (
                "literal successor identity is exact content, but actual "
                "execution and resulting ECL state require an immutable "
                "runtime root"
            ),
        },
        "authority": {
            "shipped_content_identity": True,
            "route_difficulty_cfg_overapproximation": True,
            "literal_phase_configuration_inventory": True,
            "native_transition_recurrence_join": True,
            "full_configuration_mode_cfg_overapproximation": True,
            "runtime_instruction_execution": False,
            "runtime_phase_sequence": False,
            "unconditional_runtime_successor_registry": False,
            "physical_phase_duration_or_damage_benefit": False,
            "planner_or_action_authority": False,
            "physical_trial_run": False,
        },
        "next_gate": {
            "join_key": (
                "content digest + stage + gameplay epoch + Boss pointer + "
                "main VM instruction pointer + threshold/timeout registry"
            ),
            "required_measurements": [
                "executed phase-control instruction and successor",
                "pre/post HP registry and integer timer",
                "pending health/timeout completion cause",
                "survival-equivalent damage action and exposure delta",
            ],
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
    report = build_boss_phase_configuration_atlas(
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
