from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from analysis.main_vm_source_join.mapping import infer_runtime_base
from analysis.main_vm_source_join.model import (
    ActivationBatch,
    DecisionScope,
    InventoryCapture,
    StaticInstruction,
    VmRow,
)
from analysis.main_vm_source_join.advance import (
    find_auxiliary_start_advances,
    find_fire_advances,
)
from analysis.main_vm_source_join.auxiliary import (
    auxiliary_static_semantics,
    static_auxiliary_target,
)
from analysis.main_vm_source_join.join import join_activation_support
from analysis.main_vm_source_join.trace import (
    MainVmTraceError,
    scan_schema11_trace,
)


def _instruction(
    offset: int,
    opcode: int,
    *,
    size: int = 20,
    time: int = 50,
) -> StaticInstruction:
    return StaticInstruction(
        subroutine_index=3,
        offset=offset,
        time=time,
        opcode=opcode,
        size=size,
        difficulty_mask=0xFF,
        parameter_mask=0,
        arguments=(),
    )


def _row(pc: int, timer: int, *, slot: int = 4) -> VmRow:
    return VmRow(
        slot=slot,
        enemy_pointer=0x5826C0 + slot * 0x53D0,
        enemy_flags=1,
        instruction_pointer=pc,
        timer_fraction_bits=0,
        timer_elapsed=timer,
    )


def _capture(frame: int, row: VmRow) -> InventoryCapture:
    return InventoryCapture(
        scope=DecisionScope(
            gameplay_epoch=2,
            frame=frame + 1,
            stage_route_index=5,
            spell_id=None,
        ),
        prefix_frame_before=frame,
        prefix_frame_after=frame,
        rows=(row,),
    )


def _decision(frame: int) -> dict[str, object]:
    return {
        "kind": "decision",
        "gameplay_epoch": 0,
        "frame": frame,
        "stage_route_index": 5,
        "spell": {
            "active": False,
            "spell_id": 0,
        },
    }


def _audit(frame: int, *, pc: int = 0x510100) -> dict[str, object]:
    return {
        "kind": "bullet_birth_audit",
        "schema_version": 11,
        "gameplay_epoch": 0,
        "frame": frame,
        "stage_route_index": 5,
        "alignment": {
            "enemy_prefix_frame_before": frame - 1,
            "enemy_prefix_frame_after": frame - 1,
        },
        "nonspell_main_vm_inventory": {
            "layout": "th08-enemy-main-ecl-vm-inventory-v1",
            "vm_local_layout": "th08-ecl-vm-local-projection-v1",
            "scope": "ordinary_enemy_pool_prefix_main_vm_only",
            "scanned_slots": 64,
            "active_slots": 1,
            "valid_vms": 1,
            "invalid_active_vms": 0,
            "rows": [
                [
                    0,
                    0x5826C0,
                    1,
                    pc,
                    0,
                    49,
                    [0] * 8,
                    [0] * 8,
                    [0] * 4,
                ]
            ],
            "invalid_rows": [],
            "decode_ms": 0.1,
        },
        "observation": {
            "frame_before": frame - 1,
            "frame_after": frame,
            "previous_frame_before": frame - 2,
            "previous_frame_after": frame - 2,
            "evidence_count": 1,
            "evidence": {
                "format": "columnar_v1",
                "slot": [7],
                "code": [3],
                "status": [2],
                "state": [2],
                "age": [0],
                "previous_state": [0],
                "previous_age": [0],
                "geometry": [[0.0] * 6],
                "transform_flags": [0],
                "geometry_finite": [True],
            },
        },
    }


def _audit_v12(frame: int, *, pc: int = 0x510100) -> dict[str, object]:
    record = json.loads(json.dumps(_audit(frame, pc=pc)))
    record["schema_version"] = 12
    inventory = record["nonspell_main_vm_inventory"]
    assert isinstance(inventory, dict)
    inventory.update(
        {
            "layout": "th08-enemy-main-ecl-vm-inventory-v2",
            "scope": (
                "ordinary_enemy_pool_prefix_main_vm_and_auxiliary_pointers"
            ),
            "auxiliary_context_row_layout": (
                "slot_enemy_pointer_enemy_flags_four_raw_context_pointers"
            ),
            "auxiliary_context_rows": [
                [0, 0x5826C0, 1, [0x02100000, 0, 0x021024B0, 0]]
            ],
            "non_null_auxiliary_contexts": 2,
            "invalid_auxiliary_contexts": 0,
            "invalid_auxiliary_context_rows": [],
        }
    )
    return record


class MainVmSourceMappingTests(unittest.TestCase):
    def test_auxiliary_semantics_distinguish_live_and_saved_state(self) -> None:
        semantics = auxiliary_static_semantics()
        self.assertEqual(semantics["vm_offset_in_context"], 0x08)
        self.assertEqual(semantics["live_local_offsets_in_vm"], "0x18..0x64")
        self.assertEqual(
            semantics["saved_call_frame_area_offset_in_context"],
            0x230,
        )
        self.assertEqual(semantics["saved_call_frame_stride"], 0x228)
        self.assertEqual(semantics["call_depth_offset_in_context"], 0x06)
        self.assertEqual(
            semantics["maximum_restorable_saved_call_frames"],
            15,
        )
        self.assertEqual(semantics["physical_saved_call_frame_slots"], 16)
        self.assertNotIn("maximum_saved_call_frames", semantics)
        self.assertNotIn("local_state_offset_in_context", semantics)

    def test_unique_complete_affine_base_is_selected(self) -> None:
        base = 0x510048
        instructions = (
            _instruction(0x100, 0x60),
            _instruction(0x200, 0x01),
            _instruction(0x300, 0x41),
        )
        result = infer_runtime_base(
            (base + 0x100, base + 0x200, base + 0x300),
            instructions,
        )
        self.assertEqual(result.selected_base, base)
        self.assertTrue(result.unique_complete_match)
        self.assertEqual(result.mapped_unique_pcs, 3)
        self.assertLess(result.runner_up_mapped_unique_pcs, 3)

    def test_tied_base_is_left_unresolved(self) -> None:
        instructions = (
            _instruction(0x100, 0x60),
            _instruction(0x200, 0x01),
        )
        result = infer_runtime_base((0x510100,), instructions)
        self.assertIsNone(result.selected_base)
        self.assertFalse(result.unique_complete_match)

    def test_exact_fire_to_successor_transition_is_retained(self) -> None:
        base = 0x510000
        fire = _instruction(0x100, 0x60)
        successor = _instruction(0x100 + fire.size, 0x41)
        by_pc = {
            base + fire.offset: fire,
            base + successor.offset: successor,
        }
        advances, diagnostics = find_fire_advances(
            (
                _capture(100, _row(base + fire.offset, 49)),
                _capture(102, _row(base + successor.offset, 51)),
            ),
            instructions_by_pc=by_pc,
        )
        self.assertEqual(len(advances), 1)
        self.assertEqual(
            (advances[0].support_start, advances[0].support_end),
            (101, 102),
        )
        self.assertEqual(
            diagnostics["accepted_exact_sequential_advance"],
            1,
        )

    def test_nonsequential_transition_stays_unresolved(self) -> None:
        base = 0x510000
        fire = _instruction(0x100, 0x60)
        successor = _instruction(0x100 + fire.size, 0x41)
        by_pc = {
            base + fire.offset: fire,
            base + successor.offset: successor,
        }
        advances, diagnostics = find_fire_advances(
            (
                _capture(100, _row(base + fire.offset, 49)),
                _capture(102, _row(base + 0x500, 51)),
            ),
            instructions_by_pc=by_pc,
        )
        self.assertEqual(advances, ())
        self.assertEqual(diagnostics["nonsequential_successor"], 1)

    def test_auxiliary_start_uses_the_same_exact_advance_boundary(self) -> None:
        base = 0x510000
        start = _instruction(0x300, 0x87)
        successor = _instruction(0x300 + start.size, 0x01)
        by_pc = {
            base + start.offset: start,
            base + successor.offset: successor,
        }
        advances, diagnostics = find_auxiliary_start_advances(
            (
                _capture(200, _row(base + start.offset, 60)),
                _capture(202, _row(base + successor.offset, 62)),
            ),
            instructions_by_pc=by_pc,
        )
        self.assertEqual(len(advances), 1)
        self.assertEqual(advances[0].opcode, 0x87)
        self.assertEqual(
            diagnostics["accepted_exact_sequential_advance"],
            1,
        )

    def test_static_auxiliary_target_rejects_dynamic_argument(self) -> None:
        instruction = replace(
            _instruction(0x300, 0x87),
            arguments=(0, 54),
        )
        self.assertEqual(
            static_auxiliary_target(instruction, subroutine_count=90),
            54,
        )
        self.assertIsNone(
            static_auxiliary_target(
                replace(instruction, parameter_mask=0x02),
                subroutine_count=90,
            )
        )

    def test_activation_support_join_preserves_one_to_one_scope(self) -> None:
        base = 0x510000
        fire = _instruction(0x100, 0x60)
        successor = _instruction(0x100 + fire.size, 0x41)
        advances, _diagnostics = find_fire_advances(
            (
                _capture(100, _row(base + fire.offset, 49)),
                _capture(102, _row(base + successor.offset, 51)),
            ),
            instructions_by_pc={
                base + fire.offset: fire,
                base + successor.offset: successor,
            },
        )
        batch = ActivationBatch(
            scope=_capture(102, _row(base + successor.offset, 51)).scope,
            support_start=100,
            support_end=102,
            bullet_count=12,
            ages=(0,) * 12,
        )
        joined = join_activation_support(advances, (batch,))
        self.assertEqual(joined.matched_event_indices, (0,))
        self.assertEqual(joined.matched_batch_indices, (0,))
        self.assertEqual(joined.one_to_one_event_indices, (0,))
        self.assertEqual(joined.matched_activation_bullets, 12)


class MainVmSourceTraceTests(unittest.TestCase):
    def test_schema11_trace_scan_retains_support_and_provenance(self) -> None:
        records = (_decision(20), _audit(20))
        raw = b"".join(
            (
                json.dumps(record, sort_keys=True).encode() + b"\n"
                for record in records
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_bytes(raw)
            scan = scan_schema11_trace(path)

        self.assertEqual(scan.trace_sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(scan.schema11_rows, 1)
        self.assertEqual(scan.captures[0].rows[0].instruction_pointer, 0x510100)
        self.assertEqual(
            (
                scan.activation_batches[0].support_start,
                scan.activation_batches[0].support_end,
                scan.activation_batches[0].bullet_count,
            ),
            (18, 20, 1),
        )

    def test_audit_without_preceding_decision_fails_closed(self) -> None:
        raw = json.dumps(_audit(20), sort_keys=True).encode() + b"\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_bytes(raw)
            with self.assertRaisesRegex(
                MainVmTraceError,
                "no matching decision",
            ):
                scan_schema11_trace(path)

    def test_schema12_trace_retains_auxiliary_pointer_summary(self) -> None:
        records = (_decision(20), _audit_v12(20))
        raw = b"".join(
            json.dumps(record, sort_keys=True).encode() + b"\n"
            for record in records
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_bytes(raw)
            scan = scan_schema11_trace(path)

        self.assertEqual(scan.schema11_rows, 0)
        self.assertEqual(scan.schema12_rows, 1)
        self.assertEqual(scan.auxiliary_pointer_owner_rows, 1)
        self.assertEqual(scan.non_null_auxiliary_contexts, 2)
        self.assertEqual(scan.invalid_auxiliary_contexts, 0)
        owners = scan.captures[0].auxiliary_pointer_owners
        self.assertEqual(len(owners), 1)
        self.assertEqual(owners[0].slot, 0)
        self.assertEqual(
            owners[0].context_pointers,
            (0x02100000, 0, 0x021024B0, 0),
        )
        self.assertEqual(owners[0].non_null_count, 2)


if __name__ == "__main__":
    unittest.main()
