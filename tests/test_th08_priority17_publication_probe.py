from __future__ import annotations

import ctypes
import struct
import unittest

from th08_runtime.game_state import (
    ADDR_CURRENT_INPUT,
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_ENGINE_FLAGS,
    ADDR_PREVIOUS_INPUT,
    ADDR_RAW_INPUT,
)
from th08_runtime.priority17_publication_probe import (
    PRIORITY17_EPILOGUE_ADDRESS,
    PRIORITY17_EPILOGUE_ORIGINAL,
    PRIORITY17_PADDING_ADDRESS,
    PROBE_CAPACITY,
    PROBE_EVENT_OFFSET,
    PROBE_EVENT_SIZE,
    PROBE_SERIAL_OFFSET,
    PROBE_STUB_OFFSET,
    Priority17PublicationEvent,
    Priority17PublicationProbe,
    _probe_owned_instruction_pointer,
    _Wow64Context,
    build_probe_image,
    build_probe_patches,
    build_probe_stub,
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
    def __init__(self, kernel: _MemoryKernel) -> None:
        self.kernel32 = kernel


def _event(
    serial: int,
    *,
    manager_frame: int | None = None,
) -> bytes:
    return struct.pack(
        "<IIIHHHHI",
        serial,
        serial if manager_frame is None else manager_frame,
        0x04,
        0x65,
        0x61,
        0x65,
        0,
        serial * 3,
    )


def _probe(*, serial: int, base: int = 0x02000000):
    memory = bytearray(0x2000)
    image = build_probe_image(base, 1234)
    memory[: len(image)] = image
    struct.pack_into("<I", memory, PROBE_SERIAL_OFFSET, serial)
    kernel = _MemoryKernel(memory, base)
    probe = Priority17PublicationProbe(
        api=_MemoryApi(kernel),
        pid=1234,
        handle=1,
        remote_base=base,
    )
    return probe, kernel, memory


class Priority17PublicationProbeTests(unittest.TestCase):
    def test_stub_records_callback_exit_fields_and_restores_epilogue(
        self,
    ) -> None:
        base = 0x02000000
        stub = build_probe_stub(base)

        self.assertLess(PROBE_STUB_OFFSET + len(stub), PROBE_EVENT_OFFSET)
        for address in (
            ADDR_ENEMY_MANAGER_FRAME,
            ADDR_ENGINE_FLAGS,
            ADDR_RAW_INPUT,
            ADDR_CURRENT_INPUT,
            ADDR_PREVIOUS_INPUT,
            base + PROBE_SERIAL_OFFSET,
            base + PROBE_EVENT_OFFSET,
        ):
            self.assertIn(struct.pack("<I", address), stub)
        self.assertTrue(
            stub.endswith(PRIORITY17_EPILOGUE_ORIGINAL + b"\x5d\xc3")
        )

    def test_activation_patch_uses_padding_trampoline(self) -> None:
        base = 0x02000000
        epilogue, padding = build_probe_patches(base)

        self.assertEqual(epilogue, b"\xeb\x02")
        self.assertEqual(padding[0], 0xE9)
        displacement = struct.unpack("<i", padding[1:])[0]
        target = PRIORITY17_PADDING_ADDRESS + 5 + displacement
        self.assertEqual(target, base + PROBE_STUB_OFFSET)
        self.assertEqual(
            PRIORITY17_EPILOGUE_ADDRESS + 4, PRIORITY17_PADDING_ADDRESS
        )

    def test_cleanup_quiescence_covers_trampoline_and_remote_stub(
        self,
    ) -> None:
        base = 0x02000000
        stub_size = len(build_probe_stub(base))

        self.assertEqual(ctypes.sizeof(_Wow64Context), 716)
        self.assertFalse(
            _probe_owned_instruction_pointer(
                PRIORITY17_EPILOGUE_ADDRESS,
                remote_base=base,
                stub_size=stub_size,
            )
        )
        for instruction_pointer in (
            PRIORITY17_PADDING_ADDRESS,
            PRIORITY17_PADDING_ADDRESS + 4,
            base + PROBE_STUB_OFFSET,
            base + PROBE_STUB_OFFSET + stub_size - 1,
        ):
            self.assertTrue(
                _probe_owned_instruction_pointer(
                    instruction_pointer,
                    remote_base=base,
                    stub_size=stub_size,
                )
            )
        self.assertFalse(
            _probe_owned_instruction_pointer(
                base + PROBE_STUB_OFFSET + stub_size,
                remote_base=base,
                stub_size=stub_size,
            )
        )

    def test_event_decode_retains_callback_exit_state(self) -> None:
        event = Priority17PublicationEvent.decode(_event(7, manager_frame=386))

        self.assertEqual(event.serial, 7)
        self.assertEqual(event.manager_frame, 386)
        self.assertEqual(event.raw_mask, 0x65)
        self.assertEqual(event.current_mask, 0x61)
        self.assertEqual(event.previous_mask, 0x65)
        self.assertEqual(event.replay_frame_counter, 21)

    def test_read_since_returns_exact_stable_events(self) -> None:
        probe, _kernel, memory = _probe(serial=3)
        for serial in (2, 3):
            slot = (serial - 1) & (PROBE_CAPACITY - 1)
            start = PROBE_EVENT_OFFSET + slot * PROBE_EVENT_SIZE
            memory[start : start + PROBE_EVENT_SIZE] = _event(serial)

        batch = probe.read_since(1)

        self.assertEqual(batch.status, "exact")
        self.assertEqual(batch.observed_serial, 3)
        self.assertEqual([event.serial for event in batch.events], [2, 3])
        self.assertEqual(batch.dropped_event_count, 0)

    def test_overflow_is_bounded_and_explicit(self) -> None:
        probe, _kernel, memory = _probe(serial=300)
        for serial in range(269, 301):
            slot = (serial - 1) & (PROBE_CAPACITY - 1)
            start = PROBE_EVENT_OFFSET + slot * PROBE_EVENT_SIZE
            memory[start : start + PROBE_EVENT_SIZE] = _event(serial)

        batch = probe.read_since(0, maximum_events=32)

        self.assertEqual(batch.status, "overflow_or_trace_truncation")
        self.assertEqual(batch.dropped_event_count, 268)
        self.assertEqual(batch.events[0].serial, 269)
        self.assertEqual(batch.events[-1].serial, 300)

    def test_unstable_ring_returns_unknown_without_raising(self) -> None:
        probe, kernel, memory = _probe(serial=2)
        slot = 1
        start = PROBE_EVENT_OFFSET + slot * PROBE_EVENT_SIZE
        memory[start : start + PROBE_EVENT_SIZE] = _event(2)
        kernel.mutate_serial_on_read = 2

        batch = probe.read_since(1, retries=1)

        self.assertEqual(batch.status, "race_unknown")
        self.assertIsNone(batch.observed_serial)
        self.assertEqual(batch.events, ())

    def test_header_identity_tamper_is_read_error(self) -> None:
        probe, _kernel, memory = _probe(serial=1)
        memory[:4] = b"BAD!"

        batch = probe.read_since(None)

        self.assertEqual(batch.status, "read_error")
        self.assertIn("header identity", batch.error)


if __name__ == "__main__":
    unittest.main()
