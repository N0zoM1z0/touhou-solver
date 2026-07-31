from __future__ import annotations

import struct
import unittest
from unittest.mock import patch

from th08_runtime.native_snapshot import (
    BARRIER_ALLOCATION_SIZE,
    BARRIER_ENDPOINT_FX_OFFSET,
    BARRIER_FX_SIZE,
    BARRIER_HEADER_SIZE,
    BARRIER_ROOT_FX_OFFSET,
    BARRIER_STUB_OFFSET,
    COMMAND_NONE,
    HEADER_STATUS,
    MEM_IMAGE,
    MEM_MAPPED,
    MEM_PRIVATE,
    NativeDirtyPage,
    NativeBarrierHeader,
    NativeBarrierRootCheckpoint,
    NativeSnapshot,
    NativeSnapshotRegion,
    NativeSnapshotUnknownError,
    NativeVirtualRegion,
    PAGE_READWRITE,
    STATUS_ARMED,
    STATUS_STEP_DONE,
    UPDATE_CHAIN_CALLSITE,
    build_native_snapshot_image,
    build_native_snapshot_patch,
    build_native_snapshot_stub,
    changed_byte_addresses,
    parse_native_barrier_header,
    restore_native_dirty_pages,
    select_snapshot_regions,
    snapshot_dirty_pages,
    snapshot_excluded_allocation_bases,
    verify_native_dirty_pages,
)
from th08_runtime.windows_probe import (
    MEM_COMMIT,
    PAGE_EXECUTE_READWRITE,
)


def _region(
    base: int,
    size: int,
    *,
    allocation_base: int | None = None,
    protect: int = PAGE_READWRITE,
    kind: int = MEM_PRIVATE,
) -> NativeVirtualRegion:
    return NativeVirtualRegion(
        base=base,
        size=size,
        allocation_base=(base if allocation_base is None else allocation_base),
        allocation_protect=protect,
        state=MEM_COMMIT,
        protect=protect,
        kind=kind,
    )


def _snapshot(
    captures: tuple[tuple[NativeVirtualRegion, bytes], ...],
    *,
    committed_map: tuple[tuple[int, ...], ...] | None = None,
) -> NativeSnapshot:
    regions = tuple(
        NativeSnapshotRegion(region=region, data=data) for region, data in captures
    )
    return NativeSnapshot(
        regions=regions,
        committed_map=(
            tuple(region.identity() for region, _ in captures)
            if committed_map is None
            else committed_map
        ),
        excluded_allocation_bases=(),
        excluded_regions=(),
    )


class NativeSnapshotBarrierEncodingTests(unittest.TestCase):
    def test_image_patch_and_header_bind_one_fixed_callsite(self) -> None:
        remote_base = 0x10000000
        pid = 1234
        target_manager_frame = 2129

        stub = build_native_snapshot_stub(remote_base)
        image = build_native_snapshot_image(
            remote_base,
            pid=pid,
            target_manager_frame=target_manager_frame,
        )
        patch = build_native_snapshot_patch(remote_base)
        header = parse_native_barrier_header(
            image[:BARRIER_HEADER_SIZE],
            expected_pid=pid,
        )

        self.assertLess(BARRIER_STUB_OFFSET + len(stub), BARRIER_ALLOCATION_SIZE)
        self.assertEqual(
            image[BARRIER_STUB_OFFSET : BARRIER_STUB_OFFSET + len(stub)],
            stub,
        )
        self.assertEqual(header.target_manager_frame, target_manager_frame)
        self.assertEqual(header.status, STATUS_ARMED)
        self.assertEqual(patch[:1], b"\xe8")
        displacement = struct.unpack("<i", patch[1:])[0]
        self.assertEqual(
            UPDATE_CHAIN_CALLSITE + len(patch) + displacement,
            remote_base + BARRIER_STUB_OFFSET,
        )
        self.assertIn(
            b"\x0f\xae\x05" + struct.pack("<I", remote_base + BARRIER_ROOT_FX_OFFSET),
            stub,
        )
        self.assertIn(
            b"\x0f\xae\x0d" + struct.pack("<I", remote_base + BARRIER_ROOT_FX_OFFSET),
            stub,
        )
        self.assertIn(
            b"\x0f\xae\x0d"
            + struct.pack("<I", remote_base + BARRIER_ENDPOINT_FX_OFFSET),
            stub,
        )

    def test_header_parser_fails_closed_on_identity_tamper(self) -> None:
        image = bytearray(
            build_native_snapshot_image(
                0x20000000,
                pid=55,
                target_manager_frame=99,
            )
        )
        struct.pack_into("<I", image, HEADER_STATUS, STATUS_ARMED)
        image[0] ^= 0xFF

        with self.assertRaises(ValueError):
            parse_native_barrier_header(
                bytes(image[:BARRIER_HEADER_SIZE]),
                expected_pid=55,
            )

    def test_completed_endpoint_becomes_content_addressed_subroot(self) -> None:
        endpoint = NativeBarrierHeader(
            pid=55,
            target_manager_frame=2129,
            status=STATUS_STEP_DONE,
            command=COMMAND_NONE,
            owner_thread_id=77,
            arrival_serial=1,
            step_serial=8,
            restore_serial=0,
            last_chain_result=1,
            error_code=0,
            root_esp=0x1000,
            root_ebp=0x2000,
            endpoint_esp=0x1000,
            endpoint_ebp=0x2000,
            root_manager_frame=2129,
            endpoint_manager_frame=2137,
        )
        fx_state = bytes(index & 0xFF for index in range(BARRIER_FX_SIZE))

        checkpoint = NativeBarrierRootCheckpoint.from_endpoint(
            endpoint,
            fx_state,
        )

        self.assertEqual(checkpoint.target_manager_frame, 2137)
        self.assertEqual(checkpoint.root_manager_frame, 2137)
        self.assertEqual(checkpoint.fx_state, fx_state)
        self.assertEqual(checkpoint.record()["sha256"], checkpoint.digest)

        wrong_stack = NativeBarrierHeader(
            **{
                **endpoint.__dict__,
                "endpoint_esp": 0x1004,
            }
        )
        with self.assertRaises(NativeSnapshotUnknownError):
            NativeBarrierRootCheckpoint.from_endpoint(
                wrong_stack,
                fx_state,
            )


class NativeSnapshotRegionTests(unittest.TestCase):
    def test_owner_stack_is_captured_while_frozen_stacks_are_excluded(self) -> None:
        owner_stack = _region(0x10000, 0x2000)
        frozen_stack = _region(0x20000, 0x2000)
        barrier = _region(
            0x30000,
            0x2000,
            protect=PAGE_EXECUTE_READWRITE,
        )
        game_image = _region(0x40000, 0x1000, kind=MEM_IMAGE)
        mapped = _region(0x50000, 0x1000, kind=MEM_MAPPED)
        regions = (
            owner_stack,
            frozen_stack,
            barrier,
            game_image,
            mapped,
        )

        class Frozen:
            stack_pointer = 0x20FF0

        excluded_bases = snapshot_excluded_allocation_bases(
            regions,
            owner_stack_pointer=0x11FF0,
            frozen_threads=(Frozen(),),  # type: ignore[arg-type]
            remote_base=barrier.base,
        )
        selected, excluded = select_snapshot_regions(
            regions,
            excluded_allocation_bases=excluded_bases,
            remote_base=barrier.base,
            remote_size=barrier.size,
        )

        self.assertEqual(
            tuple(region.base for region in selected),
            (owner_stack.base, game_image.base),
        )
        self.assertNotIn(owner_stack.allocation_base, excluded_bases)
        self.assertIn(frozen_stack.allocation_base, excluded_bases)
        self.assertIn(barrier.allocation_base, excluded_bases)
        self.assertEqual(
            {entry["reason"] for entry in excluded},
            {
                "thread_stack_or_explicit_allocation",
                "mapped_or_unknown_writable_region",
            },
        )

    def test_dirty_pages_and_explicit_byte_differences_are_exact(self) -> None:
        first = _region(0x1000, 8)
        second = _region(0x2000, 4)
        root = _snapshot(
            (
                (first, b"abcdefgh"),
                (second, b"wxyz"),
            )
        )
        endpoint = _snapshot(
            (
                (first, b"abcDefgH"),
                (second, b"wxyz"),
            )
        )

        dirty = snapshot_dirty_pages(root, endpoint, page_size=4)

        self.assertEqual(
            tuple(page.address for page in dirty),
            (0x1000, 0x1004),
        )
        self.assertEqual(
            changed_byte_addresses(root, endpoint),
            (0x1003, 0x1007),
        )

    def test_mapping_change_is_unknown_not_a_partial_restore(self) -> None:
        region = _region(0x1000, 4)
        root = _snapshot(((region, b"root"),))
        endpoint = _snapshot(
            ((region, b"step"),),
            committed_map=(
                region.identity(),
                _region(0x3000, 4).identity(),
            ),
        )

        with self.assertRaises(NativeSnapshotUnknownError):
            snapshot_dirty_pages(root, endpoint)

    def test_dirty_page_restore_coalesces_and_verifies_spans(self) -> None:
        pages = (
            NativeDirtyPage(0x1000, b"root", "a", "b"),
            NativeDirtyPage(0x1004, b"next", "c", "d"),
            NativeDirtyPage(0x2000, b"last", "e", "f"),
        )
        with patch("th08_runtime.native_snapshot._write_memory") as write_memory:
            restore_native_dirty_pages(object(), 7, pages)

        self.assertEqual(
            [call.args[2:4] for call in write_memory.call_args_list],
            [(0x1000, b"rootnext"), (0x2000, b"last")],
        )

        with patch(
            "th08_runtime.native_snapshot._read_exact_chunked",
            side_effect=(b"rootnext", b"last"),
        ) as read_memory:
            verify_native_dirty_pages(object(), 7, pages)

        self.assertEqual(
            [call.args[2:4] for call in read_memory.call_args_list],
            [(0x1000, 8), (0x2000, 4)],
        )


if __name__ == "__main__":
    unittest.main()
