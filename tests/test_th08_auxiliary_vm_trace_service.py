from __future__ import annotations

import unittest

from th08_live.auxiliary_vm import (
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchTraceService,
    BatchStatus,
    NativeAuxiliaryVmBatchDiagnostics,
)


class _Reader:
    def __init__(self, frames: tuple[int, ...]) -> None:
        self.frames = list(frames)
        self.reads: list[tuple[int, int]] = []

    def u32(self, _address: int) -> int:
        return self.frames.pop(0)

    def read(self, address: int, size: int) -> bytes:
        self.reads.append((address, size))
        return bytes(size)


class _Capture:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def capture_process(
        self,
        _reader,
        owner_blob: bytes,
        **arguments,
    ) -> AuxiliaryVmBatchObservation:
        self.calls.append(
            {"owner_blob_size": len(owner_blob), **arguments}
        )
        expected = int(arguments["expected_manager_frame"])
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=expected,
            manager_frame_before=expected,
            manager_frame_after=expected,
            batch_status=BatchStatus.OK,
            records=(),
            process_read_count=2,
            state_payload_bytes=0,
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
            _Reader((100, 100)),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=106,
        )
        self.assertIsNone(filtered)
        self.assertEqual(capture.calls, [])

        first = service.observe_if_due(
            _Reader((100, 100)),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=107,
        )
        self.assertIsNotNone(first)
        assert first is not None
        self.assertEqual(first["status"], "success")
        self.assertEqual(
            first["process_read_count_including_owner_capture"],
            5,
        )

        not_due = service.observe_if_due(
            _Reader((110, 110)),
            decision_frame=110,
            manager_frame=110,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=107,
        )
        self.assertIsNone(not_due)
        due = service.observe_if_due(
            _Reader((116, 116)),
            decision_frame=116,
            manager_frame=116,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=107,
        )
        self.assertIsNotNone(due)
        self.assertEqual(len(capture.calls), 2)

    def test_owner_frame_change_fails_before_native_batch(self) -> None:
        capture = _Capture()
        service = AuxiliaryVmBatchTraceService(capture=capture)
        record = service.observe_if_due(
            _Reader((100, 101)),
            decision_frame=100,
            manager_frame=100,
            gameplay_epoch=1,
            stage_route_index=5,
            spell_id=None,
        )
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["status"], "owner_frame_changed")
        self.assertIsNone(record["observation"])
        self.assertEqual(capture.calls, [])

    def test_context_change_attempts_immediately(self) -> None:
        capture = _Capture()
        service = AuxiliaryVmBatchTraceService(
            cadence_frames=16,
            capture=capture,
        )
        for epoch, spell_id in ((1, None), (2, None), (2, 107)):
            record = service.observe_if_due(
                _Reader((100, 100)),
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
