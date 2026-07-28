from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.auxiliary_vm_batch_trace import main, scan_trace
from th08_live.auxiliary_vm import (
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchRecord,
    BatchStatus,
    RecordStatus,
)
from th08_live.auxiliary_vm.model import (
    ACTIVE_VM_BYTES,
    AUXILIARY_VM_BATCH_LAYOUT_V2,
)


def _decision(frame: int) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": frame,
        "gameplay_epoch": 1,
        "stage_route_index": 5,
        "mask": 0,
        "bomb": False,
        "hit_started": False,
        "timing_ms": {"previous_iteration": 10.0},
    }


def _batch(frame: int) -> dict[str, object]:
    selected_frame = frame + 1
    observation = AuxiliaryVmBatchObservation(
        expected_manager_frame=selected_frame,
        manager_frame_before=selected_frame,
        manager_frame_after=selected_frame,
        batch_status=BatchStatus.OK,
        records=(
            AuxiliaryVmBatchRecord(
                slot=0,
                auxiliary_index=0,
                enemy_pointer=0x005826C0,
                context_pointer=0x02100000,
                context_pointer_after=0x02100000,
                enemy_flags_before=1,
                enemy_flags_after=1,
                status=RecordStatus.OK,
                target_subroutine=54,
                call_depth=0,
                auxiliary_marker=1,
                active_vm=bytes(ACTIVE_VM_BYTES),
                saved_frames=(),
            ),
        ),
        process_read_count=9,
        state_payload_bytes=ACTIVE_VM_BYTES,
        layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
        owner_manager_frame_after=selected_frame,
        owner_blob_bytes=0x53D0,
    )
    return {
        "kind": "auxiliary_vm_batch",
        "schema_version": 3,
        "authority": "trace_only_no_action_authority",
        "frame": frame,
        "snapshot_frame": frame,
        "gameplay_epoch": 1,
        "stage_route_index": 5,
        "spell_id": 107,
        "cadence_frames": 16,
        "spell_id_filter": 107,
        "native_call_mode": "gil-held",
        "status": "success",
        "error": None,
        "attempt_limit": 3,
        "attempt_count": 2,
        "selected_attempt_index": 1,
        "attempts": [
            {
                "index": 0,
                "success": False,
                "retryable": True,
                "batch_status_bits": 2,
                "selected_manager_frame": frame,
                "owner_manager_frame_after": frame,
                "context_manager_frame_before": frame,
                "manager_frame_after": frame + 1,
                "process_read_count": 9,
                "owner_blob_bytes": 0x53D0,
                "active_owner_count": 1,
                "record_count": 1,
                "non_null_context_count": 1,
                "usable_context_count": 0,
                "state_payload_bytes": ACTIVE_VM_BYTES,
                "record_status_bits": {"0": 1},
                "timing_ms": {
                    "native_call": 0.2,
                    "materialize": 0.05,
                },
            },
            {
                "index": 1,
                "success": True,
                "retryable": False,
                "batch_status_bits": 0,
                "selected_manager_frame": selected_frame,
                "owner_manager_frame_after": selected_frame,
                "context_manager_frame_before": selected_frame,
                "manager_frame_after": selected_frame,
                "process_read_count": 9,
                "owner_blob_bytes": 0x53D0,
                "active_owner_count": 1,
                "record_count": 1,
                "non_null_context_count": 1,
                "usable_context_count": 1,
                "state_payload_bytes": ACTIVE_VM_BYTES,
                "record_status_bits": {"0": 1},
                "timing_ms": {
                    "native_call": 0.25,
                    "materialize": 0.1,
                },
            },
        ],
        "selected_manager_frame": selected_frame,
        "owner_manager_frame_after": selected_frame,
        "context_manager_frame_before": selected_frame,
        "manager_frame_after": selected_frame,
        "process_read_count": 18,
        "observation": observation.compact_record(),
        "timing_ms": {
            "native_call": 0.45,
            "materialize": 0.15,
            "observation": 0.4,
            "compact": 0.05,
            "total": 1.0,
        },
    }


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


class AuxiliaryVmBatchTraceTests(unittest.TestCase):
    def test_compact_physical_gate_passes_strict_fixture(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            trace = root / "trace.jsonl"
            baseline = root / "baseline.jsonl"
            session = root / "session.json"
            output = root / "report.json"
            _write_rows(
                trace,
                [
                    _decision(100),
                    _batch(100),
                    _decision(102),
                    {
                        "kind": "summary",
                        "last_frame": 102,
                        "counter_gaps": 0,
                        "hit_count": 0,
                        "termination_reason": "route_complete",
                    },
                ],
            )
            _write_rows(
                baseline,
                [_decision(100), _decision(101)],
            )
            session.write_text(
                json.dumps(
                    {
                        "run_id": "synthetic",
                        "status": "completed",
                        "trial_accepted": True,
                        "hard_no_bomb": True,
                        "agent_summary": {
                            "termination_reason": "route_complete",
                            "decision_count": 2,
                            "hit_count": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = main(
                [
                    str(trace),
                    str(output),
                    "--baseline",
                    str(baseline),
                    "--session",
                    str(session),
                ]
            )
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result, 0)
        self.assertTrue(report["passed"])
        self.assertEqual(report["batch"]["count"], 1)
        self.assertEqual(
            report["batch"]["retried_transaction_count"],
            1,
        )

    def test_frame_mismatch_is_retained_as_validation_error(self) -> None:
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            row = _batch(100)
            row["owner_manager_frame_after"] = 102
            observation = row["observation"]
            assert isinstance(observation, dict)
            observation["owner_manager_frame_after"] = 102
            _write_rows(trace, [row])
            scan = scan_trace(trace, audit_batches=True)
        self.assertTrue(scan.validation_errors)

    def test_forged_retryability_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            row = _batch(100)
            attempts = row["attempts"]
            assert isinstance(attempts, list)
            attempts[0]["retryable"] = False
            _write_rows(trace, [row])
            scan = scan_trace(trace, audit_batches=True)
        self.assertTrue(
            any(
                "forged retryable" in error
                for error in scan.validation_errors
            )
        )

    def test_selected_attempt_summary_mismatch_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            row = _batch(100)
            attempts = row["attempts"]
            assert isinstance(attempts, list)
            attempts[1]["usable_context_count"] = 0
            _write_rows(trace, [row])
            scan = scan_trace(trace, audit_batches=True)
        self.assertTrue(
            any(
                "selected attempt/observation usable_context_count mismatch"
                in error
                for error in scan.validation_errors
            )
        )

    def test_hidden_attempt_and_timing_sum_are_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            row = _batch(100)
            row["attempt_count"] = 1
            timing = row["timing_ms"]
            assert isinstance(timing, dict)
            timing["native_call"] = 0.2
            _write_rows(trace, [row])
            with self.assertRaisesRegex(
                ValueError,
                "invalid attempt count/array",
            ):
                scan_trace(trace, audit_batches=True)

            row = _batch(100)
            timing = row["timing_ms"]
            assert isinstance(timing, dict)
            timing["native_call"] = 0.44
            _write_rows(trace, [row])
            scan = scan_trace(trace, audit_batches=True)
        self.assertTrue(
            any(
                "native_call sum mismatch" in error
                for error in scan.validation_errors
            )
        )


if __name__ == "__main__":
    unittest.main()
