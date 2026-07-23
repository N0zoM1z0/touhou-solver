#!/usr/bin/env python3
"""Conservative static control-flow analysis for decoded TH08 ECL files.

The graph models the control transfers observed in enemy_ecl_vm_step:

* relative jumps (opcodes 0x04, 0x05, and 0x28..0x33);
* direct calls (0x34 and 0x58);
* child-enemy VM starts (0x5A..0x5E);
* interrupt-slot installation (0x7E);
* enemy-end transitions (0x82);
* boss health/timeout phase transitions (0x85 and 0x86); and
* auxiliary VM starts (0x87).

Timeline enemy spawns are graph roots.  Difficulty masks are applied exactly.
Integer comparisons against the observed difficulty-index VM variable (10040)
and route-id VM variable (10052) are folded; every other conditional keeps both
successors, so the result remains an over-approximation rather than silently
dropping a possible encounter.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from th08_ecl import EclError, EclFile, SubInstruction, parse_ecl


TIMELINE_SPAWN_OPCODES = frozenset({0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x0B, 0x0C, 0x0F})
CONDITIONAL_JUMPS = frozenset(range(0x28, 0x34))
CHILD_SPAWN_OPCODES = frozenset(range(0x5A, 0x5F))
KNOWN_INT_VARIABLES = {
    10040: "difficulty_index",
    10052: "route_id",
}


@dataclass(frozen=True)
class FlowConfig:
    difficulty_index: int
    difficulty_mask: int
    route_id: int


@dataclass(frozen=True)
class SubEdge:
    source_subroutine: int
    source_offset: int
    target_subroutine: int
    kind: str


@dataclass(frozen=True)
class FlowResult:
    root_subroutines: tuple[int, ...]
    reachable_subroutines: tuple[int, ...]
    reachable_instruction_offsets: tuple[int, ...]
    edges: tuple[SubEdge, ...]
    unresolved_dynamic_subroutine_edges: tuple[tuple[int, int, int], ...]
    folded_branch_count: int
    conservative_branch_count: int


def _signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def _eligible(insn: SubInstruction, mask: int) -> bool:
    return bool(insn.difficulty_mask & mask)


def _known_int_operand(
    raw: int, dynamic: bool, config: FlowConfig
) -> int | None:
    if not dynamic:
        return _signed(raw)
    variable = _signed(raw)
    if variable == 10040:
        return config.difficulty_index
    if variable == 10052:
        return config.route_id
    return None


def _fold_int_branch(insn: SubInstruction, config: FlowConfig) -> bool | None:
    if insn.opcode not in {0x28, 0x2A, 0x2C, 0x2E, 0x30, 0x32}:
        return None
    if len(insn.arguments) != 4:
        raise EclError(
            f"conditional jump at {insn.offset:#x} does not have four arguments"
        )
    left = _known_int_operand(
        insn.arguments[0], bool(insn.parameter_mask & 0x01), config
    )
    right = _known_int_operand(
        insn.arguments[1], bool(insn.parameter_mask & 0x02), config
    )
    if left is None or right is None:
        return None
    operations = {
        0x28: lambda a, b: a == b,
        0x2A: lambda a, b: a != b,
        0x2C: lambda a, b: a < b,
        0x2E: lambda a, b: a <= b,
        0x30: lambda a, b: a > b,
        0x32: lambda a, b: a >= b,
    }
    return operations[insn.opcode](left, right)


def _jump_target(insn: SubInstruction, displacement_index: int) -> int:
    if len(insn.arguments) <= displacement_index:
        raise EclError(
            f"jump at {insn.offset:#x} lacks displacement argument "
            f"{displacement_index}"
        )
    return insn.offset + _signed(insn.arguments[displacement_index])


def _subroutine_target(
    insn: SubInstruction,
) -> tuple[int | None, str] | None:
    if insn.opcode == 0x34:
        return (_signed(insn.arguments[0]), "call")
    if insn.opcode == 0x58:
        return (_signed(insn.arguments[1]), "call_with_enemy")
    if insn.opcode in CHILD_SPAWN_OPCODES:
        return (_signed(insn.arguments[0]), "child_spawn")
    if insn.opcode == 0x7E:
        if insn.parameter_mask & 0x01:
            return (None, "interrupt_slot_dynamic")
        return (_signed(insn.arguments[0]), "interrupt_slot")
    if insn.opcode == 0x82:
        if insn.parameter_mask & 0x01:
            return (None, "enemy_end_dynamic")
        return (_signed(insn.arguments[0]), "enemy_end")
    if insn.opcode == 0x85:
        if insn.parameter_mask & 0x04:
            return (None, "health_phase_dynamic")
        return (_signed(insn.arguments[2]), "health_phase")
    if insn.opcode == 0x86:
        if insn.parameter_mask & 0x02:
            return (None, "timeout_phase_dynamic")
        return (_signed(insn.arguments[1]), "timeout_phase")
    if insn.opcode == 0x87:
        if insn.parameter_mask & 0x02:
            return (None, "aux_vm_dynamic")
        return (_signed(insn.arguments[1]), "aux_vm")
    return None


def timeline_roots(ecl: EclFile, difficulty_mask: int) -> tuple[int, ...]:
    roots = set()
    for timeline in ecl.timelines:
        for insn in timeline.instructions:
            if (
                insn.opcode in TIMELINE_SPAWN_OPCODES
                and insn.difficulty_mask & difficulty_mask
            ):
                if not insn.arguments:
                    raise EclError(
                        f"timeline spawn at {insn.offset:#x} has no subroutine argument"
                    )
                roots.add(_signed(insn.arguments[0]))
    invalid = sorted(root for root in roots if not 0 <= root < len(ecl.subroutines))
    if invalid:
        raise EclError(f"timeline refers to invalid subroutines: {invalid}")
    return tuple(sorted(roots))


def analyze_flow(ecl: EclFile, config: FlowConfig) -> FlowResult:
    roots = timeline_roots(ecl, config.difficulty_mask)
    reachable_subs: set[int] = set()
    reachable_offsets: set[int] = set()
    edges: set[SubEdge] = set()
    unresolved: set[tuple[int, int, int]] = set()
    folded = 0
    conservative = 0

    pending_subs = deque(roots)
    while pending_subs:
        sub_index = pending_subs.popleft()
        if sub_index in reachable_subs:
            continue
        if not 0 <= sub_index < len(ecl.subroutines):
            raise EclError(f"reachable edge targets invalid subroutine {sub_index}")
        reachable_subs.add(sub_index)
        sub = ecl.subroutines[sub_index]
        by_offset = {insn.offset: insn for insn in sub.instructions}
        if not sub.instructions:
            continue

        pending_offsets = [sub.instructions[0].offset]
        visited_offsets: set[int] = set()
        while pending_offsets:
            offset = pending_offsets.pop()
            if offset in visited_offsets:
                continue
            insn = by_offset.get(offset)
            if insn is None:
                raise EclError(
                    f"sub {sub_index} control flow targets non-instruction {offset:#x}"
                )
            visited_offsets.add(offset)
            reachable_offsets.add(offset)

            next_offset = insn.offset + insn.size
            has_fallthrough = next_offset in by_offset
            if not _eligible(insn, config.difficulty_mask):
                if has_fallthrough:
                    pending_offsets.append(next_offset)
                continue

            edge_target = _subroutine_target(insn)
            if edge_target is not None:
                target_sub, kind = edge_target
                if target_sub is None:
                    unresolved.add((sub_index, insn.offset, insn.opcode))
                elif target_sub >= 0:
                    if target_sub >= len(ecl.subroutines):
                        raise EclError(
                            f"sub {sub_index} edge at {insn.offset:#x} targets "
                            f"invalid subroutine {target_sub}"
                        )
                    edge = SubEdge(sub_index, insn.offset, target_sub, kind)
                    edges.add(edge)
                    if target_sub not in reachable_subs:
                        pending_subs.append(target_sub)

            if insn.opcode in {0x01, 0x35}:
                continue
            if insn.opcode == 0x04:
                pending_offsets.append(_jump_target(insn, 1))
                continue
            if insn.opcode == 0x05:
                pending_offsets.append(_jump_target(insn, 1))
                if has_fallthrough:
                    pending_offsets.append(next_offset)
                continue
            if insn.opcode in CONDITIONAL_JUMPS:
                decision = _fold_int_branch(insn, config)
                if decision is None:
                    conservative += 1
                    pending_offsets.append(_jump_target(insn, 3))
                    if has_fallthrough:
                        pending_offsets.append(next_offset)
                elif decision:
                    folded += 1
                    pending_offsets.append(_jump_target(insn, 3))
                else:
                    folded += 1
                    if has_fallthrough:
                        pending_offsets.append(next_offset)
                continue
            if has_fallthrough:
                pending_offsets.append(next_offset)

    return FlowResult(
        root_subroutines=roots,
        reachable_subroutines=tuple(sorted(reachable_subs)),
        reachable_instruction_offsets=tuple(sorted(reachable_offsets)),
        edges=tuple(
            sorted(
                edges,
                key=lambda edge: (
                    edge.source_subroutine,
                    edge.source_offset,
                    edge.target_subroutine,
                    edge.kind,
                ),
            )
        ),
        unresolved_dynamic_subroutine_edges=tuple(sorted(unresolved)),
        folded_branch_count=folded,
        conservative_branch_count=conservative,
    )


def flow_to_dict(ecl: EclFile, config: FlowConfig, result: FlowResult) -> dict[str, object]:
    return {
        "ecl_file": ecl.path.name,
        "ecl_sha256": ecl.sha256,
        "difficulty_index": config.difficulty_index,
        "difficulty_mask": config.difficulty_mask,
        "route_id": config.route_id,
        "root_subroutines": result.root_subroutines,
        "reachable_subroutines": result.reachable_subroutines,
        "reachable_instruction_count": len(result.reachable_instruction_offsets),
        "reachable_instruction_offsets": result.reachable_instruction_offsets,
        "edges": [edge.__dict__ for edge in result.edges],
        "unresolved_dynamic_subroutine_edges": [
            {"source_subroutine": sub, "source_offset": offset, "opcode": opcode}
            for sub, offset, opcode in result.unresolved_dynamic_subroutine_edges
        ],
        "folded_branch_count": result.folded_branch_count,
        "conservative_branch_count": result.conservative_branch_count,
        "limitations": [
            "Unknown runtime comparisons retain both CFG successors.",
            "A reachable phase-slot installation is treated as a possible phase transition.",
            "Built-in callbacks are not executed by this static analyzer.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ecl", type=Path)
    parser.add_argument("--difficulty-index", type=int, required=True)
    parser.add_argument("--difficulty-mask", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--route-id", type=int, default=2)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)
    try:
        ecl = parse_ecl(args.ecl)
        config = FlowConfig(args.difficulty_index, args.difficulty_mask, args.route_id)
        result = analyze_flow(ecl, config)
        rendered = json.dumps(flow_to_dict(ecl, config, result), indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (EclError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
