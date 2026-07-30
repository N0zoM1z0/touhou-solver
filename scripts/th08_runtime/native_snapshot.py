"""TH08-specific rolling native snapshot and update-chain barrier.

The injected barrier replaces only the fixed call from the 60 Hz frame pump
to the ordered calculation chain.  At one declared manager-frame root it
holds the owning thread before calculation.  It can run the original update
chain from either the immutable root FPU/SSE state or the preceding endpoint
state, and holds again before the frame pump can enter rendering.  A separate
natural-advance command returns through the original callsite and traps the
next calculation call after the intervening frame-pump work.

The Python side snapshots committed writable process bytes while every other
target thread is suspended.  It rejects mapping or thread-set changes and
restores only changed pages.  This is an offline same-session mechanism; it
does not claim that unobserved kernel, audio, renderer, or device state is
restorable.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import struct
import time
from typing import Any, Iterable

from .priority17_publication_probe import (
    INVALID_HANDLE_VALUE,
    MEM_COMMIT,
    MEM_RELEASE,
    MEM_RESERVE,
    PAGE_EXECUTE_READWRITE,
    PROCESS_QUERY_INFORMATION,
    PROCESS_VM_OPERATION,
    PROCESS_VM_READ,
    PROCESS_VM_WRITE,
    THREAD_GET_CONTEXT,
    THREAD_QUERY_INFORMATION,
    THREAD_SUSPEND_RESUME,
    TH32CS_SNAPTHREAD,
    WOW64_CONTEXT_CONTROL,
    _ThreadEntry32,
    _Wow64Context,
    _read_memory,
    _release_suspended_threads,
    _suspend_target_threads,
    _win_error,
    _write_code,
    _write_memory,
)


SNAPSHOT_SCHEMA = "th08-native-calculation-snapshot-v2"
BARRIER_MAGIC = b"T8NS"
BARRIER_VERSION = 2
BARRIER_ALLOCATION_SIZE = 0x2000
BARRIER_ROOT_FX_OFFSET = 0x100
BARRIER_ENDPOINT_FX_OFFSET = 0x300
BARRIER_STUB_OFFSET = 0x600
BARRIER_HEADER_SIZE = 0x80

UPDATE_CHAIN_CALLSITE = 0x00441F4D
UPDATE_CHAIN_CALL_ORIGINAL = b"\xe8\xfe\xaa\xff\xff"
UPDATE_CHAIN_EXECUTE = 0x0043CA50
UPDATE_CHAIN_HEAD = 0x0164F548

ADDR_REPLAY_MANAGER = 0x018B8A28
REPLAY_MODE_OFFSET = 0x10
REPLAY_INPUT_CURSOR_OFFSET = 0x50
REPLAY_UPDATE_NODE_OFFSET = 0xC8
REPLAY_FRAME_COUNTER_OFFSET = 0x00
REPLAY_PLAY_INPUT_CALLBACK = 0x00452550
REPLAY_PRIORITY = 6

STATUS_PASS_THROUGH = 0
STATUS_ARMED = 1
STATUS_ROOT_WAIT = 2
STATUS_RUNNING = 3
STATUS_STEP_DONE = 4
STATUS_RELEASED = 5
STATUS_ERROR = 6
STATUS_NATURAL_WAIT = 7
STATUS_NATURAL_RUNNING = 8
STATUS_NATURAL_ARMED = 9

COMMAND_NONE = 0
COMMAND_STEP = 1
COMMAND_RESTORE_READY = 2
COMMAND_RESUME = 3
COMMAND_CONTINUE = 4
COMMAND_NATURAL_ADVANCE = 5

ERROR_BAD_COMMAND_STATE = 1

HEADER_VERSION = 4
HEADER_PID = 8
HEADER_CALLSITE = 12
HEADER_TARGET = 16
HEADER_STUB_SIZE = 20
HEADER_TARGET_MANAGER = 24
HEADER_STATUS = 28
HEADER_COMMAND = 32
HEADER_OWNER_TID = 36
HEADER_ARRIVAL_SERIAL = 40
HEADER_STEP_SERIAL = 44
HEADER_RESTORE_SERIAL = 48
HEADER_LAST_RESULT = 52
HEADER_ERROR = 56
HEADER_ROOT_ESP = 60
HEADER_ROOT_EBP = 64
HEADER_ENDPOINT_ESP = 68
HEADER_ENDPOINT_EBP = 72
HEADER_ROOT_MANAGER = 76
HEADER_ENDPOINT_MANAGER = 80

PROCESS_ADDRESS_LIMIT = 0x80000000
MEM_PRIVATE = 0x00020000
MEM_MAPPED = 0x00040000
MEM_IMAGE = 0x01000000
PAGE_NOACCESS = 0x01
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE_WRITECOPY = 0x80
PAGE_GUARD = 0x100
PAGE_NOCACHE = 0x200
PAGE_WRITECOMBINE = 0x400
WRITABLE_PROTECTIONS = frozenset(
    {
        PAGE_READWRITE,
        PAGE_WRITECOPY,
        PAGE_EXECUTE_READWRITE,
        PAGE_EXECUTE_WRITECOPY,
    }
)

PAGE_SIZE = 0x1000
READ_CHUNK_SIZE = 1 << 20
DEFAULT_MAXIMUM_REGION_SIZE = 128 << 20
DEFAULT_MAXIMUM_SNAPSHOT_SIZE = 512 << 20


if ctypes.sizeof(ctypes.c_void_p) == 8:

    class _MemoryBasicInformation(ctypes.Structure):
        _fields_ = [
            ("BaseAddress", ctypes.c_void_p),
            ("AllocationBase", ctypes.c_void_p),
            ("AllocationProtect", wintypes.DWORD),
            ("PartitionId", wintypes.WORD),
            ("RegionSize", ctypes.c_size_t),
            ("State", wintypes.DWORD),
            ("Protect", wintypes.DWORD),
            ("Type", wintypes.DWORD),
        ]

else:

    class _MemoryBasicInformation(ctypes.Structure):
        _fields_ = [
            ("BaseAddress", ctypes.c_void_p),
            ("AllocationBase", ctypes.c_void_p),
            ("AllocationProtect", wintypes.DWORD),
            ("RegionSize", ctypes.c_size_t),
            ("State", wintypes.DWORD),
            ("Protect", wintypes.DWORD),
            ("Type", wintypes.DWORD),
        ]


@dataclass(frozen=True)
class NativeVirtualRegion:
    base: int
    size: int
    allocation_base: int
    allocation_protect: int
    state: int
    protect: int
    kind: int

    @property
    def end(self) -> int:
        return self.base + self.size

    @property
    def base_protection(self) -> int:
        return self.protect & ~(PAGE_GUARD | PAGE_NOCACHE | PAGE_WRITECOMBINE)

    @property
    def committed(self) -> bool:
        return self.state == MEM_COMMIT

    @property
    def writable(self) -> bool:
        return (
            self.committed
            and not self.protect & PAGE_GUARD
            and self.base_protection in WRITABLE_PROTECTIONS
        )

    def identity(self) -> tuple[int, ...]:
        return (
            self.base,
            self.size,
            self.allocation_base,
            self.allocation_protect,
            self.state,
            self.protect,
            self.kind,
        )

    def record(self) -> dict[str, int]:
        return {
            "base": self.base,
            "size": self.size,
            "allocation_base": self.allocation_base,
            "allocation_protect": self.allocation_protect,
            "state": self.state,
            "protect": self.protect,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class NativeSnapshotRegion:
    region: NativeVirtualRegion
    data: bytes

    def __post_init__(self) -> None:
        if len(self.data) != self.region.size:
            raise ValueError("snapshot region byte count is not exact")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    def record(self) -> dict[str, object]:
        return {**self.region.record(), "sha256": self.sha256}


@dataclass(frozen=True)
class NativeSnapshot:
    regions: tuple[NativeSnapshotRegion, ...]
    committed_map: tuple[tuple[int, ...], ...]
    excluded_allocation_bases: tuple[int, ...]
    excluded_regions: tuple[dict[str, object], ...]
    schema: str = SNAPSHOT_SCHEMA

    def __post_init__(self) -> None:
        addresses = tuple(region.region.base for region in self.regions)
        if addresses != tuple(sorted(addresses)):
            raise ValueError("snapshot regions must be address-sorted")
        if len(addresses) != len(set(addresses)):
            raise ValueError("snapshot regions must not overlap by base")

    @property
    def total_bytes(self) -> int:
        return sum(len(region.data) for region in self.regions)

    @property
    def digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(self.schema.encode("ascii"))
        for capture in self.regions:
            digest.update(
                struct.pack(
                    "<QQ",
                    capture.region.base,
                    capture.region.size,
                )
            )
            digest.update(capture.data)
        return digest.hexdigest()

    def record(self, *, include_regions: bool = True) -> dict[str, object]:
        record: dict[str, object] = {
            "schema": self.schema,
            "sha256": self.digest,
            "region_count": len(self.regions),
            "total_bytes": self.total_bytes,
            "committed_map_region_count": len(self.committed_map),
            "excluded_allocation_bases": list(self.excluded_allocation_bases),
            "excluded_regions": list(self.excluded_regions),
            "physical_predictive_authority": False,
            "external_effect_coverage": "unresolved",
        }
        if include_regions:
            record["regions"] = [capture.record() for capture in self.regions]
        return record


@dataclass(frozen=True)
class NativeDirtyPage:
    address: int
    root_data: bytes
    root_sha256: str
    endpoint_sha256: str

    def record(self) -> dict[str, object]:
        return {
            "address": self.address,
            "size": len(self.root_data),
            "root_sha256": self.root_sha256,
            "endpoint_sha256": self.endpoint_sha256,
        }


@dataclass(frozen=True)
class NativeReplayActionCarrier:
    replay_object: int
    update_node: int
    input_cursor: int
    replay_frame_counter: int
    recorded_mask: int

    def record(self) -> dict[str, int]:
        return {
            "replay_object": self.replay_object,
            "update_node": self.update_node,
            "input_cursor": self.input_cursor,
            "replay_frame_counter": self.replay_frame_counter,
            "recorded_mask": self.recorded_mask,
            "native_action_load": 0x004525BE,
            "native_action_store": 0x004525C1,
        }


@dataclass(frozen=True)
class NativeBarrierHeader:
    pid: int
    target_manager_frame: int
    status: int
    command: int
    owner_thread_id: int
    arrival_serial: int
    step_serial: int
    restore_serial: int
    last_chain_result: int
    error_code: int
    root_esp: int
    root_ebp: int
    endpoint_esp: int
    endpoint_ebp: int
    root_manager_frame: int
    endpoint_manager_frame: int

    def record(self) -> dict[str, int]:
        return {
            "pid": self.pid,
            "target_manager_frame": self.target_manager_frame,
            "status": self.status,
            "command": self.command,
            "owner_thread_id": self.owner_thread_id,
            "arrival_serial": self.arrival_serial,
            "step_serial": self.step_serial,
            "restore_serial": self.restore_serial,
            "last_chain_result": self.last_chain_result,
            "error_code": self.error_code,
            "root_esp": self.root_esp,
            "root_ebp": self.root_ebp,
            "endpoint_esp": self.endpoint_esp,
            "endpoint_ebp": self.endpoint_ebp,
            "root_manager_frame": self.root_manager_frame,
            "endpoint_manager_frame": self.endpoint_manager_frame,
        }


@dataclass(frozen=True)
class FrozenNativeThread:
    handle: int
    thread_id: int
    instruction_pointer: int
    stack_pointer: int


class NativeSnapshotUnknownError(RuntimeError):
    """The one-tick transaction crossed an unsupported state boundary."""


class NativeSnapshotUnsafeStateError(RuntimeError):
    """The injected barrier or target-thread state cannot be safely undone."""


class _X86Builder:
    def __init__(self) -> None:
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    def emit(self, payload: bytes) -> None:
        self.code += payload

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate x86 label {name}")
        self.labels[name] = len(self.code)

    def jmp(self, label: str) -> None:
        self.emit(b"\xe9")
        self.fixups.append((len(self.code), label))
        self.emit(b"\0\0\0\0")

    def jcc(self, opcode: int, label: str) -> None:
        self.emit(b"\x0f" + bytes((opcode,)))
        self.fixups.append((len(self.code), label))
        self.emit(b"\0\0\0\0")

    def finish(self) -> bytes:
        for offset, label in self.fixups:
            if label not in self.labels:
                raise ValueError(f"missing x86 label {label}")
            displacement = self.labels[label] - (offset + 4)
            struct.pack_into("<i", self.code, offset, displacement)
        return bytes(self.code)


def _u32(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"value outside uint32: {value:#x}")
    return struct.pack("<I", value)


def _relative_call(source: int, target: int) -> bytes:
    displacement = target - (source + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise ValueError("relative call target is outside rel32")
    return b"\xe8" + struct.pack("<i", displacement)


def _mov_m32_imm32(address: int, value: int) -> bytes:
    return b"\xc7\x05" + _u32(address) + _u32(value)


def _mov_m32_eax(address: int) -> bytes:
    return b"\xa3" + _u32(address)


def _mov_eax_m32(address: int) -> bytes:
    return b"\xa1" + _u32(address)


def build_native_snapshot_stub(remote_base: int) -> bytes:
    """Build the position-specific x86 calculation-chain command barrier."""

    stub_address = remote_base + BARRIER_STUB_OFFSET
    status = remote_base + HEADER_STATUS
    command = remote_base + HEADER_COMMAND
    error = remote_base + HEADER_ERROR
    target_manager = remote_base + HEADER_TARGET_MANAGER
    owner_tid = remote_base + HEADER_OWNER_TID
    arrival_serial = remote_base + HEADER_ARRIVAL_SERIAL
    step_serial = remote_base + HEADER_STEP_SERIAL
    restore_serial = remote_base + HEADER_RESTORE_SERIAL
    last_result = remote_base + HEADER_LAST_RESULT
    root_esp = remote_base + HEADER_ROOT_ESP
    root_ebp = remote_base + HEADER_ROOT_EBP
    endpoint_esp = remote_base + HEADER_ENDPOINT_ESP
    endpoint_ebp = remote_base + HEADER_ENDPOINT_EBP
    root_manager = remote_base + HEADER_ROOT_MANAGER
    endpoint_manager = remote_base + HEADER_ENDPOINT_MANAGER
    root_fx = remote_base + BARRIER_ROOT_FX_OFFSET
    endpoint_fx = remote_base + BARRIER_ENDPOINT_FX_OFFSET

    builder = _X86Builder()

    def emit_arrival(wait_status: int) -> None:
        builder.emit(b"\x64\xa1\x24\x00\x00\x00")
        builder.emit(_mov_m32_eax(owner_tid))
        builder.emit(b"\x89\x25" + _u32(root_esp))
        builder.emit(b"\x89\x2d" + _u32(root_ebp))
        builder.emit(_mov_eax_m32(0x0164D30C))
        builder.emit(_mov_m32_eax(root_manager))
        builder.emit(b"\x0f\xae\x05" + _u32(root_fx))  # fxsave
        builder.emit(b"\xff\x05" + _u32(arrival_serial))
        builder.emit(_mov_m32_imm32(status, wait_status))

    def emit_headless_step(fx_source: int) -> None:
        builder.emit(_mov_m32_imm32(command, COMMAND_NONE))
        builder.emit(_mov_m32_imm32(status, STATUS_RUNNING))
        builder.emit(b"\x0f\xae\x0d" + _u32(fx_source))  # fxrstor
        builder.emit(b"\xb9" + _u32(UPDATE_CHAIN_HEAD))
        call_source = stub_address + len(builder.code)
        builder.emit(_relative_call(call_source, UPDATE_CHAIN_EXECUTE))
        builder.emit(_mov_m32_eax(last_result))
        builder.emit(b"\x89\x25" + _u32(endpoint_esp))
        builder.emit(b"\x89\x2d" + _u32(endpoint_ebp))
        builder.emit(_mov_eax_m32(0x0164D30C))
        builder.emit(_mov_m32_eax(endpoint_manager))
        builder.emit(b"\x0f\xae\x05" + _u32(endpoint_fx))
        builder.emit(b"\xff\x05" + _u32(step_serial))
        builder.emit(_mov_m32_imm32(status, STATUS_STEP_DONE))
        builder.jmp("wait")

    builder.emit(_mov_eax_m32(status))
    builder.emit(b"\x83\xf8" + bytes((STATUS_NATURAL_ARMED,)))
    builder.jcc(0x84, "natural_arrival")  # je
    builder.emit(b"\x83\xf8" + bytes((STATUS_ARMED,)))
    builder.jcc(0x85, "pass_through")  # jne
    builder.emit(_mov_eax_m32(target_manager))
    builder.emit(b"\x3b\x05" + _u32(0x0164D30C))
    builder.jcc(0x85, "pass_through")

    emit_arrival(STATUS_ROOT_WAIT)
    builder.jmp("wait")

    builder.label("natural_arrival")
    emit_arrival(STATUS_NATURAL_WAIT)

    builder.label("wait")
    builder.emit(_mov_eax_m32(command))
    builder.emit(b"\x85\xc0")
    builder.jcc(0x84, "pause")  # je
    builder.emit(b"\x83\xf8" + bytes((COMMAND_STEP,)))
    builder.jcc(0x84, "step")
    builder.emit(b"\x83\xf8" + bytes((COMMAND_RESTORE_READY,)))
    builder.jcc(0x84, "restore")
    builder.emit(b"\x83\xf8" + bytes((COMMAND_RESUME,)))
    builder.jcc(0x84, "resume")
    builder.emit(b"\x83\xf8" + bytes((COMMAND_CONTINUE,)))
    builder.jcc(0x84, "continue")
    builder.emit(b"\x83\xf8" + bytes((COMMAND_NATURAL_ADVANCE,)))
    builder.jcc(0x84, "natural_advance")
    builder.jmp("bad_command")

    builder.label("pause")
    builder.emit(b"\xf3\x90")
    builder.jmp("wait")

    builder.label("step")
    builder.emit(_mov_eax_m32(status))
    builder.emit(b"\x83\xf8" + bytes((STATUS_ROOT_WAIT,)))
    builder.jcc(0x85, "bad_command")
    emit_headless_step(root_fx)

    builder.label("continue")
    builder.emit(_mov_eax_m32(status))
    builder.emit(b"\x83\xf8" + bytes((STATUS_STEP_DONE,)))
    builder.jcc(0x85, "bad_command")
    emit_headless_step(endpoint_fx)

    builder.label("restore")
    builder.emit(_mov_eax_m32(status))
    builder.emit(b"\x83\xf8" + bytes((STATUS_STEP_DONE,)))
    builder.jcc(0x85, "bad_command")
    builder.emit(_mov_m32_imm32(command, COMMAND_NONE))
    builder.emit(b"\x0f\xae\x0d" + _u32(root_fx))
    builder.emit(b"\xff\x05" + _u32(restore_serial))
    builder.emit(_mov_m32_imm32(status, STATUS_ROOT_WAIT))
    builder.jmp("wait")

    builder.label("resume")
    builder.emit(_mov_eax_m32(status))
    builder.emit(b"\x83\xf8" + bytes((STATUS_ROOT_WAIT,)))
    builder.jcc(0x85, "bad_command")
    builder.emit(_mov_m32_imm32(command, COMMAND_NONE))
    builder.emit(_mov_m32_imm32(status, STATUS_RUNNING))
    builder.emit(b"\x0f\xae\x0d" + _u32(root_fx))
    builder.emit(b"\xb9" + _u32(UPDATE_CHAIN_HEAD))
    call_source = stub_address + len(builder.code)
    builder.emit(_relative_call(call_source, UPDATE_CHAIN_EXECUTE))
    builder.emit(_mov_m32_eax(last_result))
    builder.emit(_mov_m32_imm32(status, STATUS_RELEASED))
    builder.emit(b"\xc3")

    builder.label("natural_advance")
    builder.emit(_mov_eax_m32(status))
    builder.emit(b"\x83\xf8" + bytes((STATUS_ROOT_WAIT,)))
    builder.jcc(0x84, "natural_advance_ready")
    builder.emit(b"\x83\xf8" + bytes((STATUS_NATURAL_WAIT,)))
    builder.jcc(0x85, "bad_command")
    builder.label("natural_advance_ready")
    builder.emit(_mov_m32_imm32(command, COMMAND_NONE))
    builder.emit(_mov_m32_imm32(status, STATUS_NATURAL_RUNNING))
    builder.emit(b"\x0f\xae\x0d" + _u32(root_fx))
    builder.emit(b"\xb9" + _u32(UPDATE_CHAIN_HEAD))
    call_source = stub_address + len(builder.code)
    builder.emit(_relative_call(call_source, UPDATE_CHAIN_EXECUTE))
    builder.emit(_mov_m32_eax(last_result))
    builder.emit(_mov_m32_imm32(status, STATUS_NATURAL_ARMED))
    builder.emit(b"\xc3")

    builder.label("bad_command")
    builder.emit(_mov_m32_imm32(command, COMMAND_NONE))
    builder.emit(_mov_m32_imm32(error, ERROR_BAD_COMMAND_STATE))
    builder.emit(_mov_m32_imm32(status, STATUS_ERROR))
    builder.jmp("wait")

    builder.label("pass_through")
    builder.emit(b"\xb9" + _u32(UPDATE_CHAIN_HEAD))
    call_source = stub_address + len(builder.code)
    builder.emit(_relative_call(call_source, UPDATE_CHAIN_EXECUTE))
    builder.emit(b"\xc3")
    return builder.finish()


def build_native_snapshot_image(
    remote_base: int,
    *,
    pid: int,
    target_manager_frame: int,
) -> bytes:
    stub = build_native_snapshot_stub(remote_base)
    if BARRIER_STUB_OFFSET + len(stub) > BARRIER_ALLOCATION_SIZE:
        raise ValueError("native snapshot stub exceeds remote allocation")
    image = bytearray(BARRIER_STUB_OFFSET + len(stub))
    image[:4] = BARRIER_MAGIC
    for offset, value in (
        (HEADER_VERSION, BARRIER_VERSION),
        (HEADER_PID, pid),
        (HEADER_CALLSITE, UPDATE_CHAIN_CALLSITE),
        (HEADER_TARGET, UPDATE_CHAIN_EXECUTE),
        (HEADER_STUB_SIZE, len(stub)),
        (HEADER_TARGET_MANAGER, target_manager_frame),
        (HEADER_STATUS, STATUS_ARMED),
    ):
        struct.pack_into("<I", image, offset, value)
    image[BARRIER_STUB_OFFSET : BARRIER_STUB_OFFSET + len(stub)] = stub
    return bytes(image)


def build_native_snapshot_patch(remote_base: int) -> bytes:
    return _relative_call(
        UPDATE_CHAIN_CALLSITE,
        remote_base + BARRIER_STUB_OFFSET,
    )


def parse_native_barrier_header(
    payload: bytes,
    *,
    expected_pid: int,
) -> NativeBarrierHeader:
    if len(payload) != BARRIER_HEADER_SIZE:
        raise ValueError("native snapshot barrier header size is invalid")
    if payload[:4] != BARRIER_MAGIC:
        raise ValueError("native snapshot barrier magic is invalid")
    values = {
        offset: struct.unpack_from("<I", payload, offset)[0]
        for offset in range(HEADER_VERSION, HEADER_ENDPOINT_MANAGER + 1, 4)
    }
    if (
        values[HEADER_VERSION] != BARRIER_VERSION
        or values[HEADER_PID] != expected_pid
        or values[HEADER_CALLSITE] != UPDATE_CHAIN_CALLSITE
        or values[HEADER_TARGET] != UPDATE_CHAIN_EXECUTE
        or not 0 < values[HEADER_STUB_SIZE] < BARRIER_ALLOCATION_SIZE
    ):
        raise ValueError("native snapshot barrier identity is invalid")
    last_result = struct.unpack(
        "<i",
        struct.pack("<I", values[HEADER_LAST_RESULT]),
    )[0]
    return NativeBarrierHeader(
        pid=values[HEADER_PID],
        target_manager_frame=values[HEADER_TARGET_MANAGER],
        status=values[HEADER_STATUS],
        command=values[HEADER_COMMAND],
        owner_thread_id=values[HEADER_OWNER_TID],
        arrival_serial=values[HEADER_ARRIVAL_SERIAL],
        step_serial=values[HEADER_STEP_SERIAL],
        restore_serial=values[HEADER_RESTORE_SERIAL],
        last_chain_result=last_result,
        error_code=values[HEADER_ERROR],
        root_esp=values[HEADER_ROOT_ESP],
        root_ebp=values[HEADER_ROOT_EBP],
        endpoint_esp=values[HEADER_ENDPOINT_ESP],
        endpoint_ebp=values[HEADER_ENDPOINT_EBP],
        root_manager_frame=values[HEADER_ROOT_MANAGER],
        endpoint_manager_frame=values[HEADER_ENDPOINT_MANAGER],
    )


def snapshot_dirty_pages(
    root: NativeSnapshot,
    endpoint: NativeSnapshot,
    *,
    page_size: int = PAGE_SIZE,
) -> tuple[NativeDirtyPage, ...]:
    if page_size <= 0:
        raise ValueError("snapshot page size must be positive")
    if root.committed_map != endpoint.committed_map:
        root_map = set(root.committed_map)
        endpoint_map = set(endpoint.committed_map)
        raise NativeSnapshotUnknownError(
            "committed virtual-memory map changed during one native tick; "
            f"removed={sorted(root_map - endpoint_map)[:8]!r}; "
            f"added={sorted(endpoint_map - root_map)[:8]!r}"
        )
    if tuple(capture.region.identity() for capture in root.regions) != tuple(
        capture.region.identity() for capture in endpoint.regions
    ):
        raise NativeSnapshotUnknownError(
            "captured native region identity changed during one tick"
        )
    dirty: list[NativeDirtyPage] = []
    for before, after in zip(root.regions, endpoint.regions, strict=True):
        for offset in range(0, len(before.data), page_size):
            root_page = before.data[offset : offset + page_size]
            endpoint_page = after.data[offset : offset + page_size]
            if root_page == endpoint_page:
                continue
            dirty.append(
                NativeDirtyPage(
                    address=before.region.base + offset,
                    root_data=root_page,
                    root_sha256=hashlib.sha256(root_page).hexdigest(),
                    endpoint_sha256=hashlib.sha256(endpoint_page).hexdigest(),
                )
            )
    return tuple(dirty)


def changed_byte_addresses(
    root: NativeSnapshot,
    changed: NativeSnapshot,
) -> tuple[int, ...]:
    if tuple(capture.region.identity() for capture in root.regions) != tuple(
        capture.region.identity() for capture in changed.regions
    ):
        raise ValueError("cannot compare different snapshot region sets")
    addresses: list[int] = []
    for before, after in zip(root.regions, changed.regions, strict=True):
        addresses.extend(
            before.region.base + offset
            for offset, (left, right) in enumerate(
                zip(before.data, after.data, strict=True)
            )
            if left != right
        )
    return tuple(addresses)


def committed_map_identity(
    regions: Iterable[NativeVirtualRegion],
) -> tuple[tuple[int, ...], ...]:
    return tuple(region.identity() for region in regions if region.committed)


def _configure_snapshot_api(api: Any) -> None:
    api.kernel32.VirtualQueryEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        ctypes.POINTER(_MemoryBasicInformation),
        ctypes.c_size_t,
    ]
    api.kernel32.VirtualQueryEx.restype = ctypes.c_size_t
    api.kernel32.VirtualAllocEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    api.kernel32.VirtualAllocEx.restype = wintypes.LPVOID
    api.kernel32.VirtualFreeEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
    ]
    api.kernel32.VirtualFreeEx.restype = wintypes.BOOL
    api.kernel32.CreateToolhelp32Snapshot.argtypes = [
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    api.kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    api.kernel32.Thread32First.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ThreadEntry32),
    ]
    api.kernel32.Thread32First.restype = wintypes.BOOL
    api.kernel32.Thread32Next.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ThreadEntry32),
    ]
    api.kernel32.Thread32Next.restype = wintypes.BOOL
    api.kernel32.OpenThread.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    api.kernel32.OpenThread.restype = wintypes.HANDLE
    api.kernel32.SuspendThread.argtypes = [wintypes.HANDLE]
    api.kernel32.SuspendThread.restype = wintypes.DWORD
    api.kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    api.kernel32.ResumeThread.restype = wintypes.DWORD
    context_reader = (
        api.kernel32.Wow64GetThreadContext
        if ctypes.sizeof(ctypes.c_void_p) == 8
        else api.kernel32.GetThreadContext
    )
    context_reader.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_Wow64Context),
    ]
    context_reader.restype = wintypes.BOOL


def query_native_virtual_regions(
    api: Any,
    handle: int,
    *,
    address_limit: int = PROCESS_ADDRESS_LIMIT,
) -> tuple[NativeVirtualRegion, ...]:
    _configure_snapshot_api(api)
    regions: list[NativeVirtualRegion] = []
    address = 0
    while address < address_limit:
        info = _MemoryBasicInformation()
        size = api.kernel32.VirtualQueryEx(
            handle,
            ctypes.c_void_p(address),
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not size:
            break
        base = int(info.BaseAddress or 0)
        region_size = int(info.RegionSize)
        if region_size <= 0 or base < address:
            raise RuntimeError("VirtualQueryEx returned a non-progressing region")
        regions.append(
            NativeVirtualRegion(
                base=base,
                size=region_size,
                allocation_base=int(info.AllocationBase or 0),
                allocation_protect=int(info.AllocationProtect),
                state=int(info.State),
                protect=int(info.Protect),
                kind=int(info.Type),
            )
        )
        address = base + region_size
    return tuple(regions)


def _read_exact_chunked(
    api: Any,
    handle: int,
    address: int,
    size: int,
) -> bytes:
    chunks = []
    for offset in range(0, size, READ_CHUNK_SIZE):
        chunk_size = min(READ_CHUNK_SIZE, size - offset)
        chunks.append(_read_memory(api, handle, address + offset, chunk_size))
    return b"".join(chunks)


def select_snapshot_regions(
    regions: tuple[NativeVirtualRegion, ...],
    *,
    excluded_allocation_bases: frozenset[int],
    remote_base: int,
    remote_size: int,
    maximum_region_size: int = DEFAULT_MAXIMUM_REGION_SIZE,
    maximum_snapshot_size: int = DEFAULT_MAXIMUM_SNAPSHOT_SIZE,
) -> tuple[
    tuple[NativeVirtualRegion, ...],
    tuple[dict[str, object], ...],
]:
    selected: list[NativeVirtualRegion] = []
    excluded: list[dict[str, object]] = []
    total = 0
    remote_end = remote_base + remote_size
    for region in regions:
        reason: str | None = None
        if not region.writable:
            continue
        if region.allocation_base in excluded_allocation_bases:
            reason = "thread_stack_or_explicit_allocation"
        elif region.base < remote_end and remote_base < region.end:
            reason = "snapshot_barrier_allocation"
        elif region.kind not in (MEM_PRIVATE, MEM_IMAGE):
            reason = "mapped_or_unknown_writable_region"
        elif region.size > maximum_region_size:
            reason = "region_size_cap"
        elif total + region.size > maximum_snapshot_size:
            reason = "snapshot_size_cap"
        if reason is not None:
            excluded.append({**region.record(), "reason": reason})
            continue
        selected.append(region)
        total += region.size
    return tuple(selected), tuple(excluded)


def capture_native_snapshot(
    api: Any,
    handle: int,
    *,
    excluded_allocation_bases: frozenset[int],
    remote_base: int,
    remote_size: int = BARRIER_ALLOCATION_SIZE,
) -> NativeSnapshot:
    regions = query_native_virtual_regions(api, handle)
    selected, excluded = select_snapshot_regions(
        regions,
        excluded_allocation_bases=excluded_allocation_bases,
        remote_base=remote_base,
        remote_size=remote_size,
    )
    captures = tuple(
        NativeSnapshotRegion(
            region=region,
            data=_read_exact_chunked(
                api,
                handle,
                region.base,
                region.size,
            ),
        )
        for region in selected
    )
    return NativeSnapshot(
        regions=captures,
        committed_map=committed_map_identity(regions),
        excluded_allocation_bases=tuple(sorted(excluded_allocation_bases)),
        excluded_regions=excluded,
    )


def recapture_native_snapshot(
    api: Any,
    handle: int,
    root: NativeSnapshot,
) -> NativeSnapshot:
    regions = query_native_virtual_regions(api, handle)
    return NativeSnapshot(
        regions=tuple(
            NativeSnapshotRegion(
                region=capture.region,
                data=_read_exact_chunked(
                    api,
                    handle,
                    capture.region.base,
                    capture.region.size,
                ),
            )
            for capture in root.regions
        ),
        committed_map=committed_map_identity(regions),
        excluded_allocation_bases=root.excluded_allocation_bases,
        excluded_regions=root.excluded_regions,
    )


def restore_native_dirty_pages(
    api: Any,
    handle: int,
    dirty_pages: tuple[NativeDirtyPage, ...],
) -> None:
    for address, data in _coalesce_native_dirty_pages(dirty_pages):
        _write_memory(
            api,
            handle,
            address,
            data,
            executable=False,
        )


def verify_native_dirty_pages(
    api: Any,
    handle: int,
    dirty_pages: tuple[NativeDirtyPage, ...],
) -> None:
    for address, expected in _coalesce_native_dirty_pages(dirty_pages):
        actual = _read_exact_chunked(
            api,
            handle,
            address,
            len(expected),
        )
        if actual != expected:
            raise NativeSnapshotUnknownError(
                "restored native dirty span does not match root bytes at "
                f"0x{address:08x}"
            )


def _coalesce_native_dirty_pages(
    dirty_pages: tuple[NativeDirtyPage, ...],
) -> tuple[tuple[int, bytes], ...]:
    spans: list[tuple[int, bytes]] = []
    for page in dirty_pages:
        if spans and spans[-1][0] + len(spans[-1][1]) == page.address:
            address, data = spans[-1]
            spans[-1] = (address, data + page.root_data)
        else:
            if spans and page.address < spans[-1][0] + len(spans[-1][1]):
                raise ValueError("native dirty pages overlap or are unsorted")
            spans.append((page.address, page.root_data))
    return tuple(spans)


def _virtual_region_containing(
    regions: tuple[NativeVirtualRegion, ...],
    address: int,
) -> NativeVirtualRegion:
    for region in regions:
        if region.base <= address < region.end:
            return region
    raise NativeSnapshotUnknownError(
        f"no virtual region contains address 0x{address:08x}"
    )


def enumerate_target_thread_ids(api: Any, pid: int) -> tuple[int, ...]:
    snapshot = api.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        raise _win_error("CreateToolhelp32Snapshot(threads)")
    thread_ids: list[int] = []
    try:
        entry = _ThreadEntry32()
        entry.dwSize = ctypes.sizeof(entry)
        if not api.kernel32.Thread32First(snapshot, ctypes.byref(entry)):
            raise _win_error("Thread32First")
        while True:
            if int(entry.th32OwnerProcessID) == pid:
                thread_ids.append(int(entry.th32ThreadID))
            if not api.kernel32.Thread32Next(snapshot, ctypes.byref(entry)):
                break
    finally:
        api.kernel32.CloseHandle(snapshot)
    return tuple(sorted(thread_ids))


def suspend_non_owner_threads(
    api: Any,
    pid: int,
    *,
    owner_thread_id: int,
) -> tuple[FrozenNativeThread, ...]:
    _configure_snapshot_api(api)
    thread_ids = enumerate_target_thread_ids(api, pid)
    if owner_thread_id not in thread_ids:
        raise NativeSnapshotUnknownError(
            "barrier owner is absent from the target thread set"
        )
    suspended: list[FrozenNativeThread] = []
    try:
        for thread_id in thread_ids:
            if thread_id == owner_thread_id:
                continue
            handle = api.kernel32.OpenThread(
                THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION,
                False,
                thread_id,
            )
            if not handle:
                raise _win_error(f"OpenThread({thread_id})")
            if api.kernel32.SuspendThread(handle) == 0xFFFFFFFF:
                api.kernel32.CloseHandle(handle)
                raise _win_error(f"SuspendThread({thread_id})")
            context = _Wow64Context()
            context.ContextFlags = WOW64_CONTEXT_CONTROL
            context_reader = (
                api.kernel32.Wow64GetThreadContext
                if ctypes.sizeof(ctypes.c_void_p) == 8
                else api.kernel32.GetThreadContext
            )
            if not context_reader(handle, ctypes.byref(context)):
                api.kernel32.ResumeThread(handle)
                api.kernel32.CloseHandle(handle)
                raise _win_error(f"GetThreadContext({thread_id})")
            suspended.append(
                FrozenNativeThread(
                    handle=handle,
                    thread_id=thread_id,
                    instruction_pointer=int(context.Eip),
                    stack_pointer=int(context.Esp),
                )
            )
        return tuple(suspended)
    except Exception as error:
        release_frozen_threads(api, suspended)
        raise NativeSnapshotUnsafeStateError(
            "could not freeze every non-owner target thread"
        ) from error


def release_frozen_threads(
    api: Any,
    frozen: Iterable[FrozenNativeThread],
) -> None:
    errors: list[str] = []
    for thread in reversed(tuple(frozen)):
        if api.kernel32.ResumeThread(thread.handle) == 0xFFFFFFFF:
            errors.append(f"ResumeThread({thread.thread_id})")
        api.kernel32.CloseHandle(thread.handle)
    if errors:
        raise NativeSnapshotUnsafeStateError(
            "failed to resume target threads: " + ", ".join(errors)
        )


def snapshot_excluded_allocation_bases(
    regions: tuple[NativeVirtualRegion, ...],
    *,
    owner_stack_pointer: int,
    frozen_threads: tuple[FrozenNativeThread, ...],
    remote_base: int,
) -> frozenset[int]:
    owner_stack = _virtual_region_containing(
        regions,
        owner_stack_pointer,
    ).allocation_base
    excluded = frozenset(
        _virtual_region_containing(regions, address).allocation_base
        for address in (
            remote_base,
            *(thread.stack_pointer for thread in frozen_threads),
        )
    )
    if owner_stack in excluded:
        raise NativeSnapshotUnknownError(
            "barrier owner stack aliases an excluded allocation"
        )
    return excluded


def resolve_native_replay_action_carrier(
    api: Any,
    handle: int,
) -> NativeReplayActionCarrier:
    replay_object = struct.unpack(
        "<I",
        _read_memory(api, handle, ADDR_REPLAY_MANAGER, 4),
    )[0]
    if not replay_object:
        raise NativeSnapshotUnknownError("native replay object is absent")
    mode = struct.unpack(
        "<I",
        _read_memory(
            api,
            handle,
            replay_object + REPLAY_MODE_OFFSET,
            4,
        ),
    )[0]
    if mode != 1:
        raise NativeSnapshotUnknownError(
            f"native replay mode is {mode}, expected playback mode 1"
        )
    update_node = struct.unpack(
        "<I",
        _read_memory(
            api,
            handle,
            replay_object + REPLAY_UPDATE_NODE_OFFSET,
            4,
        ),
    )[0]
    priority, callback, context = struct.unpack(
        "<H2xI20xI",
        _read_memory(api, handle, update_node, 32),
    )
    if (
        priority != REPLAY_PRIORITY
        or callback != REPLAY_PLAY_INPUT_CALLBACK
        or context != replay_object
    ):
        raise NativeSnapshotUnknownError(
            "native replay update node identity does not match priority-6 playback"
        )
    input_cursor = struct.unpack(
        "<I",
        _read_memory(
            api,
            handle,
            replay_object + REPLAY_INPUT_CURSOR_OFFSET,
            4,
        ),
    )[0]
    if not input_cursor:
        raise NativeSnapshotUnknownError("native replay input cursor is null")
    replay_frame_counter = struct.unpack(
        "<I",
        _read_memory(
            api,
            handle,
            replay_object + REPLAY_FRAME_COUNTER_OFFSET,
            4,
        ),
    )[0]
    recorded_mask = struct.unpack(
        "<H",
        _read_memory(api, handle, input_cursor, 2),
    )[0]
    return NativeReplayActionCarrier(
        replay_object=replay_object,
        update_node=update_node,
        input_cursor=input_cursor,
        replay_frame_counter=replay_frame_counter,
        recorded_mask=recorded_mask,
    )


def write_native_replay_action(
    api: Any,
    handle: int,
    carrier: NativeReplayActionCarrier,
    mask: int,
) -> None:
    if not 0 <= mask <= 0xFFFF or mask & 0x02:
        raise ValueError("native replay action must be a uint16 no-Bomb mask")
    _write_memory(
        api,
        handle,
        carrier.input_cursor,
        struct.pack("<H", mask),
        executable=False,
    )


class NativeCalculationBarrier:
    """Installed rolling update-chain call barrier for one manager-frame root."""

    def __init__(
        self,
        *,
        api: Any,
        pid: int,
        handle: int,
        remote_base: int,
    ) -> None:
        self.api = api
        self.pid = pid
        self.handle = handle
        self.remote_base = remote_base
        self._installed = True
        self._closed = False

    @classmethod
    def install(
        cls,
        api: Any,
        pid: int,
        *,
        target_manager_frame: int,
    ) -> NativeCalculationBarrier:
        if target_manager_frame <= 0:
            raise ValueError("snapshot target manager frame must be positive")
        _configure_snapshot_api(api)
        access = (
            PROCESS_QUERY_INFORMATION
            | PROCESS_VM_OPERATION
            | PROCESS_VM_READ
            | PROCESS_VM_WRITE
        )
        handle = api.kernel32.OpenProcess(access, False, pid)
        if not handle:
            raise _win_error("OpenProcess(native snapshot)")
        remote_base = 0
        callsite_active = False
        try:
            if (
                _read_memory(
                    api,
                    handle,
                    UPDATE_CHAIN_CALLSITE,
                    len(UPDATE_CHAIN_CALL_ORIGINAL),
                )
                != UPDATE_CHAIN_CALL_ORIGINAL
            ):
                raise RuntimeError("update-chain callsite does not match shipped bytes")
            allocated = api.kernel32.VirtualAllocEx(
                handle,
                None,
                BARRIER_ALLOCATION_SIZE,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE,
            )
            remote_base = int(allocated or 0)
            if not remote_base or remote_base >= PROCESS_ADDRESS_LIMIT:
                raise _win_error("VirtualAllocEx(native snapshot)")
            image = build_native_snapshot_image(
                remote_base,
                pid=pid,
                target_manager_frame=target_manager_frame,
            )
            _write_memory(
                api,
                handle,
                remote_base,
                image,
                executable=True,
            )
            patch = build_native_snapshot_patch(remote_base)
            suspended = _suspend_target_threads(api, pid)
            release_errors: tuple[str, ...] = ()
            try:
                if any(
                    UPDATE_CHAIN_CALLSITE
                    <= thread.instruction_pointer
                    < UPDATE_CHAIN_CALLSITE + len(patch)
                    for thread in suspended
                ):
                    raise NativeSnapshotUnknownError(
                        "target thread is executing the snapshot callsite"
                    )
                if (
                    _read_memory(
                        api,
                        handle,
                        UPDATE_CHAIN_CALLSITE,
                        len(UPDATE_CHAIN_CALL_ORIGINAL),
                    )
                    != UPDATE_CHAIN_CALL_ORIGINAL
                ):
                    raise RuntimeError(
                        "update-chain callsite changed before activation"
                    )
                callsite_active = True
                _write_code(
                    api,
                    handle,
                    UPDATE_CHAIN_CALLSITE,
                    patch,
                )
                if (
                    _read_memory(
                        api,
                        handle,
                        UPDATE_CHAIN_CALLSITE,
                        len(patch),
                    )
                    != patch
                ):
                    raise RuntimeError("native snapshot callsite verification failed")
            except Exception:
                if callsite_active:
                    _write_code(
                        api,
                        handle,
                        UPDATE_CHAIN_CALLSITE,
                        UPDATE_CHAIN_CALL_ORIGINAL,
                    )
                    callsite_active = False
                raise
            finally:
                release_errors = _release_suspended_threads(api, suspended)
            if release_errors:
                raise NativeSnapshotUnsafeStateError(
                    "activation left target threads suspended: "
                    + "; ".join(release_errors)
                )
            return cls(
                api=api,
                pid=pid,
                handle=handle,
                remote_base=remote_base,
            )
        except Exception:
            if remote_base and not callsite_active:
                api.kernel32.VirtualFreeEx(
                    handle,
                    ctypes.c_void_p(remote_base),
                    0,
                    MEM_RELEASE,
                )
            api.kernel32.CloseHandle(handle)
            raise

    def header(self) -> NativeBarrierHeader:
        return parse_native_barrier_header(
            _read_memory(
                self.api,
                self.handle,
                self.remote_base,
                BARRIER_HEADER_SIZE,
            ),
            expected_pid=self.pid,
        )

    def wait_for_status(
        self,
        expected_status: int,
        *,
        timeout_seconds: float,
        minimum_serial: tuple[str, int] | None = None,
    ) -> NativeBarrierHeader:
        deadline = time.perf_counter() + timeout_seconds
        last_header: NativeBarrierHeader | None = None
        while time.perf_counter() < deadline:
            header = self.header()
            last_header = header
            if header.status == STATUS_ERROR:
                raise NativeSnapshotUnknownError(
                    f"native snapshot barrier error {header.error_code}"
                )
            serial_ok = True
            if minimum_serial is not None:
                name, value = minimum_serial
                serial_ok = int(getattr(header, name)) >= value
            if header.status == expected_status and serial_ok:
                return header
            time.sleep(0.0005)
        raise TimeoutError(
            "native snapshot barrier did not reach status "
            f"{expected_status}; last header={last_header!r}"
        )

    def wait_for_root(self, *, timeout_seconds: float) -> NativeBarrierHeader:
        return self.wait_for_status(
            STATUS_ROOT_WAIT,
            timeout_seconds=timeout_seconds,
            minimum_serial=("arrival_serial", 1),
        )

    def _command(self, command: int) -> None:
        header = self.header()
        if header.command != COMMAND_NONE:
            raise NativeSnapshotUnknownError(
                "native snapshot barrier still owns an earlier command"
            )
        _write_memory(
            self.api,
            self.handle,
            self.remote_base + HEADER_COMMAND,
            struct.pack("<I", command),
            executable=False,
        )

    def step(self, *, timeout_seconds: float) -> NativeBarrierHeader:
        before = self.header()
        if before.status != STATUS_ROOT_WAIT:
            raise NativeSnapshotUnknownError(
                "native one-tick step requires restored root wait"
            )
        self._command(COMMAND_STEP)
        return self.wait_for_status(
            STATUS_STEP_DONE,
            timeout_seconds=timeout_seconds,
            minimum_serial=("step_serial", before.step_serial + 1),
        )

    def continue_step(self, *, timeout_seconds: float) -> NativeBarrierHeader:
        before = self.header()
        if before.status != STATUS_STEP_DONE:
            raise NativeSnapshotUnknownError(
                "rolling native step requires a completed endpoint"
            )
        self._command(COMMAND_CONTINUE)
        return self.wait_for_status(
            STATUS_STEP_DONE,
            timeout_seconds=timeout_seconds,
            minimum_serial=("step_serial", before.step_serial + 1),
        )

    def natural_advance(self, *, timeout_seconds: float) -> NativeBarrierHeader:
        before = self.header()
        if before.status not in (STATUS_ROOT_WAIT, STATUS_NATURAL_WAIT):
            raise NativeSnapshotUnknownError(
                "natural advance requires a trapped calculation-call boundary"
            )
        self._command(COMMAND_NATURAL_ADVANCE)
        return self.wait_for_status(
            STATUS_NATURAL_WAIT,
            timeout_seconds=timeout_seconds,
            minimum_serial=("arrival_serial", before.arrival_serial + 1),
        )

    def mark_restore_ready(
        self,
        *,
        timeout_seconds: float,
    ) -> NativeBarrierHeader:
        before = self.header()
        if before.status != STATUS_STEP_DONE:
            raise NativeSnapshotUnknownError(
                "restore acknowledgement requires a completed step"
            )
        self._command(COMMAND_RESTORE_READY)
        return self.wait_for_status(
            STATUS_ROOT_WAIT,
            timeout_seconds=timeout_seconds,
            minimum_serial=("restore_serial", before.restore_serial + 1),
        )

    def installation_record(self) -> dict[str, object]:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "role": "offline_same_session_native_calculation_snapshot",
            "callsite": UPDATE_CHAIN_CALLSITE,
            "original_target": UPDATE_CHAIN_EXECUTE,
            "update_chain_head": UPDATE_CHAIN_HEAD,
            "render_chain_executed_inside_step": False,
            "rolling_endpoint_fx": True,
            "natural_next_call_trap": True,
            "remote_base": self.remote_base,
            "action_authority": False,
            "external_effect_coverage": "unresolved",
        }

    def close_after_target_termination(self) -> None:
        """Drop the local handle after the caller has terminated the target."""

        if self._closed:
            return
        self._closed = True
        self._installed = False
        self.api.kernel32.CloseHandle(self.handle)


__all__ = [
    "BARRIER_ALLOCATION_SIZE",
    "BARRIER_HEADER_SIZE",
    "BARRIER_MAGIC",
    "BARRIER_STUB_OFFSET",
    "BARRIER_VERSION",
    "COMMAND_NONE",
    "COMMAND_CONTINUE",
    "COMMAND_NATURAL_ADVANCE",
    "COMMAND_RESTORE_READY",
    "COMMAND_STEP",
    "NativeBarrierHeader",
    "NativeCalculationBarrier",
    "NativeDirtyPage",
    "NativeReplayActionCarrier",
    "NativeSnapshot",
    "NativeSnapshotRegion",
    "NativeSnapshotUnknownError",
    "NativeSnapshotUnsafeStateError",
    "NativeVirtualRegion",
    "SNAPSHOT_SCHEMA",
    "STATUS_ROOT_WAIT",
    "STATUS_STEP_DONE",
    "STATUS_NATURAL_WAIT",
    "UPDATE_CHAIN_CALLSITE",
    "UPDATE_CHAIN_CALL_ORIGINAL",
    "UPDATE_CHAIN_EXECUTE",
    "build_native_snapshot_image",
    "build_native_snapshot_patch",
    "build_native_snapshot_stub",
    "capture_native_snapshot",
    "changed_byte_addresses",
    "committed_map_identity",
    "enumerate_target_thread_ids",
    "parse_native_barrier_header",
    "query_native_virtual_regions",
    "recapture_native_snapshot",
    "release_frozen_threads",
    "resolve_native_replay_action_carrier",
    "restore_native_dirty_pages",
    "select_snapshot_regions",
    "snapshot_dirty_pages",
    "snapshot_excluded_allocation_bases",
    "suspend_non_owner_threads",
    "verify_native_dirty_pages",
    "write_native_replay_action",
]
