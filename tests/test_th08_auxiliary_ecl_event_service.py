from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from th08_ecl_auxiliary import PHYSICAL_TIMING_UNAVAILABLE
from th08_ecl_tool.core import EclFile, parse_ecl
from th08_live.auxiliary_vm import (
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchRecord,
    BatchStatus,
    RecordStatus,
)
from th08_live.auxiliary_vm.event_service import (
    AuxiliaryEclEventConfiguration,
    AuxiliaryEclEventTraceService,
)
from th08_live.auxiliary_vm.event_program import (
    AuxiliaryEclEventProgram,
    _RelativeInstruction,
)
from th08_live.auxiliary_vm.model import (
    ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
    ACTIVE_VM_BYTES,
    AUXILIARY_VM_BATCH_LAYOUT_V2,
)
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion


_BASE = 0x00500000
_ECL_PATH = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "decoded"
    / "ecldata5.ecl"
)
_ECL_SHA256 = (
    "3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19"
)


def _active_vm(
    pc: int,
    *,
    marker: int = 1,
    elapsed: int = 0,
) -> bytes:
    raw = bytearray(ACTIVE_VM_BYTES)
    struct.pack_into("<IiIi", raw, 0, pc, elapsed - 1, 0, elapsed)
    struct.pack_into(
        "<I",
        raw,
        ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
        marker,
    )
    return bytes(raw)


class AuxiliaryEclEventTraceServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.image = _ECL_PATH.read_bytes()
        cls.ecl: EclFile = parse_ecl(_ECL_PATH)
        assert hashlib.sha256(cls.image).hexdigest() == _ECL_SHA256

    @classmethod
    def _pc(cls, target: int) -> int:
        return _BASE + cls.ecl.subroutines[target].instructions[0].offset

    @classmethod
    def _record(
        cls,
        target: int = 69,
        *,
        pc_target: int | None = None,
        marker: int = 1,
        record_marker: int | None = None,
        call_depth: int = 0,
        active_vm: bytes | None = None,
        status: RecordStatus = RecordStatus.OK,
    ) -> AuxiliaryVmBatchRecord:
        raw = (
            _active_vm(
                cls._pc(target if pc_target is None else pc_target),
                marker=marker,
            )
            if active_vm is None
            else active_vm
        )
        return AuxiliaryVmBatchRecord(
            slot=3,
            auxiliary_index=2,
            enemy_pointer=0x005826C0,
            context_pointer=0x02100000,
            context_pointer_after=0x02100000,
            enemy_flags_before=1,
            enemy_flags_after=1,
            status=status,
            target_subroutine=target,
            call_depth=call_depth,
            auxiliary_marker=(
                marker if record_marker is None else record_marker
            ),
            active_vm=raw,
            saved_frames=(),
        )

    @staticmethod
    def _observation(
        records: tuple[AuxiliaryVmBatchRecord, ...],
        *,
        batch_status: BatchStatus = BatchStatus.OK,
    ) -> AuxiliaryVmBatchObservation:
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=200,
            manager_frame_before=200,
            manager_frame_after=200,
            batch_status=batch_status,
            records=records,
            process_read_count=5,
            state_payload_bytes=sum(len(record.active_vm) for record in records),
            layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
            owner_manager_frame_after=200,
            owner_blob_bytes=64 * 0x53D0,
        )

    @staticmethod
    def _version(
        *,
        normalized_sha256: str = _ECL_SHA256,
        route_id: int = 2,
        difficulty_index: int = 3,
        stage_route_index: int = 5,
        gameplay_epoch: int = 7,
    ) -> RuntimeEclAcceptedVersion:
        return RuntimeEclAcceptedVersion(
            runtime_base=_BASE,
            image_length=len(
                AuxiliaryEclEventTraceServiceTests.image
            ),
            relocated_sha256="1" * 64,
            normalized_sha256=normalized_sha256,
            static_sha256=_ECL_SHA256,
            route_id=route_id,
            difficulty_index=difficulty_index,
            stage_route_index=stage_route_index,
            gameplay_epoch=gameplay_epoch,
            decision_frame=1,
            snapshot_frame=1,
        )

    def _service(
        self,
        *,
        prepare: bool = True,
    ) -> AuxiliaryEclEventTraceService:
        service = AuxiliaryEclEventTraceService(
            AuxiliaryEclEventConfiguration(
                static_path=_ECL_PATH,
                expected_static_sha256=_ECL_SHA256,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
        )
        if prepare:
            preparation = service.prepare_if_needed(
                self._version(),
                gameplay_epoch=7,
                stage_route_index=5,
                decision_frame=1,
                snapshot_frame=1,
            )
            assert preparation is not None
            self.assertEqual(preparation["status"], "success")
            self.assertEqual(
                preparation["schema"],
                "th08-auxiliary-ecl-event-preparation-v2",
            )
            self.assertEqual(
                preparation["observation_epoch_semantics"],
                "provenance_not_program_mutation",
            )
            self.assertEqual(preparation["accepted_gameplay_epoch"], 7)
            self.assertEqual(preparation["observation_gameplay_epoch"], 7)
            self.assertEqual(preparation["prevalidated_instruction_count"], 1664)
            self.assertEqual(preparation["bound_instruction_count"], 9)
            program_identity = preparation["program_identity"]
            assert isinstance(program_identity, dict)
            self.assertNotIn("gameplay_epoch", program_identity)
            self.assertEqual(
                preparation["program_identity_key"],
                [
                    program_identity[key]
                    for key in (
                        "runtime_base",
                        "image_length",
                        "relocated_sha256",
                        "normalized_sha256",
                        "static_sha256",
                        "route_id",
                        "difficulty_index",
                        "stage_route_index",
                    )
                ],
            )
            self.assertEqual(preparation["decision_frame"], 1)
            self.assertEqual(preparation["snapshot_frame"], 1)
            self.assertIsNone(
                service.prepare_if_needed(
                    self._version(),
                    gameplay_epoch=7,
                    stage_route_index=5,
                    decision_frame=2,
                    snapshot_frame=2,
                )
            )
        return service

    def test_exact_runtime_version_lowers_all_supported_cycles(self) -> None:
        records = tuple(self._record(target) for target in (69, 72, 73))
        result = self._service().derive(
            self._observation(records),
            runtime_version=self._version(),
            gameplay_epoch=7,
            stage_route_index=5,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["schema"],
            "th08-auxiliary-ecl-event-derivation-v3",
        )
        self.assertEqual(result["authority"], "trace_only_no_action_authority")
        self.assertEqual(result["active_difficulty_mask"], 0x08)
        self.assertEqual(
            result["target_horizons"],
            {"69": 16, "72": 16, "73": 60},
        )
        self.assertEqual(result["request_count"], 3)
        self.assertEqual(result["complete_count"], 3)
        self.assertEqual(result["unknown_count"], 0)
        self.assertEqual(
            result["cache"],
            {
                "request_count": 3,
                "request_local_hits": 0,
                "persistent_hits": 0,
                "misses": 3,
                "evictions": 0,
                "entries_after": 3,
                "capacity": 512,
            },
        )
        requests = result["requests"]
        assert isinstance(requests, list)
        self.assertEqual(
            [request["observation_record_index"] for request in requests],
            [0, 1, 2],
        )
        self.assertEqual(
            [request["status"] for request in requests],
            ["complete", "complete", "complete"],
        )
        lowering = result["lowering"]
        assert isinstance(lowering, dict)
        self.assertEqual(lowering["request_count"], 3)
        self.assertEqual(lowering["unique_result_count"], 3)
        self.assertTrue(
            all(
                item["physical_timing_status"]
                == PHYSICAL_TIMING_UNAVAILABLE
                for item in lowering["unique_results"]
            )
        )
        repeated = self._service()
        first = repeated.derive(
            self._observation(records),
            runtime_version=self._version(),
            gameplay_epoch=7,
            stage_route_index=5,
        )
        second = repeated.derive(
            self._observation(records),
            runtime_version=self._version(),
            gameplay_epoch=7,
            stage_route_index=5,
        )
        self.assertEqual(first["lowering"], second["lowering"])
        self.assertEqual(second["cache"]["persistent_hits"], 3)
        self.assertEqual(second["cache"]["misses"], 0)

    def test_missing_or_mismatched_runtime_identity_fails_closed(self) -> None:
        observation = self._observation((self._record(),))
        cases = (
            (None, 7, 5, "runtime_identity_unavailable"),
            (
                self._version(normalized_sha256="0" * 64),
                7,
                5,
                "runtime_identity_mismatch",
            ),
            (
                self._version(route_id=1),
                7,
                5,
                "runtime_identity_mismatch",
            ),
            (
                self._version(stage_route_index=4),
                7,
                5,
                "runtime_identity_mismatch",
            ),
        )
        service = self._service()
        for version, epoch, stage, status in cases:
            with self.subTest(status=status, version=version):
                result = service.derive(
                    observation,
                    runtime_version=version,
                    gameplay_epoch=epoch,
                    stage_route_index=stage,
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(result["request_count"], 0)
                self.assertIsNone(result["lowering"])
                if version is not None:
                    self.assertEqual(
                        result["runtime_version"],
                        version.record(),
                    )

    def test_same_program_crosses_observation_epochs_and_reuses_cache(
        self,
    ) -> None:
        service = self._service()
        observation = self._observation((self._record(),))
        first = service.derive(
            observation,
            runtime_version=self._version(gameplay_epoch=7),
            gameplay_epoch=8,
            stage_route_index=5,
        )
        second = service.derive(
            observation,
            runtime_version=self._version(gameplay_epoch=7),
            gameplay_epoch=10,
            stage_route_index=5,
        )

        self.assertEqual(first["status"], "success")
        self.assertEqual(second["status"], "success")
        self.assertEqual(first["accepted_gameplay_epoch"], 7)
        self.assertEqual(first["observation_gameplay_epoch"], 8)
        self.assertEqual(second["accepted_gameplay_epoch"], 7)
        self.assertEqual(second["observation_gameplay_epoch"], 10)
        self.assertEqual(second["cache"]["persistent_hits"], 1)
        self.assertEqual(second["cache"]["misses"], 0)
        self.assertEqual(
            first["program_identity_key"],
            second["program_identity_key"],
        )

    def test_invalid_accepted_runtime_base_fails_closed(self) -> None:
        version = self._version()
        invalid = RuntimeEclAcceptedVersion(
            runtime_base=0,
            image_length=version.image_length,
            relocated_sha256=version.relocated_sha256,
            normalized_sha256=version.normalized_sha256,
            static_sha256=version.static_sha256,
            route_id=version.route_id,
            difficulty_index=version.difficulty_index,
            stage_route_index=version.stage_route_index,
            gameplay_epoch=version.gameplay_epoch,
            decision_frame=version.decision_frame,
            snapshot_frame=version.snapshot_frame,
        )
        service = self._service(prepare=False)
        preparation = service.prepare_if_needed(
            invalid,
            gameplay_epoch=7,
            stage_route_index=5,
            decision_frame=1,
            snapshot_frame=1,
        )
        assert preparation is not None
        self.assertEqual(
            preparation["status"],
            "runtime_program_bind_failed",
        )
        result = service.derive(
            self._observation((self._record(),)),
            runtime_version=invalid,
            gameplay_epoch=7,
            stage_route_index=5,
        )
        self.assertEqual(result["status"], "runtime_program_unprepared")
        self.assertEqual(result["runtime_version"], invalid.record())
        self.assertEqual(result["request_count"], 0)

    def test_record_mismatches_remain_explicit_unknowns(self) -> None:
        records = (
            self._record(call_depth=1),
            self._record(target=68),
            self._record(marker=1, record_marker=2),
            self._record(target=69, pc_target=72),
            self._record(active_vm=b"short"),
        )
        result = self._service().derive(
            self._observation(records),
            runtime_version=self._version(),
            gameplay_epoch=7,
            stage_route_index=5,
        )

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["request_count"], 5)
        self.assertEqual(result["complete_count"], 0)
        self.assertEqual(result["unknown_count"], 5)
        requests = result["requests"]
        assert isinstance(requests, list)
        self.assertEqual(
            [request["status"] for request in requests[:4]],
            [
                "unsupported_call_depth",
                "unsupported_target",
                "auxiliary_marker_mismatch",
                "target_pc_mismatch",
            ],
        )
        self.assertTrue(str(requests[4]["status"]).startswith("invalid_state:"))
        lowering = result["lowering"]
        assert isinstance(lowering, dict)
        self.assertEqual(lowering["request_count"], 0)

    def test_unusable_batch_and_empty_success_are_distinct(self) -> None:
        service = self._service()
        unavailable = service.derive(
            self._observation(
                (),
                batch_status=BatchStatus.PROCESS_READ_FAILED,
            ),
            runtime_version=self._version(),
            gameplay_epoch=7,
            stage_route_index=5,
        )
        self.assertEqual(
            unavailable["status"],
            "auxiliary_batch_unavailable",
        )

        empty = service.derive(
            self._observation(()),
            runtime_version=self._version(),
            gameplay_epoch=7,
            stage_route_index=5,
        )
        self.assertEqual(empty["status"], "empty_complete")
        self.assertEqual(empty["request_count"], 0)
        lowering = empty["lowering"]
        assert isinstance(lowering, dict)
        self.assertEqual(lowering["request_count"], 0)
        self.assertEqual(
            empty["cache"],
            {
                "request_count": 0,
                "request_local_hits": 0,
                "persistent_hits": 0,
                "misses": 0,
                "evictions": 0,
                "entries_after": 0,
                "capacity": 512,
            },
        )

    def test_static_digest_is_checked_before_service_use(self) -> None:
        with self.assertRaisesRegex(ValueError, "digest"):
            AuxiliaryEclEventTraceService(
                AuxiliaryEclEventConfiguration(
                    static_path=_ECL_PATH,
                    expected_static_sha256="0" * 64,
                    expected_route_id=2,
                    expected_difficulty_index=3,
                    expected_stage_route_index=5,
                )
            )

    def test_prevalidated_target_closure_rejects_escape(self) -> None:
        escaping = _RelativeInstruction(
            offset=0x100,
            time=0,
            opcode=99,
            size=44,
            difficulty_mask=0xFF,
            parameter_mask=0,
            payload=b"\x00" * 32,
            owner=69,
        )
        with self.assertRaisesRegex(ValueError, "escaping successor"):
            AuxiliaryEclEventProgram._validate_target_closure(
                [escaping],
                active_difficulty_mask=0x08,
            )


if __name__ == "__main__":
    unittest.main()
