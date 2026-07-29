from __future__ import annotations

import base64
import hashlib
import unittest
import zlib

from th08_live.auxiliary_vm import (
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchRecord,
    AuxiliaryVmBatchTraceService,
    BatchStatus,
    NativeAuxiliaryVmBatchDiagnostics,
    RecordStatus,
    auxiliary_vm_batch_attempt_retryable,
)
from th08_live.auxiliary_vm.model import (
    AUXILIARY_VM_BATCH_LAYOUT_V2,
    UNOBSERVED_MANAGER_FRAME,
)
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion


class _Reader:
    def __init__(self, capture_frame: int) -> None:
        self.capture_frame = capture_frame

    def u32(self, _address: int) -> int:
        raise AssertionError("v3 service must not read a Python frame bracket")

    def read(self, address: int, size: int) -> bytes:
        raise AssertionError(
            f"v3 service must not copy Python owner bytes at {address:#x}"
            f"/{size}"
        )


class _Capture:
    def __init__(
        self,
        *,
        batch_statuses: tuple[BatchStatus, ...] = (BatchStatus.OK,),
        records: tuple[AuxiliaryVmBatchRecord, ...] = (),
    ) -> None:
        self.calls: list[dict[str, object]] = []
        self.batch_statuses = batch_statuses
        self.records = records

    def capture_process(
        self,
        reader,
        **arguments,
    ) -> AuxiliaryVmBatchObservation:
        call_index = len(self.calls)
        if call_index >= len(self.batch_statuses):
            if self.batch_statuses != (BatchStatus.OK,):
                raise AssertionError("unexpected auxiliary-VM retry")
            status_index = 0
        else:
            status_index = call_index
        self.calls.append(dict(arguments))
        batch_status = self.batch_statuses[status_index]
        selected = reader.capture_frame + call_index
        owner_after = (
            selected + 1
            if batch_status
            & BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
            else selected
        )
        context_frame = (
            UNOBSERVED_MANAGER_FRAME
            if batch_status
            & BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
            else (
                selected + 1
                if batch_status & BatchStatus.FRAME_BEFORE_MISMATCH
                else selected
            )
        )
        final_frame = (
            UNOBSERVED_MANAGER_FRAME
            if batch_status
            & (
                BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
                | BatchStatus.FRAME_BEFORE_MISMATCH
            )
            else (
                selected + 1
                if batch_status & BatchStatus.FRAME_AFTER_MISMATCH
                else selected
            )
        )
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=selected,
            manager_frame_before=context_frame,
            manager_frame_after=final_frame,
            batch_status=batch_status,
            records=self.records,
            process_read_count=(
                3
                if batch_status
                & BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
                else 5
            ),
            state_payload_bytes=0,
            layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
            owner_manager_frame_after=owner_after,
            owner_blob_bytes=64 * 0x53D0,
        )

    @staticmethod
    def diagnostics() -> NativeAuxiliaryVmBatchDiagnostics:
        return NativeAuxiliaryVmBatchDiagnostics(0.25, 0.1)


class _EventService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.unavailable_calls: list[str] = []

    def derive(self, observation, **arguments) -> dict[str, object]:
        self.calls.append(
            {
                "observation": observation,
                **arguments,
            }
        )
        return {"status": "derived"}

    def unavailable_record(
        self,
        reason: str,
        **_arguments,
    ) -> dict[str, object]:
        self.unavailable_calls.append(reason)
        return {"status": reason}


class _FailingCapture:
    @staticmethod
    def capture_process(_reader, **_arguments) -> AuxiliaryVmBatchObservation:
        raise OSError("unavailable")


class AuxiliaryVmBatchTraceServiceTests(unittest.TestCase):
    @staticmethod
    def _observation(
        *,
        batch_status: BatchStatus,
        record_status: RecordStatus = RecordStatus.OK,
    ) -> AuxiliaryVmBatchObservation:
        records = ()
        if record_status != RecordStatus.OK:
            records = (
                AuxiliaryVmBatchRecord(
                    slot=0,
                    auxiliary_index=0,
                    enemy_pointer=0x005826C0,
                    context_pointer=0x02100000,
                    context_pointer_after=0x02100000,
                    enemy_flags_before=1,
                    enemy_flags_after=1,
                    status=record_status,
                    target_subroutine=None,
                    call_depth=None,
                    auxiliary_marker=None,
                    active_vm=b"",
                    saved_frames=(),
                ),
            )
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=100,
            manager_frame_before=100,
            manager_frame_after=101,
            batch_status=batch_status,
            records=records,
            process_read_count=8,
            state_payload_bytes=0,
            layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
            owner_manager_frame_after=100,
            owner_blob_bytes=64 * 0x53D0,
        )

    def test_spell_filter_and_changed_frame_cadence(self) -> None:
        capture = _Capture()
        service = AuxiliaryVmBatchTraceService(
            cadence_frames=16,
            spell_id_filter=107,
            capture=capture,
        )
        filtered = service.observe_if_due(
            _Reader(103),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=106,
        )
        self.assertIsNone(filtered)
        self.assertEqual(capture.calls, [])

        first = service.observe_if_due(
            _Reader(103),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=107,
        )
        self.assertIsNotNone(first)
        assert first is not None
        self.assertEqual(first["status"], "success")
        self.assertEqual(first["schema_version"], 3)
        self.assertEqual(first["snapshot_frame"], 100)
        self.assertEqual(first["selected_manager_frame"], 103)
        self.assertEqual(first["process_read_count"], 5)
        self.assertNotIn("expected_manager_frame", capture.calls[0])

        not_due = service.observe_if_due(
            _Reader(113),
            decision_frame=110,
            manager_frame=110,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=107,
        )
        self.assertIsNone(not_due)
        due = service.observe_if_due(
            _Reader(119),
            decision_frame=116,
            manager_frame=116,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=107,
        )
        self.assertIsNotNone(due)
        self.assertEqual(len(capture.calls), 2)

    def test_owner_frame_change_retries_and_selects_later_version(self) -> None:
        capture = _Capture(
            batch_statuses=(
                BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH,
                BatchStatus.OK,
            )
        )
        service = AuxiliaryVmBatchTraceService(capture=capture)
        record = service.observe_if_due(
            _Reader(100),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=None,
        )
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["status"], "success")
        self.assertIsNotNone(record["observation"])
        self.assertEqual(record["selected_manager_frame"], 101)
        self.assertEqual(record["attempt_count"], 2)
        self.assertEqual(record["selected_attempt_index"], 1)
        attempts = record["attempts"]
        assert isinstance(attempts, list)
        self.assertTrue(attempts[0]["retryable"])
        self.assertFalse(attempts[1]["retryable"])
        self.assertEqual(record["process_read_count"], 8)
        timing = record["timing_ms"]
        assert isinstance(timing, dict)
        self.assertEqual(timing["native_call"], 0.5)
        self.assertEqual(timing["materialize"], 0.2)
        self.assertEqual(len(capture.calls), 2)

    def test_second_retry_success_selects_third_version(self) -> None:
        capture = _Capture(
            batch_statuses=(
                BatchStatus.FRAME_AFTER_MISMATCH,
                BatchStatus.FRAME_BEFORE_MISMATCH,
                BatchStatus.OK,
            )
        )
        record = AuxiliaryVmBatchTraceService(
            capture=capture
        ).observe_if_due(
            _Reader(100),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=None,
        )
        assert record is not None
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["selected_manager_frame"], 102)
        self.assertEqual(record["attempt_count"], 3)
        self.assertEqual(record["selected_attempt_index"], 2)
        self.assertEqual(record["process_read_count"], 15)
        self.assertEqual(len(capture.calls), 3)

    def test_retry_exhaustion_and_terminal_failure_stop_exactly(self) -> None:
        exhausted_capture = _Capture(
            batch_statuses=(
                BatchStatus.FRAME_AFTER_MISMATCH,
                BatchStatus.FRAME_BEFORE_MISMATCH,
                BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH,
            )
        )
        exhausted = AuxiliaryVmBatchTraceService(
            capture=exhausted_capture
        ).observe_if_due(
            _Reader(100),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=None,
        )
        assert exhausted is not None
        self.assertEqual(exhausted["status"], "retry_exhausted")
        self.assertEqual(exhausted["attempt_count"], 3)
        self.assertIsNone(exhausted["observation"])
        self.assertEqual(len(exhausted_capture.calls), 3)

        terminal_capture = _Capture(
            batch_statuses=(BatchStatus.PROCESS_READ_FAILED,)
        )
        terminal = AuxiliaryVmBatchTraceService(
            capture=terminal_capture
        ).observe_if_due(
            _Reader(100),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=None,
        )
        assert terminal is not None
        self.assertEqual(terminal["status"], "terminal_rejected")
        self.assertEqual(terminal["attempt_count"], 1)
        self.assertEqual(len(terminal_capture.calls), 1)

    def test_retry_classifier_rejects_semantic_record_failure(self) -> None:
        self.assertFalse(
            auxiliary_vm_batch_attempt_retryable(
                self._observation(
                    batch_status=BatchStatus.FRAME_AFTER_MISMATCH,
                    record_status=RecordStatus.ACTIVE_PC_INVALID,
                )
            )
        )

    def test_retry_classifier_has_a_closed_status_whitelist(self) -> None:
        allowed_batches = (
            BatchStatus.FRAME_BEFORE_MISMATCH,
            BatchStatus.FRAME_AFTER_MISMATCH,
            BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH,
            (
                BatchStatus.FRAME_BEFORE_MISMATCH
                | BatchStatus.FRAME_AFTER_MISMATCH
                | BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
            ),
        )
        allowed_records = (
            RecordStatus.NULL,
            RecordStatus.CONTEXT_CHANGED,
            RecordStatus.OWNER_INACTIVE,
            RecordStatus.OWNER_FLAGS_CHANGED,
            RecordStatus.POINTER_CHANGED,
            (
                RecordStatus.CONTEXT_CHANGED
                | RecordStatus.OWNER_FLAGS_CHANGED
            ),
        )
        for batch_status in allowed_batches:
            with self.subTest(batch_status=batch_status):
                self.assertTrue(
                    auxiliary_vm_batch_attempt_retryable(
                        self._observation(batch_status=batch_status)
                    )
                )
            for record_status in allowed_records:
                with self.subTest(
                    batch_status=batch_status,
                    record_status=record_status,
                ):
                    self.assertTrue(
                        auxiliary_vm_batch_attempt_retryable(
                            self._observation(
                                batch_status=batch_status,
                                record_status=record_status,
                            )
                        )
                    )

        forbidden_batches = (
            BatchStatus.OUTPUT_CAPACITY,
            BatchStatus.OWNER_BLOB_INVALID,
            BatchStatus.UNSUPPORTED_PLATFORM,
            BatchStatus.PROCESS_READ_FAILED,
            BatchStatus(1 << 30),
        )
        for batch_status in forbidden_batches:
            with self.subTest(batch_status=batch_status):
                self.assertFalse(
                    auxiliary_vm_batch_attempt_retryable(
                        self._observation(batch_status=batch_status)
                    )
                )

        forbidden_records = tuple(
            status
            for status in RecordStatus
            if status not in allowed_records
            and status not in (RecordStatus.OK,)
        ) + (RecordStatus(1 << 30),)
        for record_status in forbidden_records:
            with self.subTest(record_status=record_status):
                self.assertFalse(
                    auxiliary_vm_batch_attempt_retryable(
                        self._observation(
                            batch_status=(
                                BatchStatus.FRAME_AFTER_MISMATCH
                            ),
                            record_status=record_status,
                        )
                    )
                )

        self.assertFalse(
            auxiliary_vm_batch_attempt_retryable(
                self._observation(
                    batch_status=BatchStatus.OK,
                    record_status=RecordStatus.ACTIVE_PC_INVALID,
                )
            )
        )

    def test_context_change_attempts_immediately(self) -> None:
        capture = _Capture()
        service = AuxiliaryVmBatchTraceService(
            cadence_frames=16,
            capture=capture,
        )
        for epoch, spell_id in ((1, None), (2, None), (2, 107)):
            record = service.observe_if_due(
                _Reader(102),
                decision_frame=100,
                manager_frame=100,
                gameplay_epoch=epoch,
                stage_route_index=5,
                spell_id=spell_id,
            )
            self.assertIsNotNone(record)
        self.assertEqual(len(capture.calls), 3)

    def test_default_v3_trace_keeps_hash_only_record_schema(self) -> None:
        active_vm = b"\x01" * 0x228
        saved_frame = b"\x02" * 0x228
        capture = _Capture(
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
                    target_subroutine=69,
                    call_depth=0,
                    auxiliary_marker=1,
                    active_vm=active_vm,
                    saved_frames=(saved_frame,),
                ),
            )
        )
        record = AuxiliaryVmBatchTraceService(
            capture=capture
        ).observe_if_due(
            _Reader(100),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=7,
            stage_route_index=5,
            spell_id=107,
        )

        assert record is not None
        self.assertEqual(record["schema_version"], 3)
        self.assertNotIn("event_derivation", record)
        timing = record["timing_ms"]
        assert isinstance(timing, dict)
        self.assertNotIn("event_derive", timing)
        observation = record["observation"]
        assert isinstance(observation, dict)
        records = observation["records"]
        assert isinstance(records, list)
        self.assertNotIn("active_vm_hex", records[0])
        self.assertNotIn("saved_frame_hex", records[0])
        self.assertIsNotNone(records[0]["active_vm_sha256"])
        self.assertEqual(len(records[0]["saved_frame_sha256"]), 1)

    def test_event_v6_reuses_capture_and_bundles_replay_state(self) -> None:
        active_vm = b"\x01" * 0x228
        saved_frame = b"\x02" * 0x228
        captured = AuxiliaryVmBatchRecord(
            slot=0,
            auxiliary_index=0,
            enemy_pointer=0x005826C0,
            context_pointer=0x02100000,
            context_pointer_after=0x02100000,
            enemy_flags_before=1,
            enemy_flags_after=1,
            status=RecordStatus.OK,
            target_subroutine=69,
            call_depth=0,
            auxiliary_marker=1,
            active_vm=active_vm,
            saved_frames=(saved_frame,),
        )
        capture = _Capture(records=(captured,))
        event_service = _EventService()
        version = RuntimeEclAcceptedVersion(
            runtime_base=0x00500000,
            image_length=0x100,
            relocated_sha256="1" * 64,
            normalized_sha256="2" * 64,
            static_sha256="2" * 64,
            route_id=2,
            difficulty_index=3,
            stage_route_index=5,
            gameplay_epoch=7,
            decision_frame=1,
            snapshot_frame=1,
        )
        record = AuxiliaryVmBatchTraceService(
            capture=capture,
            event_service=event_service,
        ).observe_if_due(
            _Reader(100),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=7,
            stage_route_index=5,
            spell_id=107,
            runtime_ecl_version=version,
        )

        assert record is not None
        self.assertEqual(record["schema_version"], 6)
        self.assertEqual(record["event_derivation"], {"status": "derived"})
        self.assertEqual(len(capture.calls), 1)
        self.assertEqual(len(event_service.calls), 1)
        event_call = event_service.calls[0]
        self.assertIs(event_call["runtime_version"], version)
        self.assertEqual(event_call["gameplay_epoch"], 7)
        self.assertEqual(event_call["stage_route_index"], 5)
        observation = record["observation"]
        assert isinstance(observation, dict)
        records = observation["records"]
        assert isinstance(records, list)
        self.assertNotIn("active_vm_hex", records[0])
        self.assertNotIn("saved_frame_hex", records[0])
        bundle = observation["replay_state_bundle"]
        assert isinstance(bundle, dict)
        self.assertEqual(
            bundle["schema"],
            "th08-auxiliary-vm-replay-bundle-v1",
        )
        self.assertEqual(bundle["encoding"], "zlib-base64")
        self.assertEqual(bundle["blob_bytes"], 0x228)
        self.assertEqual(bundle["blob_count"], 2)
        self.assertEqual(
            bundle["blob_sha256"],
            [
                hashlib.sha256(active_vm).hexdigest(),
                hashlib.sha256(saved_frame).hexdigest(),
            ],
        )
        payload = zlib.decompress(
            base64.b64decode(bundle["payload_base64"])
        )
        self.assertEqual(payload, active_vm + saved_frame)
        self.assertEqual(
            bundle["uncompressed_sha256"],
            hashlib.sha256(payload).hexdigest(),
        )
        timing = record["timing_ms"]
        assert isinstance(timing, dict)
        self.assertIn("event_derive", timing)
        self.assertEqual(record["process_read_count"], 5)

    def test_event_v6_native_error_has_explicit_unavailable_result(self) -> None:
        event_service = _EventService()
        record = AuxiliaryVmBatchTraceService(
            capture=_FailingCapture(),
            event_service=event_service,
        ).observe_if_due(
            _Reader(100),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=7,
            stage_route_index=5,
            spell_id=107,
        )

        assert record is not None
        self.assertEqual(record["schema_version"], 6)
        self.assertEqual(record["status"], "native_transaction_failed")
        self.assertEqual(
            record["event_derivation"],
            {"status": "native_transaction_failed"},
        )
        self.assertEqual(
            event_service.unavailable_calls,
            ["native_transaction_failed"],
        )
        self.assertEqual(event_service.calls, [])


if __name__ == "__main__":
    unittest.main()
