"""Bounded trace-only native ring for TH08 ordinary-enemy lifecycles.

The probe covers the two shipped ordinary-enemy allocation paths, every
revalidated active-bit clear, and the distinct global forced-HP-zero write.
It is default-off infrastructure and has no action authority.  Installation
and cleanup reuse the already tested Win32 remote-memory/thread primitives
from the priority-17 publication probe; lifecycle-specific activation remains
multi-site, exact-byte guarded, and reversible.

The native producer is single-threaded: every covered site executes on the
enemy-management game thread.  Each stub writes pre-instruction fields into
an unpublished ring slot, replays the exact overwritten instruction bytes,
then writes post-instruction fields and commits the event serial before the
header serial.  A reader accepts a batch only when every slot serial and the
double-read header serial agree.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct
import time
from typing import Any
import zlib

from .game_state import ADDR_ENEMY_MANAGER_FRAME, ADDR_STAGE_ROUTE_INDEX
from .priority17_publication_probe import (
    MEM_COMMIT,
    MEM_RELEASE,
    MEM_RESERVE,
    PAGE_EXECUTE_READWRITE,
    PROCESS_QUERY_INFORMATION,
    PROCESS_VM_OPERATION,
    PROCESS_VM_READ,
    PROCESS_VM_WRITE,
    Priority17ProbeUnsafeStateError,
    _configure_api,
    _read_memory,
    _release_suspended_threads,
    _suspend_target_threads,
    _win_error,
    _write_code,
    _write_memory,
)


PROBE_SCHEMA = "th08-enemy-lifecycle-probe-v2"
PROBE_MAGIC = b"ELR2"
PROBE_VERSION = 2
PROBE_CAPACITY = 256
PROBE_EVENT_SIZE = 48
PROBE_ALLOCATION_SIZE = 0x4000
PROBE_HEADER_SIZE = 32
PROBE_SERIAL_OFFSET = 16
PROBE_STUB_OFFSET = 0x100
PROBE_STUB_STRIDE = 0x100
PROBE_EVENT_OFFSET = 0x1000

ENEMY_POOL_BASE = 0x005826C0
ENEMY_POOL_SIZE = 480
ENEMY_STRIDE = 0x53D0
ENEMY_HP_OFFSET = 0x2DFC
ENEMY_FLAGS_OFFSET = 0x3324
ENEMY_FRAME_DAMAGE_OFFSET = 0x3354

FORCED_ZERO_RETURN_SPELL_FINISH = 0x0041622A
FORCED_ZERO_RETURN_OPCODE_5F = 0x0041DA8E
FORCED_ZERO_RETURN_BOSS_DEFEAT = 0x0042D941
FORCED_ZERO_RETURN_MESSAGE_START = 0x00433DA4
FORCED_ZERO_RETURN_ADDRESSES = frozenset(
    {
        FORCED_ZERO_RETURN_SPELL_FINISH,
        FORCED_ZERO_RETURN_OPCODE_5F,
        FORCED_ZERO_RETURN_BOSS_DEFEAT,
        FORCED_ZERO_RETURN_MESSAGE_START,
    }
)

_HEADER = struct.Struct("<4s7I")
_EVENT = struct.Struct("<IIIIIIiiiIiI")


class EnemyLifecycleKind(IntEnum):
    ALLOCATE_TIMELINE = 1
    ALLOCATE_INHERITED_REGISTERS = 2
    RETIRE_INITIAL_VM_TIMELINE = 3
    RETIRE_INITIAL_VM_INHERITED = 4
    RETIRE_MAIN_VM = 5
    RETIRE_OFFSCREEN_CULL = 6
    RETIRE_DEFEAT_MODE0 = 7
    FORCED_HP_ZERO = 8


_ALLOCATION_KINDS = frozenset(
    {
        EnemyLifecycleKind.ALLOCATE_TIMELINE,
        EnemyLifecycleKind.ALLOCATE_INHERITED_REGISTERS,
    }
)
_RETIREMENT_KINDS = frozenset(
    {
        EnemyLifecycleKind.RETIRE_INITIAL_VM_TIMELINE,
        EnemyLifecycleKind.RETIRE_INITIAL_VM_INHERITED,
        EnemyLifecycleKind.RETIRE_MAIN_VM,
        EnemyLifecycleKind.RETIRE_OFFSCREEN_CULL,
        EnemyLifecycleKind.RETIRE_DEFEAT_MODE0,
    }
)


@dataclass(frozen=True)
class EnemyLifecycleHookSite:
    name: str
    address: int
    original: bytes
    kind: EnemyLifecycleKind
    pointer_source: str
    capture_return_address: bool = False
    capture_root_subroutine: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("lifecycle hook name must be nonempty")
        if not 0 < self.address <= 0xFFFFFFFF:
            raise ValueError("lifecycle hook address is outside uint32")
        if len(self.original) < 5:
            raise ValueError("lifecycle hook span cannot hold a rel32 detour")
        if self.pointer_source not in {"ebp_minus_8", "eax", "ecx", "edx"}:
            raise ValueError("unsupported lifecycle enemy-pointer source")
        if self.capture_return_address != (
            self.kind is EnemyLifecycleKind.FORCED_HP_ZERO
        ):
            raise ValueError("only forced-HP-zero hooks capture a return address")
        if self.capture_root_subroutine != (self.kind in _ALLOCATION_KINDS):
            raise ValueError(
                "only allocation hooks capture a root subroutine"
            )

    @property
    def return_address(self) -> int:
        return self.address + len(self.original)


HOOK_SITES = (
    EnemyLifecycleHookSite(
        name="allocate_timeline",
        address=0x0042A55F,
        original=b"\x8b\x55\xf8\x8b\x45\xfc\x89\x82\x0c\x2e\x00\x00",
        kind=EnemyLifecycleKind.ALLOCATE_TIMELINE,
        pointer_source="ebp_minus_8",
        capture_root_subroutine=True,
    ),
    EnemyLifecycleHookSite(
        name="allocate_inherited_registers",
        address=0x0042A6FF,
        original=b"\x8b\x55\xf8\x8b\x45\xfc\x89\x82\x0c\x2e\x00\x00",
        kind=EnemyLifecycleKind.ALLOCATE_INHERITED_REGISTERS,
        pointer_source="ebp_minus_8",
        capture_root_subroutine=True,
    ),
    EnemyLifecycleHookSite(
        name="retire_initial_vm_timeline",
        address=0x0042A5F5,
        original=b"\x89\x81\x24\x33\x00\x00",
        kind=EnemyLifecycleKind.RETIRE_INITIAL_VM_TIMELINE,
        pointer_source="ecx",
    ),
    EnemyLifecycleHookSite(
        name="retire_initial_vm_inherited",
        address=0x0042A787,
        original=b"\x89\x90\x24\x33\x00\x00",
        kind=EnemyLifecycleKind.RETIRE_INITIAL_VM_INHERITED,
        pointer_source="eax",
    ),
    EnemyLifecycleHookSite(
        name="retire_main_vm",
        address=0x0042C9B1,
        original=b"\x89\x90\x24\x33\x00\x00",
        kind=EnemyLifecycleKind.RETIRE_MAIN_VM,
        pointer_source="eax",
    ),
    EnemyLifecycleHookSite(
        name="retire_offscreen_cull",
        address=0x0042CDFE,
        original=b"\x89\x90\x24\x33\x00\x00",
        kind=EnemyLifecycleKind.RETIRE_OFFSCREEN_CULL,
        pointer_source="eax",
    ),
    EnemyLifecycleHookSite(
        name="retire_defeat_mode0",
        address=0x0042D899,
        original=b"\x89\x8a\x24\x33\x00\x00",
        kind=EnemyLifecycleKind.RETIRE_DEFEAT_MODE0,
        pointer_source="edx",
    ),
    EnemyLifecycleHookSite(
        name="forced_hp_zero",
        address=0x0042F039,
        original=b"\xc7\x81\xfc\x2d\x00\x00\x00\x00\x00\x00",
        kind=EnemyLifecycleKind.FORCED_HP_ZERO,
        pointer_source="ecx",
        capture_return_address=True,
    ),
)


def _site_digest() -> int:
    payload = bytearray()
    for site in HOOK_SITES:
        payload += struct.pack("<II", site.address, int(site.kind))
        payload += struct.pack("<I", len(site.original))
        payload += site.original
        payload += site.name.encode("ascii") + b"\0"
        payload += site.pointer_source.encode("ascii") + b"\0"
        payload += bytes(
            (site.capture_return_address, site.capture_root_subroutine)
        )
    return zlib.crc32(payload) & 0xFFFFFFFF


PROBE_SITE_DIGEST = _site_digest()


class EnemyLifecycleProbeUnsafeStateError(RuntimeError):
    """One or more lifecycle detours, stubs, or suspended threads remain."""


def _u32(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"value is outside uint32: {value:#x}")
    return struct.pack("<I", value)


def _relative_jump(source: int, target: int) -> bytes:
    displacement = target - (source + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise ValueError("relative jump target is outside rel32 range")
    return b"\xe9" + struct.pack("<i", displacement)


def _load_enemy_pointer(pointer_source: str) -> bytes:
    if pointer_source == "ebp_minus_8":
        return b"\x8b\x5d\xf8"  # mov ebx, [ebp - 8]
    if pointer_source == "eax":
        return b"\x89\xc3"  # mov ebx, eax
    if pointer_source == "ecx":
        return b"\x89\xcb"  # mov ebx, ecx
    if pointer_source == "edx":
        return b"\x89\xd3"  # mov ebx, edx
    raise ValueError("unsupported lifecycle enemy-pointer source")


def _select_unpublished_event(
    *,
    serial_address: int,
    event_base: int,
) -> bytes:
    code = bytearray()
    code += b"\xa1" + _u32(serial_address)  # mov eax, [serial]
    code += b"\x40"  # inc eax
    code += b"\x89\xc1\x49"  # mov ecx, eax; dec ecx
    code += b"\x81\xe1" + _u32(PROBE_CAPACITY - 1)
    code += b"\x6b\xc9" + bytes((PROBE_EVENT_SIZE,))
    code += b"\x81\xc1" + _u32(event_base)
    return bytes(code)


def build_site_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    """Build one position-specific pre/replay/post/commit x86 site stub."""

    site_index = HOOK_SITES.index(site)
    stub_address = (
        remote_base + PROBE_STUB_OFFSET + site_index * PROBE_STUB_STRIDE
    )
    serial_address = remote_base + PROBE_SERIAL_OFFSET
    event_base = remote_base + PROBE_EVENT_OFFSET

    code = bytearray()
    code += b"\x9c\x60"  # pushfd; pushad
    code += _load_enemy_pointer(site.pointer_source)
    code += _select_unpublished_event(
        serial_address=serial_address,
        event_base=event_base,
    )
    # Invalidate the overwritten old slot before changing any payload field.
    # The header remains unchanged until all pre/post fields are complete.
    code += b"\x89\x01"  # event.serial = next serial (unpublished)
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x51\x04"  # manager_frame
    code += b"\xc7\x41\x08" + _u32(int(site.kind))
    code += b"\x89\x59\x0c"  # enemy_pointer
    code += b"\x8b\x93" + _u32(ENEMY_FLAGS_OFFSET)
    code += b"\x89\x51\x10"  # flags_before
    code += b"\x8b\x93" + _u32(ENEMY_HP_OFFSET)
    code += b"\x89\x51\x18"  # hp_before
    code += b"\x8b\x93" + _u32(ENEMY_FRAME_DAMAGE_OFFSET)
    code += b"\x89\x51\x20"  # frame_damage
    if site.capture_return_address:
        code += b"\x8b\x55\x04"  # mov edx, [ebp + 4]
    else:
        code += b"\x31\xd2"  # xor edx, edx
    code += b"\x89\x51\x24"  # aux/caller return address
    if site.capture_root_subroutine:
        code += b"\x0f\xbf\x55\x08"  # movsx edx, word [ebp + 8]
    else:
        code += b"\x83\xca\xff"  # or edx, -1
    code += b"\x89\x51\x28"  # root subroutine, or -1 when not an allocation
    code += b"\x8b\x15" + _u32(ADDR_STAGE_ROUTE_INDEX)
    code += b"\x89\x51\x2c"  # native stage-route index
    code += b"\x61\x9d"  # popad; popfd

    # Exact shipped bytes execute before publication of the event.
    code += site.original

    code += b"\x9c\x60"  # pushfd; pushad
    code += _load_enemy_pointer(site.pointer_source)
    code += _select_unpublished_event(
        serial_address=serial_address,
        event_base=event_base,
    )
    code += b"\x8b\x93" + _u32(ENEMY_FLAGS_OFFSET)
    code += b"\x89\x51\x14"  # flags_after
    code += b"\x8b\x93" + _u32(ENEMY_HP_OFFSET)
    code += b"\x89\x51\x1c"  # hp_after
    code += b"\x89\x01"  # event.serial = eax
    code += b"\xa3" + _u32(serial_address)  # header.serial = eax
    code += b"\x61\x9d"  # popad; popfd

    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)
    if len(code) > PROBE_STUB_STRIDE:
        raise ValueError(f"lifecycle stub {site.name} exceeds its fixed slot")
    return bytes(code)


def build_probe_image(remote_base: int, pid: int) -> bytes:
    """Build the initialized lifecycle header and all site stubs."""

    if not 0 < pid <= 0xFFFFFFFF:
        raise ValueError("pid is outside uint32")
    if (
        PROBE_EVENT_OFFSET + PROBE_CAPACITY * PROBE_EVENT_SIZE
        > PROBE_ALLOCATION_SIZE
    ):
        raise ValueError("enemy lifecycle event ring exceeds remote allocation")
    image = bytearray(PROBE_EVENT_OFFSET)
    image[:PROBE_HEADER_SIZE] = _HEADER.pack(
        PROBE_MAGIC,
        PROBE_VERSION,
        PROBE_CAPACITY,
        PROBE_EVENT_SIZE,
        0,
        pid,
        PROBE_SITE_DIGEST,
        len(HOOK_SITES),
    )
    for index, site in enumerate(HOOK_SITES):
        stub = build_site_stub(remote_base, site)
        start = PROBE_STUB_OFFSET + index * PROBE_STUB_STRIDE
        image[start : start + len(stub)] = stub
    return bytes(image)


def build_probe_patches(remote_base: int) -> tuple[bytes, ...]:
    """Return direct rel32 detours padded across each exact hook span."""

    patches: list[bytes] = []
    for index, site in enumerate(HOOK_SITES):
        stub_address = (
            remote_base + PROBE_STUB_OFFSET + index * PROBE_STUB_STRIDE
        )
        detour = _relative_jump(site.address, stub_address)
        patches.append(detour + b"\x90" * (len(site.original) - len(detour)))
    return tuple(patches)


@dataclass(frozen=True)
class EnemyLifecycleEvent:
    serial: int
    manager_frame: int
    kind: EnemyLifecycleKind
    enemy_pointer: int
    flags_before: int
    flags_after: int
    hp_before: int
    hp_after: int
    frame_damage: int
    caller_return_address: int
    root_subroutine: int | None
    stage_route_index: int

    @classmethod
    def decode(cls, payload: bytes) -> EnemyLifecycleEvent:
        if len(payload) != PROBE_EVENT_SIZE:
            raise ValueError("enemy lifecycle event size is invalid")
        (
            serial,
            manager_frame,
            kind_value,
            enemy_pointer,
            flags_before,
            flags_after,
            hp_before,
            hp_after,
            frame_damage,
            caller_return_address,
            root_subroutine,
            stage_route_index,
        ) = _EVENT.unpack(payload)
        try:
            kind = EnemyLifecycleKind(kind_value)
        except ValueError as error:
            raise ValueError("enemy lifecycle event kind is invalid") from error
        offset = enemy_pointer - ENEMY_POOL_BASE
        if (
            offset < 0
            or offset >= ENEMY_POOL_SIZE * ENEMY_STRIDE
            or offset % ENEMY_STRIDE
        ):
            raise ValueError("enemy lifecycle pointer is outside the ordinary pool")
        if kind is EnemyLifecycleKind.FORCED_HP_ZERO:
            if caller_return_address not in FORCED_ZERO_RETURN_ADDRESSES:
                raise ValueError("forced-HP-zero caller is not a shipped caller")
        elif caller_return_address:
            raise ValueError("non-forced lifecycle event has a caller address")
        if kind in _ALLOCATION_KINDS:
            if root_subroutine < 0:
                raise ValueError(
                    "allocation lifecycle event has no root subroutine"
                )
        elif root_subroutine != -1:
            raise ValueError(
                "non-allocation lifecycle event has a root subroutine"
            )
        if not 0 <= stage_route_index <= 8:
            raise ValueError(
                "lifecycle event stage-route index is outside 0..8"
            )
        return cls(
            serial=serial,
            manager_frame=manager_frame,
            kind=kind,
            enemy_pointer=enemy_pointer,
            flags_before=flags_before,
            flags_after=flags_after,
            hp_before=hp_before,
            hp_after=hp_after,
            frame_damage=frame_damage,
            caller_return_address=caller_return_address,
            root_subroutine=(
                root_subroutine if kind in _ALLOCATION_KINDS else None
            ),
            stage_route_index=stage_route_index,
        )

    @property
    def slot(self) -> int:
        return (self.enemy_pointer - ENEMY_POOL_BASE) // ENEMY_STRIDE

    @property
    def is_allocation(self) -> bool:
        return self.kind in _ALLOCATION_KINDS

    @property
    def is_retirement(self) -> bool:
        return self.kind in _RETIREMENT_KINDS

    @property
    def is_forced_hp_zero(self) -> bool:
        return self.kind is EnemyLifecycleKind.FORCED_HP_ZERO

    @property
    def reconstructed_pre_damage_hp(self) -> int | None:
        if self.kind is not EnemyLifecycleKind.RETIRE_DEFEAT_MODE0:
            return None
        return self.hp_before + self.frame_damage

    def compact_record(self) -> dict[str, object]:
        return {
            "serial": self.serial,
            "manager_frame": self.manager_frame,
            "kind": self.kind.name.lower(),
            "slot": self.slot,
            "enemy_pointer": self.enemy_pointer,
            "flags_before": self.flags_before,
            "flags_after": self.flags_after,
            "hp_before": self.hp_before,
            "hp_after": self.hp_after,
            "frame_damage": self.frame_damage,
            "reconstructed_pre_damage_hp": self.reconstructed_pre_damage_hp,
            "caller_return_address": self.caller_return_address or None,
            "root_subroutine": self.root_subroutine,
            "stage_route_index": self.stage_route_index,
        }


@dataclass(frozen=True)
class EnemyLifecycleBatch:
    status: str
    previous_serial: int | None
    observed_serial: int | None
    events: tuple[EnemyLifecycleEvent, ...]
    dropped_event_count: int
    error: str | None = None

    def compact_record(self) -> dict[str, object]:
        return {
            "schema": PROBE_SCHEMA,
            "role": "trace_only_no_action_authority",
            "status": self.status,
            "previous_serial": self.previous_serial,
            "observed_serial": self.observed_serial,
            "events": [event.compact_record() for event in self.events],
            "dropped_event_count": self.dropped_event_count,
            "error": self.error,
            "action_authority": False,
        }


def _parse_header(payload: bytes, *, pid: int) -> int:
    if len(payload) != PROBE_HEADER_SIZE:
        raise ValueError("enemy lifecycle probe header size is invalid")
    (
        magic,
        version,
        capacity,
        event_size,
        serial,
        recorded_pid,
        site_digest,
        hook_count,
    ) = _HEADER.unpack(payload)
    if (
        magic != PROBE_MAGIC
        or version != PROBE_VERSION
        or capacity != PROBE_CAPACITY
        or event_size != PROBE_EVENT_SIZE
        or recorded_pid != pid
        or site_digest != PROBE_SITE_DIGEST
        or hook_count != len(HOOK_SITES)
    ):
        raise ValueError("enemy lifecycle probe header identity is invalid")
    return serial


def _probe_owned_instruction_pointer(
    instruction_pointer: int,
    *,
    remote_base: int,
) -> bool:
    if _instruction_pointer_in_hook_span(instruction_pointer):
        return True
    for index, site in enumerate(HOOK_SITES):
        stub = build_site_stub(remote_base, site)
        stub_start = (
            remote_base + PROBE_STUB_OFFSET + index * PROBE_STUB_STRIDE
        )
        if stub_start <= instruction_pointer < stub_start + len(stub):
            return True
    return False


def _instruction_pointer_in_hook_span(instruction_pointer: int) -> bool:
    return any(
        site.address <= instruction_pointer < site.return_address
        for site in HOOK_SITES
    )


class EnemyLifecycleProbe:
    """Installed default-off lifecycle probe with bounded fail-open reads."""

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
        self._active_sites = set(range(len(HOOK_SITES)))
        self._closed = False

    @classmethod
    def install(cls, api: Any, pid: int) -> EnemyLifecycleProbe:
        _configure_api(api)
        access = (
            PROCESS_QUERY_INFORMATION
            | PROCESS_VM_OPERATION
            | PROCESS_VM_READ
            | PROCESS_VM_WRITE
        )
        handle = api.kernel32.OpenProcess(access, False, pid)
        if not handle:
            raise _win_error("OpenProcess(enemy lifecycle probe)")
        remote_base = 0
        active_sites: set[int] = set()
        target_suspend_unsafe = False
        try:
            for site in HOOK_SITES:
                observed = _read_memory(
                    api,
                    handle,
                    site.address,
                    len(site.original),
                )
                if observed != site.original:
                    raise RuntimeError(
                        f"lifecycle site {site.name} does not match shipped bytes"
                    )

            allocated = api.kernel32.VirtualAllocEx(
                handle,
                None,
                PROBE_ALLOCATION_SIZE,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE,
            )
            remote_base = int(allocated or 0)
            if not remote_base or remote_base > 0xFFFFFFFF:
                raise _win_error("VirtualAllocEx(enemy lifecycle probe)")
            image = build_probe_image(remote_base, pid)
            _write_memory(api, handle, remote_base, image, executable=True)
            patches = build_probe_patches(remote_base)

            suspended: tuple[Any, ...] | None = None
            for _attempt in range(8):
                try:
                    candidate = _suspend_target_threads(api, pid)
                except Priority17ProbeUnsafeStateError as error:
                    target_suspend_unsafe = True
                    raise EnemyLifecycleProbeUnsafeStateError(
                        "lifecycle activation could not restore target suspension"
                    ) from error
                if not any(
                    _instruction_pointer_in_hook_span(
                        thread.instruction_pointer
                    )
                    for thread in candidate
                ):
                    suspended = candidate
                    break
                release_errors = _release_suspended_threads(api, candidate)
                if release_errors:
                    target_suspend_unsafe = True
                    raise EnemyLifecycleProbeUnsafeStateError(
                        "lifecycle activation could not release an in-flight "
                        "hook-span thread: "
                        + "; ".join(release_errors)
                    )
                time.sleep(0.001)
            if suspended is None:
                raise RuntimeError(
                    "lifecycle hook span remained in flight across "
                    "activation retries"
                )
            activation_error: Exception | None = None
            cleanup_errors: list[str] = []
            try:
                for site in HOOK_SITES:
                    if (
                        _read_memory(
                            api,
                            handle,
                            site.address,
                            len(site.original),
                        )
                        != site.original
                    ):
                        raise RuntimeError(
                            f"lifecycle site {site.name} changed before activation"
                        )
                for index, (site, patch) in enumerate(zip(HOOK_SITES, patches)):
                    # A write attempt is considered live until exact rollback
                    # is observed, even if cache/protection cleanup later fails.
                    active_sites.add(index)
                    _write_code(api, handle, site.address, patch)
                    if (
                        _read_memory(
                            api,
                            handle,
                            site.address,
                            len(patch),
                        )
                        != patch
                    ):
                        raise RuntimeError(
                            f"lifecycle site {site.name} patch verification failed"
                        )
            except Exception as error:
                activation_error = error
                for index in sorted(active_sites, reverse=True):
                    site = HOOK_SITES[index]
                    try:
                        _write_code(api, handle, site.address, site.original)
                        if (
                            _read_memory(
                                api,
                                handle,
                                site.address,
                                len(site.original),
                            )
                            == site.original
                        ):
                            active_sites.discard(index)
                        else:
                            cleanup_errors.append(
                                f"{site.name} rollback verification failed"
                            )
                    except Exception as rollback_error:
                        cleanup_errors.append(
                            f"{site.name} rollback failed: "
                            f"{type(rollback_error).__name__}: {rollback_error}"
                        )
            release_errors = _release_suspended_threads(api, suspended)
            if release_errors:
                target_suspend_unsafe = True
                cleanup_errors.extend(release_errors)
            if activation_error is not None:
                if active_sites or target_suspend_unsafe:
                    raise EnemyLifecycleProbeUnsafeStateError(
                        "lifecycle activation cleanup is unsafe: "
                        + "; ".join(cleanup_errors or [str(activation_error)])
                    ) from activation_error
                if cleanup_errors:
                    raise RuntimeError(
                        f"{activation_error}; " + "; ".join(cleanup_errors)
                    ) from activation_error
                raise activation_error
            if target_suspend_unsafe:
                raise EnemyLifecycleProbeUnsafeStateError(
                    "lifecycle activation left a target thread suspended: "
                    + "; ".join(cleanup_errors)
                )
            return cls(
                api=api,
                pid=pid,
                handle=handle,
                remote_base=remote_base,
            )
        except Exception as install_error:
            if remote_base and not active_sites:
                api.kernel32.VirtualFreeEx(
                    handle,
                    remote_base,
                    0,
                    MEM_RELEASE,
                )
            api.kernel32.CloseHandle(handle)
            if active_sites or target_suspend_unsafe:
                raise EnemyLifecycleProbeUnsafeStateError(
                    "lifecycle detour or thread rollback was not verified; "
                    "the target must be terminated before gameplay"
                ) from install_error
            raise

    def installation_record(self) -> dict[str, object]:
        return {
            "schema": PROBE_SCHEMA,
            "role": "trace_only_no_action_authority",
            "status": "installed",
            "remote_base": self.remote_base,
            "capacity": PROBE_CAPACITY,
            "event_size": PROBE_EVENT_SIZE,
            "site_digest": PROBE_SITE_DIGEST,
            "sites": [
                {
                    "name": site.name,
                    "address": site.address,
                    "kind": site.kind.name.lower(),
                }
                for site in HOOK_SITES
            ],
            "action_authority": False,
        }

    def sample_serial(self) -> int:
        header = _read_memory(
            self.api,
            self.handle,
            self.remote_base,
            PROBE_HEADER_SIZE,
        )
        return _parse_header(header, pid=self.pid)

    def read_since(
        self,
        previous_serial: int | None,
        *,
        maximum_events: int = 64,
        retries: int = 3,
    ) -> EnemyLifecycleBatch:
        if maximum_events <= 0 or maximum_events > PROBE_CAPACITY:
            raise ValueError("maximum_events is outside lifecycle capacity")
        if retries <= 0:
            raise ValueError("retries must be positive")
        if previous_serial is None:
            try:
                serial = self.sample_serial()
            except Exception as error:
                return EnemyLifecycleBatch(
                    status="read_error",
                    previous_serial=None,
                    observed_serial=None,
                    events=(),
                    dropped_event_count=0,
                    error=f"{type(error).__name__}: {error}",
                )
            return EnemyLifecycleBatch(
                status="baseline",
                previous_serial=None,
                observed_serial=serial,
                events=(),
                dropped_event_count=0,
            )

        for _attempt in range(retries):
            try:
                serial_before = self.sample_serial()
                distance = (serial_before - previous_serial) & 0xFFFFFFFF
                if distance >= 1 << 31:
                    raise ValueError("enemy lifecycle serial moved backward")
                retained = min(distance, PROBE_CAPACITY, maximum_events)
                dropped = distance - retained
                first = (serial_before - retained + 1) & 0xFFFFFFFF
                events: list[EnemyLifecycleEvent] = []
                for offset in range(retained):
                    expected = (first + offset) & 0xFFFFFFFF
                    slot = (expected - 1) & (PROBE_CAPACITY - 1)
                    payload = _read_memory(
                        self.api,
                        self.handle,
                        self.remote_base
                        + PROBE_EVENT_OFFSET
                        + slot * PROBE_EVENT_SIZE,
                        PROBE_EVENT_SIZE,
                    )
                    event = EnemyLifecycleEvent.decode(payload)
                    if event.serial != expected:
                        raise RuntimeError(
                            "enemy lifecycle event slot changed during read"
                        )
                    events.append(event)
                serial_after = self.sample_serial()
                if serial_after != serial_before:
                    continue
                status = (
                    "no_events"
                    if not distance
                    else "exact"
                    if not dropped
                    else "overflow_or_trace_truncation"
                )
                return EnemyLifecycleBatch(
                    status=status,
                    previous_serial=previous_serial,
                    observed_serial=serial_after,
                    events=tuple(events),
                    dropped_event_count=dropped,
                )
            except (OSError, RuntimeError):
                continue
            except Exception as error:
                return EnemyLifecycleBatch(
                    status="read_error",
                    previous_serial=previous_serial,
                    observed_serial=None,
                    events=(),
                    dropped_event_count=0,
                    error=f"{type(error).__name__}: {error}",
                )
        return EnemyLifecycleBatch(
            status="race_unknown",
            previous_serial=previous_serial,
            observed_serial=None,
            events=(),
            dropped_event_count=0,
            error="enemy lifecycle ring did not stabilize within retry budget",
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        ordinary_errors: list[str] = []
        unsafe_errors: list[str] = []
        suspended: tuple[Any, ...] | None = None
        try:
            for _attempt in range(8):
                try:
                    candidate = _suspend_target_threads(self.api, self.pid)
                except Exception as error:
                    unsafe_errors.append(
                        "target suspension for lifecycle cleanup failed: "
                        f"{type(error).__name__}: {error}"
                    )
                    break
                if not any(
                    _probe_owned_instruction_pointer(
                        thread.instruction_pointer,
                        remote_base=self.remote_base,
                    )
                    for thread in candidate
                ):
                    suspended = candidate
                    break
                release_errors = _release_suspended_threads(
                    self.api,
                    candidate,
                )
                if release_errors:
                    unsafe_errors.extend(release_errors)
                    break
                time.sleep(0.001)
            if suspended is None and not unsafe_errors:
                unsafe_errors.append(
                    "lifecycle probe code remained in flight across cleanup retries"
                )

            if suspended is not None:
                for index in sorted(self._active_sites, reverse=True):
                    site = HOOK_SITES[index]
                    try:
                        _write_code(
                            self.api,
                            self.handle,
                            site.address,
                            site.original,
                        )
                        if (
                            _read_memory(
                                self.api,
                                self.handle,
                                site.address,
                                len(site.original),
                            )
                            == site.original
                        ):
                            self._active_sites.discard(index)
                        else:
                            unsafe_errors.append(
                                f"{site.name} restore verification failed"
                            )
                    except Exception as error:
                        unsafe_errors.append(
                            f"{site.name} restore failed: "
                            f"{type(error).__name__}: {error}"
                        )
                if not self._active_sites:
                    if not self.api.kernel32.VirtualFreeEx(
                        self.handle,
                        self.remote_base,
                        0,
                        MEM_RELEASE,
                    ):
                        ordinary_errors.append(
                            str(_win_error("VirtualFreeEx(enemy lifecycle probe)"))
                        )
                release_errors = _release_suspended_threads(
                    self.api,
                    suspended,
                )
                if release_errors:
                    unsafe_errors.extend(release_errors)
        finally:
            self.api.kernel32.CloseHandle(self.handle)
        if self._active_sites:
            unsafe_errors.append(
                "lifecycle activation detours remain installed: "
                + ", ".join(HOOK_SITES[index].name for index in self._active_sites)
            )
        if unsafe_errors:
            raise EnemyLifecycleProbeUnsafeStateError(
                "enemy lifecycle probe cleanup is unsafe; terminate the target: "
                + "; ".join(unsafe_errors)
            )
        if ordinary_errors:
            raise RuntimeError(
                "enemy lifecycle probe cleanup failed: "
                + "; ".join(ordinary_errors)
            )


__all__ = [
    "ENEMY_FLAGS_OFFSET",
    "ENEMY_FRAME_DAMAGE_OFFSET",
    "ENEMY_HP_OFFSET",
    "ENEMY_POOL_BASE",
    "ENEMY_POOL_SIZE",
    "ENEMY_STRIDE",
    "FORCED_ZERO_RETURN_ADDRESSES",
    "HOOK_SITES",
    "PROBE_CAPACITY",
    "PROBE_EVENT_OFFSET",
    "PROBE_EVENT_SIZE",
    "PROBE_HEADER_SIZE",
    "PROBE_SCHEMA",
    "PROBE_SERIAL_OFFSET",
    "PROBE_SITE_DIGEST",
    "PROBE_STUB_OFFSET",
    "PROBE_STUB_STRIDE",
    "EnemyLifecycleBatch",
    "EnemyLifecycleEvent",
    "EnemyLifecycleHookSite",
    "EnemyLifecycleKind",
    "EnemyLifecycleProbe",
    "EnemyLifecycleProbeUnsafeStateError",
    "build_probe_image",
    "build_probe_patches",
    "build_site_stub",
]
