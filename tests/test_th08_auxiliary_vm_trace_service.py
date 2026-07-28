from __future__ import annotations

import unittest

from th08_live.auxiliary_vm import (
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchTraceService,
    BatchStatus,
    NativeAuxiliaryVmBatchDiagnostics,
)
from th08_live.auxiliary_vm.model import (
    AUXILIARY_VM_BATCH_LAYOUT_V2,
    UNOBSERVED_MANAGER_FRAME,
)


class _Reader:
    def __init__(self, capture_frame: int) -> None:
        self.capture_frame = capture_frame

    def u32(self, _address: int) -> int:
        raise AssertionError("v2 service must not read a Python frame bracket")

    def read(self, address: int, size: int) -> bytes:
        raise AssertionError(
            f"v2 service must not copy Python owner bytes at {address:#x}"
            f"/{size}"
        )


class _Capture:
    def __init__(
        self,
        *,
        batch_status: BatchStatus = BatchStatus.OK,
    ) -> None:
        self.calls: list[dict[str, object]] = []
        self.batch_status = batch_status

    def capture_process(
        self,
        reader,
        **arguments,
    ) -> AuxiliaryVmBatchObservation:
        self.calls.append(dict(arguments))
        selected = reader.capture_frame
        owner_after = (
            selected + 1
            if self.batch_status
            & BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
            else selected
        )
        inner_frame = (
            UNOBSERVED_MANAGER_FRAME
            if self.batch_status
            & BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
            else selected
        )
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=selected,
            manager_frame_before=inner_frame,
            manager_frame_after=inner_frame,
            batch_status=self.batch_status,
            records=(),
            process_read_count=5,
            state_payload_bytes=0,
            layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
            owner_manager_frame_after=owner_after,
            owner_blob_bytes=64 * 0x53D0,
        )

    @staticmethod
    def diagnostics() -> NativeAuxiliaryVmBatchDiagnostics:
        return NativeAuxiliaryVmBatchDiagnostics(0.25, 0.1)


class AuxiliaryVmBatchTraceServiceTests(unittest.TestCase):
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
        self.assertEqual(first["schema_version"], 2)
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

    def test_owner_frame_change_is_visible_from_native_transaction(self) -> None:
        capture = _Capture(
            batch_status=BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
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
        self.assertEqual(record["status"], "rejected")
        self.assertIsNotNone(record["observation"])
        self.assertEqual(record["selected_manager_frame"], 100)
        self.assertEqual(record["owner_manager_frame_after"], 101)
        self.assertEqual(len(capture.calls), 1)

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


if __name__ == "__main__":
    unittest.main()
