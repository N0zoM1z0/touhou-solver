from __future__ import annotations

import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from analysis.auxiliary_pointer_inventory.analysis import (
    analyze_pointer_dynamics,
)
from analysis.auxiliary_pointer_inventory.report import (
    AuxiliaryPointerReportError,
    build_auxiliary_pointer_report,
    canonical_report_bytes,
)
from analysis.main_vm_source_join.model import (
    AuxiliaryPointerOwner,
    DecisionScope,
    InventoryCapture,
    TraceScan,
)


def _capture(
    frame: int,
    *owners: AuxiliaryPointerOwner,
    epoch: int = 1,
) -> InventoryCapture:
    return InventoryCapture(
        scope=DecisionScope(
            gameplay_epoch=epoch,
            frame=frame,
            stage_route_index=4,
            spell_id=None,
        ),
        prefix_frame_before=frame,
        prefix_frame_after=frame,
        rows=(),
        auxiliary_pointer_owners=owners,
    )


def _owner(
    slot: int,
    pointers: tuple[int, int, int, int],
    *,
    flags: int = 1,
) -> AuxiliaryPointerOwner:
    return AuxiliaryPointerOwner(
        slot=slot,
        enemy_pointer=0x005826C0 + slot * 0x53D0,
        enemy_flags=flags,
        context_pointers=pointers,
    )


class AuxiliaryPointerDynamicsTests(unittest.TestCase):
    def test_transitions_and_reuse_remain_observation_level(self) -> None:
        captures = (
            _capture(10, _owner(0, (0x2100000, 0, 0x21024B0, 0))),
            _capture(12, _owner(0, (0x2100000, 0x2200000, 0, 0))),
            _capture(15, _owner(0, (0x2300000, 0x2200000, 0, 0))),
            _capture(18, _owner(1, (0x2100000, 0, 0, 0))),
        )
        dynamics = analyze_pointer_dynamics(captures)

        self.assertEqual(dynamics.comparable_capture_pairs, 3)
        self.assertEqual(dynamics.capture_frame_gaps, (2, 3, 3))
        self.assertEqual(
            dynamics.owner_transitions,
            {
                "same_slot_present": 2,
                "slot_appeared": 1,
                "slot_disappeared": 1,
                "enemy_flags_changed": 0,
            },
        )
        self.assertEqual(
            dynamics.pointer_transitions,
            {
                "same_null": 3,
                "same_non_null": 2,
                "null_to_non_null": 1,
                "non_null_to_null": 1,
                "non_null_replaced": 1,
            },
        )
        self.assertEqual(
            dynamics.pointer_tokens[0x2100000],
            frozenset({(0, 0), (1, 0)}),
        )
        self.assertTrue(
            any(
                run.pointer == 0x2200000
                and run.observation_count == 2
                and run.observed_frame_span == 3
                for run in dynamics.observed_runs
            )
        )

    def test_epoch_boundary_censors_runs_and_resets_transitions(self) -> None:
        dynamics = analyze_pointer_dynamics(
            (
                _capture(10, _owner(0, (0x2100000, 0, 0, 0)), epoch=1),
                _capture(2, _owner(0, (0x2100000, 0, 0, 0)), epoch=2),
            )
        )
        self.assertEqual(dynamics.comparable_capture_pairs, 0)
        self.assertEqual(sum(dynamics.pointer_transitions.values()), 0)
        self.assertEqual(len(dynamics.observed_runs), 2)
        self.assertTrue(
            all(
                run.left_censored and run.right_censored
                for run in dynamics.observed_runs
            )
        )


class AuxiliaryPointerReportTests(unittest.TestCase):
    def test_report_selects_bounded_native_batch_and_hashes_content(self) -> None:
        captures = (
            _capture(10, _owner(0, (0x2100000, 0, 0, 0))),
            _capture(12, _owner(0, (0x2100000, 0x2200000, 0, 0))),
        )
        scan = TraceScan(
            trace_sha256="a" * 64,
            trace_bytes=123,
            trace_lines=4,
            schema11_rows=0,
            captures=captures,
            activation_batches=(),
            invalid_active_vm_rows=0,
            schema12_rows=2,
            auxiliary_pointer_owner_rows=2,
            non_null_auxiliary_contexts=3,
            invalid_auxiliary_contexts=0,
        )
        with patch(
            "analysis.auxiliary_pointer_inventory.report.scan_schema11_trace",
            return_value=scan,
        ):
            report = build_auxiliary_pointer_report(Path("trace.jsonl"))

        self.assertEqual(
            report["delivery_decision"]["selected_design"],
            "native_compact_batch",
        )
        self.assertEqual(
            report["capture_density"]["non_null_contexts_per_capture"]["max"],
            2,
        )
        digest = report.pop("report_digest")
        self.assertEqual(
            digest,
            hashlib.sha256(canonical_report_bytes(report)).hexdigest(),
        )

    def test_report_rejects_schema11_pointer_substitution(self) -> None:
        scan = TraceScan(
            trace_sha256="b" * 64,
            trace_bytes=1,
            trace_lines=1,
            schema11_rows=1,
            captures=(_capture(10),),
            activation_batches=(),
            invalid_active_vm_rows=0,
        )
        with (
            patch(
                "analysis.auxiliary_pointer_inventory.report."
                "scan_schema11_trace",
                return_value=scan,
            ),
            self.assertRaisesRegex(
                AuxiliaryPointerReportError,
                "pure schema-12",
            ),
        ):
            build_auxiliary_pointer_report(Path("trace.jsonl"))


if __name__ == "__main__":
    unittest.main()
