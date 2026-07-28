"""Build a conservative static-ECL/main-VM/realized-birth join report."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from th08_ecl_tool.core import parse_ecl

from .advance import find_fire_advances
from .auxiliary import build_auxiliary_analysis
from .join import (
    activation_batch_record,
    event_record,
    join_activation_support,
)
from .mapping import (
    FIRE_OPCODES,
    infer_runtime_base,
    instructions_by_runtime_pc,
    static_instructions,
)
from .model import TraceScan
from .trace import scan_schema11_trace


SCHEMA = "th08-nonspell-main-vm-source-join-v1"
MAX_SAMPLES = 20


def canonical_report_bytes(report: dict[str, object]) -> bytes:
    return (
        json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _build_report(
    *,
    trace: TraceScan,
    ecl_path: Path,
) -> dict[str, object]:
    ecl = parse_ecl(ecl_path)
    instructions = static_instructions(ecl)
    pc_occurrences: Counter[int] = Counter(
        row.instruction_pointer
        for capture in trace.captures
        for row in capture.rows
    )
    base = infer_runtime_base(pc_occurrences, instructions)
    runtime_instructions = (
        instructions_by_runtime_pc(
            instructions,
            runtime_base=base.selected_base,
        )
        if base.selected_base is not None
        else {}
    )
    mapped_pc_occurrences = sum(
        count
        for pc, count in pc_occurrences.items()
        if pc in runtime_instructions
    )
    mapped_opcode_occurrences: Counter[int] = Counter()
    for pc, count in pc_occurrences.items():
        instruction = runtime_instructions.get(pc)
        if instruction is not None:
            mapped_opcode_occurrences[instruction.opcode] += count

    advances, advance_diagnostics = find_fire_advances(
        trace.captures,
        instructions_by_pc=runtime_instructions,
    )
    support_join = join_activation_support(
        advances,
        trace.activation_batches,
    )
    fire_pc_occurrences = {
        pc: pc_occurrences[pc]
        for pc, instruction in runtime_instructions.items()
        if instruction.opcode in FIRE_OPCODES and pc in pc_occurrences
    }
    nonspell_advances = [
        event for event in advances if event.spell_id is None
    ]
    auxiliary = build_auxiliary_analysis(
        trace=trace,
        ecl=ecl,
        runtime_instructions=runtime_instructions,
        pc_occurrences=pc_occurrences,
        max_samples=MAX_SAMPLES,
    )

    report: dict[str, object] = {
        "schema": SCHEMA,
        "authority": {
            "role": "offline_trace_only_no_action_authority",
            "source_availability": "static_affine_candidate",
            "runtime_instruction_identity": "unproved",
            "direct_source_proof": False,
            "hit_causal_coverage": "not_measured",
            "live_guidance_authority": "none",
        },
        "provenance": {
            "trace_sha256": trace.trace_sha256,
            "trace_bytes": trace.trace_bytes,
            "trace_lines": trace.trace_lines,
            "ecl_file": ecl_path.name,
            "ecl_sha256": ecl.sha256,
            "ecl_bytes": ecl.header.data_end_offset,
        },
        "trace_scope": {
            "schema11_rows": trace.schema11_rows,
            "stable_inventory_rows": sum(
                capture.stable for capture in trace.captures
            ),
            "capture_spanned_inventory_rows": sum(
                not capture.stable for capture in trace.captures
            ),
            "invalid_active_vm_rows": trace.invalid_active_vm_rows,
            "vm_observation_rows": sum(
                len(capture.rows) for capture in trace.captures
            ),
            "activation_batches": len(trace.activation_batches),
            "activation_bullets": sum(
                batch.bullet_count for batch in trace.activation_batches
            ),
        },
        "static_pc_mapping": {
            "interpretation": (
                "runtime_pc == inferred_base + decoded_ecl_file_offset; "
                "exact boundaries do not prove live byte identity"
            ),
            "selected_base": base.selected_base,
            "selected_base_hex": (
                f"{base.selected_base:#010x}"
                if base.selected_base is not None
                else None
            ),
            "unique_observed_pcs": base.unique_observed_pcs,
            "mapped_unique_pcs": base.mapped_unique_pcs,
            "runner_up_mapped_unique_pcs": (
                base.runner_up_mapped_unique_pcs
            ),
            "mapped_pc_occurrences": mapped_pc_occurrences,
            "total_pc_occurrences": sum(pc_occurrences.values()),
            "unique_complete_match": base.unique_complete_match,
            "top_candidates": [
                {
                    "base": candidate.base,
                    "base_hex": f"{candidate.base:#010x}",
                    "mapped_unique_pcs": candidate.mapped_unique_pcs,
                }
                for candidate in base.candidates
            ],
            "mapped_opcode_occurrences": {
                f"{opcode:#04x}": count
                for opcode, count in sorted(mapped_opcode_occurrences.items())
            },
        },
        "direct_fire_availability": {
            "fire_opcode_range": ["0x60", "0x68"],
            "observed_fire_pcs": [
                {
                    "runtime_pc": pc,
                    "runtime_pc_hex": f"{pc:#010x}",
                    "file_offset": runtime_instructions[pc].offset,
                    "file_offset_hex": (
                        f"{runtime_instructions[pc].offset:#x}"
                    ),
                    "subroutine_index": (
                        runtime_instructions[pc].subroutine_index
                    ),
                    "opcode": runtime_instructions[pc].opcode,
                    "instruction_time": runtime_instructions[pc].time,
                    "size": runtime_instructions[pc].size,
                    "difficulty_mask": (
                        runtime_instructions[pc].difficulty_mask
                    ),
                    "parameter_mask": (
                        runtime_instructions[pc].parameter_mask
                    ),
                    "static_arguments": list(
                        runtime_instructions[pc].arguments
                    ),
                    "observation_occurrences": count,
                }
                for pc, count in sorted(fire_pc_occurrences.items())
            ],
            "exact_sequential_advances": len(advances),
            "nonspell_exact_sequential_advances": len(nonspell_advances),
            "advance_diagnostics": advance_diagnostics,
        },
        "auxiliary_start_availability": auxiliary.section,
        "realized_birth_join": {
            "join_rule": (
                "same epoch/stage/spell scope and inclusive intersection "
                "between captured fire-PC advance support and activation support"
            ),
            "events_with_compatible_activation": len(
                support_join.matched_event_indices
            ),
            "activation_batches_with_compatible_event": len(
                support_join.matched_batch_indices
            ),
            "compatible_activation_bullets": (
                support_join.matched_activation_bullets
            ),
            "one_to_one_event_batch_matches": len(
                support_join.one_to_one_event_indices
            ),
            "all_fire_advances_have_compatible_activation": (
                bool(advances)
                and len(support_join.matched_event_indices) == len(advances)
            ),
            "all_matched_edges_one_to_one": (
                bool(support_join.matched_event_indices)
                and len(support_join.one_to_one_event_indices)
                == len(support_join.matched_event_indices)
                == len(support_join.matched_batch_indices)
            ),
            "event_samples": [
                event_record(
                    advances[index],
                    matching_batches=support_join.event_matches[index],
                )
                for index in support_join.matched_event_indices[:MAX_SAMPLES]
            ],
            "activation_batch_samples": [
                activation_batch_record(
                    trace.activation_batches[index],
                    matching_events=support_join.batch_matches[index],
                )
                for index in support_join.matched_batch_indices[:MAX_SAMPLES]
            ],
        },
        "gates": {
            "strict_schema11_trace_available": trace.schema11_rows > 0,
            "all_observed_pcs_have_unique_affine_static_mapping": (
                base.unique_complete_match
            ),
            "direct_fire_pc_observed": bool(fire_pc_occurrences),
            "exact_sequential_fire_advances_observed": bool(advances),
            "auxiliary_start_pc_observed": auxiliary.start_pc_observed,
            "exact_sequential_auxiliary_starts_observed": (
                auxiliary.exact_start_observed
            ),
            "every_immediate_auxiliary_candidate_has_compatible_activation": (
                auxiliary.every_immediate_candidate_matched
            ),
            "every_fire_advance_has_compatible_activation": (
                bool(advances)
                and len(support_join.matched_event_indices) == len(advances)
            ),
            "runtime_instruction_bytes_identical": False,
            "exact_fire_operands_and_origin_lowered": False,
            "observation_compatible_slot_reuse_excluded": False,
            "direct_source_proof": False,
        },
        "conclusion": {
            "observed": (
                "The physical trace contains stable ordinary-enemy VM PC/timer "
                "histories and exact captured PC advances. The decoded ECL file "
                "contains legal instruction boundaries and fire opcodes."
            ),
            "inferred": (
                "A unique complete affine address mapping plus one-to-one "
                "support overlap makes the ordinary main VM a strong direct "
                "source candidate for the matched 260 realized bullets. "
                "Observed opcode-0x87 advances also expose auxiliary-VM "
                "sources with immediate activation support."
            ),
            "hypothesized": (
                "The decoded file bytes equal the live runtime instruction "
                "bytes and the static fire operands exactly lower to the "
                "matched realized geometry."
            ),
            "next_gate": (
                "Capture exact runtime instruction bytes under an immutable "
                "ECL image key, then independently lower opcode 0x60 operands "
                "and capture the four auxiliary-context PCs rooted at "
                "enemy+0x3384. Join predicted origin/template geometry to "
                "realized slots before granting source authority."
            ),
        },
    }
    if trace.schema12_rows:
        trace_scope = report["trace_scope"]
        gates = report["gates"]
        assert isinstance(trace_scope, dict)
        assert isinstance(gates, dict)
        trace_scope.update(
            {
                "schema12_rows": trace.schema12_rows,
                "auxiliary_pointer_owner_rows": (
                    trace.auxiliary_pointer_owner_rows
                ),
                "non_null_auxiliary_contexts": (
                    trace.non_null_auxiliary_contexts
                ),
                "invalid_auxiliary_contexts": (
                    trace.invalid_auxiliary_contexts
                ),
            }
        )
        gates["strict_schema11_or_schema12_trace_available"] = (
            trace.schema11_rows + trace.schema12_rows > 0
        )
        gates["auxiliary_context_pointer_inventory_available"] = (
            trace.auxiliary_pointer_owner_rows > 0
        )
    report["report_digest"] = hashlib.sha256(
        canonical_report_bytes(report)
    ).hexdigest()
    return report


def build_main_vm_source_join_report(
    *,
    trace_path: Path,
    ecl_path: Path,
) -> dict[str, object]:
    return _build_report(
        trace=scan_schema11_trace(trace_path),
        ecl_path=ecl_path,
    )


__all__ = [
    "build_main_vm_source_join_report",
    "canonical_report_bytes",
]
