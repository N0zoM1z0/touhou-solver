from __future__ import annotations

import ctypes
from types import SimpleNamespace
import struct
import unittest
from unittest import mock

import th08_runtime.enemy_lifecycle_probe as lifecycle_probe
from th08_runtime.enemy_lifecycle_probe import (
    ENEMY_POOL_BASE,
    ENEMY_STRIDE,
    FORCED_ZERO_RETURN_SPELL_FINISH,
    HOOK_SITES,
    PROBE_CAPACITY,
    PROBE_EVENT_OFFSET,
    PROBE_EVENT_SIZE,
    PROBE_SERIAL_OFFSET,
    PROBE_STUB_OFFSET,
    PROBE_STUB_STRIDE,
    EnemyLifecycleEvent,
    EnemyLifecycleKind,
    EnemyLifecycleProbe,
    EnemyLifecycleProbeUnsafeStateError,
    _instruction_pointer_in_hook_span,
    _probe_owned_instruction_pointer,
    build_probe_image,
    build_probe_patches,
    build_site_stub,
)


class _MemoryKernel:
    def __init__(self, memory: bytearray, base: int) -> None:
        self.memory = memory
        self.base = base
        self.serial_reads = 0
        self.mutate_serial_on_read: int | None = None

    def ReadProcessMemory(
        self,
        _handle,
        address,
        buffer,
        size,
        count_pointer,
    ) -> int:
        raw_address = int(
            address.value if hasattr(address, "value") else address
        )
        if raw_address == self.base:
            self.serial_reads += 1
            if (
                self.mutate_serial_on_read is not None
                and self.serial_reads == self.mutate_serial_on_read
            ):
                current = struct.unpack_from(
                    "<I",
                    self.memory,
                    PROBE_SERIAL_OFFSET,
                )[0]
                struct.pack_into(
                    "<I",
                    self.memory,
                    PROBE_SERIAL_OFFSET,
                    current + 1,
                )
        offset = raw_address - self.base
        payload = bytes(self.memory[offset : offset + size])
        ctypes.memmove(buffer, payload, size)
        count_pointer._obj.value = size
        return 1


class _MemoryApi:
    def __init__(self, kernel) -> None:
        self.kernel32 = kernel


class _InstallKernel:
    def __init__(self, remote_base: int) -> None:
        self.remote_base = remote_base
        self.freed = False
        self.closed: list[int] = []

    def OpenProcess(self, _access, _inherit, _pid):
        return 7

    def VirtualAllocEx(self, _handle, _address, _size, _allocation, _protect):
        return self.remote_base

    def VirtualFreeEx(self, _handle, address, _size, _release):
        raw = int(address.value if hasattr(address, "value") else address)
        if raw != self.remote_base:
            return 0
        self.freed = True
        return 1

    def CloseHandle(self, handle):
        self.closed.append(handle)
        return 1


def _event(
    serial: int,
    *,
    kind: EnemyLifecycleKind = EnemyLifecycleKind.RETIRE_MAIN_VM,
    slot: int = 3,
    caller: int = 0,
    hp_before: int = 5,
    hp_after: int = 5,
    frame_damage: int = 0,
    root_subroutine: int | None = None,
    stage_route_index: int = 5,
) -> bytes:
    encoded_root = (
        root_subroutine
        if root_subroutine is not None
        else (
            7
            if kind
            in {
                EnemyLifecycleKind.ALLOCATE_TIMELINE,
                EnemyLifecycleKind.ALLOCATE_INHERITED_REGISTERS,
            }
            else -1
        )
    )
    return struct.pack(
        "<IIIIIIiiiIiI",
        serial,
        1000 + serial,
        int(kind),
        ENEMY_POOL_BASE + slot * ENEMY_STRIDE,
        0x101,
        0x100,
        hp_before,
        hp_after,
        frame_damage,
        caller,
        encoded_root,
        stage_route_index,
    )


def _probe(*, serial: int, base: int = 0x02000000):
    memory = bytearray(0x4000)
    image = build_probe_image(base, 1234)
    memory[: len(image)] = image
    struct.pack_into("<I", memory, PROBE_SERIAL_OFFSET, serial)
    kernel = _MemoryKernel(memory, base)
    probe = EnemyLifecycleProbe(
        api=_MemoryApi(kernel),
        pid=1234,
        handle=1,
        remote_base=base,
    )
    return probe, kernel, memory


class EnemyLifecycleProbeTests(unittest.TestCase):
    def test_revalidated_hook_bytes_and_reasons_are_pinned(self) -> None:
        self.assertEqual(
            [(site.address, site.kind, site.original) for site in HOOK_SITES],
            [
                (
                    0x0042A55F,
                    EnemyLifecycleKind.ALLOCATE_TIMELINE,
                    bytes.fromhex("8b55f88b45fc89820c2e0000"),
                ),
                (
                    0x0042A6FF,
                    EnemyLifecycleKind.ALLOCATE_INHERITED_REGISTERS,
                    bytes.fromhex("8b55f88b45fc89820c2e0000"),
                ),
                (
                    0x0042A5F5,
                    EnemyLifecycleKind.RETIRE_INITIAL_VM_TIMELINE,
                    bytes.fromhex("898124330000"),
                ),
                (
                    0x0042A787,
                    EnemyLifecycleKind.RETIRE_INITIAL_VM_INHERITED,
                    bytes.fromhex("899024330000"),
                ),
                (
                    0x0042C9B1,
                    EnemyLifecycleKind.RETIRE_MAIN_VM,
                    bytes.fromhex("899024330000"),
                ),
                (
                    0x0042CDFE,
                    EnemyLifecycleKind.RETIRE_OFFSCREEN_CULL,
                    bytes.fromhex("899024330000"),
                ),
                (
                    0x0042D899,
                    EnemyLifecycleKind.RETIRE_DEFEAT_MODE0,
                    bytes.fromhex("898a24330000"),
                ),
                (
                    0x0042F039,
                    EnemyLifecycleKind.FORCED_HP_ZERO,
                    bytes.fromhex("c781fc2d000000000000"),
                ),
            ],
        )
        self.assertEqual(
            [site.capture_root_subroutine for site in HOOK_SITES],
            [True, True, False, False, False, False, False, False],
        )

    def test_stubs_replay_original_then_return_and_fit_fixed_slots(self) -> None:
        remote_base = 0x02000000
        for index, site in enumerate(HOOK_SITES):
            stub = build_site_stub(remote_base, site)
            self.assertTrue(stub.startswith(b"\x9c\x60"))
            self.assertIn(site.original, stub)
            if site.capture_root_subroutine:
                self.assertIn(b"\x0f\xbf\x55\x08\x89\x51\x28", stub)
            self.assertLessEqual(len(stub), PROBE_STUB_STRIDE)
            self.assertEqual(stub[-5], 0xE9)
            displacement = struct.unpack("<i", stub[-4:])[0]
            jump_source = (
                remote_base
                + PROBE_STUB_OFFSET
                + index * PROBE_STUB_STRIDE
                + len(stub)
                - 5
            )
            self.assertEqual(
                jump_source + 5 + displacement,
                site.return_address,
            )

    def test_activation_patches_cover_complete_instruction_spans(self) -> None:
        remote_base = 0x02000000
        patches = build_probe_patches(remote_base)
        self.assertEqual(len(patches), len(HOOK_SITES))
        for index, (site, patch) in enumerate(zip(HOOK_SITES, patches)):
            self.assertEqual(len(patch), len(site.original))
            self.assertEqual(patch[0], 0xE9)
            displacement = struct.unpack("<i", patch[1:5])[0]
            self.assertEqual(
                site.address + 5 + displacement,
                remote_base
                + PROBE_STUB_OFFSET
                + index * PROBE_STUB_STRIDE,
            )
            self.assertEqual(patch[5:], b"\x90" * (len(patch) - 5))

    def test_cleanup_quiescence_covers_every_patch_and_stub(self) -> None:
        remote_base = 0x02000000
        for index, site in enumerate(HOOK_SITES):
            self.assertTrue(
                _probe_owned_instruction_pointer(
                    site.address,
                    remote_base=remote_base,
                )
            )
            stub = build_site_stub(remote_base, site)
            stub_start = (
                remote_base
                + PROBE_STUB_OFFSET
                + index * PROBE_STUB_STRIDE
            )
            self.assertTrue(
                _probe_owned_instruction_pointer(
                    stub_start + len(stub) - 1,
                    remote_base=remote_base,
                )
            )
        self.assertFalse(
            _probe_owned_instruction_pointer(
                0x00401000,
                remote_base=remote_base,
            )
        )
        self.assertFalse(_instruction_pointer_in_hook_span(0x00401000))

    def test_event_decode_retains_reason_and_damage_crossing_inputs(self) -> None:
        event = EnemyLifecycleEvent.decode(
            _event(
                7,
                kind=EnemyLifecycleKind.RETIRE_DEFEAT_MODE0,
                slot=11,
                hp_before=-2,
                hp_after=-2,
                frame_damage=9,
            )
        )
        self.assertEqual(event.slot, 11)
        self.assertTrue(event.is_retirement)
        self.assertFalse(event.is_allocation)
        self.assertEqual(event.reconstructed_pre_damage_hp, 7)
        self.assertEqual(
            event.compact_record()["kind"],
            "retire_defeat_mode0",
        )
        self.assertIsNone(event.root_subroutine)

    def test_allocation_event_retains_exact_root_subroutine(self) -> None:
        event = EnemyLifecycleEvent.decode(
            _event(
                6,
                kind=EnemyLifecycleKind.ALLOCATE_TIMELINE,
                slot=9,
                root_subroutine=31,
            )
        )
        self.assertTrue(event.is_allocation)
        self.assertEqual(event.root_subroutine, 31)
        self.assertEqual(event.stage_route_index, 5)
        self.assertEqual(event.compact_record()["root_subroutine"], 31)
        with self.assertRaisesRegex(ValueError, "no root subroutine"):
            EnemyLifecycleEvent.decode(
                _event(
                    6,
                    kind=EnemyLifecycleKind.ALLOCATE_TIMELINE,
                    root_subroutine=-1,
                )
            )
        with self.assertRaisesRegex(ValueError, "stage-route index"):
            EnemyLifecycleEvent.decode(
                _event(
                    6,
                    kind=EnemyLifecycleKind.ALLOCATE_TIMELINE,
                    stage_route_index=9,
                )
            )
        with self.assertRaisesRegex(ValueError, "non-allocation"):
            EnemyLifecycleEvent.decode(
                _event(
                    6,
                    kind=EnemyLifecycleKind.RETIRE_MAIN_VM,
                    root_subroutine=31,
                )
            )

    def test_forced_zero_requires_one_of_the_four_shipped_callers(self) -> None:
        event = EnemyLifecycleEvent.decode(
            _event(
                8,
                kind=EnemyLifecycleKind.FORCED_HP_ZERO,
                caller=FORCED_ZERO_RETURN_SPELL_FINISH,
                hp_before=200,
                hp_after=0,
            )
        )
        self.assertTrue(event.is_forced_hp_zero)
        with self.assertRaisesRegex(ValueError, "shipped caller"):
            EnemyLifecycleEvent.decode(
                _event(
                    8,
                    kind=EnemyLifecycleKind.FORCED_HP_ZERO,
                    caller=0x00401000,
                )
            )

    def test_read_since_returns_exact_stable_events(self) -> None:
        probe, _kernel, memory = _probe(serial=3)
        for serial in (2, 3):
            slot = (serial - 1) & (PROBE_CAPACITY - 1)
            start = PROBE_EVENT_OFFSET + slot * PROBE_EVENT_SIZE
            memory[start : start + PROBE_EVENT_SIZE] = _event(serial)
        batch = probe.read_since(1)
        self.assertEqual(batch.status, "exact")
        self.assertEqual([event.serial for event in batch.events], [2, 3])
        self.assertEqual(batch.dropped_event_count, 0)

    def test_overflow_is_bounded_and_explicit(self) -> None:
        probe, _kernel, memory = _probe(serial=300)
        for serial in range(45, 301):
            slot = (serial - 1) & (PROBE_CAPACITY - 1)
            start = PROBE_EVENT_OFFSET + slot * PROBE_EVENT_SIZE
            memory[start : start + PROBE_EVENT_SIZE] = _event(serial)
        batch = probe.read_since(0, maximum_events=64)
        self.assertEqual(batch.status, "overflow_or_trace_truncation")
        self.assertEqual(len(batch.events), 64)
        self.assertEqual(batch.events[0].serial, 237)
        self.assertEqual(batch.events[-1].serial, 300)
        self.assertEqual(batch.dropped_event_count, 236)

    def test_unstable_ring_returns_unknown_without_partial_events(self) -> None:
        probe, kernel, memory = _probe(serial=2)
        for serial in (1, 2):
            slot = (serial - 1) & (PROBE_CAPACITY - 1)
            start = PROBE_EVENT_OFFSET + slot * PROBE_EVENT_SIZE
            memory[start : start + PROBE_EVENT_SIZE] = _event(serial)
        kernel.mutate_serial_on_read = 2
        batch = probe.read_since(0, retries=1)
        self.assertEqual(batch.status, "race_unknown")
        self.assertEqual(batch.events, ())

    def test_in_progress_overwrite_invalidates_oldest_full_ring_slot(self) -> None:
        probe, _kernel, memory = _probe(serial=PROBE_CAPACITY)
        for serial in range(1, PROBE_CAPACITY + 1):
            slot = (serial - 1) & (PROBE_CAPACITY - 1)
            start = PROBE_EVENT_OFFSET + slot * PROBE_EVENT_SIZE
            memory[start : start + PROBE_EVENT_SIZE] = _event(serial)
        # Producer has selected serial 257 and invalidated slot 0, but has not
        # committed header.serial past 256. A full-ring read must not accept
        # the partially overwritten event as serial 1.
        struct.pack_into("<I", memory, PROBE_EVENT_OFFSET, 257)
        batch = probe.read_since(0, maximum_events=PROBE_CAPACITY, retries=1)
        self.assertEqual(batch.status, "race_unknown")
        self.assertEqual(batch.events, ())

    def test_install_and_close_are_activation_last_and_restore_all_sites(
        self,
    ) -> None:
        remote_base = 0x02000000
        kernel = _InstallKernel(remote_base)
        api = _MemoryApi(kernel)
        site_memory = {site.address: site.original for site in HOOK_SITES}
        write_order: list[int] = []

        def read_memory(_api, _handle, address, size):
            payload = site_memory[address]
            return payload[:size]

        def write_code(_api, _handle, address, payload):
            write_order.append(address)
            site_memory[address] = payload

        suspended = (SimpleNamespace(instruction_pointer=0x00401000),)
        with (
            mock.patch.object(lifecycle_probe, "_configure_api"),
            mock.patch.object(lifecycle_probe, "_read_memory", read_memory),
            mock.patch.object(lifecycle_probe, "_write_memory"),
            mock.patch.object(lifecycle_probe, "_write_code", write_code),
            mock.patch.object(
                lifecycle_probe,
                "_suspend_target_threads",
                return_value=suspended,
            ),
            mock.patch.object(
                lifecycle_probe,
                "_release_suspended_threads",
                return_value=(),
            ),
        ):
            probe = EnemyLifecycleProbe.install(api, 1234)
            self.assertEqual(write_order, [site.address for site in HOOK_SITES])
            self.assertFalse(kernel.freed)
            probe.close()
        self.assertEqual(
            write_order[len(HOOK_SITES) :],
            [site.address for site in reversed(HOOK_SITES)],
        )
        self.assertTrue(kernel.freed)
        self.assertTrue(all(site_memory[s.address] == s.original for s in HOOK_SITES))

    def test_failed_activation_rolls_back_every_attempted_site(self) -> None:
        remote_base = 0x02000000
        kernel = _InstallKernel(remote_base)
        api = _MemoryApi(kernel)
        site_memory = {site.address: site.original for site in HOOK_SITES}
        activation_writes = 0

        def read_memory(_api, _handle, address, size):
            return site_memory[address][:size]

        def write_code(_api, _handle, address, payload):
            nonlocal activation_writes
            if payload != next(
                site.original for site in HOOK_SITES if site.address == address
            ):
                activation_writes += 1
                if activation_writes == 3:
                    raise OSError("synthetic third-site activation failure")
            site_memory[address] = payload

        suspended = (SimpleNamespace(instruction_pointer=0x00401000),)
        with (
            mock.patch.object(lifecycle_probe, "_configure_api"),
            mock.patch.object(lifecycle_probe, "_read_memory", read_memory),
            mock.patch.object(lifecycle_probe, "_write_memory"),
            mock.patch.object(lifecycle_probe, "_write_code", write_code),
            mock.patch.object(
                lifecycle_probe,
                "_suspend_target_threads",
                return_value=suspended,
            ),
            mock.patch.object(
                lifecycle_probe,
                "_release_suspended_threads",
                return_value=(),
            ),
        ):
            with self.assertRaisesRegex(OSError, "third-site"):
                EnemyLifecycleProbe.install(api, 1234)
        self.assertTrue(kernel.freed)
        self.assertTrue(all(site_memory[s.address] == s.original for s in HOOK_SITES))

    def test_activation_waits_until_no_thread_is_inside_a_patch_span(
        self,
    ) -> None:
        remote_base = 0x02000000
        kernel = _InstallKernel(remote_base)
        api = _MemoryApi(kernel)
        site_memory = {site.address: site.original for site in HOOK_SITES}

        def read_memory(_api, _handle, address, size):
            return site_memory[address][:size]

        def write_code(_api, _handle, address, payload):
            site_memory[address] = payload

        in_flight = (
            SimpleNamespace(instruction_pointer=HOOK_SITES[0].address),
        )
        quiescent = (SimpleNamespace(instruction_pointer=0x00401000),)
        with (
            mock.patch.object(lifecycle_probe, "_configure_api"),
            mock.patch.object(lifecycle_probe, "_read_memory", read_memory),
            mock.patch.object(lifecycle_probe, "_write_memory"),
            mock.patch.object(lifecycle_probe, "_write_code", write_code),
            mock.patch.object(
                lifecycle_probe,
                "_suspend_target_threads",
                side_effect=(in_flight, quiescent, quiescent),
            ),
            mock.patch.object(
                lifecycle_probe,
                "_release_suspended_threads",
                return_value=(),
            ) as release,
            mock.patch.object(lifecycle_probe.time, "sleep"),
        ):
            probe = EnemyLifecycleProbe.install(api, 1234)
            self.assertEqual(release.call_count, 2)
            probe.close()
            self.assertEqual(release.call_count, 3)

    def test_failed_close_restore_is_unsafe_and_does_not_free_stub(self) -> None:
        remote_base = 0x02000000
        kernel = _InstallKernel(remote_base)
        api = _MemoryApi(kernel)
        probe = EnemyLifecycleProbe(
            api=api,
            pid=1234,
            handle=7,
            remote_base=remote_base,
        )
        site_memory = {
            site.address: patch
            for site, patch in zip(
                HOOK_SITES,
                build_probe_patches(remote_base),
            )
        }
        failed_address = HOOK_SITES[3].address

        def read_memory(_api, _handle, address, size):
            return site_memory[address][:size]

        def write_code(_api, _handle, address, payload):
            if address == failed_address:
                raise OSError("synthetic restore failure")
            site_memory[address] = payload

        suspended = (SimpleNamespace(instruction_pointer=0x00401000),)
        with (
            mock.patch.object(lifecycle_probe, "_read_memory", read_memory),
            mock.patch.object(lifecycle_probe, "_write_code", write_code),
            mock.patch.object(
                lifecycle_probe,
                "_suspend_target_threads",
                return_value=suspended,
            ),
            mock.patch.object(
                lifecycle_probe,
                "_release_suspended_threads",
                return_value=(),
            ),
        ):
            with self.assertRaisesRegex(
                EnemyLifecycleProbeUnsafeStateError,
                "detours remain installed",
            ):
                probe.close()
        self.assertFalse(kernel.freed)


if __name__ == "__main__":
    unittest.main()
