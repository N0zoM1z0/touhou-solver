"""Bounded trace-only native ring for TH08 enemy and item lifecycles.

The probe covers the two shipped ordinary-enemy allocation paths, every
revalidated active-bit clear, the distinct global forced-HP-zero write,
successful item allocation, the pre/post transaction of one native item
pickup, and actual resolved enemy-HP damage commits.  It is default-off
infrastructure and has no action authority.
Installation and cleanup reuse the already tested Win32 remote-memory/thread
primitives from the priority-17 publication probe; lifecycle-specific
activation remains multi-site, exact-byte guarded, and reversible.

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
import math
import struct
import time
from typing import Any
import zlib

from .game_state import (
    ADDR_CURRENT_INPUT,
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_GAMEPLAY_RNG,
    ADDR_PLAYER,
    ADDR_ROUTE_ID,
    ADDR_RUN_STATE_INNER_POINTER,
    ADDR_STAGE_ROUTE_INDEX,
    PLAYER_BOMB_ACTIVE_OFFSET,
    PLAYER_FOCUS_LOGIC_OFFSET,
    PLAYER_POSITION_OFFSET,
    PLAYER_SHOT_POOL_OFFSET,
    PLAYER_SHOT_POOL_SIZE,
    PLAYER_SHOT_SLOT_STATE_OFFSET,
    PLAYER_SHOT_SLOT_STRIDE,
    PLAYER_SHOT_TIMER_OFFSET,
    RUN_STATE_BOMBS_OFFSET,
    RUN_STATE_LIVES_OFFSET,
    RUN_STATE_POWER_OFFSET,
)
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


PROBE_SCHEMA = "th08-enemy-item-damage-lifecycle-probe-v4"
PROBE_MAGIC = b"ELR4"
PROBE_VERSION = 4
PROBE_CAPACITY = 256
PROBE_EVENT_SIZE = 128
PROBE_ALLOCATION_SIZE = 0x10000
PROBE_HEADER_SIZE = 32
PROBE_SERIAL_OFFSET = 16
PROBE_PICKUP_SCRATCH_OFFSET = 0x40
PROBE_DAMAGE_SCRATCH_OFFSET = 0xC0
PROBE_STUB_OFFSET = 0x200
PROBE_STUB_STRIDE = 0x240
PROBE_EVENT_OFFSET = 0x2400

ENEMY_POOL_BASE = 0x005826C0
ENEMY_POOL_SIZE = 480
ENEMY_STRIDE = 0x53D0
ENEMY_HP_OFFSET = 0x2DFC
ENEMY_FLAGS_OFFSET = 0x3324
ENEMY_FLAGS2_OFFSET = 0x3328
ENEMY_FRAME_DAMAGE_OFFSET = 0x3354
ENEMY_POSITION_OFFSET = 0x2D88
ENEMY_DAMAGE_HITBOX_OFFSET = 0x2D70
ENEMY_ALTERNATE_HITBOX_OFFSET = 0x2D7C
ENEMY_MAIN_VM_OFFSET = 0x7F8
ENEMY_MAIN_VM_TIMER_CURRENT_OFFSET = ENEMY_MAIN_VM_OFFSET + 0x0C

PLAYER_DAMAGE_TIMER_OFFSET = 0xE2AF4
PLAYER_SHOT_SLOT_TYPE_OFFSET = PLAYER_SHOT_SLOT_STATE_OFFSET + 2

ITEM_POOL_BASE = 0x01653648
ITEM_POOL_SIZE = 2096
ITEM_STRIDE = 0x2E4
ITEM_POSITION_OFFSET = 0x2A4
ITEM_VELOCITY_OFFSET = 0x2B0
ITEM_TYPE_OFFSET = 0x2D4
ITEM_ACTIVE_OFFSET = 0x2D5
ITEM_LISTED_OFFSET = 0x2D6
ITEM_MOTION_STATE_OFFSET = 0x2D7
ITEM_FULL_VALUE_OFFSET = 0x2D8
ITEM_NEXT_OFFSET = 0x2DC
ITEM_PREVIOUS_OFFSET = 0x2E0
ITEM_MANAGER_NEXT_ALLOCATION_OFFSET = 0x17ADA4

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
_EVENT = struct.Struct("<32I")
_EVENT_PAYLOAD_OFFSET = 0x28
_EVENT_PAYLOAD_COUNT = 22
_UNKNOWN_U32 = 0xFFFFFFFF

# Every shipped direct caller of item_pool_spawn, represented by the return
# address observed at the successful-allocation hook.
ITEM_ALLOCATION_RETURN_ADDRESSES = frozenset(
    {
        0x00417622,
        0x004176D6,
        0x0041D35C,
        0x0041D370,
        0x0041D482,
        0x0041D641,
        0x004253BC,
        0x004253D6,
        0x0042B04D,
        0x0042B1B6,
        0x0042B2B3,
        0x0042BF0B,
        0x0042BF86,
        0x0042C087,
        0x0042C09B,
        0x0042C166,
        0x0042DA59,
        0x0042F0A7,
        0x0042F146,
        0x004308EA,
        0x0043091F,
        0x00430A68,
        0x00430B3F,
        0x00430B61,
        0x00430C7C,
        0x00430CF5,
        0x00430DEE,
        0x00431655,
        0x0043166D,
        0x00431694,
        0x0043170F,
        0x00431727,
        0x0043174E,
        0x0043183C,
        0x00431853,
        0x0043187B,
        0x0043194D,
        0x00431965,
        0x0043198C,
        0x00431A5E,
        0x00431A76,
        0x00431A9D,
        0x0044AACE,
        0x0044AAF4,
        0x0044AB14,
        0x0044CDD3,
        0x0044CDEB,
        0x0044CE03,
        0x0044CE1A,
        0x0044CE32,
        0x0044CE4A,
        0x0044CE93,
        0x0044CED8,
        0x0044CEEF,
        0x0044CF07,
        0x0044CF1F,
        0x0044CF36,
        0x00451897,
    }
)
ENEMY_DEFEAT_ITEM_ALLOCATION_RETURN_ADDRESSES = frozenset(
    {
        0x0042BF0B,
        0x0042BF86,
        0x0042C087,
        0x0042C09B,
        0x0042C166,
    }
)


class EnemyLifecycleKind(IntEnum):
    ALLOCATE_TIMELINE = 1
    ALLOCATE_INHERITED_REGISTERS = 2
    RETIRE_INITIAL_VM_TIMELINE = 3
    RETIRE_INITIAL_VM_INHERITED = 4
    RETIRE_MAIN_VM = 5
    RETIRE_OFFSCREEN_CULL = 6
    RETIRE_DEFEAT_MODE0 = 7
    FORCED_HP_ZERO = 8
    ITEM_ALLOCATE = 9
    ITEM_PICKUP = 10
    ITEM_CULL = 11
    ENEMY_DAMAGE = 12


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
_ENEMY_KINDS = _ALLOCATION_KINDS | _RETIREMENT_KINDS | {
    EnemyLifecycleKind.FORCED_HP_ZERO,
    EnemyLifecycleKind.ENEMY_DAMAGE,
}
_ITEM_KINDS = frozenset(
    {
        EnemyLifecycleKind.ITEM_ALLOCATE,
        EnemyLifecycleKind.ITEM_PICKUP,
        EnemyLifecycleKind.ITEM_CULL,
    }
)


@dataclass(frozen=True)
class EnemyLifecycleHookSite:
    name: str
    address: int
    original: bytes
    kind: EnemyLifecycleKind
    pointer_source: str
    role: str = "enemy_event"
    capture_return_address: bool = False
    capture_root_subroutine: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("lifecycle hook name must be nonempty")
        if not 0 < self.address <= 0xFFFFFFFF:
            raise ValueError("lifecycle hook address is outside uint32")
        if len(self.original) < 5:
            raise ValueError("lifecycle hook span cannot hold a rel32 detour")
        if self.pointer_source not in {
            "ebp_minus_8",
            "ebp_minus_24",
            "ebp_minus_38",
            "eax",
            "ecx",
            "edx",
        }:
            raise ValueError("unsupported lifecycle enemy-pointer source")
        if self.role not in {
            "enemy_event",
            "item_allocate",
            "item_cull",
            "item_pickup_begin",
            "item_pickup_commit",
            "enemy_damage_begin",
            "enemy_damage_commit",
        }:
            raise ValueError("unsupported lifecycle hook role")
        expected_return_capture = (
            self.kind is EnemyLifecycleKind.FORCED_HP_ZERO
            or self.role == "item_allocate"
        )
        if self.capture_return_address != expected_return_capture:
            raise ValueError(
                "return-address capture does not match lifecycle hook role"
            )
        if self.capture_root_subroutine != (
            self.role == "enemy_event" and self.kind in _ALLOCATION_KINDS
        ):
            raise ValueError(
                "only allocation hooks capture a root subroutine"
            )
        expected_pointer_source = {
            "item_allocate": "ebp_minus_8",
            "item_cull": "ebp_minus_24",
            "item_pickup_begin": "ebp_minus_24",
            "item_pickup_commit": "ebp_minus_24",
            "enemy_damage_begin": "ebp_minus_38",
            "enemy_damage_commit": "ebp_minus_38",
        }.get(self.role)
        if (
            expected_pointer_source is not None
            and self.pointer_source != expected_pointer_source
        ):
            raise ValueError("specialized hook has the wrong pointer source")
        if (
            self.role.startswith("item_")
            and self.kind not in _ITEM_KINDS
        ):
            raise ValueError("item hook must use an item lifecycle kind")
        if (
            self.role.startswith("enemy_damage_")
            and self.kind is not EnemyLifecycleKind.ENEMY_DAMAGE
        ):
            raise ValueError("damage hook must use the enemy-damage kind")

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
    EnemyLifecycleHookSite(
        name="enemy_damage_begin",
        address=0x0042D06D,
        original=(
            b"\x8b\x4d\xc8"
            b"\xc7\x81\x54\x33\x00\x00\x00\x00\x00\x00"
        ),
        kind=EnemyLifecycleKind.ENEMY_DAMAGE,
        pointer_source="ebp_minus_38",
        role="enemy_damage_begin",
    ),
    EnemyLifecycleHookSite(
        name="enemy_damage_commit",
        address=0x0042D343,
        original=(
            b"\x2b\x45\xe8"
            b"\x8b\x4d\xc8"
            b"\x89\x81\xfc\x2d\x00\x00"
        ),
        kind=EnemyLifecycleKind.ENEMY_DAMAGE,
        pointer_source="ebp_minus_38",
        role="enemy_damage_commit",
    ),
    EnemyLifecycleHookSite(
        name="item_allocate",
        address=0x0044044D,
        original=b"\x8b\x4d\xf8\x89\x4d\xf0",
        kind=EnemyLifecycleKind.ITEM_ALLOCATE,
        pointer_source="ebp_minus_8",
        role="item_allocate",
        capture_return_address=True,
    ),
    EnemyLifecycleHookSite(
        name="item_cull",
        address=0x00440991,
        original=b"\x8b\x4d\xdc\xe8\xd7\x0d\x00\x00",
        kind=EnemyLifecycleKind.ITEM_CULL,
        pointer_source="ebp_minus_24",
        role="item_cull",
    ),
    EnemyLifecycleHookSite(
        name="item_pickup_begin",
        address=0x00440A39,
        original=b"\x66\x89\x90\xda\x00\x00\x00",
        kind=EnemyLifecycleKind.ITEM_PICKUP,
        pointer_source="ebp_minus_24",
        role="item_pickup_begin",
    ),
    EnemyLifecycleHookSite(
        name="item_pickup_commit",
        address=0x00440C1E,
        original=b"\x8b\x4d\xdc\xe8\x4a\x0b\x00\x00",
        kind=EnemyLifecycleKind.ITEM_PICKUP,
        pointer_source="ebp_minus_24",
        role="item_pickup_commit",
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
        payload += site.role.encode("ascii") + b"\0"
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


def _signed_u32(value: int) -> int:
    return value - 0x100000000 if value & 0x80000000 else value


def _float_u32(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]


def _relative_jump(source: int, target: int) -> bytes:
    displacement = target - (source + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise ValueError("relative jump target is outside rel32 range")
    return b"\xe9" + struct.pack("<i", displacement)


def _relative_call(source: int, target: int) -> bytes:
    displacement = target - (source + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise ValueError("relative call target is outside rel32 range")
    return b"\xe8" + struct.pack("<i", displacement)


def _load_enemy_pointer(pointer_source: str) -> bytes:
    if pointer_source == "ebp_minus_8":
        return b"\x8b\x5d\xf8"  # mov ebx, [ebp - 8]
    if pointer_source == "ebp_minus_24":
        return b"\x8b\x5d\xdc"  # mov ebx, [ebp - 0x24]
    if pointer_source == "ebp_minus_38":
        return b"\x8b\x5d\xc8"  # mov ebx, [ebp - 0x38]
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
    # IMUL r32, r/m32, imm8 sign-extends its immediate.  Event sizes at or
    # above 0x80 therefore require the imm32 encoding or the selected slot
    # walks backwards from the ring base.
    code += b"\x69\xc9" + _u32(PROBE_EVENT_SIZE)
    code += b"\x81\xc1" + _u32(event_base)
    return bytes(code)


def _initialize_unpublished_event(
    *,
    serial_address: int,
    event_base: int,
) -> bytes:
    """Select, invalidate, and zero one fixed-size unpublished event.

    On return ESI is the next serial and ECX is the event pointer.  Callers
    execute inside pushad/pushfd and may freely use the remaining registers.
    """

    code = bytearray(
        _select_unpublished_event(
            serial_address=serial_address,
            event_base=event_base,
        )
    )
    code += b"\x89\xc6"  # mov esi, eax
    code += b"\x89\x01"  # event.serial = next serial (unpublished)
    code += b"\x89\xca"  # mov edx, ecx
    code += b"\x8d\x79\x04"  # lea edi, [ecx + 4]
    code += b"\xb9" + _u32(PROBE_EVENT_SIZE // 4 - 1)
    code += b"\x31\xc0\xf3\xab"  # xor eax, eax; rep stosd
    code += b"\x89\xd1"  # mov ecx, edx
    code += b"\x89\xf0"  # mov eax, esi
    return bytes(code)


def _commit_event(serial_address: int) -> bytes:
    return (
        b"\x89\x31"  # event.serial = esi
        + b"\x89\xf0"  # mov eax, esi
        + b"\xa3"
        + _u32(serial_address)  # header.serial = esi
    )


def _fill_item_common_fields(
    *,
    event_pointer: str,
    item_pointer: str,
    include_resource_after: bool,
) -> bytes:
    """Fill shared item/player/resource payload fields.

    ``event_pointer`` is either ``ecx`` for a ring event or ``edi`` for the
    fixed pickup scratch. ``item_pointer`` is currently constrained to EBX.
    """

    if event_pointer not in {"ecx", "edi"} or item_pointer != "ebx":
        raise ValueError("unsupported item field register assignment")
    base = b"\x89\x91" if event_pointer == "ecx" else b"\x89\x97"
    code = bytearray()

    def store_edx(offset: int) -> None:
        code.extend(base + _u32(offset))

    for item_offset, payload_index, width in (
        (ITEM_TYPE_OFFSET, 0, "byte"),
        (ITEM_MOTION_STATE_OFFSET, 1, "byte"),
        (ITEM_FULL_VALUE_OFFSET, 2, "byte"),
    ):
        if width == "byte":
            code.extend(b"\x0f\xb6\x93" + _u32(item_offset))
        store_edx(_EVENT_PAYLOAD_OFFSET + 4 * payload_index)
    for item_offset, payload_index in (
        (ITEM_POSITION_OFFSET, 3),
        (ITEM_POSITION_OFFSET + 4, 4),
        (ITEM_VELOCITY_OFFSET, 5),
        (ITEM_VELOCITY_OFFSET + 4, 6),
    ):
        code.extend(b"\x8b\x93" + _u32(item_offset))
        store_edx(_EVENT_PAYLOAD_OFFSET + 4 * payload_index)
    for address, payload_index in (
        (ADDR_PLAYER + PLAYER_POSITION_OFFSET, 7),
        (ADDR_PLAYER + PLAYER_POSITION_OFFSET + 4, 8),
    ):
        code.extend(b"\x8b\x15" + _u32(address))
        store_edx(_EVENT_PAYLOAD_OFFSET + 4 * payload_index)
    for address, payload_index in (
        (ADDR_PLAYER, 9),
        (ADDR_PLAYER + PLAYER_FOCUS_LOGIC_OFFSET, 10),
    ):
        code.extend(b"\x0f\xb6\x15" + _u32(address))
        store_edx(_EVENT_PAYLOAD_OFFSET + 4 * payload_index)
    code.extend(b"\x0f\xb7\x15" + _u32(ADDR_CURRENT_INPUT))
    store_edx(_EVENT_PAYLOAD_OFFSET + 4 * 11)

    code.extend(b"\x8b\x15" + _u32(ADDR_RUN_STATE_INNER_POINTER))
    for resource_offset, before_index, after_index in (
        (RUN_STATE_POWER_OFFSET, 12, 13),
        (RUN_STATE_LIVES_OFFSET, 14, 15),
        (RUN_STATE_BOMBS_OFFSET, 16, 17),
    ):
        code.extend(b"\x8b\x82" + _u32(resource_offset))
        if event_pointer == "ecx":
            code.extend(b"\x89\x81" + _u32(
                _EVENT_PAYLOAD_OFFSET + 4 * before_index
            ))
            if include_resource_after:
                code.extend(b"\x89\x81" + _u32(
                    _EVENT_PAYLOAD_OFFSET + 4 * after_index
                ))
        else:
            code.extend(b"\x89\x87" + _u32(
                _EVENT_PAYLOAD_OFFSET + 4 * before_index
            ))
            if include_resource_after:
                code.extend(b"\x89\x87" + _u32(
                    _EVENT_PAYLOAD_OFFSET + 4 * after_index
                ))
            else:
                code.extend(b"\xc7\x87" + _u32(
                    _EVENT_PAYLOAD_OFFSET + 4 * after_index
                ) + _u32(_UNKNOWN_U32))
    return bytes(code)


def _capture_item_source_enemy_pointer() -> bytes:
    """Store an exact defeat-helper owner pointer in payload[20], else zero."""

    code = bytearray(b"\x8b\x55\x04")  # mov edx, [ebp + 4]
    equal_jumps: list[int] = []
    for return_address in sorted(
        ENEMY_DEFEAT_ITEM_ALLOCATION_RETURN_ADDRESSES
    ):
        code += b"\x81\xfa" + _u32(return_address)  # cmp edx, imm32
        equal_jumps.append(len(code))
        code += b"\x74\x00"  # je capture_owner
    code += b"\x31\xd2"  # xor edx, edx
    no_owner_jump = len(code)
    code += b"\xeb\x00"  # jmp store_owner
    capture_owner = len(code)
    code += b"\x8b\x45\x00"  # mov eax, [ebp]
    code += b"\x8b\x50\xec"  # mov edx, [eax - 0x14]
    store_owner = len(code)
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 20)
    for jump in equal_jumps:
        displacement = capture_owner - (jump + 2)
        if not -128 <= displacement <= 127:
            raise ValueError("item source-owner branch exceeds rel8")
        code[jump + 1] = displacement & 0xFF
    displacement = store_owner - (no_owner_jump + 2)
    if not -128 <= displacement <= 127:
        raise ValueError("item no-owner branch exceeds rel8")
    code[no_owner_jump + 1] = displacement & 0xFF
    return bytes(code)


def _build_enemy_site_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    site_index = HOOK_SITES.index(site)
    stub_address = (
        remote_base + PROBE_STUB_OFFSET + site_index * PROBE_STUB_STRIDE
    )
    serial_address = remote_base + PROBE_SERIAL_OFFSET
    event_base = remote_base + PROBE_EVENT_OFFSET

    code = bytearray()
    code += b"\x9c\x60"  # pushfd; pushad
    code += _load_enemy_pointer(site.pointer_source)
    code += _initialize_unpublished_event(
        serial_address=serial_address,
        event_base=event_base,
    )
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x51\x04"  # manager_frame
    code += b"\xc7\x41\x08" + _u32(int(site.kind))
    code += b"\x89\x59\x0c"  # enemy_pointer
    code += b"\x8b\x15" + _u32(ADDR_STAGE_ROUTE_INDEX)
    code += b"\x89\x51\x10"  # native stage-route index
    code += b"\x83\xca\xff"  # or edx, -1
    for offset in (0x18, 0x1C, 0x20, 0x24):
        code += b"\x89\x51" + bytes((offset,))
    code += b"\x8b\x93" + _u32(ENEMY_FLAGS_OFFSET)
    code += b"\x89\x51\x28"  # flags_before
    code += b"\x8b\x93" + _u32(ENEMY_HP_OFFSET)
    code += b"\x89\x51\x30"  # hp_before
    code += b"\x8b\x93" + _u32(ENEMY_FRAME_DAMAGE_OFFSET)
    code += b"\x89\x51\x38"  # frame_damage
    if site.capture_return_address:
        code += b"\x8b\x55\x04"  # mov edx, [ebp + 4]
    else:
        code += b"\x31\xd2"  # xor edx, edx
    code += b"\x89\x51\x14"  # aux/caller return address
    if site.capture_root_subroutine:
        code += b"\x0f\xbf\x55\x08"  # movsx edx, word [ebp + 8]
    else:
        code += b"\x83\xca\xff"  # or edx, -1
    code += b"\x89\x51\x3c"  # root subroutine, or -1 when not an allocation
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
    code += b"\x89\x51\x2c"  # flags_after
    code += b"\x8b\x93" + _u32(ENEMY_HP_OFFSET)
    code += b"\x89\x51\x34"  # hp_after
    code += b"\x89\x01"  # event.serial = eax
    code += b"\xa3" + _u32(serial_address)  # header.serial = eax
    code += b"\x61\x9d"  # popad; popfd

    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)
    if len(code) > PROBE_STUB_STRIDE:
        raise ValueError(f"lifecycle stub {site.name} exceeds its fixed slot")
    return bytes(code)


def _build_item_allocate_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    site_index = HOOK_SITES.index(site)
    stub_address = (
        remote_base + PROBE_STUB_OFFSET + site_index * PROBE_STUB_STRIDE
    )
    serial_address = remote_base + PROBE_SERIAL_OFFSET
    event_base = remote_base + PROBE_EVENT_OFFSET
    code = bytearray(b"\x9c\x60")
    code += _load_enemy_pointer(site.pointer_source)
    code += _initialize_unpublished_event(
        serial_address=serial_address,
        event_base=event_base,
    )
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x51\x04"
    code += b"\xc7\x41\x08" + _u32(int(site.kind))
    code += b"\x89\x59\x0c"
    code += b"\x8b\x15" + _u32(ADDR_STAGE_ROUTE_INDEX)
    code += b"\x89\x51\x10"
    code += b"\x8b\x55\x04"  # caller return address
    code += b"\x89\x51\x14"
    code += b"\x83\xca\xff"
    code += b"\x89\x51\x18"  # RNG-before state unavailable
    code += b"\x89\x51\x1c"  # RNG-before calls unavailable
    code += b"\x0f\xb7\x15" + _u32(ADDR_GAMEPLAY_RNG)
    code += b"\x89\x51\x20"
    code += b"\x8b\x15" + _u32(ADDR_GAMEPLAY_RNG + 4)
    code += b"\x89\x51\x24"
    code += _fill_item_common_fields(
        event_pointer="ecx",
        item_pointer="ebx",
        include_resource_after=True,
    )
    code += b"\x8b\x55\xf4"  # item manager from [ebp - 0x0c]
    code += b"\x8b\x82" + _u32(ITEM_MANAGER_NEXT_ALLOCATION_OFFSET)
    code += b"\x89\x81" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 18)
    code += b"\x8b\x93" + _u32(ITEM_PREVIOUS_OFFSET)
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 19)
    code += _capture_item_source_enemy_pointer()
    code += b"\x8b\x55\x0c"  # effective/mutated item-type argument
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 21)
    code += _commit_event(serial_address)
    code += b"\x61\x9d"
    code += site.original
    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)
    if len(code) > PROBE_STUB_STRIDE:
        raise ValueError(f"lifecycle stub {site.name} exceeds its fixed slot")
    return bytes(code)


def _build_item_cull_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    site_index = HOOK_SITES.index(site)
    stub_address = (
        remote_base + PROBE_STUB_OFFSET + site_index * PROBE_STUB_STRIDE
    )
    serial_address = remote_base + PROBE_SERIAL_OFFSET
    event_base = remote_base + PROBE_EVENT_OFFSET
    code = bytearray(b"\x9c\x60")
    code += _load_enemy_pointer(site.pointer_source)
    code += _initialize_unpublished_event(
        serial_address=serial_address,
        event_base=event_base,
    )
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x51\x04"
    code += b"\xc7\x41\x08" + _u32(int(site.kind))
    code += b"\x89\x59\x0c"
    code += b"\x8b\x15" + _u32(ADDR_STAGE_ROUTE_INDEX)
    code += b"\x89\x51\x10"
    code += b"\x83\xca\xff"
    for offset in (0x18, 0x1C, 0x20, 0x24):
        code += b"\x89\x51" + bytes((offset,))
    code += _fill_item_common_fields(
        event_pointer="ecx",
        item_pointer="ebx",
        include_resource_after=True,
    )
    code += b"\x8b\x93" + _u32(ITEM_PREVIOUS_OFFSET)
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 19)
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 20)
    code += b"\x89\x99" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 21)
    code += _commit_event(serial_address)
    code += b"\x61\x9d"
    code += b"\x8b\x4d\xdc"
    call_source = stub_address + len(code)
    code += _relative_call(call_source, 0x00441770)
    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)
    if len(code) > PROBE_STUB_STRIDE:
        raise ValueError(f"lifecycle stub {site.name} exceeds its fixed slot")
    return bytes(code)


def _build_item_pickup_begin_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    site_index = HOOK_SITES.index(site)
    stub_address = (
        remote_base + PROBE_STUB_OFFSET + site_index * PROBE_STUB_STRIDE
    )
    scratch = remote_base + PROBE_PICKUP_SCRATCH_OFFSET
    code = bytearray(b"\x9c\x60")
    code += _load_enemy_pointer(site.pointer_source)
    code += b"\xbf" + _u32(scratch)
    code += b"\xb9" + _u32(PROBE_EVENT_SIZE // 4)
    code += b"\x31\xc0\xf3\xab"  # zero complete scratch
    code += b"\xbf" + _u32(scratch)
    code += b"\xc7\x07" + _u32(0x49545042)  # "ITPB" valid-begin marker
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x57\x04"
    code += b"\xc7\x47\x08" + _u32(int(site.kind))
    code += b"\x89\x5f\x0c"
    code += b"\x8b\x15" + _u32(ADDR_STAGE_ROUTE_INDEX)
    code += b"\x89\x57\x10"
    code += b"\x0f\xb7\x15" + _u32(ADDR_GAMEPLAY_RNG)
    code += b"\x89\x57\x18"
    code += b"\x8b\x15" + _u32(ADDR_GAMEPLAY_RNG + 4)
    code += b"\x89\x57\x1c"
    code += b"\xc7\x47\x20" + _u32(_UNKNOWN_U32)
    code += b"\xc7\x47\x24" + _u32(_UNKNOWN_U32)
    code += _fill_item_common_fields(
        event_pointer="edi",
        item_pointer="ebx",
        include_resource_after=False,
    )
    code += b"\x8b\x93" + _u32(ITEM_PREVIOUS_OFFSET)
    code += b"\x89\x97" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 19)
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x97" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 20)
    # payload[21] remains zero until the matching commit site.
    code += b"\x61\x9d"
    code += site.original
    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)
    if len(code) > PROBE_STUB_STRIDE:
        raise ValueError(f"lifecycle stub {site.name} exceeds its fixed slot")
    return bytes(code)


def _build_item_pickup_commit_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    site_index = HOOK_SITES.index(site)
    stub_address = (
        remote_base + PROBE_STUB_OFFSET + site_index * PROBE_STUB_STRIDE
    )
    serial_address = remote_base + PROBE_SERIAL_OFFSET
    event_base = remote_base + PROBE_EVENT_OFFSET
    scratch = remote_base + PROBE_PICKUP_SCRATCH_OFFSET
    code = bytearray(b"\x9c\x60")
    code += _load_enemy_pointer(site.pointer_source)
    guard_jumps: list[int] = []
    code += b"\x81\x3d" + _u32(scratch) + _u32(0x49545042)
    guard_jumps.append(len(code))
    code += b"\x0f\x85\x00\x00\x00\x00"
    code += b"\x39\x1d" + _u32(scratch + 0x0C)
    guard_jumps.append(len(code))
    code += b"\x0f\x85\x00\x00\x00\x00"
    code += b"\xa1" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x39\x05" + _u32(scratch + 0x04)
    guard_jumps.append(len(code))
    code += b"\x0f\x85\x00\x00\x00\x00"
    code += _select_unpublished_event(
        serial_address=serial_address,
        event_base=event_base,
    )
    code += b"\x89\xc5"  # mov ebp, eax (saved next serial)
    code += b"\x89\x01"  # invalidate selected event slot
    code += b"\x89\xca"  # preserve event pointer in edx
    code += b"\x8d\x79\x04"
    code += b"\xbe" + _u32(scratch + 4)
    code += b"\xb9" + _u32(PROBE_EVENT_SIZE // 4 - 1)
    code += b"\xf3\xa5"  # rep movsd scratch[1:] -> event[1:]
    code += b"\x89\xd1"  # restore event pointer
    code += b"\x0f\xb7\x15" + _u32(ADDR_GAMEPLAY_RNG)
    code += b"\x89\x51\x20"
    code += b"\x8b\x15" + _u32(ADDR_GAMEPLAY_RNG + 4)
    code += b"\x89\x51\x24"
    code += b"\x8b\x15" + _u32(ADDR_RUN_STATE_INNER_POINTER)
    for resource_offset, after_index in (
        (RUN_STATE_POWER_OFFSET, 13),
        (RUN_STATE_LIVES_OFFSET, 15),
        (RUN_STATE_BOMBS_OFFSET, 17),
    ):
        code += b"\x8b\x82" + _u32(resource_offset)
        code += b"\x89\x81" + _u32(
            _EVENT_PAYLOAD_OFFSET + 4 * after_index
        )
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 20)
    code += b"\x89\x99" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 21)
    code += b"\xc7\x05" + _u32(scratch) + _u32(0)
    code += b"\x89\xe8"  # mov eax, ebp
    code += b"\x89\x01"
    code += b"\xa3" + _u32(serial_address)
    code += b"\x61\x9d"
    code += b"\x8b\x4d\xdc"  # replay mov ecx, [ebp - 0x24]
    call_source = stub_address + len(code)
    code += _relative_call(call_source, 0x00441770)
    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)

    replay_only = len(code)
    code += b"\xc7\x05" + _u32(scratch) + _u32(0)
    code += b"\x61\x9d"
    code += b"\x8b\x4d\xdc"
    call_source = stub_address + len(code)
    code += _relative_call(call_source, 0x00441770)
    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)
    for jump in guard_jumps:
        displacement = replay_only - (jump + 6)
        struct.pack_into("<i", code, jump + 2, displacement)
    if len(code) > PROBE_STUB_STRIDE:
        raise ValueError(f"lifecycle stub {site.name} exceeds its fixed slot")
    return bytes(code)


def _build_enemy_damage_begin_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    site_index = HOOK_SITES.index(site)
    stub_address = (
        remote_base + PROBE_STUB_OFFSET + site_index * PROBE_STUB_STRIDE
    )
    scratch = remote_base + PROBE_DAMAGE_SCRATCH_OFFSET
    code = bytearray(b"\x9c\x60")
    code += _load_enemy_pointer(site.pointer_source)
    code += b"\xbf" + _u32(scratch)
    code += b"\xb9" + _u32(PROBE_EVENT_SIZE // 4)
    code += b"\x31\xc0\xf3\xab"  # zero complete scratch
    code += b"\xbf" + _u32(scratch)
    code += b"\xc7\x07" + _u32(0x42474D44)  # "DMGB" valid-begin marker
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x57\x04"
    code += b"\xc7\x47\x08" + _u32(int(site.kind))
    code += b"\x89\x5f\x0c"
    code += b"\x8b\x15" + _u32(ADDR_STAGE_ROUTE_INDEX)
    code += b"\x89\x57\x10"
    code += b"\x0f\xb7\x15" + _u32(ADDR_GAMEPLAY_RNG)
    code += b"\x89\x57\x18"
    code += b"\x8b\x15" + _u32(ADDR_GAMEPLAY_RNG + 4)
    code += b"\x89\x57\x1c"
    code += b"\xc7\x47\x20" + _u32(_UNKNOWN_U32)
    code += b"\xc7\x47\x24" + _u32(_UNKNOWN_U32)

    for enemy_offset, payload_index in (
        (ENEMY_FLAGS_OFFSET, 0),
        (ENEMY_FLAGS2_OFFSET, 1),
        (ENEMY_HP_OFFSET, 2),
        (ENEMY_POSITION_OFFSET, 5),
        (ENEMY_POSITION_OFFSET + 4, 6),
        (ENEMY_MAIN_VM_OFFSET, 9),
        (ENEMY_MAIN_VM_TIMER_CURRENT_OFFSET, 10),
    ):
        code += b"\x8b\x93" + _u32(enemy_offset)
        code += b"\x89\x97" + _u32(
            _EVENT_PAYLOAD_OFFSET + 4 * payload_index
        )
    for payload_index in (3, 4, 21):
        code += b"\xc7\x87" + _u32(
            _EVENT_PAYLOAD_OFFSET + 4 * payload_index
        ) + _u32(_UNKNOWN_U32)

    # Capture the exact hitbox pair selected by the native damage path.
    # A nonzero-magnitude alternate width at +0x2d7c selects the alternate
    # pair; both signed zero encodings select the primary pair at +0x2d70.
    code += b"\x8b\x83" + _u32(ENEMY_ALTERNATE_HITBOX_OFFSET)
    code += b"\x25\xff\xff\xff\x7f\x85\xc0"
    primary_jump = len(code)
    code += b"\x74\x00"
    for enemy_offset, payload_index in (
        (ENEMY_ALTERNATE_HITBOX_OFFSET, 7),
        (ENEMY_ALTERNATE_HITBOX_OFFSET + 4, 8),
    ):
        code += b"\x8b\x93" + _u32(enemy_offset)
        code += b"\x89\x97" + _u32(
            _EVENT_PAYLOAD_OFFSET + 4 * payload_index
        )
    selected_jump = len(code)
    code += b"\xeb\x00"
    primary_hitbox = len(code)
    for enemy_offset, payload_index in (
        (ENEMY_DAMAGE_HITBOX_OFFSET, 7),
        (ENEMY_DAMAGE_HITBOX_OFFSET + 4, 8),
    ):
        code += b"\x8b\x93" + _u32(enemy_offset)
        code += b"\x89\x97" + _u32(
            _EVENT_PAYLOAD_OFFSET + 4 * payload_index
        )
    selected_hitbox = len(code)
    for jump, target in (
        (primary_jump, primary_hitbox),
        (selected_jump, selected_hitbox),
    ):
        displacement = target - (jump + 2)
        if not -128 <= displacement <= 127:
            raise ValueError("damage hitbox-selection branch exceeds rel8")
        code[jump + 1] = displacement & 0xFF

    # Pack focus/player-state/Bomb/alternate-hitbox/route context into one
    # uint32.  The alternate-hitbox bit records nonzero float magnitude,
    # treating both +0.0 and -0.0 as disabled.  Bit 18 is filled by the
    # commit stub from [ebp-0x14].
    code += b"\x0f\xb6\x15" + _u32(
        ADDR_PLAYER + PLAYER_FOCUS_LOGIC_OFFSET
    )
    code += b"\x0f\xb6\x05" + _u32(ADDR_PLAYER)
    code += b"\xc1\xe0\x08\x09\xc2"
    code += b"\x83\x3d" + _u32(
        ADDR_PLAYER + PLAYER_BOMB_ACTIVE_OFFSET
    ) + b"\x00"
    code += b"\x0f\x95\xc0\x0f\xb6\xc0\xc1\xe0\x10\x09\xc2"
    code += b"\x8b\x83" + _u32(ENEMY_ALTERNATE_HITBOX_OFFSET)
    code += b"\x25\xff\xff\xff\x7f"
    code += b"\x85\xc0\x0f\x95\xc0\x0f\xb6\xc0\xc1\xe0\x11\x09\xc2"
    code += b"\x0f\xb6\x05" + _u32(ADDR_ROUTE_ID)
    code += b"\xc1\xe0\x18\x09\xc2"
    code += b"\x89\x97" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 11)

    code += b"\x0f\xb7\x15" + _u32(ADDR_CURRENT_INPUT)
    code += b"\x89\x97" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 12)
    code += b"\x8b\x15" + _u32(ADDR_RUN_STATE_INNER_POINTER)
    code += b"\x8b\x82" + _u32(RUN_STATE_POWER_OFFSET)
    code += b"\x89\x87" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 13)
    for address, payload_index in (
        (ADDR_PLAYER + PLAYER_SHOT_TIMER_OFFSET, 14),
        (ADDR_PLAYER + PLAYER_SHOT_TIMER_OFFSET + 4, 15),
        (ADDR_PLAYER + PLAYER_SHOT_TIMER_OFFSET + 8, 16),
        (ADDR_PLAYER + PLAYER_DAMAGE_TIMER_OFFSET, 17),
        (ADDR_PLAYER + PLAYER_DAMAGE_TIMER_OFFSET + 4, 18),
        (ADDR_PLAYER + PLAYER_DAMAGE_TIMER_OFFSET + 8, 19),
    ):
        code += b"\x8b\x15" + _u32(address)
        code += b"\x89\x97" + _u32(
            _EVENT_PAYLOAD_OFFSET + 4 * payload_index
        )

    # Count occupied slots and slots satisfying the shipped damage-loop
    # predicate: state != 0 and (state == 1 or type == 3).
    code += b"\x31\xd2\x31\xdb"
    code += b"\xbe" + _u32(ADDR_PLAYER + PLAYER_SHOT_POOL_OFFSET)
    code += b"\xb9" + _u32(PLAYER_SHOT_POOL_SIZE)
    loop_start = len(code)
    code += b"\x0f\xb7\x86" + _u32(PLAYER_SHOT_SLOT_STATE_OFFSET)
    code += b"\x85\xc0"
    jump_zero = len(code)
    code += b"\x74\x00"
    code += b"\x42"  # inc edx (occupied)
    code += b"\x83\xf8\x01"
    jump_state_one = len(code)
    code += b"\x74\x00"
    code += (
        b"\x66\x83\xbe"
        + _u32(PLAYER_SHOT_SLOT_TYPE_OFFSET)
        + b"\x03"
    )
    jump_not_type_three = len(code)
    code += b"\x75\x00"
    eligible = len(code)
    code += b"\x43"  # inc ebx (eligible)
    next_slot = len(code)
    code += b"\x81\xc6" + _u32(PLAYER_SHOT_SLOT_STRIDE)
    code += b"\x49"
    loop_jump = len(code)
    code += b"\x75\x00"
    for jump, target in (
        (jump_zero, next_slot),
        (jump_state_one, eligible),
        (jump_not_type_three, next_slot),
        (loop_jump, loop_start),
    ):
        displacement = target - (jump + 2)
        if not -128 <= displacement <= 127:
            raise ValueError("damage shot-count branch exceeds rel8")
        code[jump + 1] = displacement & 0xFF
    code += b"\x89\xd8\xc1\xe0\x10\x09\xd0"
    code += b"\xa3" + _u32(
        scratch + _EVENT_PAYLOAD_OFFSET + 4 * 20
    )

    code += b"\x61\x9d"
    code += site.original
    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)
    if len(code) > PROBE_STUB_STRIDE:
        raise ValueError(f"lifecycle stub {site.name} exceeds its fixed slot")
    return bytes(code)


def _build_enemy_damage_commit_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    site_index = HOOK_SITES.index(site)
    stub_address = (
        remote_base + PROBE_STUB_OFFSET + site_index * PROBE_STUB_STRIDE
    )
    serial_address = remote_base + PROBE_SERIAL_OFFSET
    event_base = remote_base + PROBE_EVENT_OFFSET
    scratch = remote_base + PROBE_DAMAGE_SCRATCH_OFFSET
    code = bytearray(b"\x9c\x60")
    code += _load_enemy_pointer(site.pointer_source)
    guard_jumps: list[int] = []
    code += b"\x81\x3d" + _u32(scratch) + _u32(0x42474D44)
    guard_jumps.append(len(code))
    code += b"\x0f\x85\x00\x00\x00\x00"
    code += b"\x39\x1d" + _u32(scratch + 0x0C)
    guard_jumps.append(len(code))
    code += b"\x0f\x85\x00\x00\x00\x00"
    code += b"\xa1" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x39\x05" + _u32(scratch + 0x04)
    guard_jumps.append(len(code))
    code += b"\x0f\x85\x00\x00\x00\x00"
    code += _select_unpublished_event(
        serial_address=serial_address,
        event_base=event_base,
    )
    code += b"\x89\x01"  # invalidate selected event slot
    code += b"\x89\xca"  # preserve event pointer in edx
    code += b"\x8d\x79\x04"
    code += b"\xbe" + _u32(scratch + 4)
    code += b"\xb9" + _u32(PROBE_EVENT_SIZE // 4 - 1)
    code += b"\xf3\xa5"
    code += b"\x89\xd1"
    code += b"\x89\x59\x14"  # exact commit enemy pointer
    code += b"\x8b\x55\xe8"  # resolved damage [ebp - 0x18]
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 4)
    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 21)
    code += b"\x83\x7d\xec\x00"  # Bomb damage-region overlap flag
    code += b"\x0f\x95\xc0\x0f\xb6\xc0\xc1\xe0\x12"
    code += b"\x09\x81" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 11)
    code += b"\x61\x9d"

    # Exact shipped subtract/reload/write span executes before publication.
    code += site.original

    code += b"\x9c\x60"
    code += _load_enemy_pointer(site.pointer_source)
    code += _select_unpublished_event(
        serial_address=serial_address,
        event_base=event_base,
    )
    code += b"\x8b\x93" + _u32(ENEMY_HP_OFFSET)
    code += b"\x89\x91" + _u32(_EVENT_PAYLOAD_OFFSET + 4 * 3)
    code += b"\x0f\xb7\x15" + _u32(ADDR_GAMEPLAY_RNG)
    code += b"\x89\x51\x20"
    code += b"\x8b\x15" + _u32(ADDR_GAMEPLAY_RNG + 4)
    code += b"\x89\x51\x24"
    code += b"\xc7\x05" + _u32(scratch) + _u32(0)
    code += b"\x89\x01"
    code += b"\xa3" + _u32(serial_address)
    code += b"\x61\x9d"
    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)

    # Installation may occur while the game thread is already between the
    # paired sites.  A missing/mismatched begin record must replay the shipped
    # commit without consuming a ring serial or publishing stale scratch.
    replay_only = len(code)
    code += b"\xc7\x05" + _u32(scratch) + _u32(0)
    code += b"\x61\x9d"
    code += site.original
    jump_source = stub_address + len(code)
    code += _relative_jump(jump_source, site.return_address)
    for jump in guard_jumps:
        displacement = replay_only - (jump + 6)
        struct.pack_into("<i", code, jump + 2, displacement)
    if len(code) > PROBE_STUB_STRIDE:
        raise ValueError(f"lifecycle stub {site.name} exceeds its fixed slot")
    return bytes(code)


def build_site_stub(
    remote_base: int,
    site: EnemyLifecycleHookSite,
) -> bytes:
    """Build one role-specific replay-safe x86 hook stub."""

    if site.role == "enemy_event":
        return _build_enemy_site_stub(remote_base, site)
    if site.role == "item_allocate":
        return _build_item_allocate_stub(remote_base, site)
    if site.role == "item_cull":
        return _build_item_cull_stub(remote_base, site)
    if site.role == "item_pickup_begin":
        return _build_item_pickup_begin_stub(remote_base, site)
    if site.role == "item_pickup_commit":
        return _build_item_pickup_commit_stub(remote_base, site)
    if site.role == "enemy_damage_begin":
        return _build_enemy_damage_begin_stub(remote_base, site)
    if site.role == "enemy_damage_commit":
        return _build_enemy_damage_commit_stub(remote_base, site)
    raise ValueError(f"unsupported lifecycle hook role {site.role}")


def build_probe_image(remote_base: int, pid: int) -> bytes:
    """Build the initialized lifecycle header and all site stubs."""

    if not 0 < pid <= 0xFFFFFFFF:
        raise ValueError("pid is outside uint32")
    if PROBE_DAMAGE_SCRATCH_OFFSET + PROBE_EVENT_SIZE > PROBE_STUB_OFFSET:
        raise ValueError("lifecycle scratch records overlap the stub region")
    if (
        PROBE_STUB_OFFSET + len(HOOK_SITES) * PROBE_STUB_STRIDE
        > PROBE_EVENT_OFFSET
    ):
        raise ValueError("lifecycle stubs overlap the event ring")
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
    subject_pointer: int
    stage_route_index: int
    caller_return_address: int
    rng_state_before: int | None
    rng_calls_before: int | None
    rng_state_after: int | None
    rng_calls_after: int | None
    payload: tuple[int, ...]

    @classmethod
    def decode(cls, payload: bytes) -> EnemyLifecycleEvent:
        if len(payload) != PROBE_EVENT_SIZE:
            raise ValueError("enemy lifecycle event size is invalid")
        words = _EVENT.unpack(payload)
        (
            serial,
            manager_frame,
            kind_value,
            subject_pointer,
            stage_route_index,
            caller_return_address,
            rng_state_before,
            rng_calls_before,
            rng_state_after,
            rng_calls_after,
            *event_payload,
        ) = words
        try:
            kind = EnemyLifecycleKind(kind_value)
        except ValueError as error:
            raise ValueError("enemy lifecycle event kind is invalid") from error
        if not 0 <= stage_route_index <= 8:
            raise ValueError(
                "lifecycle event stage-route index is outside 0..8"
            )
        event = cls(
            serial=serial,
            manager_frame=manager_frame,
            kind=kind,
            subject_pointer=subject_pointer,
            stage_route_index=stage_route_index,
            caller_return_address=caller_return_address,
            rng_state_before=(
                None if rng_state_before == _UNKNOWN_U32 else rng_state_before
            ),
            rng_calls_before=(
                None if rng_calls_before == _UNKNOWN_U32 else rng_calls_before
            ),
            rng_state_after=(
                None if rng_state_after == _UNKNOWN_U32 else rng_state_after
            ),
            rng_calls_after=(
                None if rng_calls_after == _UNKNOWN_U32 else rng_calls_after
            ),
            payload=tuple(event_payload),
        )
        event._validate()
        return event

    def _validate(self) -> None:
        if len(self.payload) != _EVENT_PAYLOAD_COUNT:
            raise ValueError("lifecycle event payload size is invalid")
        if self.kind in _ENEMY_KINDS:
            offset = self.subject_pointer - ENEMY_POOL_BASE
            if (
                offset < 0
                or offset >= ENEMY_POOL_SIZE * ENEMY_STRIDE
                or offset % ENEMY_STRIDE
            ):
                raise ValueError(
                    "enemy lifecycle pointer is outside the ordinary pool"
                )
            if self.kind is EnemyLifecycleKind.ENEMY_DAMAGE:
                if (
                    self.rng_state_before is None
                    or self.rng_calls_before is None
                    or self.rng_state_after is None
                    or self.rng_calls_after is None
                ):
                    raise ValueError(
                        "enemy damage transaction has incomplete RNG identity"
                    )
                if (
                    self.rng_state_before > 0xFFFF
                    or self.rng_state_after > 0xFFFF
                ):
                    raise ValueError(
                        "enemy damage transaction has invalid RNG state"
                    )
                if self.caller_return_address != self.subject_pointer:
                    raise ValueError(
                        "enemy damage begin/commit pointer identity disagrees"
                    )
                if self.damage_commit_manager_frame != self.manager_frame:
                    raise ValueError(
                        "enemy damage crossed an enemy-manager frame"
                    )
                if self.damage_resolved <= 0:
                    raise ValueError(
                        "enemy damage transaction has nonpositive damage"
                    )
                if self.hp_before - self.damage_resolved != self.hp_after:
                    raise ValueError(
                        "enemy damage transaction HP arithmetic disagrees"
                    )
                if not self.damage_flags & 0x01:
                    raise ValueError(
                        "enemy damage transaction begins on an inactive slot"
                    )
                if self.damage_context_word & ~0xFF07FFFF:
                    raise ValueError(
                        "enemy damage context has nonzero reserved bits"
                    )
                if self.damage_input_current & ~0xFFFF:
                    raise ValueError(
                        "enemy damage active input is invalid"
                    )
                if (
                    self.damage_eligible_shot_count
                    > self.damage_occupied_shot_count
                    or self.damage_occupied_shot_count
                    > PLAYER_SHOT_POOL_SIZE
                ):
                    raise ValueError(
                        "enemy damage shot-pool counts are impossible"
                    )
                for name, value in (
                    ("enemy_x", self.damage_enemy_x),
                    ("enemy_y", self.damage_enemy_y),
                    ("hitbox_width", self.damage_hitbox_width),
                    ("hitbox_height", self.damage_hitbox_height),
                    ("power", self.damage_power),
                ):
                    if not math.isfinite(value):
                        raise ValueError(
                            f"enemy damage {name} is not finite"
                        )
                return
            if any(
                value is not None
                for value in (
                    self.rng_state_before,
                    self.rng_calls_before,
                    self.rng_state_after,
                    self.rng_calls_after,
                )
            ):
                raise ValueError("enemy lifecycle event unexpectedly carries RNG")
            if self.kind is EnemyLifecycleKind.FORCED_HP_ZERO:
                if self.caller_return_address not in (
                    FORCED_ZERO_RETURN_ADDRESSES
                ):
                    raise ValueError(
                        "forced-HP-zero caller is not a shipped caller"
                    )
            elif self.caller_return_address:
                raise ValueError(
                    "non-forced enemy lifecycle event has a caller address"
                )
            if self.kind in _ALLOCATION_KINDS:
                root = _signed_u32(self.payload[5])
                if not 0 <= root <= 0x7FFF:
                    raise ValueError(
                        "allocation lifecycle event has no root subroutine"
                    )
            elif _signed_u32(self.payload[5]) != -1:
                raise ValueError(
                    "non-allocation lifecycle event has a root subroutine"
                )
            if any(self.payload[6:]):
                raise ValueError("enemy lifecycle event has nonzero tail payload")
            return

        offset = self.subject_pointer - ITEM_POOL_BASE
        if (
            offset < 0
            or offset >= ITEM_POOL_SIZE * ITEM_STRIDE
            or offset % ITEM_STRIDE
        ):
            raise ValueError("item lifecycle pointer is outside the item pool")
        if self.item_type not in range(9):
            raise ValueError("item lifecycle type is outside 0..8")
        if self.item_motion_state not in {0, 1, 2, 3, 5}:
            raise ValueError("item lifecycle motion state is unsupported")
        if self.payload[2] not in {0, 1}:
            raise ValueError("item lifecycle full-value flag is invalid")
        for name, value in (
            ("item_x", self.item_x),
            ("item_y", self.item_y),
            ("item_velocity_x", self.item_velocity_x),
            ("item_velocity_y", self.item_velocity_y),
            ("player_x", self.player_x),
            ("player_y", self.player_y),
            ("power_before", self.power_before),
            ("power_after", self.power_after),
            ("lives_before", self.lives_before),
            ("lives_after", self.lives_after),
            ("bombs_before", self.bombs_before),
            ("bombs_after", self.bombs_after),
        ):
            if not math.isfinite(value):
                raise ValueError(f"item lifecycle {name} is not finite")
        if self.player_state not in range(256):
            raise ValueError("item lifecycle player state is invalid")
        if self.focus_logic not in range(256):
            raise ValueError("item lifecycle focus state is invalid")
        if self.input_current & ~0xFFFF:
            raise ValueError("item lifecycle active input is invalid")
        if self.kind is EnemyLifecycleKind.ITEM_ALLOCATE:
            if self.rng_state_after is None or self.rng_state_after > 0xFFFF:
                raise ValueError("item allocation post-RNG state is invalid")
            if self.rng_calls_after is None:
                raise ValueError("item allocation post-RNG calls are missing")
            if self.caller_return_address not in (
                ITEM_ALLOCATION_RETURN_ADDRESSES
            ):
                raise ValueError(
                    "item allocation caller is not a shipped caller"
                )
            if self.rng_state_before is not None or self.rng_calls_before is not None:
                raise ValueError(
                    "post-only item allocation invents a pre-RNG state"
                )
            if not 0 <= self.allocation_next_index < ITEM_POOL_SIZE:
                raise ValueError("item allocation cursor is outside the pool")
            if self.payload[21] != self.item_type:
                raise ValueError(
                    "item allocation effective type disagrees with call argument"
                )
            owner = self.payload[20]
            if self.caller_return_address in (
                ENEMY_DEFEAT_ITEM_ALLOCATION_RETURN_ADDRESSES
            ):
                offset = owner - ENEMY_POOL_BASE
                if (
                    offset < 0
                    or offset >= ENEMY_POOL_SIZE * ENEMY_STRIDE
                    or offset % ENEMY_STRIDE
                ):
                    raise ValueError(
                        "defeat-item allocation has no exact source enemy"
                    )
            elif owner:
                raise ValueError(
                    "non-defeat item allocation invents a source enemy"
                )
        elif self.kind is EnemyLifecycleKind.ITEM_PICKUP:
            if self.caller_return_address:
                raise ValueError("item pickup unexpectedly carries a caller")
            if self.rng_state_before is None or self.rng_calls_before is None:
                raise ValueError("item pickup pre-RNG state is missing")
            if self.rng_state_before > 0xFFFF:
                raise ValueError("item pickup pre-RNG state is invalid")
            if self.rng_state_after is None or self.rng_state_after > 0xFFFF:
                raise ValueError("item pickup post-RNG state is invalid")
            if self.rng_calls_after is None:
                raise ValueError("item pickup post-RNG calls are missing")
            if self.payload[21] != self.subject_pointer:
                raise ValueError(
                    "item pickup begin/commit pointer identity disagrees"
                )
            if self.manager_frame != self.commit_manager_frame:
                raise ValueError(
                    "item pickup crossed an enemy-manager frame"
                )
        elif self.kind is EnemyLifecycleKind.ITEM_CULL:
            if self.caller_return_address:
                raise ValueError("item cull unexpectedly carries a caller")
            if any(
                value is not None
                for value in (
                    self.rng_state_before,
                    self.rng_calls_before,
                    self.rng_state_after,
                    self.rng_calls_after,
                )
            ):
                raise ValueError("item cull unexpectedly carries RNG")
            if self.payload[21] != self.subject_pointer:
                raise ValueError("item cull pointer identity disagrees")
            if self.manager_frame != self.commit_manager_frame:
                raise ValueError("item cull manager frame identity disagrees")
            if (
                self.power_before != self.power_after
                or self.lives_before != self.lives_after
                or self.bombs_before != self.bombs_after
            ):
                raise ValueError("item cull unexpectedly changes resources")
        else:
            raise ValueError("unsupported item lifecycle kind")

    @property
    def slot(self) -> int:
        if self.kind not in _ENEMY_KINDS:
            raise ValueError("item event has no enemy slot")
        return (self.subject_pointer - ENEMY_POOL_BASE) // ENEMY_STRIDE

    @property
    def item_slot(self) -> int:
        if self.kind not in _ITEM_KINDS:
            raise ValueError("enemy event has no item slot")
        return (self.subject_pointer - ITEM_POOL_BASE) // ITEM_STRIDE

    @property
    def enemy_pointer(self) -> int:
        if self.kind not in _ENEMY_KINDS:
            raise ValueError("item event has no enemy pointer")
        return self.subject_pointer

    @property
    def item_pointer(self) -> int:
        if self.kind not in _ITEM_KINDS:
            raise ValueError("enemy event has no item pointer")
        return self.subject_pointer

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
    def is_damage_event(self) -> bool:
        return self.kind is EnemyLifecycleKind.ENEMY_DAMAGE

    @property
    def is_item_event(self) -> bool:
        return self.kind in _ITEM_KINDS

    @property
    def flags_before(self) -> int:
        return self.payload[0]

    @property
    def flags_after(self) -> int:
        return self.payload[1]

    @property
    def hp_before(self) -> int:
        return _signed_u32(self.payload[2])

    @property
    def hp_after(self) -> int:
        return _signed_u32(self.payload[3])

    @property
    def frame_damage(self) -> int:
        return _signed_u32(self.payload[4])

    @property
    def damage_flags(self) -> int:
        return self.payload[0]

    @property
    def damage_flags2(self) -> int:
        return self.payload[1]

    @property
    def damage_resolved(self) -> int:
        return _signed_u32(self.payload[4])

    @property
    def damage_enemy_x(self) -> float:
        return _float_u32(self.payload[5])

    @property
    def damage_enemy_y(self) -> float:
        return _float_u32(self.payload[6])

    @property
    def damage_hitbox_width(self) -> float:
        return _float_u32(self.payload[7])

    @property
    def damage_hitbox_height(self) -> float:
        return _float_u32(self.payload[8])

    @property
    def damage_main_vm_pc(self) -> int:
        return self.payload[9]

    @property
    def damage_main_vm_timer_current(self) -> int:
        return _signed_u32(self.payload[10])

    @property
    def damage_context_word(self) -> int:
        return self.payload[11]

    @property
    def damage_focus_logic(self) -> int:
        return self.damage_context_word & 0xFF

    @property
    def damage_player_state(self) -> int:
        return (self.damage_context_word >> 8) & 0xFF

    @property
    def damage_bomb_active(self) -> bool:
        return bool(self.damage_context_word & (1 << 16))

    @property
    def damage_alternate_hitbox_nonzero(self) -> bool:
        return bool(self.damage_context_word & (1 << 17))

    @property
    def damage_region_overlap(self) -> bool:
        return bool(self.damage_context_word & (1 << 18))

    @property
    def damage_route_id(self) -> int:
        return (self.damage_context_word >> 24) & 0xFF

    @property
    def damage_power(self) -> float:
        return _float_u32(self.payload[13])

    @property
    def damage_input_current(self) -> int:
        return self.payload[12]

    @property
    def damage_shot_emission_timer(self) -> dict[str, int]:
        return {
            "previous": _signed_u32(self.payload[14]),
            "fraction_bits": self.payload[15],
            "current": _signed_u32(self.payload[16]),
        }

    @property
    def damage_timer(self) -> dict[str, int]:
        return {
            "previous": _signed_u32(self.payload[17]),
            "fraction_bits": self.payload[18],
            "current": _signed_u32(self.payload[19]),
        }

    @property
    def damage_occupied_shot_count(self) -> int:
        return self.payload[20] & 0xFFFF

    @property
    def damage_eligible_shot_count(self) -> int:
        return self.payload[20] >> 16

    @property
    def damage_commit_manager_frame(self) -> int:
        return self.payload[21]

    @property
    def root_subroutine(self) -> int | None:
        root = _signed_u32(self.payload[5])
        return root if self.kind in _ALLOCATION_KINDS else None

    @property
    def item_type(self) -> int:
        return self.payload[0]

    @property
    def item_motion_state(self) -> int:
        return self.payload[1]

    @property
    def item_full_value(self) -> bool:
        return bool(self.payload[2])

    @property
    def item_x(self) -> float:
        return _float_u32(self.payload[3])

    @property
    def item_y(self) -> float:
        return _float_u32(self.payload[4])

    @property
    def item_velocity_x(self) -> float:
        return _float_u32(self.payload[5])

    @property
    def item_velocity_y(self) -> float:
        return _float_u32(self.payload[6])

    @property
    def player_x(self) -> float:
        return _float_u32(self.payload[7])

    @property
    def player_y(self) -> float:
        return _float_u32(self.payload[8])

    @property
    def player_state(self) -> int:
        return self.payload[9]

    @property
    def focus_logic(self) -> int:
        return self.payload[10]

    @property
    def input_current(self) -> int:
        return self.payload[11]

    @property
    def power_before(self) -> float:
        return _float_u32(self.payload[12])

    @property
    def power_after(self) -> float:
        return _float_u32(self.payload[13])

    @property
    def lives_before(self) -> float:
        return _float_u32(self.payload[14])

    @property
    def lives_after(self) -> float:
        return _float_u32(self.payload[15])

    @property
    def bombs_before(self) -> float:
        return _float_u32(self.payload[16])

    @property
    def bombs_after(self) -> float:
        return _float_u32(self.payload[17])

    @property
    def allocation_next_index(self) -> int:
        return self.payload[18]

    @property
    def active_previous_pointer(self) -> int:
        return self.payload[19]

    @property
    def commit_manager_frame(self) -> int:
        return self.payload[20]

    @property
    def source_enemy_pointer(self) -> int | None:
        if self.kind is not EnemyLifecycleKind.ITEM_ALLOCATE:
            return None
        return self.payload[20] or None

    @property
    def reconstructed_pre_damage_hp(self) -> int | None:
        if self.kind is not EnemyLifecycleKind.RETIRE_DEFEAT_MODE0:
            return None
        return self.hp_before + self.frame_damage

    def compact_record(self) -> dict[str, object]:
        common: dict[str, object] = {
            "serial": self.serial,
            "manager_frame": self.manager_frame,
            "kind": self.kind.name.lower(),
            "stage_route_index": self.stage_route_index,
        }
        if self.kind is EnemyLifecycleKind.ENEMY_DAMAGE:
            common.update(
                {
                    "slot": self.slot,
                    "enemy_pointer": self.enemy_pointer,
                    "commit_enemy_pointer": self.caller_return_address,
                    "flags": self.damage_flags,
                    "flags2": self.damage_flags2,
                    "hp_before": self.hp_before,
                    "hp_after": self.hp_after,
                    "resolved_damage": self.damage_resolved,
                    "enemy_position": {
                        "x": self.damage_enemy_x,
                        "y": self.damage_enemy_y,
                    },
                    "damage_hitbox": {
                        "width": self.damage_hitbox_width,
                        "height": self.damage_hitbox_height,
                    },
                    "main_vm_pc": self.damage_main_vm_pc,
                    "main_vm_timer_current": (
                        self.damage_main_vm_timer_current
                    ),
                    "player_context": {
                        "focus_logic": self.damage_focus_logic,
                        "player_state": self.damage_player_state,
                        "bomb_active": self.damage_bomb_active,
                        "alternate_hitbox_nonzero": (
                            self.damage_alternate_hitbox_nonzero
                        ),
                        "damage_region_overlap": self.damage_region_overlap,
                        "route_id": self.damage_route_id,
                        "input_current": self.damage_input_current,
                        "power": self.damage_power,
                    },
                    "shot_emission_timer": self.damage_shot_emission_timer,
                    "damage_timer": self.damage_timer,
                    "shot_pool": {
                        "occupied": self.damage_occupied_shot_count,
                        "eligible_for_damage_loop": (
                            self.damage_eligible_shot_count
                        ),
                    },
                    "rng_before": {
                        "state": self.rng_state_before,
                        "calls": self.rng_calls_before,
                    },
                    "rng_after": {
                        "state": self.rng_state_after,
                        "calls": self.rng_calls_after,
                    },
                    "commit_manager_frame": (
                        self.damage_commit_manager_frame
                    ),
                }
            )
            return common
        if self.kind in _ENEMY_KINDS:
            common.update(
                {
                    "slot": self.slot,
                    "enemy_pointer": self.enemy_pointer,
                    "flags_before": self.flags_before,
                    "flags_after": self.flags_after,
                    "hp_before": self.hp_before,
                    "hp_after": self.hp_after,
                    "frame_damage": self.frame_damage,
                    "reconstructed_pre_damage_hp": (
                        self.reconstructed_pre_damage_hp
                    ),
                    "caller_return_address": (
                        self.caller_return_address or None
                    ),
                    "root_subroutine": self.root_subroutine,
                }
            )
            return common
        common.update(
            {
                "item_slot": self.item_slot,
                "item_pointer": self.item_pointer,
                "item_type": self.item_type,
                "motion_state": self.item_motion_state,
                "full_value": self.item_full_value,
                "item_position": {
                    "x": self.item_x,
                    "y": self.item_y,
                },
                "item_velocity": {
                    "x": self.item_velocity_x,
                    "y": self.item_velocity_y,
                },
                "player_position": {
                    "x": self.player_x,
                    "y": self.player_y,
                },
                "player_state": self.player_state,
                "focus_logic": self.focus_logic,
                "input_current": self.input_current,
                "resources_before": {
                    "power": self.power_before,
                    "lives": self.lives_before,
                    "bombs": self.bombs_before,
                },
                "resources_after": {
                    "power": self.power_after,
                    "lives": self.lives_after,
                    "bombs": self.bombs_after,
                },
                "rng_before": (
                    None
                    if self.rng_state_before is None
                    else {
                        "state": self.rng_state_before,
                        "calls": self.rng_calls_before,
                    }
                ),
                "rng_after": (
                    None
                    if self.rng_state_after is None
                    else {
                        "state": self.rng_state_after,
                        "calls": self.rng_calls_after,
                    }
                ),
                "caller_return_address": (
                    self.caller_return_address or None
                ),
                "active_previous_pointer": (
                    self.active_previous_pointer or None
                ),
                "source_enemy_pointer": self.source_enemy_pointer,
                "allocation_next_index": (
                    self.allocation_next_index
                    if self.kind is EnemyLifecycleKind.ITEM_ALLOCATE
                    else None
                ),
            }
        )
        return common


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
                    "role": site.role,
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
        maximum_events: int = PROBE_CAPACITY,
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
                raw_events = bytearray()
                if retained:
                    first_slot = (first - 1) & (PROBE_CAPACITY - 1)
                    first_count = min(
                        retained,
                        PROBE_CAPACITY - first_slot,
                    )
                    raw_events += _read_memory(
                        self.api,
                        self.handle,
                        self.remote_base
                        + PROBE_EVENT_OFFSET
                        + first_slot * PROBE_EVENT_SIZE,
                        first_count * PROBE_EVENT_SIZE,
                    )
                    remaining = retained - first_count
                    if remaining:
                        raw_events += _read_memory(
                            self.api,
                            self.handle,
                            self.remote_base + PROBE_EVENT_OFFSET,
                            remaining * PROBE_EVENT_SIZE,
                        )
                for offset in range(retained):
                    expected = (first + offset) & 0xFFFFFFFF
                    start = offset * PROBE_EVENT_SIZE
                    payload = bytes(
                        raw_events[start : start + PROBE_EVENT_SIZE]
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
    "ENEMY_DEFEAT_ITEM_ALLOCATION_RETURN_ADDRESSES",
    "ENEMY_FLAGS_OFFSET",
    "ENEMY_FRAME_DAMAGE_OFFSET",
    "ENEMY_HP_OFFSET",
    "ENEMY_POOL_BASE",
    "ENEMY_POOL_SIZE",
    "ENEMY_STRIDE",
    "FORCED_ZERO_RETURN_ADDRESSES",
    "HOOK_SITES",
    "ITEM_ALLOCATION_RETURN_ADDRESSES",
    "ITEM_POOL_BASE",
    "ITEM_POOL_SIZE",
    "ITEM_STRIDE",
    "PROBE_ALLOCATION_SIZE",
    "PROBE_CAPACITY",
    "PROBE_EVENT_OFFSET",
    "PROBE_EVENT_SIZE",
    "PROBE_HEADER_SIZE",
    "PROBE_PICKUP_SCRATCH_OFFSET",
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
