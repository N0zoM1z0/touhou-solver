#!/usr/bin/env python3
"""Build a Lunatic Route-2 symbolic ECL event atlas for mandatory stages."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from th08_ecl import (
    TIMELINE_OPCODE_NAMES,
    EclFile,
    SubInstruction,
    TimelineInstruction,
    parse_ecl,
)
from th08_ecl_callback_model import CALLBACK_SPECS
from th08_ecl_flow import FlowConfig, analyze_flow
from th08_ecl_opcodes import opcode_spec


SCHEMA = "th08-mandatory-event-atlas-v1"
TASKBOOK_CARD = "CONTENT-02"
EXPECTED_CONTENT_MANIFEST_SHA256 = (
    "3a52b6f485ada63c833f77ae8cd1653f469ae4fadeef3c38336a737c7e753ae1"
)
ROUTE_ID = 2
DIFFICULTY_INDEX = 3
DIFFICULTY_MASK = 0x08
TIMELINE_UNKNOWN_OPCODES = frozenset({0x06, 0x09})


@dataclass(frozen=True)
class StageSpec:
    key: str
    label: str
    route_stage_index: int
    ecl_name: str
    spell_practice_ecl_name: str


STAGES = (
    StageSpec("stage3", "Stage 3", 2, "ecldata3.ecl", "ecldata3sp.ecl"),
    StageSpec(
        "stage4a",
        "Stage 4A / Reimu",
        3,
        "ecldata4a.ecl",
        "ecldata4asp.ecl",
    ),
    StageSpec("stage5", "Stage 5", 5, "ecldata5.ecl", "ecldata5sp.ecl"),
    StageSpec(
        "final_b",
        "Final B / Kaguya",
        7,
        "ecldata7.ecl",
        "ecldata7sp.ecl",
    ),
)

SUB_EVENT_CLASSES = {
    "indexed_enemy_reference": frozenset(range(0x56, 0x5A)),
    "enemy_birth": frozenset(range(0x5A, 0x5F)),
    "forced_enemy_hp_zero": frozenset({0x5F}),
    "hostile_fire": frozenset(range(0x60, 0x6E)),
    "emission_origin": frozenset({0x6E}),
    "bullet_transform": frozenset({0x6F}),
    "bullet_cancel": frozenset({0x70, 0xA1, 0xA2}),
    "laser_lifecycle": frozenset(
        {*range(0x72, 0x7A), 0x9A, 0xA7, 0xAA, 0xAB, 0xAC}
    ),
    "spell_lifecycle": frozenset({0x7A, 0x7B, 0x9B, 0xB0, 0xB8}),
    "phase_control": frozenset(
        {0x53, 0x7F, *range(0x81, 0x88), 0x94, 0x99, 0x9E, 0xA0, 0xB1}
    ),
    "callback": frozenset({0x88, 0x89}),
    "item_resource": frozenset({0x5F, *range(0x8D, 0x91), 0xA8}),
    "scheduler_gate": frozenset({0xAD, 0xAF}),
    "movement_redirect": frozenset({*range(0x3F, 0x4D), 0xB2}),
}

TIMELINE_EVENT_CLASSES = {
    "timeline_enemy_birth": frozenset(
        {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0C, 0x0F}
    ),
    "timeline_wait_or_marker": frozenset({0x07, 0x0A, 0x0D, 0x0E}),
    "timeline_control": frozenset({0x08, 0x10}),
    "timeline_unknown": TIMELINE_UNKNOWN_OPCODES,
}


class EventAtlasError(ValueError):
    """Raised when the atlas cannot preserve its immutable authority."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def _event_classes(scope: str, opcode: int) -> tuple[str, ...]:
    mapping = (
        SUB_EVENT_CLASSES if scope == "subroutine" else TIMELINE_EVENT_CLASSES
    )
    return tuple(
        name for name, opcodes in mapping.items() if opcode in opcodes
    )


def _argument_words(arguments: tuple[int, ...]) -> list[str]:
    return [f"0x{word:08x}" for word in arguments]


def _callback_detail(instruction: SubInstruction) -> dict[str, object]:
    if instruction.opcode not in {0x88, 0x89}:
        return {}
    dynamic = bool(instruction.parameter_mask & 0x01)
    index = None if dynamic else _signed(instruction.arguments[0])
    if instruction.opcode == 0x88:
        action = "invoke"
    elif index is not None and index < 0:
        action = "clear_per_frame"
    else:
        action = "install_per_frame"
    result: dict[str, object] = {
        "action": action,
        "callback_index": index,
        "callback_index_dynamic": dynamic,
    }
    if index is not None and index >= 0:
        if index >= len(CALLBACK_SPECS):
            raise EventAtlasError(
                f"callback index {index} is outside the native table"
            )
        callback = CALLBACK_SPECS[index]
        result.update(
            {
                "callback_address": f"0x{callback.address:08x}",
                "callback_name": callback.name,
                "callback_confidence": callback.confidence,
            }
        )
    return result


def _sub_occurrence(
    *,
    ecl: EclFile,
    subroutine_index: int,
    instruction: SubInstruction,
    reachable_offsets: set[int],
) -> dict[str, object]:
    specification = opcode_spec(instruction.opcode)
    return {
        "symbolic_id": (
            f"{ecl.path.name}:sub:{subroutine_index}:"
            f"0x{instruction.offset:08x}"
        ),
        "scope": "subroutine",
        "scope_index": subroutine_index,
        "file_offset": instruction.offset,
        "time": instruction.time,
        "opcode": instruction.opcode,
        "opcode_hex": f"0x{instruction.opcode:02x}",
        "opcode_name": specification.name,
        "opcode_category": specification.category,
        "semantic_confidence": specification.confidence,
        "event_classes": list(
            _event_classes("subroutine", instruction.opcode)
        ),
        "difficulty_mask": instruction.difficulty_mask,
        "parameter_mask": instruction.parameter_mask,
        "size": instruction.size,
        "argument_words": _argument_words(instruction.arguments),
        "route_static_status": (
            "conservative_route_reachable"
            if instruction.offset in reachable_offsets
            else "difficulty_eligible_cfg_unreachable"
        ),
        "callback": _callback_detail(instruction),
    }


def _timeline_confidence(opcode: int) -> str:
    return "unknown" if opcode in TIMELINE_UNKNOWN_OPCODES else "observed"


def _timeline_occurrence(
    *,
    ecl: EclFile,
    timeline_index: int,
    instruction: TimelineInstruction,
) -> dict[str, object]:
    name = TIMELINE_OPCODE_NAMES.get(
        instruction.opcode,
        f"unknown_timeline_{instruction.opcode:02x}",
    )
    return {
        "symbolic_id": (
            f"{ecl.path.name}:timeline:{timeline_index}:"
            f"0x{instruction.offset:08x}"
        ),
        "scope": "timeline",
        "scope_index": timeline_index,
        "file_offset": instruction.offset,
        "time": instruction.time,
        "opcode": instruction.opcode,
        "opcode_hex": f"0x{instruction.opcode:02x}",
        "opcode_name": name,
        "opcode_category": "timeline",
        "semantic_confidence": _timeline_confidence(instruction.opcode),
        "event_classes": list(
            _event_classes("timeline", instruction.opcode)
        ),
        "difficulty_mask": instruction.difficulty_mask,
        "size": instruction.size,
        "argument_words": _argument_words(instruction.arguments),
        "route_static_status": "difficulty_eligible_timeline_schedule_candidate",
    }


def _content_assets(
    manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise EventAtlasError("content manifest assets are missing")
    result: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(
            asset.get("name"),
            str,
        ):
            raise EventAtlasError("content manifest contains malformed asset")
        name = asset["name"]
        if name in result:
            raise EventAtlasError(f"duplicate content asset {name}")
        result[name] = asset
    return result


def _validate_ecl_asset(
    *,
    ecl: EclFile,
    assets: dict[str, dict[str, Any]],
) -> None:
    asset = assets.get(ecl.path.name)
    if (
        asset is None
        or asset.get("category") != "ecl"
        or asset.get("decoded_sha256") != ecl.sha256
    ):
        raise EventAtlasError(
            f"decoded ECL disagrees with content manifest: {ecl.path.name}"
        )


def _class_matrix(
    occurrences: list[dict[str, object]],
) -> dict[str, dict[str, int]]:
    all_classes = sorted(
        {*SUB_EVENT_CLASSES.keys(), *TIMELINE_EVENT_CLASSES.keys()}
    )
    matrix: dict[str, dict[str, int]] = {}
    for event_class in all_classes:
        matching = [
            occurrence
            for occurrence in occurrences
            if event_class in occurrence["event_classes"]
        ]
        statuses = Counter(
            str(occurrence["route_static_status"])
            for occurrence in matching
        )
        matrix[event_class] = {
            "total": len(matching),
            "conservative_route_reachable": statuses[
                "conservative_route_reachable"
            ],
            "difficulty_eligible_cfg_unreachable": statuses[
                "difficulty_eligible_cfg_unreachable"
            ],
            "timeline_schedule_candidate": statuses[
                "difficulty_eligible_timeline_schedule_candidate"
            ],
        }
    return matrix


def _stage_atlas(
    *,
    decoded_dir: Path,
    stage: StageSpec,
    assets: dict[str, dict[str, Any]],
    content_manifest: dict[str, Any],
) -> dict[str, object]:
    ecl = parse_ecl(decoded_dir / stage.ecl_name)
    spell_practice = parse_ecl(
        decoded_dir / stage.spell_practice_ecl_name
    )
    _validate_ecl_asset(ecl=ecl, assets=assets)
    _validate_ecl_asset(ecl=spell_practice, assets=assets)

    flow = analyze_flow(
        ecl,
        FlowConfig(
            difficulty_index=DIFFICULTY_INDEX,
            difficulty_mask=DIFFICULTY_MASK,
            route_id=ROUTE_ID,
        ),
    )
    reachable_offsets = set(flow.reachable_instruction_offsets)
    occurrences: list[dict[str, object]] = []
    all_eligible_confidence: Counter[str] = Counter()
    unknown_occurrences: list[dict[str, object]] = []

    for subroutine in ecl.subroutines:
        for instruction in subroutine.instructions:
            if not instruction.difficulty_mask & DIFFICULTY_MASK:
                continue
            specification = opcode_spec(instruction.opcode)
            all_eligible_confidence[specification.confidence] += 1
            classes = _event_classes("subroutine", instruction.opcode)
            if specification.confidence == "unknown":
                unknown_occurrences.append(
                    {
                        "symbolic_id": (
                            f"{ecl.path.name}:sub:{subroutine.index}:"
                            f"0x{instruction.offset:08x}"
                        ),
                        "opcode_hex": f"0x{instruction.opcode:02x}",
                        "opcode_name": specification.name,
                        "route_static_status": (
                            "conservative_route_reachable"
                            if instruction.offset in reachable_offsets
                            else "difficulty_eligible_cfg_unreachable"
                        ),
                    }
                )
            if classes:
                occurrences.append(
                    _sub_occurrence(
                        ecl=ecl,
                        subroutine_index=subroutine.index,
                        instruction=instruction,
                        reachable_offsets=reachable_offsets,
                    )
                )

    for timeline in ecl.timelines:
        for instruction in timeline.instructions:
            if not instruction.difficulty_mask & DIFFICULTY_MASK:
                continue
            confidence = _timeline_confidence(instruction.opcode)
            all_eligible_confidence[confidence] += 1
            classes = _event_classes("timeline", instruction.opcode)
            if confidence == "unknown":
                unknown_occurrences.append(
                    {
                        "symbolic_id": (
                            f"{ecl.path.name}:timeline:{timeline.index}:"
                            f"0x{instruction.offset:08x}"
                        ),
                        "opcode_hex": f"0x{instruction.opcode:02x}",
                        "opcode_name": TIMELINE_OPCODE_NAMES.get(
                            instruction.opcode,
                            f"unknown_timeline_{instruction.opcode:02x}",
                        ),
                        "route_static_status": (
                            "difficulty_eligible_timeline_schedule_candidate"
                        ),
                    }
                )
            if classes:
                occurrences.append(
                    _timeline_occurrence(
                        ecl=ecl,
                        timeline_index=timeline.index,
                        instruction=instruction,
                    )
                )

    occurrences.sort(
        key=lambda occurrence: (
            0 if occurrence["scope"] == "timeline" else 1,
            int(occurrence["scope_index"]),
            int(occurrence["file_offset"]),
        )
    )
    scene = content_manifest["mandatory_scenes"][stage.key]
    return {
        "key": stage.key,
        "label": stage.label,
        "route_stage_index": stage.route_stage_index,
        "content_set_sha256": scene["content_set_sha256"],
        "route_ecl": {
            "name": ecl.path.name,
            "sha256": ecl.sha256,
            "subroutine_count": ecl.header.subroutine_count,
            "timeline_count": ecl.header.timeline_count,
        },
        "spell_practice_reference": {
            "name": spell_practice.path.name,
            "sha256": spell_practice.sha256,
            "natural_route_authority": False,
        },
        "flow": {
            "root_subroutines": list(flow.root_subroutines),
            "reachable_subroutine_count": len(flow.reachable_subroutines),
            "reachable_instruction_count": len(
                flow.reachable_instruction_offsets
            ),
            "edge_count": len(flow.edges),
            "folded_branch_count": flow.folded_branch_count,
            "conservative_branch_count": flow.conservative_branch_count,
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
            "reachability_authority": (
                "conservative_static_overapproximation_not_runtime_execution"
            ),
        },
        "eligible_instruction_semantic_confidence": {
            key: all_eligible_confidence[key]
            for key in sorted(all_eligible_confidence)
        },
        "event_occurrence_count": len(occurrences),
        "event_class_matrix": _class_matrix(occurrences),
        "unknown_semantic_occurrences": unknown_occurrences,
        "event_occurrences": occurrences,
    }


def build_event_atlas(
    *,
    decoded_dir: Path,
    content_manifest_path: Path,
) -> dict[str, object]:
    if _sha256_path(content_manifest_path) != EXPECTED_CONTENT_MANIFEST_SHA256:
        raise EventAtlasError("unexpected immutable content-manifest SHA-256")
    content_manifest = json.loads(content_manifest_path.read_bytes())
    if (
        content_manifest.get("schema")
        != "th08-immutable-content-manifest-v1"
        or content_manifest.get("classification", {}).get(
            "content_identity_gate_passed"
        )
        is not True
    ):
        raise EventAtlasError("content manifest has no identity authority")
    assets = _content_assets(content_manifest)
    stages = [
        _stage_atlas(
            decoded_dir=decoded_dir,
            stage=stage,
            assets=assets,
            content_manifest=content_manifest,
        )
        for stage in STAGES
    ]

    aggregate_matrix: dict[str, dict[str, int]] = {}
    for event_class in sorted(
        {*SUB_EVENT_CLASSES.keys(), *TIMELINE_EVENT_CLASSES.keys()}
    ):
        aggregate_matrix[event_class] = {
            key: sum(
                int(stage["event_class_matrix"][event_class][key])
                for stage in stages
            )
            for key in (
                "total",
                "conservative_route_reachable",
                "difficulty_eligible_cfg_unreachable",
                "timeline_schedule_candidate",
            )
        }

    unknown_priority = [
        {
            "stage": stage["key"],
            "workload_has_retained_physical_reach": True,
            "event_execution_observed": False,
            "static_unknown_occurrence_count": len(
                stage["unknown_semantic_occurrences"]
            ),
            "occurrences": stage["unknown_semantic_occurrences"],
        }
        for stage in stages
        if stage["unknown_semantic_occurrences"]
    ]
    report: dict[str, object] = {
        "schema": SCHEMA,
        "taskbook_card": TASKBOOK_CARD,
        "status": "static_atlas_foundation_physical_event_join_open",
        "immutable_content_manifest": {
            "path": (
                "artifacts/runtime_reports/"
                "th08_immutable_content_manifest_20260731.json"
            ),
            "sha256": EXPECTED_CONTENT_MANIFEST_SHA256,
            "content_set_sha256": content_manifest["content_scope"][
                "content_set_sha256"
            ],
        },
        "route_profile": {
            "team": "Sakuya/Remilia",
            "route_id": ROUTE_ID,
            "difficulty": "Lunatic",
            "difficulty_index": DIFFICULTY_INDEX,
            "difficulty_mask": DIFFICULTY_MASK,
        },
        "symbolic_origin_contract": {
            "identity": (
                "content-set digest + decoded ECL SHA-256 + scope/index + "
                "decoded file offset"
            ),
            "runtime_mapping": (
                "after exact runtime-image normalization, runtime_pc equals "
                "runtime_ecl_base plus decoded file offset"
            ),
            "runtime_mapping_verified_per_occurrence": False,
        },
        "stage_count": len(stages),
        "event_occurrence_count": sum(
            int(stage["event_occurrence_count"]) for stage in stages
        ),
        "event_class_matrix": aggregate_matrix,
        "unknown_priority": {
            "basis": (
                "mandatory workload physical reach only; individual static "
                "instruction execution is not observed"
            ),
            "stages": unknown_priority,
        },
        "stages": stages,
        "classification": {
            "mandatory_static_event_classes_inventoried": True,
            "content_versions_exact": True,
            "lunatic_mask_applied": True,
            "route_and_difficulty_branches_folded_where_observable": True,
            "unknown_runtime_branches_preserved": True,
            "native_event_execution_join_complete": False,
            "content_02_exit_gate_passed": False,
        },
        "authority": {
            "kind": "offline_conservative_static_event_atlas",
            "runtime_execution_authority": False,
            "event_side_effect_authority": False,
            "future_event_prediction_authority": False,
            "planner_or_action_authority": False,
            "physical_trial_run": False,
        },
        "next_gate": {
            "requires_exact_runtime_image_and_pc_join": True,
            "requires_event_specific_native_execution_evidence": True,
            "requires_unknown_timeline_06_09_revalidation": True,
            "do_not_block_other_high_roi_tasks_on_capture_debt": True,
        },
    }
    payload = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_digest"] = _sha256_bytes(payload)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoded-dir", type=Path, required=True)
    parser.add_argument("--content-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_event_atlas(
        decoded_dir=args.decoded_dir,
        content_manifest_path=args.content_manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
