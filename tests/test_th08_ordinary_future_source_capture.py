from __future__ import annotations

import struct
import unittest

from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_FLAGS_OFFSET,
    ENEMY_MANAGER_TEMPLATE_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
)
from th08_runtime.ordinary_future_source_capture import (
    _read_active_enemy_records,
)


class _Reader:
    def __init__(self, slab: bytes) -> None:
        self.slab = slab
        self.reads: list[tuple[int, int]] = []

    def read(self, address: int, size: int) -> bytes:
        self.reads.append((address, size))
        return self.slab

    def u32(self, _address: int) -> int:
        raise AssertionError("the coherent enemy slab must not use sparse reads")


class _IntoReader(_Reader):
    def __init__(self, slab: bytes) -> None:
        super().__init__(slab)
        self.into_reads: list[tuple[int, int]] = []

    @staticmethod
    def allocate_buffer(size: int) -> bytearray:
        return bytearray(size)

    def read_into(self, address: int, buffer: bytearray) -> bytearray:
        self.into_reads.append((address, len(buffer)))
        buffer[:] = self.slab
        return buffer

    def read(self, _address: int, _size: int) -> bytes:
        raise AssertionError("persistent capture must use read_into")


class OrdinaryFutureSourceCaptureTests(unittest.TestCase):
    def test_manager_and_pool_use_one_contiguous_versioned_read(self) -> None:
        slab = bytearray((ENEMY_POOL_SIZE + 1) * ENEMY_STRIDE)
        struct.pack_into(
            "<I",
            slab,
            ENEMY_FLAGS_OFFSET,
            ENEMY_ACTIVE_FLAG,
        )
        active_slot = 479
        struct.pack_into(
            "<I",
            slab,
            (active_slot + 1) * ENEMY_STRIDE + ENEMY_FLAGS_OFFSET,
            ENEMY_ACTIVE_FLAG,
        )
        reader = _Reader(bytes(slab))

        manager, ordinary, active_count = _read_active_enemy_records(reader)

        self.assertEqual(len(manager), ENEMY_STRIDE)
        self.assertEqual(len(ordinary), ENEMY_POOL_SIZE * ENEMY_STRIDE)
        self.assertEqual(active_count, 2)
        self.assertEqual(
            reader.reads,
            [
                (
                    ENEMY_MANAGER_TEMPLATE_BASE,
                    (ENEMY_POOL_SIZE + 1) * ENEMY_STRIDE,
                )
            ],
        )

    def test_truncated_enemy_slab_fails_closed(self) -> None:
        reader = _Reader(b"\0" * ENEMY_STRIDE)

        with self.assertRaisesRegex(ValueError, "slab is truncated"):
            _read_active_enemy_records(reader)

    def test_persistent_destination_avoids_raw_and_slice_copies(self) -> None:
        slab = bytearray((ENEMY_POOL_SIZE + 1) * ENEMY_STRIDE)
        struct.pack_into(
            "<I",
            slab,
            ENEMY_STRIDE + ENEMY_FLAGS_OFFSET,
            ENEMY_ACTIVE_FLAG,
        )
        reader = _IntoReader(bytes(slab))
        destination = reader.allocate_buffer(len(slab))

        manager, ordinary, active_count = _read_active_enemy_records(
            reader,
            slab_buffer=destination,
        )

        self.assertIsInstance(manager, memoryview)
        self.assertIsInstance(ordinary, memoryview)
        self.assertIs(manager.obj, destination)
        self.assertIs(ordinary.obj, destination)
        self.assertEqual(active_count, 1)
        self.assertEqual(
            reader.into_reads,
            [(ENEMY_MANAGER_TEMPLATE_BASE, len(slab))],
        )


if __name__ == "__main__":
    unittest.main()
