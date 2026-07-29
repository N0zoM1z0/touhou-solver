from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest

from analysis.auxiliary_ecl_event.physical_report import (
    AuxiliaryEclEventPhysicalAuditError,
    build_physical_report,
)
from analysis.th08_runtime_ecl_identity_audit import (
    STAGE5_STATIC_LABEL,
    STAGE5_STATIC_LENGTH,
    STAGE5_STATIC_SHA256,
)
from th08_ecl_tool.core import parse_ecl
from th08_live.auxiliary_vm.event_service import (
    AuxiliaryEclEventConfiguration,
    AuxiliaryEclEventTraceService,
)
from th08_live.auxiliary_vm.model import (
    ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
    ACTIVE_VM_BYTES,
    AUXILIARY_VM_BATCH_LAYOUT_V2,
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchRecord,
    BatchStatus,
    RecordStatus,
)
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion
from th08_runtime.game_state import EXPECTED_EXE_SHA256


_ROOT = Path(__file__).resolve().parents[1]
_ECL = _ROOT / STAGE5_STATIC_LABEL
_BASE = 0x02100000


def _decision(frame: int) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": frame,
        "gameplay_epoch": 0,
        "stage_route_index": 5,
        "mask": 1,
        "bomb": False,
        "hit_started": False,
        "timing_ms": {"previous_iteration": 0.5},
    }


def _identity() -> dict[str, object]:
    return {
        "schema": "th08-runtime-ecl-identity-observation-v1",
        "kind": "runtime_ecl_identity",
        "status": "exact_match",
        "authority": "trace_only_instruction_byte_identity",
        "pid": 1234,
        "executable_sha256": EXPECTED_EXE_SHA256,
        "route_id": 2,
        "difficulty_index": 3,
        "stage_route_index": 5,
        "gameplay_epoch": 0,
        "decision_frame": 102,
        "snapshot_frame": 102,
        "static_image": {
            "label": STAGE5_STATIC_LABEL,
            "length": STAGE5_STATIC_LENGTH,
            "sha256": STAGE5_STATIC_SHA256,
        },
        "capture": {
            "schema": "th08-runtime-ecl-image-capture-v1",
            "runtime_base": _BASE,
            "image_length": STAGE5_STATIC_LENGTH,
            "subroutine_count": 80,
            "timeline_count": 1,
            "relocated_sha256": "1" * 64,
            "normalized_sha256": STAGE5_STATIC_SHA256,
            "capture_ms": 0.5,
            "read_count": 4,
        },
        "identity": {
            "schema": "th08-runtime-ecl-image-identity-v1",
            "exact_match": True,
            "static_sha256": STAGE5_STATIC_SHA256,
            "normalized_runtime_sha256": STAGE5_STATIC_SHA256,
            "image_length": STAGE5_STATIC_LENGTH,
            "first_difference_offset": None,
        },
        "error": None,
        "transaction_ms": 0.75,
    }


def _version() -> RuntimeEclAcceptedVersion:
    return RuntimeEclAcceptedVersion(
        runtime_base=_BASE,
        image_length=STAGE5_STATIC_LENGTH,
        relocated_sha256="1" * 64,
        normalized_sha256=STAGE5_STATIC_SHA256,
        static_sha256=STAGE5_STATIC_SHA256,
        route_id=2,
        difficulty_index=3,
        stage_route_index=5,
        gameplay_epoch=0,
        decision_frame=102,
        snapshot_frame=102,
    )


def _batch() -> dict[str, object]:
    ecl = parse_ecl(_ECL)
    pc = _BASE + ecl.subroutines[69].instructions[0].offset
    active_vm = bytearray(ACTIVE_VM_BYTES)
    struct.pack_into("<IiIi", active_vm, 0, pc, -1, 0, 0)
    struct.pack_into(
        "<I",
        active_vm,
        ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
        1,
    )
    record = AuxiliaryVmBatchRecord(
        slot=0,
        auxiliary_index=0,
        enemy_pointer=0x005826C0,
        context_pointer=0x02200000,
        context_pointer_after=0x02200000,
        enemy_flags_before=1,
        enemy_flags_after=1,
        status=RecordStatus.OK,
        target_subroutine=69,
        call_depth=0,
        auxiliary_marker=1,
        active_vm=bytes(active_vm),
        saved_frames=(),
    )
    observation = AuxiliaryVmBatchObservation(
        expected_manager_frame=102,
        manager_frame_before=102,
        manager_frame_after=102,
        batch_status=BatchStatus.OK,
        records=(record,),
        process_read_count=5,
        state_payload_bytes=ACTIVE_VM_BYTES,
        layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
        owner_manager_frame_after=102,
        owner_blob_bytes=64 * 0x53D0,
    )
    event_service = AuxiliaryEclEventTraceService(
        AuxiliaryEclEventConfiguration(
            static_path=_ECL,
            expected_static_sha256=STAGE5_STATIC_SHA256,
            expected_route_id=2,
            expected_difficulty_index=3,
            expected_stage_route_index=5,
        )
    )
    preparation = event_service.prepare_if_needed(
        _version(),
        gameplay_epoch=0,
        stage_route_index=5,
        decision_frame=101,
        snapshot_frame=101,
    )
    assert preparation is not None
    assert preparation["status"] == "success"
    event = event_service.derive(
        observation,
        runtime_version=_version(),
        gameplay_epoch=0,
        stage_route_index=5,
    )
    event["schema"] = "th08-auxiliary-ecl-event-derivation-v1"
    event.pop("cache")
    return {
        "kind": "auxiliary_vm_batch",
        "schema_version": 4,
        "authority": "trace_only_no_action_authority",
        "frame": 102,
        "snapshot_frame": 102,
        "gameplay_epoch": 0,
        "stage_route_index": 5,
        "spell_id": 107,
        "cadence_frames": 16,
        "spell_id_filter": 107,
        "native_call_mode": "gil-held",
        "status": "success",
        "error": None,
        "attempt_limit": 3,
        "attempt_count": 1,
        "selected_attempt_index": 0,
        "attempts": [
            {
                "index": 0,
                "success": True,
                "retryable": False,
                "batch_status_bits": 0,
                "selected_manager_frame": 102,
                "owner_manager_frame_after": 102,
                "context_manager_frame_before": 102,
                "manager_frame_after": 102,
                "process_read_count": 5,
                "owner_blob_bytes": 64 * 0x53D0,
                "active_owner_count": 1,
                "record_count": 1,
                "non_null_context_count": 1,
                "usable_context_count": 1,
                "state_payload_bytes": ACTIVE_VM_BYTES,
                "record_status_bits": {"0": 1},
                "timing_ms": {
                    "native_call": 0.2,
                    "materialize": 0.05,
                },
            }
        ],
        "selected_manager_frame": 102,
        "owner_manager_frame_after": 102,
        "context_manager_frame_before": 102,
        "manager_frame_after": 102,
        "process_read_count": 5,
        "observation": observation.compact_record(
            include_replay_state=True
        ),
        "event_derivation": event,
        "timing_ms": {
            "native_call": 0.2,
            "materialize": 0.05,
            "observation": 0.3,
            "event_derive": 0.2,
            "compact": 0.1,
            "previous_emit": 0.2,
            "total": 0.8,
        },
    }


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


class AuxiliaryEclEventPhysicalReportTests(unittest.TestCase):
    def _fixture(
        self,
        root: Path,
        *,
        batch: dict[str, object] | None = None,
    ) -> tuple[Path, Path, Path]:
        trace = root / "trace.jsonl"
        baseline = root / "baseline.jsonl"
        session = root / "session.json"
        _write_rows(
            trace,
            [
                _decision(100),
                _identity(),
                _decision(102),
                _batch() if batch is None else batch,
                _decision(104),
                {
                    "kind": "summary",
                    "last_frame": 104,
                    "counter_gaps": 0,
                    "hit_count": 0,
                    "termination_reason": "route_complete",
                },
            ],
        )
        _write_rows(
            baseline,
            [
                _decision(100),
                _decision(102),
                _decision(104),
                {
                    "kind": "summary",
                    "termination_reason": "route_complete",
                },
            ],
        )
        session.write_text(
            json.dumps(
                {
                    "run_id": "synthetic",
                    "status": "completed",
                    "trial_accepted": True,
                    "hard_no_bomb": True,
                    "trace_auxiliary_vm_batches": True,
                    "trace_auxiliary_ecl_events": True,
                    "auxiliary_vm_batch_spell_id": 107,
                    "runtime_ecl_static_sha256": STAGE5_STATIC_SHA256,
                    "agent_summary": {
                        "termination_reason": "route_complete",
                        "hit_count": 0,
                    },
                }
            ),
            encoding="utf-8",
        )
        return trace, baseline, session

    def test_exact_replay_and_transport_gate_passes(self) -> None:
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(Path(temporary))
            report = build_physical_report(
                trace,
                baseline,
                session,
                _ECL,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["replay"]["request_count"], 1)
        self.assertEqual(report["replay"]["complete_count"], 1)
        self.assertEqual(report["replay"]["unknown_count"], 0)
        self.assertEqual(
            report["replay"]["target_subroutines"],
            {"69": 1},
        )
        self.assertEqual(
            report["authority_boundary"]["physical_action"],
            "none",
        )

    def test_raw_hash_tamper_fails_closed(self) -> None:
        batch = _batch()
        observation = batch["observation"]
        assert isinstance(observation, dict)
        records = observation["records"]
        assert isinstance(records, list)
        records[0]["active_vm_sha256"] = "0" * 64
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(
                Path(temporary),
                batch=batch,
            )
            with self.assertRaisesRegex(
                AuxiliaryEclEventPhysicalAuditError,
                "hash mismatch",
            ):
                build_physical_report(trace, baseline, session, _ECL)

    def test_oracle_result_tamper_fails_closed(self) -> None:
        batch = copy.deepcopy(_batch())
        event = batch["event_derivation"]
        assert isinstance(event, dict)
        lowering = event["lowering"]
        assert isinstance(lowering, dict)
        results = lowering["unique_results"]
        assert isinstance(results, list)
        intents = results[0]["intents"]
        assert isinstance(intents, list)
        intents[0]["opcode"] += 1
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(
                Path(temporary),
                batch=batch,
            )
            with self.assertRaisesRegex(
                AuxiliaryEclEventPhysicalAuditError,
                "byte oracle",
            ):
                build_physical_report(trace, baseline, session, _ECL)

    def test_runtime_version_tamper_fails_closed(self) -> None:
        batch = _batch()
        event = batch["event_derivation"]
        assert isinstance(event, dict)
        version = event["runtime_version"]
        assert isinstance(version, dict)
        version["runtime_base"] += 4
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(
                Path(temporary),
                batch=batch,
            )
            with self.assertRaisesRegex(
                AuxiliaryEclEventPhysicalAuditError,
                "runtime version",
            ):
                build_physical_report(trace, baseline, session, _ECL)

    def test_static_digest_argument_cannot_change_the_gate(self) -> None:
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(Path(temporary))
            with self.assertRaisesRegex(
                AuxiliaryEclEventPhysicalAuditError,
                "static Stage-5",
            ):
                build_physical_report(
                    trace,
                    baseline,
                    session,
                    _ECL,
                    expected_ecl_sha256=hashlib.sha256(b"other").hexdigest(),
                )


if __name__ == "__main__":
    unittest.main()
