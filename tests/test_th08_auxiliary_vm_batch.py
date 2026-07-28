from __future__ import annotations

import os
import random
import struct
import unittest

from th08_live.auxiliary_vm import (
    BatchStatus,
    NativeAuxiliaryVmBatchCapture,
    RecordStatus,
    decode_auxiliary_vm_batch_fixture,
    decode_auxiliary_vm_batch_owned_fixture,
    native_auxiliary_vm_batch_available,
)
from th08_live.auxiliary_vm.model import (
    ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
    ACTIVE_VM_BYTES,
    CONTEXT_BYTES,
    MAXIMUM_STATE_PAYLOAD_BYTES,
    SAVED_FRAME_BASE_OFFSET,
)


_ARENA_BASE = 0x02100000
_POOL_BASE = 0x005826C0
_STRIDE = 0x53D0
_FLAGS_OFFSET = 0x3324
_POINTER_OFFSET = 0x3384


def _owner_blob(
    pointers: tuple[int, int, int, int],
    *,
    flags: int = 1,
) -> bytes:
    blob = bytearray(_STRIDE)
    struct.pack_into("<I", blob, _FLAGS_OFFSET, flags)
    struct.pack_into("<4I", blob, _POINTER_OFFSET, *pointers)
    return bytes(blob)


def _context(
    *,
    depth: int,
    auxiliary_index: int,
    active_pc: int = 0x03100100,
) -> bytes:
    context = bytearray(CONTEXT_BYTES)
    struct.pack_into("<I", context, 0, 54)
    struct.pack_into("<h", context, 6, depth)
    struct.pack_into("<I", context, 8, active_pc)
    struct.pack_into(
        "<I",
        context,
        8 + ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
        auxiliary_index + 1,
    )
    for index in range(16):
        base = SAVED_FRAME_BASE_OFFSET + index * ACTIVE_VM_BYTES
        struct.pack_into("<I", context, base, 0x03101000 + index * 0x20)
        context[base + 4 : base + ACTIVE_VM_BYTES] = bytes(
            [0x40 + index]
        ) * (ACTIVE_VM_BYTES - 4)
    return bytes(context)


def _decode(
    before_owner: bytes,
    after_owner: bytes,
    before_arena: bytes,
    after_arena: bytes | None = None,
    *,
    expected_frame: int = 100,
    frame_before: int = 100,
    frame_after: int = 100,
    capacity: int = MAXIMUM_STATE_PAYLOAD_BYTES,
):
    return decode_auxiliary_vm_batch_fixture(
        before_owner,
        after_owner,
        before_arena,
        before_arena if after_arena is None else after_arena,
        arena_base=_ARENA_BASE,
        pool_base=_POOL_BASE,
        record_count=1,
        enemy_stride=_STRIDE,
        enemy_flags_offset=_FLAGS_OFFSET,
        enemy_active_flag=1,
        context_pointer_offset=_POINTER_OFFSET,
        expected_manager_frame=expected_frame,
        manager_frame_before=frame_before,
        manager_frame_after=frame_after,
        output_payload_capacity=capacity,
    )


def _decode_native(
    capture: NativeAuxiliaryVmBatchCapture,
    before_owner: bytes,
    after_owner: bytes,
    before_arena: bytes,
    after_arena: bytes | None = None,
    *,
    expected_frame: int = 100,
    frame_before: int = 100,
    frame_after: int = 100,
    capacity: int = MAXIMUM_STATE_PAYLOAD_BYTES,
):
    return capture.decode_fixture(
        before_owner,
        after_owner,
        before_arena,
        before_arena if after_arena is None else after_arena,
        arena_base=_ARENA_BASE,
        pool_base=_POOL_BASE,
        record_count=1,
        enemy_stride=_STRIDE,
        enemy_flags_offset=_FLAGS_OFFSET,
        enemy_active_flag=1,
        context_pointer_offset=_POINTER_OFFSET,
        expected_manager_frame=expected_frame,
        manager_frame_before=frame_before,
        manager_frame_after=frame_after,
        output_payload_capacity=capacity,
    )


def _decode_owned(
    before_owner: bytes,
    after_owner: bytes,
    before_arena: bytes,
    after_arena: bytes | None = None,
    *,
    selected_frame: int = 100,
    owner_frame_after: int = 100,
    context_frame_before: int = 100,
    frame_after: int = 100,
    capacity: int = MAXIMUM_STATE_PAYLOAD_BYTES,
):
    return decode_auxiliary_vm_batch_owned_fixture(
        before_owner,
        after_owner,
        before_arena,
        before_arena if after_arena is None else after_arena,
        arena_base=_ARENA_BASE,
        pool_base=_POOL_BASE,
        record_count=1,
        enemy_stride=_STRIDE,
        enemy_flags_offset=_FLAGS_OFFSET,
        enemy_active_flag=1,
        context_pointer_offset=_POINTER_OFFSET,
        selected_manager_frame=selected_frame,
        owner_manager_frame_after=owner_frame_after,
        context_manager_frame_before=context_frame_before,
        manager_frame_after=frame_after,
        output_payload_capacity=capacity,
    )


def _decode_owned_native(
    capture: NativeAuxiliaryVmBatchCapture,
    before_owner: bytes,
    after_owner: bytes,
    before_arena: bytes,
    after_arena: bytes | None = None,
    *,
    selected_frame: int = 100,
    owner_frame_after: int = 100,
    context_frame_before: int = 100,
    frame_after: int = 100,
    capacity: int = MAXIMUM_STATE_PAYLOAD_BYTES,
):
    return capture.decode_owned_fixture(
        before_owner,
        after_owner,
        before_arena,
        before_arena if after_arena is None else after_arena,
        arena_base=_ARENA_BASE,
        pool_base=_POOL_BASE,
        record_count=1,
        enemy_stride=_STRIDE,
        enemy_flags_offset=_FLAGS_OFFSET,
        enemy_active_flag=1,
        context_pointer_offset=_POINTER_OFFSET,
        selected_manager_frame=selected_frame,
        owner_manager_frame_after=owner_frame_after,
        context_manager_frame_before=context_frame_before,
        manager_frame_after=frame_after,
        output_payload_capacity=capacity,
    )


class AuxiliaryVmScalarBatchTests(unittest.TestCase):
    def test_depth_zero_preserves_active_vm_and_null_rows(self) -> None:
        pointer = _ARENA_BASE
        owner = _owner_blob((pointer, 0, 0, 0))
        arena = _context(depth=0, auxiliary_index=0)
        observation = _decode(owner, owner, arena)

        self.assertTrue(observation.success)
        self.assertEqual(len(observation.records), 4)
        self.assertEqual(observation.non_null_context_count, 1)
        self.assertEqual(observation.usable_context_count, 1)
        self.assertEqual(observation.state_payload_bytes, ACTIVE_VM_BYTES)
        self.assertEqual(observation.records[0].call_depth, 0)
        self.assertEqual(
            len(observation.records[0].active_vm),
            ACTIVE_VM_BYTES,
        )
        self.assertEqual(observation.records[0].saved_frames, ())
        self.assertEqual(
            observation.records[1].status,
            RecordStatus.NULL,
        )

    def test_depth_fifteen_excludes_nonrestorable_physical_slot_fifteen(
        self,
    ) -> None:
        pointer = _ARENA_BASE
        owner = _owner_blob((pointer, 0, 0, 0))
        arena = _context(depth=15, auxiliary_index=0)
        observation = _decode(owner, owner, arena)
        record = observation.records[0]

        self.assertTrue(observation.success)
        self.assertEqual(len(record.saved_frames), 15)
        self.assertEqual(
            observation.state_payload_bytes,
            16 * ACTIVE_VM_BYTES,
        )
        self.assertEqual(record.saved_frames[-1][4], 0x40 + 14)
        self.assertNotEqual(record.saved_frames[-1][4], 0x40 + 15)

    def test_invalid_depth_and_saved_pc_fail_closed(self) -> None:
        pointer = _ARENA_BASE
        owner = _owner_blob((pointer, 0, 0, 0))
        invalid_depth = _decode(
            owner,
            owner,
            _context(depth=-1, auxiliary_index=0),
        )
        self.assertFalse(invalid_depth.success)
        self.assertTrue(
            invalid_depth.records[0].status
            & RecordStatus.CALL_DEPTH_INVALID
        )

        invalid_saved = bytearray(_context(depth=1, auxiliary_index=0))
        struct.pack_into("<I", invalid_saved, SAVED_FRAME_BASE_OFFSET, 0)
        observation = _decode(
            owner,
            owner,
            bytes(invalid_saved),
        )
        self.assertFalse(observation.success)
        self.assertTrue(
            observation.records[0].status & RecordStatus.SAVED_PC_INVALID
        )
        self.assertEqual(observation.records[0].active_vm, b"")

    def test_context_header_and_owner_pointer_churn_fail_closed(self) -> None:
        pointer = _ARENA_BASE
        owner = _owner_blob((pointer, 0, 0, 0))
        changed_context = bytearray(_context(depth=0, auxiliary_index=0))
        struct.pack_into("<I", changed_context, 8, 0x03100200)
        context_churn = _decode(
            owner,
            owner,
            _context(depth=0, auxiliary_index=0),
            bytes(changed_context),
        )
        self.assertFalse(context_churn.success)
        self.assertTrue(
            context_churn.records[0].status
            & RecordStatus.CONTEXT_CHANGED
        )

        changed_owner = _owner_blob((0, 0, 0, 0))
        owner_churn = _decode(
            owner,
            changed_owner,
            _context(depth=0, auxiliary_index=0),
        )
        self.assertFalse(owner_churn.success)
        self.assertTrue(
            owner_churn.records[0].status & RecordStatus.POINTER_CHANGED
        )

    def test_marker_capacity_and_frame_brackets_fail_closed(self) -> None:
        pointer = _ARENA_BASE
        owner = _owner_blob((pointer, 0, 0, 0))
        wrong_marker = bytearray(_context(depth=0, auxiliary_index=0))
        struct.pack_into(
            "<I",
            wrong_marker,
            8 + ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
            4,
        )
        marker = _decode(owner, owner, bytes(wrong_marker))
        self.assertTrue(
            marker.records[0].status
            & RecordStatus.AUXILIARY_MARKER_MISMATCH
        )

        capacity = _decode(
            owner,
            owner,
            _context(depth=0, auxiliary_index=0),
            capacity=ACTIVE_VM_BYTES - 1,
        )
        self.assertTrue(
            capacity.records[0].status & RecordStatus.PAYLOAD_CAPACITY
        )

        frame = _decode(
            owner,
            owner,
            _context(depth=0, auxiliary_index=0),
            frame_after=101,
        )
        self.assertEqual(
            frame.batch_status,
            BatchStatus.FRAME_AFTER_MISMATCH,
        )
        self.assertFalse(frame.success)

    def test_malformed_owner_blob_and_context_address_fail_closed(self) -> None:
        malformed = _decode(b"", b"", b"")
        self.assertEqual(
            malformed.batch_status,
            BatchStatus.OWNER_BLOB_INVALID,
        )
        self.assertEqual(malformed.records, ())

        pointer = 0xFFFFFFFF
        owner = _owner_blob((pointer, 0, 0, 0))
        observation = _decode(owner, owner, b"")
        self.assertTrue(
            observation.records[0].status
            & RecordStatus.CONTEXT_ADDRESS_INVALID
        )

    def test_owned_schedule_exposes_every_manager_bracket(self) -> None:
        pointer = _ARENA_BASE
        owner = _owner_blob((pointer, 0, 0, 0))
        arena = _context(depth=1, auxiliary_index=0)
        v1 = _decode(owner, owner, arena)
        owned = _decode_owned(owner, owner, arena)
        self.assertTrue(owned.success)
        self.assertEqual(owned.records, v1.records)
        self.assertEqual(
            owned.process_read_count,
            v1.process_read_count + 3,
        )
        self.assertEqual(owned.owner_blob_bytes, _STRIDE)

        owner_mismatch = _decode_owned(
            owner,
            owner,
            arena,
            owner_frame_after=101,
        )
        self.assertEqual(
            owner_mismatch.batch_status,
            BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH,
        )
        self.assertEqual(owner_mismatch.process_read_count, 3)
        self.assertEqual(owner_mismatch.records, ())

        context_mismatch = _decode_owned(
            owner,
            owner,
            arena,
            context_frame_before=101,
        )
        self.assertEqual(
            context_mismatch.batch_status,
            BatchStatus.FRAME_BEFORE_MISMATCH,
        )
        self.assertEqual(context_mismatch.process_read_count, 4)
        self.assertEqual(context_mismatch.records, ())

        final_mismatch = _decode_owned(
            owner,
            owner,
            arena,
            frame_after=101,
        )
        self.assertEqual(
            final_mismatch.batch_status,
            BatchStatus.FRAME_AFTER_MISMATCH,
        )
        self.assertFalse(final_mismatch.success)
        self.assertEqual(final_mismatch.usable_context_count, 0)


@unittest.skipUnless(
    native_auxiliary_vm_batch_available(),
    "native auxiliary-VM trace library is not built",
)
class AuxiliaryVmNativeParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = NativeAuxiliaryVmBatchCapture()

    def assert_fixture_parity(
        self,
        before_owner: bytes,
        after_owner: bytes,
        before_arena: bytes,
        after_arena: bytes | None = None,
        **kwargs,
    ) -> None:
        scalar = _decode(
            before_owner,
            after_owner,
            before_arena,
            after_arena,
            **kwargs,
        )
        native = _decode_native(
            self.capture,
            before_owner,
            after_owner,
            before_arena,
            after_arena,
            **kwargs,
        )
        self.assertEqual(native, scalar)

    def assert_owned_fixture_parity(
        self,
        before_owner: bytes,
        after_owner: bytes,
        before_arena: bytes,
        after_arena: bytes | None = None,
        **kwargs,
    ) -> None:
        scalar = _decode_owned(
            before_owner,
            after_owner,
            before_arena,
            after_arena,
            **kwargs,
        )
        native = _decode_owned_native(
            self.capture,
            before_owner,
            after_owner,
            before_arena,
            after_arena,
            **kwargs,
        )
        self.assertEqual(native, scalar)

    def test_revalidated_depths_and_failures_match_scalar(self) -> None:
        for depth in (0, 1, 14, 15):
            with self.subTest(depth=depth):
                pointer = _ARENA_BASE
                owner = _owner_blob((pointer, 0, 0, 0))
                self.assert_fixture_parity(
                    owner,
                    owner,
                    _context(depth=depth, auxiliary_index=0),
                )

        pointer = _ARENA_BASE
        owner = _owner_blob((pointer, 0, 0, 0))
        invalid_saved_pc = bytearray(_context(depth=1, auxiliary_index=0))
        struct.pack_into("<I", invalid_saved_pc, SAVED_FRAME_BASE_OFFSET, 0)
        self.assert_fixture_parity(
            owner,
            owner,
            bytes(invalid_saved_pc),
        )
        self.assert_fixture_parity(
            owner,
            _owner_blob((0, 0, 0, 0)),
            _context(depth=0, auxiliary_index=0),
        )
        self.assert_fixture_parity(
            owner,
            owner[:-1],
            _context(depth=0, auxiliary_index=0),
        )
        self.assert_fixture_parity(
            owner,
            owner,
            _context(depth=0, auxiliary_index=0),
            capacity=ACTIVE_VM_BYTES - 1,
        )
        self.assert_fixture_parity(
            owner,
            owner,
            _context(depth=0, auxiliary_index=0),
            frame_before=99,
        )
        self.assert_fixture_parity(
            owner,
            owner,
            _context(depth=0, auxiliary_index=0),
            frame_after=101,
        )

    def test_randomized_status_and_byte_parity(self) -> None:
        rng = random.Random(0xA0EC1)
        for case in range(128):
            depth = rng.choice((-2, -1, 0, 1, 14, 15, 16, 31))
            auxiliary_index = rng.randrange(4)
            context = bytearray(
                _context(
                    depth=depth,
                    auxiliary_index=auxiliary_index,
                    active_pc=rng.choice(
                        (0, 0x03100100, 0x7FFFFFFF, 0x80000000)
                    ),
                )
            )
            if rng.randrange(4) == 0:
                struct.pack_into(
                    "<I",
                    context,
                    8 + ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
                    rng.randrange(8),
                )
            pointers = [0, 0, 0, 0]
            pointers[auxiliary_index] = _ARENA_BASE
            owner = _owner_blob(tuple(pointers))
            owner_after = bytearray(owner)
            if rng.randrange(5) == 0:
                struct.pack_into(
                    "<I",
                    owner_after,
                    _FLAGS_OFFSET,
                    rng.choice((0, 3)),
                )
            if rng.randrange(5) == 0:
                struct.pack_into(
                    "<I",
                    owner_after,
                    _POINTER_OFFSET + auxiliary_index * 4,
                    rng.choice((0, _ARENA_BASE + CONTEXT_BYTES)),
                )
            arena_after = bytearray(context)
            if rng.randrange(5) == 0:
                arena_after[rng.randrange(12)] ^= 0x5A
            capacity = rng.choice(
                (
                    MAXIMUM_STATE_PAYLOAD_BYTES,
                    0,
                    ACTIVE_VM_BYTES - 1,
                    (1 + max(0, min(depth, 15))) * ACTIVE_VM_BYTES,
                )
            )
            with self.subTest(case=case):
                self.assert_fixture_parity(
                    owner,
                    bytes(owner_after),
                    bytes(context),
                    bytes(arena_after),
                    capacity=capacity,
                )

    def test_owned_fixture_frames_and_random_bytes_match_scalar(self) -> None:
        pointer = _ARENA_BASE
        owner = _owner_blob((pointer, 0, 0, 0))
        for frames in (
            {},
            {"owner_frame_after": 101},
            {"context_frame_before": 101},
            {"frame_after": 101},
        ):
            with self.subTest(frames=frames):
                self.assert_owned_fixture_parity(
                    owner,
                    owner,
                    _context(depth=15, auxiliary_index=0),
                    **frames,
                )
        self.assert_owned_fixture_parity(b"", b"", b"")
        self.assert_owned_fixture_parity(
            owner,
            owner,
            _context(depth=0, auxiliary_index=0),
            capacity=ACTIVE_VM_BYTES - 1,
        )

        rng = random.Random(0xCE0164)
        for case in range(64):
            depth = rng.choice((0, 1, 14, 15))
            context = bytearray(
                _context(depth=depth, auxiliary_index=0)
            )
            if rng.randrange(5) == 0:
                context[rng.randrange(12)] ^= 0x3C
            frame_case = rng.randrange(5)
            frames: dict[str, int] = {}
            if frame_case == 1:
                frames["owner_frame_after"] = 101
            elif frame_case == 2:
                frames["context_frame_before"] = 101
            elif frame_case == 3:
                frames["frame_after"] = 101
            with self.subTest(case=case):
                self.assert_owned_fixture_parity(
                    owner,
                    owner,
                    bytes(context),
                    **frames,
                )

    def test_maximum_batch_is_ordered_bounded_and_deterministic(self) -> None:
        owner = bytearray(64 * _STRIDE)
        arena = bytearray(256 * CONTEXT_BYTES)
        depths = (0, 1, 14, 15)
        for slot in range(64):
            base = slot * _STRIDE
            struct.pack_into("<I", owner, base + _FLAGS_OFFSET, 1)
            pointers = []
            for auxiliary_index, depth in enumerate(depths):
                index = slot * 4 + auxiliary_index
                pointer = _ARENA_BASE + index * CONTEXT_BYTES
                pointers.append(pointer)
                context = _context(
                    depth=depth,
                    auxiliary_index=auxiliary_index,
                )
                start = index * CONTEXT_BYTES
                arena[start : start + CONTEXT_BYTES] = context
            struct.pack_into(
                "<4I",
                owner,
                base + _POINTER_OFFSET,
                *pointers,
            )

        arguments = {
            "arena_base": _ARENA_BASE,
            "pool_base": _POOL_BASE,
            "record_count": 64,
            "enemy_stride": _STRIDE,
            "enemy_flags_offset": _FLAGS_OFFSET,
            "enemy_active_flag": 1,
            "context_pointer_offset": _POINTER_OFFSET,
            "expected_manager_frame": 100,
            "manager_frame_before": 100,
            "manager_frame_after": 100,
        }
        owner_bytes = bytes(owner)
        arena_bytes = bytes(arena)
        scalar = decode_auxiliary_vm_batch_fixture(
            owner_bytes,
            owner_bytes,
            arena_bytes,
            arena_bytes,
            **arguments,
        )
        native = self.capture.decode_fixture(
            owner_bytes,
            owner_bytes,
            arena_bytes,
            arena_bytes,
            **arguments,
        )
        repeated = self.capture.decode_fixture(
            owner_bytes,
            owner_bytes,
            arena_bytes,
            arena_bytes,
            **arguments,
        )
        self.assertEqual(native, scalar)
        self.assertEqual(repeated, native)
        self.assertEqual(len(native.records), 256)
        self.assertEqual(native.usable_context_count, 256)
        self.assertEqual(native.process_read_count, 834)

        owned_arguments = {
            "arena_base": _ARENA_BASE,
            "pool_base": _POOL_BASE,
            "record_count": 64,
            "enemy_stride": _STRIDE,
            "enemy_flags_offset": _FLAGS_OFFSET,
            "enemy_active_flag": 1,
            "context_pointer_offset": _POINTER_OFFSET,
            "selected_manager_frame": 100,
            "owner_manager_frame_after": 100,
            "context_manager_frame_before": 100,
            "manager_frame_after": 100,
        }
        scalar_owned = decode_auxiliary_vm_batch_owned_fixture(
            owner_bytes,
            owner_bytes,
            arena_bytes,
            arena_bytes,
            **owned_arguments,
        )
        native_owned = self.capture.decode_owned_fixture(
            owner_bytes,
            owner_bytes,
            arena_bytes,
            arena_bytes,
            **owned_arguments,
        )
        self.assertEqual(native_owned, scalar_owned)
        self.assertEqual(native_owned.usable_context_count, 256)
        self.assertEqual(native_owned.process_read_count, 837)
        self.assertEqual(native_owned.owner_blob_bytes, 64 * _STRIDE)

    def test_process_entry_fails_without_emulation_or_input(self) -> None:
        class InvalidReader:
            handle = -1

        observation = self.capture.capture_process(
            InvalidReader(),
            pool_base=_POOL_BASE,
            manager_frame_address=0x0164D30C,
            record_count=64,
            enemy_stride=_STRIDE,
            enemy_flags_offset=_FLAGS_OFFSET,
            enemy_active_flag=1,
            context_pointer_offset=_POINTER_OFFSET,
        )
        expected = (
            BatchStatus.PROCESS_READ_FAILED
            if os.name == "nt"
            else BatchStatus.UNSUPPORTED_PLATFORM
        )
        self.assertEqual(observation.batch_status, expected)
        self.assertEqual(observation.records, ())


if __name__ == "__main__":
    unittest.main()
