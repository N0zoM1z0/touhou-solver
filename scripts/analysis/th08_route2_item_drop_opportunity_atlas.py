#!/usr/bin/env python3
"""Build a pinned Route-2 enemy item/drop opportunity atlas."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from th08_ecl import TIMELINE_OPCODE_NAMES, EclFile, SubInstruction, parse_ecl
from th08_ecl_flow import (
    TIMELINE_SPAWN_OPCODES,
    FlowConfig,
    SubEdge,
    analyze_flow,
)
from th08_ecl_opcodes import opcode_spec
from th08_enemy_item_drop_model import (
    DEFAULT_DROP_SEQUENCE_TYPES,
    ENEMY_DEFEAT_DROP_MODES,
    ENEMY_NO_DROP_MODE,
    ENEMY_POINT_DROP_COUNT_OFFSET,
    ENEMY_POWER_DROP_COUNT_OFFSET,
    ENEMY_PRIMARY_DROP_TYPE_OFFSET,
)
from th08_item_model import (
    ITEM_POINT,
    ITEM_POWER_SMALL,
)


SCHEMA = "th08-route2-item-drop-opportunity-atlas-v1"
TASKBOOK_CARDS = ("COMBAT-KILL-01", "POWER-ROUTE-01")
EXPECTED_CONTENT_MANIFEST_SHA256 = (
    "3a52b6f485ada63c833f77ae8cd1653f469ae4fadeef3c38336a737c7e753ae1"
)
ROUTE_ID = 2
DIFFICULTY_INDEX = 3
DIFFICULTY_MASK = 0x08

ITEM_OPCODES = frozenset({0x8D, 0x8E, 0x8F, 0x90, 0xA8})
DIRECT_ITEM_OPCODES = frozenset({0x8D, 0x8E, 0xA8})
DROP_CONFIGURATION_OPCODES = frozenset({0x8F, 0x90})
DEFEAT_MODE_OPCODE = 0x81
CALLBACK_OPCODES = frozenset({0x88, 0x89})
ROUTE_ITEM_CALLBACK_INDEX = 31
BOSS_CONTROL_OPCODES = frozenset({0x53, 0x7A, 0x83, 0x85, 0x86, 0xB0, 0xB1})

SAME_SOURCE_EDGE_KINDS = frozenset({"call", "interrupt_slot", "aux_vm"})
PROGRAM_ORIGIN_EDGE_KINDS = frozenset(
    {
        "child_spawn",
        "call_with_enemy",
        "enemy_end",
        "health_phase",
        "timeout_phase",
    }
)
ALLOCATION_ORIGIN_KINDS = frozenset({"timeline_spawn", "child_spawn"})


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


class ItemDropOpportunityAtlasError(ValueError):
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
        raise ItemDropOpportunityAtlasError(
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
        raise ItemDropOpportunityAtlasError(
            f"{ecl.path.name} is absent from immutable content manifest"
        )
    if asset.get("decoded_sha256") != ecl.sha256:
        raise ItemDropOpportunityAtlasError(
            f"{ecl.path.name} decoded SHA differs from immutable manifest"
        )


def _operand(
    instruction: SubInstruction,
    index: int,
    name: str,
) -> dict[str, object]:
    if index >= len(instruction.arguments):
        raise ItemDropOpportunityAtlasError(
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


def _item_site(
    *,
    ecl: EclFile,
    subroutine_index: int,
    instruction: SubInstruction,
    reachable_offsets: set[int],
) -> dict[str, object]:
    specification = opcode_spec(instruction.opcode)
    site: dict[str, object] = {
        "symbolic_id": (
            f"{ecl.path.name}:sub:{subroutine_index}:"
            f"0x{instruction.offset:08x}"
        ),
        "subroutine": subroutine_index,
        "file_offset": instruction.offset,
        "local_vm_timer_guard": instruction.time,
        "opcode": instruction.opcode,
        "opcode_hex": f"0x{instruction.opcode:02x}",
        "opcode_name": specification.name,
        "semantic_confidence": specification.confidence,
        "difficulty_mask": instruction.difficulty_mask,
        "parameter_mask": instruction.parameter_mask,
        "argument_words_signed": [
            _signed(argument) for argument in instruction.arguments
        ],
        "route_static_status": (
            "conservative_route_reachable"
            if instruction.offset in reachable_offsets
            else "difficulty_eligible_cfg_unreachable"
        ),
    }
    if instruction.opcode == 0x8D:
        item_type = _operand(instruction, 0, "item_type")
        site["effect"] = {
            "kind": "spawn_one_item",
            "item_type": item_type,
            "position": "enemy_position",
            "motion_state": 0,
        }
    elif instruction.opcode == 0x8E:
        count = _operand(instruction, 0, "count")
        literal = count["literal_value"]
        if literal is not None and int(literal) < 0:
            raise ItemDropOpportunityAtlasError(
                "literal item-bundle count cannot be negative"
            )
        site["effect"] = {
            "kind": "spawn_power_bundle",
            "count": count,
            "below_full_power_composition": (
                {
                    "large_power": int(int(literal) > 0),
                    "small_power": max(0, int(literal) - 1),
                    "point": 0,
                }
                if literal is not None
                else None
            ),
            "full_power_composition": (
                {"large_power": 0, "small_power": 0, "point": int(literal)}
                if literal is not None
                else None
            ),
            "position": "independent_random_square_plus_minus_64",
            "rng_next_unit_calls": (
                2 * int(literal) if literal is not None else None
            ),
        }
    elif instruction.opcode == 0x8F:
        item_type = _operand(instruction, 0, "primary_defeat_item_type")
        site["effect"] = {
            "kind": "set_primary_defeat_item_type",
            "item_type": item_type,
            "enemy_offset": ENEMY_PRIMARY_DROP_TYPE_OFFSET,
        }
    elif instruction.opcode == 0x90:
        point_count = _operand(instruction, 0, "point_item_count")
        power_count = _operand(instruction, 1, "power_item_count")
        for operand in (point_count, power_count):
            literal = operand["literal_value"]
            if literal is not None and int(literal) < 0:
                raise ItemDropOpportunityAtlasError(
                    "literal configured-drop count cannot be negative"
                )
        point_literal = point_count["literal_value"]
        power_literal = power_count["literal_value"]
        site["effect"] = {
            "kind": "set_defeat_item_counts",
            "point_item_count": point_count,
            "power_item_count": power_count,
            "point_count_enemy_offset": ENEMY_POINT_DROP_COUNT_OFFSET,
            "power_count_enemy_offset": ENEMY_POWER_DROP_COUNT_OFFSET,
            "defeat_consumption_order": [
                "primary_item",
                "power_item_count",
                "point_item_count",
            ],
            "configured_position_rng_next_unit_calls": (
                2 * (int(point_literal) + int(power_literal))
                if point_literal is not None and power_literal is not None
                else None
            ),
        }
    elif instruction.opcode == 0xA8:
        count = _operand(instruction, 0, "point_item_count")
        literal = count["literal_value"]
        if literal is not None and int(literal) < 0:
            raise ItemDropOpportunityAtlasError(
                "literal point-item count cannot be negative"
            )
        site["effect"] = {
            "kind": "spawn_point_items",
            "count": count,
            "item_type": ITEM_POINT,
            "position": "independent_random_square_plus_minus_64",
            "rng_next_unit_calls": (
                2 * int(literal) if literal is not None else None
            ),
        }
    else:
        raise ItemDropOpportunityAtlasError(
            f"unsupported item opcode {instruction.opcode:#x}"
        )
    return site


def _defeat_mode_site(
    ecl: EclFile,
    subroutine_index: int,
    instruction: SubInstruction,
) -> dict[str, object]:
    mode = _operand(instruction, 0, "defeat_mode")
    literal = mode["literal_value"]
    if literal is not None and int(literal) not in {
        *ENEMY_DEFEAT_DROP_MODES,
        ENEMY_NO_DROP_MODE,
    }:
        raise ItemDropOpportunityAtlasError(
            f"literal defeat mode {literal} is outside 0..3"
        )
    return {
        "symbolic_id": (
            f"{ecl.path.name}:sub:{subroutine_index}:"
            f"0x{instruction.offset:08x}"
        ),
        "subroutine": subroutine_index,
        "file_offset": instruction.offset,
        "local_vm_timer_guard": instruction.time,
        "parameter_mask": instruction.parameter_mask,
        "mode": mode,
    }


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


def _timeline_origins(ecl: EclFile) -> dict[int, list[dict[str, object]]]:
    origins: dict[int, list[dict[str, object]]] = defaultdict(list)
    for timeline in ecl.timelines:
        for instruction in timeline.instructions:
            if (
                instruction.opcode not in TIMELINE_SPAWN_OPCODES
                or not instruction.difficulty_mask & DIFFICULTY_MASK
            ):
                continue
            root = _signed(instruction.arguments[0])
            origins[root].append(
                {
                    "kind": "timeline_spawn",
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
                }
            )
    return origins


def _edge_origins(
    ecl: EclFile,
    edges: Iterable[SubEdge],
) -> dict[int, list[dict[str, object]]]:
    origins: dict[int, list[dict[str, object]]] = defaultdict(list)
    for edge in edges:
        if edge.kind not in PROGRAM_ORIGIN_EDGE_KINDS:
            continue
        origins[edge.target_subroutine].append(
            {
                "kind": edge.kind,
                "symbolic_id": (
                    f"{ecl.path.name}:sub:{edge.source_subroutine}:"
                    f"0x{edge.source_offset:08x}"
                ),
                "source_subroutine": edge.source_subroutine,
                "source_offset": edge.source_offset,
            }
        )
    return origins


def _program_report(
    *,
    ecl: EclFile,
    root_subroutine: int,
    origins: list[dict[str, object]],
    flow,
    item_site_by_offset: dict[int, dict[str, object]],
) -> dict[str, object]:
    reachable_offsets = set(flow.reachable_instruction_offsets)
    component = _source_owned_subroutines(root_subroutine, flow.edges)
    item_sites = sorted(
        (
            item_site_by_offset[instruction.offset]
            for subroutine in component
            for instruction in ecl.subroutines[subroutine].instructions
            if (
                instruction.offset in reachable_offsets
                and instruction.offset in item_site_by_offset
            )
        ),
        key=lambda row: (int(row["subroutine"]), int(row["file_offset"])),
    )
    defeat_mode_sites = sorted(
        (
            _defeat_mode_site(ecl, subroutine, instruction)
            for subroutine in component
            for instruction in ecl.subroutines[subroutine].instructions
            if (
                instruction.offset in reachable_offsets
                and _eligible(instruction)
                and instruction.opcode == DEFEAT_MODE_OPCODE
            )
        ),
        key=lambda row: (int(row["subroutine"]), int(row["file_offset"])),
    )
    boss_sites = [
        instruction
        for subroutine in component
        for instruction in ecl.subroutines[subroutine].instructions
        if (
            instruction.offset in reachable_offsets
            and _eligible(instruction)
            and instruction.opcode in BOSS_CONTROL_OPCODES
        )
    ]
    callback_31_sites = [
        instruction
        for subroutine in component
        for instruction in ecl.subroutines[subroutine].instructions
        if (
            instruction.offset in reachable_offsets
            and _eligible(instruction)
            and instruction.opcode in CALLBACK_OPCODES
            and not instruction.parameter_mask & 1
            and _signed(instruction.arguments[0]) == ROUTE_ITEM_CALLBACK_INDEX
        )
    ]
    literal_modes = {
        int(site["mode"]["literal_value"])
        for site in defeat_mode_sites
        if site["mode"]["literal_value"] is not None
    }
    dynamic_mode = any(
        bool(site["mode"]["dynamic"]) for site in defeat_mode_sites
    )
    possible_modes = sorted({0, *literal_modes})
    origin_kinds = sorted({str(origin["kind"]) for origin in origins})
    allocation_origin = any(
        kind in ALLOCATION_ORIGIN_KINDS for kind in origin_kinds
    )
    boss_possible = bool(boss_sites)
    primary_override_sites = [
        site for site in item_sites if int(site["opcode"]) == 0x8F
    ]
    direct_sites = [
        site
        for site in item_sites
        if int(site["opcode"]) in DIRECT_ITEM_OPCODES
    ]
    count_sites = [
        site for site in item_sites if int(site["opcode"]) == 0x90
    ]
    configured_power_counts = sorted(
        {
            int(site["effect"]["power_item_count"]["literal_value"])
            for site in count_sites
            if site["effect"]["power_item_count"]["literal_value"] is not None
        }
    )
    direct_bundle_counts = sorted(
        {
            int(site["effect"]["count"]["literal_value"])
            for site in direct_sites
            if (
                int(site["opcode"]) == 0x8E
                and site["effect"]["count"]["literal_value"] is not None
            )
        }
    )
    ordinary_default_primary_candidate = bool(
        allocation_origin
        and not boss_possible
        and not primary_override_sites
        and not dynamic_mode
        and any(mode in ENEMY_DEFEAT_DROP_MODES for mode in possible_modes)
    )
    return {
        "program_id": f"{ecl.path.name}:root:{root_subroutine}",
        "source_emission_join_key": {
            "route_ecl_sha256": ecl.sha256,
            "root_subroutine": root_subroutine,
        },
        "root_subroutine": root_subroutine,
        "origins": sorted(
            origins,
            key=lambda row: (
                str(row["kind"]),
                int(row["file_offset"])
                if "file_offset" in row
                else int(row["source_offset"]),
            ),
        ),
        "origin_kinds": origin_kinds,
        "source_owned_subroutines": list(component),
        "item_sites": item_sites,
        "defeat_mode_sites": defeat_mode_sites,
        "classification": {
            "allocation_origin": allocation_origin,
            "boss_control_possible": boss_possible,
            "ordinary_compatible": not boss_possible,
            "direct_item_site_count": len(direct_sites),
            "drop_configuration_site_count": len(item_sites)
            - len(direct_sites),
            "route_item_callback_31_site_count": len(callback_31_sites),
            "possible_defeat_modes": possible_modes,
            "dynamic_defeat_mode": dynamic_mode,
            "mode3_drop_bypass_possible": ENEMY_NO_DROP_MODE in possible_modes,
            "primary_drop_override_site_count": len(primary_override_sites),
            "ordinary_default_small_power_on_eligible_hp_defeat_candidate": (
                ordinary_default_primary_candidate
            ),
            "configured_extra_power_count_candidates": configured_power_counts,
            "direct_power_bundle_count_candidates": direct_bundle_counts,
            "runtime_end_and_execution_join_required": True,
        },
    }


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
    all_item_sites = [
        _item_site(
            ecl=ecl,
            subroutine_index=subroutine_index,
            instruction=instruction,
            reachable_offsets=reachable_offsets,
        )
        for subroutine_index, subroutine in enumerate(ecl.subroutines)
        for instruction in subroutine.instructions
        if _eligible(instruction) and instruction.opcode in ITEM_OPCODES
    ]
    item_site_by_offset = {
        int(site["file_offset"]): site for site in all_item_sites
    }
    timeline_origins = _timeline_origins(ecl)
    edge_origins = _edge_origins(ecl, flow.edges)
    roots = sorted({*timeline_origins, *edge_origins})
    programs = [
        _program_report(
            ecl=ecl,
            root_subroutine=root,
            origins=[*timeline_origins.get(root, ()), *edge_origins.get(root, ())],
            flow=flow,
            item_site_by_offset=item_site_by_offset,
        )
        for root in roots
    ]
    reachable_item_sites = [
        site
        for site in all_item_sites
        if site["route_static_status"] == "conservative_route_reachable"
    ]
    reachable_histogram = Counter(
        str(site["opcode_hex"]) for site in reachable_item_sites
    )
    mapped_offsets = {
        int(site["file_offset"])
        for program in programs
        for site in program["item_sites"]
    }
    unmapped = sorted(
        int(site["file_offset"])
        for site in reachable_item_sites
        if int(site["file_offset"]) not in mapped_offsets
    )
    if unmapped:
        raise ItemDropOpportunityAtlasError(
            f"{ecl.path.name} has route-reachable item sites outside program "
            f"roots: {unmapped}"
        )
    classifications = [program["classification"] for program in programs]
    timeline_spawn_count = sum(
        len(origins) for origins in timeline_origins.values()
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
            "unresolved_dynamic_subroutine_edges": [
                list(row) for row in flow.unresolved_dynamic_subroutine_edges
            ],
        },
        "summary": {
            "timeline_spawn_instance_count": timeline_spawn_count,
            "program_root_count": len(programs),
            "allocation_program_count": sum(
                bool(row["allocation_origin"]) for row in classifications
            ),
            "ordinary_compatible_program_count": sum(
                bool(row["ordinary_compatible"]) for row in classifications
            ),
            "ordinary_default_small_power_candidate_program_count": sum(
                bool(
                    row[
                        "ordinary_default_small_power_on_eligible_hp_defeat_candidate"
                    ]
                )
                for row in classifications
            ),
            "eligible_item_site_count": len(all_item_sites),
            "reachable_item_site_count": len(reachable_item_sites),
            "unreachable_item_site_count": len(all_item_sites)
            - len(reachable_item_sites),
            "reachable_item_opcode_histogram": dict(
                sorted(reachable_histogram.items())
            ),
            "dynamic_item_operand_site_count": sum(
                bool(int(site["parameter_mask"])) for site in reachable_item_sites
            ),
            "reachable_primary_drop_override_site_count": sum(
                int(site["opcode"]) == 0x8F for site in reachable_item_sites
            ),
        },
        "item_sites": all_item_sites,
        "programs": programs,
    }


def build_item_drop_opportunity_atlas(
    *,
    decoded_dir: Path,
    content_manifest_path: Path,
) -> dict[str, object]:
    manifest_sha256 = _sha256_path(content_manifest_path)
    if manifest_sha256 != EXPECTED_CONTENT_MANIFEST_SHA256:
        raise ItemDropOpportunityAtlasError(
            "immutable content manifest SHA differs from accepted checkpoint"
        )
    manifest = json.loads(content_manifest_path.read_text(encoding="utf-8"))
    assets = _asset_index(manifest)
    stages = [
        _stage_report(decoded_dir=decoded_dir, stage=stage, assets=assets)
        for stage in STAGES
    ]
    summaries = [stage["summary"] for stage in stages]
    histogram = Counter()
    for summary in summaries:
        histogram.update(summary["reachable_item_opcode_histogram"])
    integer_keys = (
        "timeline_spawn_instance_count",
        "program_root_count",
        "allocation_program_count",
        "ordinary_compatible_program_count",
        "ordinary_default_small_power_candidate_program_count",
        "eligible_item_site_count",
        "reachable_item_site_count",
        "unreachable_item_site_count",
        "dynamic_item_operand_site_count",
        "reachable_primary_drop_override_site_count",
    )
    result: dict[str, object] = {
        "schema": SCHEMA,
        "taskbook_cards": list(TASKBOOK_CARDS),
        "status": "static_opportunity_index_runtime_join_required",
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
        "native_semantics": {
            "template_defaults": {
                "primary_defeat_item_type": ITEM_POWER_SMALL,
                "point_item_count": 0,
                "power_item_count": 0,
                "evidence": (
                    "enemy manager/template zero initialization at 0x00429E1F "
                    "and template copy at 0x0042A55D/0x0042A6FD"
                ),
            },
            "defeat_drop_helper": {
                "address": "0x0042BEA0",
                "invoked_modes": sorted(ENEMY_DEFEAT_DROP_MODES),
                "bypassed_mode": ENEMY_NO_DROP_MODE,
                "request_order": [
                    "primary_item",
                    "power_item_count",
                    "point_item_count",
                ],
                "no_bomb_primary_motion_state": 0,
                "configured_count_motion_state": 0,
                "primary_minus_one_schedule": {
                    "period": 3,
                    "table": list(DEFAULT_DROP_SEQUENCE_TYPES),
                },
                "configured_count_reset_after_helper": True,
            },
            "power_focus_coupling": {
                "ordinary_template_primary_request": ITEM_POWER_SMALL,
                "route2_low_power_unfocused_auto_homing": False,
                "route2_low_power_focused_auto_homing_above_line": True,
                "boundary": (
                    "item spawn does not prove allocation, pickup, Power gain, "
                    "or survival-feasible collection"
                ),
            },
        },
        "summary": {
            **{
                key: sum(int(summary[key]) for summary in summaries)
                for key in integer_keys
            },
            "reachable_item_opcode_histogram": dict(sorted(histogram.items())),
        },
        "stages": stages,
        "authority": {
            "shipped_template_and_handler_semantics": True,
            "shipped_content_identity": True,
            "route_difficulty_cfg_overapproximation": True,
            "literal_item_configuration_inventory": True,
            "runtime_instruction_execution": False,
            "runtime_enemy_generation_or_end_reason": False,
            "successful_item_allocation_or_pickup": False,
            "causal_power_or_later_combat_benefit": False,
            "planner_or_action_authority": False,
            "physical_trial_run": False,
        },
        "next_gate": {
            "join_key": (
                "content digest + stage + gameplay epoch + enemy generation + "
                "root subroutine + main/aux VM PC + defeat mode + drop fields"
            ),
            "required_measurements": [
                "ordered HP defeat versus scripted/offscreen retirement",
                "same-update primary/count fields before helper execution",
                "item allocation identity and randomized position",
                "pickup identity and Power threshold crossing",
                "survival-feasible action and later damage/kill consequence",
            ],
            "selection_use": (
                "prefer immutable roots around ordinary allocation programs "
                "with configured extra Power counts or dense emitter value; "
                "never infer a pickup from static availability"
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
    report = build_item_drop_opportunity_atlas(
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
