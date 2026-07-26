#!/usr/bin/env python3
"""Generate pinned Sakuya/Remilia route manifests from decoded TH08 data.

This is a route-analysis manifest, not a solved input trace. It fixes the
player resources, stage ECL sequence, difficulty mask, and all matching
spell-card start records so later simulator/search work has an explicit target.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

from th08_ecl_callback_model import CALLBACK_SPECS
from th08_ecl import EclError, decode_spell_card_start, parse_ecl
from th08_ecl_flow import FlowConfig, analyze_flow
from th08_sht import ShtError, parse_sht


ROUTE_ID = 2
PRIMARY_SHT = "ply02a.sht"
SECONDARY_SHT = "ply02as.sht"

PHASE_COMPONENT_EDGE_KINDS = frozenset(
    {"call", "call_with_enemy", "child_spawn", "interrupt_slot", "aux_vm"}
)
PHASE_TRANSITION_EDGE_KINDS = frozenset(
    {"enemy_end", "health_phase", "timeout_phase"}
)
FEATURE_OPCODES = {
    "bullet_emit": frozenset(range(0x60, 0x69)),
    "transform_define": frozenset({0x6F}),
    "laser_spawn": frozenset({0x72, 0x73}),
    "callback_invoke": frozenset({0x88}),
    "callback_install": frozenset({0x89}),
}


@dataclass(frozen=True)
class StageTarget:
    internal_stage_index: int
    label: str
    ecl_file: str


@dataclass(frozen=True)
class RouteProfile:
    name: str
    difficulty: str
    difficulty_index: int
    active_difficulty_mask: int
    stages: tuple[StageTarget, ...]
    branch_note: str


COMMON_STAGES = (
    StageTarget(0, "Stage 1", "ecldata1.ecl"),
    StageTarget(1, "Stage 2", "ecldata2.ecl"),
    StageTarget(2, "Stage 3", "ecldata3.ecl"),
    StageTarget(3, "Stage 4A / Reimu", "ecldata4a.ecl"),
    StageTarget(5, "Stage 5", "ecldata5.ecl"),
)


PROFILES = (
    RouteProfile(
        name="sakuya_remilia_lunatic_final_a",
        difficulty="Lunatic",
        difficulty_index=3,
        active_difficulty_mask=0x08,
        stages=COMMON_STAGES + (StageTarget(6, "Final A / Eirin", "ecldata6.ecl"),),
        branch_note="Final A branch retained as a distinct reachable Lunatic ending.",
    ),
    RouteProfile(
        name="sakuya_remilia_lunatic_final_b",
        difficulty="Lunatic",
        difficulty_index=3,
        active_difficulty_mask=0x08,
        stages=COMMON_STAGES + (StageTarget(7, "Final B / Kaguya", "ecldata7.ecl"),),
        branch_note="Primary full Lunatic acceptance branch; includes Kaguya and Last Spells.",
    ),
    RouteProfile(
        name="sakuya_remilia_extra",
        difficulty="Extra",
        difficulty_index=4,
        active_difficulty_mask=0x0F,
        stages=(StageTarget(8, "Extra / Mokou", "ecldata8.ecl"),),
        branch_note="Extra uses its dedicated ECL; its spell records carry mask 0xFF.",
    ),
    RouteProfile(
        name="sakuya_remilia_easy_final_b",
        difficulty="Easy",
        difficulty_index=0,
        active_difficulty_mask=0x01,
        stages=COMMON_STAGES + (StageTarget(7, "Final B / Kaguya", "ecldata7.ecl"),),
        branch_note="Original Game Start Easy route 2 ending at Final B.",
    ),
    RouteProfile(
        name="sakuya_remilia_normal_final_b",
        difficulty="Normal",
        difficulty_index=1,
        active_difficulty_mask=0x02,
        stages=COMMON_STAGES + (StageTarget(7, "Final B / Kaguya", "ecldata7.ecl"),),
        branch_note="Original Game Start Normal route 2 ending at Final B.",
    ),
    RouteProfile(
        name="sakuya_remilia_hard_final_b",
        difficulty="Hard",
        difficulty_index=2,
        active_difficulty_mask=0x04,
        stages=COMMON_STAGES + (StageTarget(7, "Final B / Kaguya", "ecldata7.ecl"),),
        branch_note="Original Game Start Hard route 2 ending at Final B.",
    ),
)


def _spell_component_report(ecl, flow, root_subroutine: int, mask: int) -> dict[str, object]:
    """Return the conservative subgraph belonging to one spell phase.

    Calls, spawned children, interrupt handlers, and auxiliary VMs are part of
    the current phase. Enemy-end/health/timeout edges are exits into another
    phase and are reported without traversing them.
    """

    edges_by_source = defaultdict(list)
    for edge in flow.edges:
        edges_by_source[edge.source_subroutine].append(edge)

    component_subs: set[int] = set()
    component_edges = set()
    pending = deque([root_subroutine])
    while pending:
        sub_index = pending.popleft()
        if sub_index in component_subs:
            continue
        component_subs.add(sub_index)
        for edge in edges_by_source[sub_index]:
            if edge.kind not in PHASE_COMPONENT_EDGE_KINDS:
                continue
            component_edges.add(edge)
            if edge.target_subroutine not in component_subs:
                pending.append(edge.target_subroutine)

    transition_edges = {
        edge
        for sub_index in component_subs
        for edge in edges_by_source[sub_index]
        if edge.kind in PHASE_TRANSITION_EDGE_KINDS
    }
    reachable_offsets = set(flow.reachable_instruction_offsets)
    aggregate = Counter()
    per_subroutine = []
    for sub_index in sorted(component_subs):
        feature_counts = Counter()
        eligible_instruction_count = 0
        for insn in ecl.subroutines[sub_index].instructions:
            if insn.offset not in reachable_offsets or not insn.difficulty_mask & mask:
                continue
            eligible_instruction_count += 1
            for feature, opcodes in FEATURE_OPCODES.items():
                if insn.opcode in opcodes:
                    feature_counts[feature] += 1
        aggregate.update(feature_counts)
        per_subroutine.append(
            {
                "subroutine": sub_index,
                "eligible_instruction_count": eligible_instruction_count,
                "feature_counts": {
                    feature: feature_counts[feature] for feature in FEATURE_OPCODES
                },
            }
        )

    edge_key = lambda edge: (
        edge.source_subroutine,
        edge.source_offset,
        edge.target_subroutine,
        edge.kind,
    )
    return {
        "component_subroutines": sorted(component_subs),
        "component_edges": [
            edge.__dict__ for edge in sorted(component_edges, key=edge_key)
        ],
        "phase_transition_edges": [
            edge.__dict__ for edge in sorted(transition_edges, key=edge_key)
        ],
        "feature_counts": {
            feature: aggregate[feature] for feature in FEATURE_OPCODES
        },
        "subroutine_features": per_subroutine,
    }


def _signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def _callback_report(ecl, flow, mask: int) -> tuple[list[dict[str, object]], list[int]]:
    reachable_offsets = set(flow.reachable_instruction_offsets)
    occurrences = []
    indices = set()
    for sub in ecl.subroutines:
        for insn in sub.instructions:
            if (
                insn.offset not in reachable_offsets
                or not insn.difficulty_mask & mask
                or insn.opcode not in {0x88, 0x89}
            ):
                continue
            dynamic = bool(insn.parameter_mask & 1)
            callback_index = None if dynamic else _signed(insn.arguments[0])
            if insn.opcode == 0x88:
                action = "invoke"
            elif callback_index is not None and callback_index < 0:
                action = "clear_per_frame"
            else:
                action = "install_per_frame"
            occurrence: dict[str, object] = {
                "subroutine": sub.index,
                "time": insn.time,
                "offset": insn.offset,
                "opcode": insn.opcode,
                "action": action,
                "callback_index": callback_index,
                "callback_index_dynamic": dynamic,
                "argument_1": _signed(insn.arguments[1]),
            }
            if callback_index is not None and callback_index >= 0:
                if callback_index >= len(CALLBACK_SPECS):
                    raise EclError(
                        f"callback index {callback_index} at {insn.offset:#x} "
                        "is outside the native 32-entry table"
                    )
                spec = CALLBACK_SPECS[callback_index]
                occurrence.update(
                    {
                        "callback_address": spec.address,
                        "callback_name": spec.name,
                        "callback_confidence": spec.confidence,
                    }
                )
                indices.add(callback_index)
            occurrences.append(occurrence)
    return occurrences, sorted(indices)


def _stage_report(
    decoded_dir: Path, target: StageTarget, profile: RouteProfile
) -> dict[str, object]:
    ecl = parse_ecl(decoded_dir / target.ecl_file)
    flow = analyze_flow(
        ecl,
        FlowConfig(
            difficulty_index=profile.difficulty_index,
            difficulty_mask=profile.active_difficulty_mask,
            route_id=ROUTE_ID,
        ),
    )
    reachable_offsets = set(flow.reachable_instruction_offsets)
    callback_occurrences, callback_indices = _callback_report(
        ecl, flow, profile.active_difficulty_mask
    )
    candidates = []
    reachable = []
    for sub in ecl.subroutines:
        for insn in sub.instructions:
            if (
                insn.opcode != 0x7A
                or not insn.difficulty_mask & profile.active_difficulty_mask
            ):
                continue
            occurrence = {
                **decode_spell_card_start(insn),
                "subroutine": sub.index,
                "time": insn.time,
                "offset": insn.offset,
                "difficulty_mask": insn.difficulty_mask,
            }
            candidates.append(occurrence)
            if insn.offset in reachable_offsets:
                occurrence.update(
                    _spell_component_report(
                        ecl, flow, sub.index, profile.active_difficulty_mask
                    )
                )
                reachable.append(occurrence)
    return {
        "internal_stage_index": target.internal_stage_index,
        "label": target.label,
        "ecl_file": target.ecl_file,
        "ecl_sha256": ecl.sha256,
        "subroutine_count": ecl.header.subroutine_count,
        "timeline_count": ecl.header.timeline_count,
        "timeline_root_subroutines": flow.root_subroutines,
        "reachable_subroutine_count": len(flow.reachable_subroutines),
        "reachable_subroutines": flow.reachable_subroutines,
        "flow_edge_count": len(flow.edges),
        "folded_branch_count": flow.folded_branch_count,
        "conservative_branch_count": flow.conservative_branch_count,
        "unresolved_dynamic_subroutine_edges": [
            {"source_subroutine": sub, "source_offset": offset, "opcode": opcode}
            for sub, offset, opcode in flow.unresolved_dynamic_subroutine_edges
        ],
        "candidate_spell_occurrence_count": len(candidates),
        "candidate_unique_spell_ids": sorted(
            {int(item["spell_id"]) for item in candidates}
        ),
        "reachable_spell_occurrence_count": len(reachable),
        "reachable_unique_spell_ids": sorted(
            {int(item["spell_id"]) for item in reachable}
        ),
        "reachable_spell_occurrences": reachable,
        "reachable_callback_indices": callback_indices,
        "reachable_callback_occurrences": callback_occurrences,
    }


def build_manifest(decoded_dir: Path, profile: RouteProfile) -> dict[str, object]:
    primary = parse_sht(decoded_dir / PRIMARY_SHT)
    secondary = parse_sht(decoded_dir / SECONDARY_SHT)
    stages = [
        _stage_report(decoded_dir, target, profile)
        for target in profile.stages
    ]
    return {
        "profile": profile.name,
        "status": "analysis_target_not_yet_solved",
        "route_id": ROUTE_ID,
        "team": "Sakuya/Remilia",
        "difficulty": profile.difficulty,
        "difficulty_index": profile.difficulty_index,
        "active_difficulty_mask": profile.active_difficulty_mask,
        "branch_note": profile.branch_note,
        "player": {
            "primary_sht": PRIMARY_SHT,
            "primary_sht_sha256": primary.sha256,
            "secondary_sht": SECONDARY_SHT,
            "secondary_sht_sha256": secondary.sha256,
            "bomb_gate_reset_value": primary.header.bomb_gate_reset_value,
            "unfocused_cardinal_speed": primary.header.unfocused_cardinal_speed,
            "unfocused_diagonal_axis_speed": primary.header.unfocused_diagonal_axis_speed,
            "focused_cardinal_speed": secondary.header.focused_cardinal_speed,
            "focused_diagonal_axis_speed": secondary.header.focused_diagonal_axis_speed,
        },
        "stage_count": len(stages),
        "candidate_spell_occurrence_count": sum(
            int(stage["candidate_spell_occurrence_count"]) for stage in stages
        ),
        "candidate_unique_spell_ids": sorted(
            {
                spell_id
                for stage in stages
                for spell_id in stage["candidate_unique_spell_ids"]
            }
        ),
        "reachable_spell_occurrence_count": sum(
            int(stage["reachable_spell_occurrence_count"]) for stage in stages
        ),
        "reachable_unique_spell_ids": sorted(
            {
                spell_id
                for stage in stages
                for spell_id in stage["reachable_unique_spell_ids"]
            }
        ),
        "reachable_callback_indices": sorted(
            {
                callback_index
                for stage in stages
                for callback_index in stage["reachable_callback_indices"]
            }
        ),
        "stages": stages,
    }


def format_manifest(manifest: dict[str, object]) -> str:
    player = manifest["player"]
    lines = [
        f"# {manifest['profile']}",
        "",
        f"Status: `{manifest['status']}`",
        "",
        f"- Team: {manifest['team']} (route ID {manifest['route_id']})",
        f"- Difficulty: {manifest['difficulty']} (mask `0x{manifest['active_difficulty_mask']:02x}`)",
        f"- Branch: {manifest['branch_note']}",
        f"- Player resources: `{player['primary_sht']}` + `{player['secondary_sht']}`",
        (
            "- Movement: unfocused "
            f"{player['unfocused_cardinal_speed']:.7g}/"
            f"{player['unfocused_diagonal_axis_speed']:.7g}; focused "
            f"{player['focused_cardinal_speed']:.7g}/"
            f"{player['focused_diagonal_axis_speed']:.7g}"
        ),
        f"- Post-spawn/bomb gate reset value: {player['bomb_gate_reset_value']}",
        f"- Difficulty-mask candidate spell IDs: {len(manifest['candidate_unique_spell_ids'])}",
        f"- Statically reachable spell IDs: {len(manifest['reachable_unique_spell_ids'])}",
        f"- Reachable built-in callback indices: {manifest['reachable_callback_indices']}",
        "",
        "Reachability includes timeline roots, relative jumps, calls, child spawns,",
        "interrupt slots, enemy-end transitions, health/timeout transitions, and auxiliary VMs.",
        "Unknown runtime comparisons retain both",
        "branches, so this is a conservative static set pending replay validation.",
        "",
    ]
    for stage in manifest["stages"]:
        lines.extend(
            [
                f"## {stage['label']}",
                "",
                f"ECL: `{stage['ecl_file']}` (`{stage['ecl_sha256']}`)",
                "",
                "| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |",
                "| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |",
            ]
        )
        for spell in stage["reachable_spell_occurrences"]:
            lines.append(
                f"| {spell['spell_id']} | {spell['name']} | {spell['owner']} | "
                f"{spell['subroutine']} | "
                f"{', '.join(str(value) for value in spell['component_subroutines'])} | "
                f"{spell['feature_counts']['bullet_emit']} | "
                f"{spell['feature_counts']['transform_define']} | "
                f"{spell['feature_counts']['laser_spawn']} |"
            )
        lines.append("")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded", type=Path, help="decoded ECL/SHT directory")
    parser.add_argument("output", type=Path, help="manifest output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        for profile in PROFILES:
            manifest = build_manifest(args.decoded, profile)
            (args.output / f"{profile.name}.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            (args.output / f"{profile.name}.md").write_text(
                format_manifest(manifest), encoding="utf-8"
            )
            print(
                f"{profile.name}: stages={manifest['stage_count']} "
                f"reachable_spell_occurrences={manifest['reachable_spell_occurrence_count']} "
                f"reachable_unique_spell_ids={len(manifest['reachable_unique_spell_ids'])}"
            )
        return 0
    except (EclError, ShtError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
