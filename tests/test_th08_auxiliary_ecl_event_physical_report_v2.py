from __future__ import annotations

import copy
import json
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest

from analysis.auxiliary_ecl_event.physical_report_v2 import (
    AuxiliaryEclEventPhysicalAuditError,
    build_physical_report_v2,
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


def _observation(
    frame: int,
    *,
    populated: bool,
) -> AuxiliaryVmBatchObservation:
    records: tuple[AuxiliaryVmBatchRecord, ...] = ()
    state_payload_bytes = 0
    if populated:
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
        records = (
            AuxiliaryVmBatchRecord(
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
            ),
        )
        state_payload_bytes = ACTIVE_VM_BYTES
    return AuxiliaryVmBatchObservation(
        expected_manager_frame=frame,
        manager_frame_before=frame,
        manager_frame_after=frame,
        batch_status=BatchStatus.OK,
        records=records,
        process_read_count=5,
        state_payload_bytes=state_payload_bytes,
        layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
        owner_manager_frame_after=frame,
        owner_blob_bytes=64 * 0x53D0,
    )


def _batch_row(
    observation: AuxiliaryVmBatchObservation,
    event: dict[str, object],
    *,
    frame: int,
    previous_emit_ms: float | None,
) -> dict[str, object]:
    return {
        "kind": "auxiliary_vm_batch",
        "schema_version": 5,
        "authority": "trace_only_no_action_authority",
        "frame": frame,
        "snapshot_frame": frame,
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
                "selected_manager_frame": frame,
                "owner_manager_frame_after": frame,
                "context_manager_frame_before": frame,
                "manager_frame_after": frame,
                "process_read_count": 5,
                "owner_blob_bytes": 64 * 0x53D0,
                "active_owner_count": observation.active_owner_count,
                "record_count": len(observation.records),
                "non_null_context_count": (
                    observation.non_null_context_count
                ),
                "usable_context_count": observation.usable_context_count,
                "state_payload_bytes": observation.state_payload_bytes,
                "record_status_bits": (
                    {"0": len(observation.records)}
                    if observation.records
                    else {}
                ),
                "timing_ms": {
                    "native_call": 0.2,
                    "materialize": 0.05,
                },
            }
        ],
        "selected_manager_frame": frame,
        "owner_manager_frame_after": frame,
        "context_manager_frame_before": frame,
        "manager_frame_after": frame,
        "process_read_count": 5,
        "observation": observation.compact_record(
            include_replay_bundle=True
        ),
        "event_derivation": event,
        "timing_ms": {
            "native_call": 0.2,
            "materialize": 0.05,
            "observation": 0.3,
            "event_derive": 0.2,
            "compact": 0.1,
            "previous_emit": previous_emit_ms,
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


class AuxiliaryEclEventPhysicalReportV2Tests(unittest.TestCase):
    def _rows(
        self,
    ) -> tuple[
        dict[str, object],
        dict[str, object],
        dict[str, object],
    ]:
        service = AuxiliaryEclEventTraceService(
            AuxiliaryEclEventConfiguration(
                static_path=_ECL,
                expected_static_sha256=STAGE5_STATIC_SHA256,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
        )
        preparation = service.prepare_if_needed(
            _version(),
            gameplay_epoch=0,
            stage_route_index=5,
            decision_frame=102,
            snapshot_frame=102,
        )
        assert preparation is not None
        empty_observation = _observation(120, populated=False)
        nonempty_observation = _observation(136, populated=True)
        empty_event = service.derive(
            empty_observation,
            runtime_version=_version(),
            gameplay_epoch=0,
            stage_route_index=5,
        )
        nonempty_event = service.derive(
            nonempty_observation,
            runtime_version=_version(),
            gameplay_epoch=0,
            stage_route_index=5,
        )
        return (
            preparation,
            _batch_row(
                empty_observation,
                empty_event,
                frame=120,
                previous_emit_ms=None,
            ),
            _batch_row(
                nonempty_observation,
                nonempty_event,
                frame=136,
                previous_emit_ms=0.2,
            ),
        )

    def _fixture(
        self,
        root: Path,
        *,
        preparation: dict[str, object] | None = None,
        batches: list[dict[str, object]] | None = None,
    ) -> tuple[Path, Path, Path]:
        default_preparation, empty, nonempty = self._rows()
        trace = root / "trace.jsonl"
        baseline = root / "baseline.jsonl"
        session = root / "session.json"
        rows = [
            _decision(100),
            _identity(),
            _decision(102),
        ]
        selected_preparation = (
            default_preparation if preparation is None else preparation
        )
        if selected_preparation:
            rows.append(selected_preparation)
        rows.extend(
            [
                _decision(120),
                _decision(136),
                *(batches if batches is not None else [empty, nonempty]),
                _decision(138),
                {
                    "kind": "summary",
                    "last_frame": 138,
                    "counter_gaps": 0,
                    "hit_count": 0,
                    "termination_reason": "route_complete",
                },
            ]
        )
        _write_rows(trace, rows)
        _write_rows(
            baseline,
            [
                _decision(100),
                _decision(102),
                _decision(120),
                _decision(136),
                _decision(138),
                {
                    "kind": "summary",
                    "termination_reason": "route_complete",
                },
            ],
        )
        session.write_text(
            json.dumps(
                {
                    "run_id": "synthetic-v2",
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

    def test_exact_empty_prefix_bundle_cache_and_oracle_gate_passes(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(Path(temporary))
            report = build_physical_report_v2(
                trace,
                baseline,
                session,
                _ECL,
            )
        self.assertTrue(report["passed"])
        self.assertEqual(report["replay"]["empty_prefix_frames"], [120])
        self.assertEqual(report["replay"]["request_count"], 1)
        self.assertEqual(report["cache"]["misses"], 1)
        self.assertEqual(report["cache"]["entries_after"], 1)
        self.assertTrue(all(report["gates"].values()))

    def test_bundle_payload_tamper_fails_closed(self) -> None:
        _, empty, nonempty = self._rows()
        tampered = copy.deepcopy(nonempty)
        observation = tampered["observation"]
        assert isinstance(observation, dict)
        bundle = observation["replay_state_bundle"]
        assert isinstance(bundle, dict)
        payload = str(bundle["payload_base64"])
        bundle["payload_base64"] = ("A" if payload[0] != "A" else "B") + payload[1:]
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(
                Path(temporary),
                batches=[empty, tampered],
            )
            with self.assertRaisesRegex(
                AuxiliaryEclEventPhysicalAuditError,
                "replay",
            ):
                build_physical_report_v2(
                    trace,
                    baseline,
                    session,
                    _ECL,
                )

    def test_cache_stat_tamper_fails_closed(self) -> None:
        _, empty, nonempty = self._rows()
        tampered = copy.deepcopy(nonempty)
        event = tampered["event_derivation"]
        assert isinstance(event, dict)
        cache = event["cache"]
        assert isinstance(cache, dict)
        cache["misses"] = 0
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(
                Path(temporary),
                batches=[empty, tampered],
            )
            with self.assertRaisesRegex(
                AuxiliaryEclEventPhysicalAuditError,
                "cache statistics",
            ):
                build_physical_report_v2(
                    trace,
                    baseline,
                    session,
                    _ECL,
                )

    def test_empty_after_nonempty_rejects_prefix_gate(self) -> None:
        _, empty, nonempty = self._rows()
        late_empty = copy.deepcopy(empty)
        late_event = late_empty["event_derivation"]
        assert isinstance(late_event, dict)
        late_cache = late_event["cache"]
        assert isinstance(late_cache, dict)
        late_cache["entries_after"] = 1
        with TemporaryDirectory() as temporary:
            trace, baseline, session = self._fixture(
                Path(temporary),
                batches=[nonempty, late_empty],
            )
            report = build_physical_report_v2(
                trace,
                baseline,
                session,
                _ECL,
            )
        self.assertFalse(report["passed"])
        self.assertFalse(report["gates"]["empty_prefix_valid"])

    def test_missing_or_slow_preparation_rejects_gate(self) -> None:
        preparation, empty, nonempty = self._rows()
        cases: list[dict[str, object]] = []
        missing: dict[str, object] = {}
        cases.append(missing)
        slow = copy.deepcopy(preparation)
        timing = slow["timing_ms"]
        assert isinstance(timing, dict)
        timing["total"] = 8.01
        cases.append(slow)
        for candidate in cases:
            with self.subTest(candidate=candidate):
                with TemporaryDirectory() as temporary:
                    trace, baseline, session = self._fixture(
                        Path(temporary),
                        preparation=candidate,
                        batches=[empty, nonempty],
                    )
                    report = build_physical_report_v2(
                        trace,
                        baseline,
                        session,
                        _ECL,
                    )
                self.assertFalse(report["passed"])
                self.assertFalse(
                    report["gates"]["preparation_exact_and_bounded"]
                )


if __name__ == "__main__":
    unittest.main()
