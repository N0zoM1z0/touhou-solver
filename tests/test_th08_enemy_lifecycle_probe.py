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
    ITEM_ALLOCATION_RETURN_ADDRESSES,
    ITEM_POOL_BASE,
    ITEM_STRIDE,
    PROBE_ALLOCATION_SIZE,
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
    payload = [0] * 22
    payload[0] = 0x101
    payload[1] = 0x100
    payload[2] = hp_before & 0xFFFFFFFF
    payload[3] = hp_after & 0xFFFFFFFF
    payload[4] = frame_damage & 0xFFFFFFFF
    payload[5] = encoded_root & 0xFFFFFFFF
    return struct.pack(
        "<32I",
        serial,
        1000 + serial,
        int(kind),
        ENEMY_POOL_BASE + slot * ENEMY_STRIDE,
        stage_route_index,
        caller,
        0xFFFFFFFF,
        0xFFFFFFFF,
        0xFFFFFFFF,
        0xFFFFFFFF,
        *payload,
    )


def _f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def _item_event(
    serial: int,
    *,
    kind: EnemyLifecycleKind,
    slot: int = 4,
    caller: int = 0,
    stage_route_index: int = 0,
    item_type: int = 0,
    motion_state: int = 1,
    power_before: float = 7.0,
    power_after: float = 8.0,
    rng_state_before: int = 0x1234,
    rng_calls_before: int = 100,
    rng_state_after: int = 0x5678,
    rng_calls_after: int = 100,
    commit_pointer: int | None = None,
    commit_frame: int | None = None,
    source_enemy_pointer: int | None = None,
) -> bytes:
    item_pointer = ITEM_POOL_BASE + slot * ITEM_STRIDE
    frame = 2000 + serial
    payload = [
        item_type,
        motion_state,
        0,
        _f32_bits(100.0),
        _f32_bits(80.0),
        _f32_bits(0.5),
        _f32_bits(-1.25),
        _f32_bits(104.0),
        _f32_bits(84.0),
        0,
        1,
        0x10,
        _f32_bits(power_before),
        _f32_bits(power_after),
        _f32_bits(2.0),
        _f32_bits(2.0),
        _f32_bits(3.0),
        _f32_bits(3.0),
        19 if kind is EnemyLifecycleKind.ITEM_ALLOCATE else 0,
        0,
        (
            source_enemy_pointer or 0
            if kind is EnemyLifecycleKind.ITEM_ALLOCATE
            else (frame if commit_frame is None else commit_frame)
        ),
        (
            item_type
            if kind is EnemyLifecycleKind.ITEM_ALLOCATE
            else (
                item_pointer
                if commit_pointer is None
                else commit_pointer
            )
        ),
    ]
    before_state = (
        0xFFFFFFFF
        if kind
        in {
            EnemyLifecycleKind.ITEM_ALLOCATE,
            EnemyLifecycleKind.ITEM_CULL,
        }
        else rng_state_before
    )
    before_calls = (
        0xFFFFFFFF
        if kind
        in {
            EnemyLifecycleKind.ITEM_ALLOCATE,
            EnemyLifecycleKind.ITEM_CULL,
        }
        else rng_calls_before
    )
    after_state = (
        0xFFFFFFFF
        if kind is EnemyLifecycleKind.ITEM_CULL
        else rng_state_after
    )
    after_calls = (
        0xFFFFFFFF
        if kind is EnemyLifecycleKind.ITEM_CULL
        else rng_calls_after
    )
    return struct.pack(
        "<32I",
        serial,
        frame,
        int(kind),
        item_pointer,
        stage_route_index,
        caller,
        before_state,
        before_calls,
        after_state,
        after_calls,
        *payload,
    )


def _damage_event(
    serial: int,
    *,
    slot: int = 6,
    stage_route_index: int = 5,
    commit_pointer: int | None = None,
    commit_frame: int | None = None,
    hp_before: int = 150,
    hp_after: int = 143,
    damage: int = 7,
    flags: int = 0x101,
    flags2: int = 0,
    context_word: int = (2 << 24) | (1 << 17) | 1,
    occupied_shots: int = 12,
    eligible_shots: int = 9,
) -> bytes:
    enemy_pointer = ENEMY_POOL_BASE + slot * ENEMY_STRIDE
    frame = 3000 + serial
    payload = [
        flags,
        flags2,
        hp_before & 0xFFFFFFFF,
        hp_after & 0xFFFFFFFF,
        damage & 0xFFFFFFFF,
        _f32_bits(96.0),
        _f32_bits(120.0),
        _f32_bits(24.0),
        _f32_bits(16.0),
        0x00510040,
        223,
        context_word,
        0x11,
        _f32_bits(64.0),
        10,
        _f32_bits(0.25),
        11,
        21,
        _f32_bits(0.5),
        22,
        occupied_shots | (eligible_shots << 16),
        frame if commit_frame is None else commit_frame,
    ]
    return struct.pack(
        "<32I",
        serial,
        frame,
        int(EnemyLifecycleKind.ENEMY_DAMAGE),
        enemy_pointer,
        stage_route_index,
        enemy_pointer if commit_pointer is None else commit_pointer,
        0x1234,
        100,
        0x5678,
        103,
        *payload,
    )


def _probe(*, serial: int, base: int = 0x02000000):
    memory = bytearray(PROBE_ALLOCATION_SIZE)
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
                (
                    0x0042D06D,
                    EnemyLifecycleKind.ENEMY_DAMAGE,
                    bytes.fromhex(
                        "8b4dc8c7815433000000000000"
                    ),
                ),
                (
                    0x0042D343,
                    EnemyLifecycleKind.ENEMY_DAMAGE,
                    bytes.fromhex(
                        "2b45e88b4dc88981fc2d0000"
                    ),
                ),
                (
                    0x0044044D,
                    EnemyLifecycleKind.ITEM_ALLOCATE,
                    bytes.fromhex("8b4df8894df0"),
                ),
                (
                    0x00440991,
                    EnemyLifecycleKind.ITEM_CULL,
                    bytes.fromhex("8b4ddce8d70d0000"),
                ),
                (
                    0x00440A39,
                    EnemyLifecycleKind.ITEM_PICKUP,
                    bytes.fromhex("668990da000000"),
                ),
                (
                    0x00440C1E,
                    EnemyLifecycleKind.ITEM_PICKUP,
                    bytes.fromhex("8b4ddce84a0b0000"),
                ),
            ],
        )
        self.assertEqual(
            [site.capture_root_subroutine for site in HOOK_SITES],
            [
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
        )
        self.assertEqual(
            [site.role for site in HOOK_SITES[8:10]],
            ["enemy_damage_begin", "enemy_damage_commit"],
        )
        self.assertEqual(
            [site.role for site in HOOK_SITES[-4:]],
            [
                "item_allocate",
                "item_cull",
                "item_pickup_begin",
                "item_pickup_commit",
            ],
        )

    def test_stubs_replay_original_then_return_and_fit_fixed_slots(self) -> None:
        remote_base = 0x02000000
        self.assertLessEqual(
            PROBE_STUB_OFFSET + len(HOOK_SITES) * PROBE_STUB_STRIDE,
            PROBE_EVENT_OFFSET,
        )
        for index, site in enumerate(HOOK_SITES):
            stub = build_site_stub(remote_base, site)
            self.assertTrue(stub.startswith(b"\x9c\x60"))
            if site.role not in {"item_cull", "item_pickup_commit"}:
                self.assertIn(site.original, stub)
            else:
                replay = stub.index(b"\x8b\x4d\xdc\xe8")
                displacement = struct.unpack(
                    "<i",
                    stub[replay + 4 : replay + 8],
                )[0]
                call_source = (
                    remote_base
                    + PROBE_STUB_OFFSET
                    + index * PROBE_STUB_STRIDE
                    + replay
                    + 3
                )
                self.assertEqual(
                    call_source + 5 + displacement,
                    0x00441770,
                )
            if site.capture_root_subroutine:
                self.assertIn(b"\x0f\xbf\x55\x08\x89\x51\x3c", stub)
            if site.role == "item_allocate":
                self.assertIn(
                    b"\x81\xfa\x0b\xbf\x42\x00",
                    stub,
                )
                self.assertIn(
                    b"\x8b\x45\x00\x8b\x50\xec",
                    stub,
                )
            if site.role == "enemy_damage_begin":
                self.assertIn(
                    b"\xc7\x07" + struct.pack("<I", 0x42474D44),
                    stub,
                )
                self.assertIn(
                    b"\x25\xff\xff\xff\x7f\x85\xc0",
                    stub,
                )
                selection = stub.index(
                    b"\x8b\x83"
                    + struct.pack(
                        "<I",
                        lifecycle_probe.ENEMY_ALTERNATE_HITBOX_OFFSET,
                    )
                    + b"\x25\xff\xff\xff\x7f\x85\xc0\x74"
                )
                primary_branch = selection + 13
                alternate_load = primary_branch + 2
                self.assertEqual(
                    stub[alternate_load : alternate_load + 6],
                    b"\x8b\x93"
                    + struct.pack(
                        "<I",
                        lifecycle_probe.ENEMY_ALTERNATE_HITBOX_OFFSET,
                    ),
                )
                primary_target = (
                    primary_branch
                    + 2
                    + struct.unpack(
                        "<b",
                        stub[primary_branch + 1 : primary_branch + 2],
                    )[0]
                )
                self.assertEqual(
                    stub[primary_target : primary_target + 6],
                    b"\x8b\x93"
                    + struct.pack(
                        "<I",
                        lifecycle_probe.ENEMY_DAMAGE_HITBOX_OFFSET,
                    ),
                )
                for offset in (
                    lifecycle_probe.ENEMY_DAMAGE_HITBOX_OFFSET,
                    lifecycle_probe.ENEMY_DAMAGE_HITBOX_OFFSET + 4,
                    lifecycle_probe.ENEMY_ALTERNATE_HITBOX_OFFSET,
                    lifecycle_probe.ENEMY_ALTERNATE_HITBOX_OFFSET + 4,
                ):
                    self.assertIn(
                        b"\x8b\x93" + struct.pack("<I", offset),
                        stub,
                    )
                self.assertIn(
                    b"\x0f\xb7\x86"
                    + struct.pack(
                        "<I",
                        lifecycle_probe.PLAYER_SHOT_SLOT_STATE_OFFSET,
                    ),
                    stub,
                )
                self.assertIn(
                    b"\x66\x83\xbe"
                    + struct.pack(
                        "<I",
                        lifecycle_probe.PLAYER_SHOT_SLOT_TYPE_OFFSET,
                    )
                    + b"\x03",
                    stub,
                )
            if site.role == "enemy_damage_commit":
                scratch = (
                    remote_base
                    + lifecycle_probe.PROBE_DAMAGE_SCRATCH_OFFSET
                )
                self.assertIn(
                    b"\x81\x3d"
                    + struct.pack("<I", scratch)
                    + struct.pack("<I", 0x42474D44),
                    stub,
                )
                self.assertIn(
                    b"\x39\x1d" + struct.pack("<I", scratch + 0x0C),
                    stub,
                )
                self.assertEqual(
                    stub.count(
                        b"\xc7\x05"
                        + struct.pack("<I", scratch)
                        + struct.pack("<I", 0)
                    ),
                    2,
                )
                self.assertEqual(stub.count(site.original), 2)
            if site.role == "item_pickup_commit":
                scratch = (
                    remote_base
                    + lifecycle_probe.PROBE_PICKUP_SCRATCH_OFFSET
                )
                self.assertIn(
                    b"\x81\x3d"
                    + struct.pack("<I", scratch)
                    + struct.pack("<I", 0x49545042),
                    stub,
                )
                self.assertIn(
                    b"\x39\x1d" + struct.pack("<I", scratch + 0x0C),
                    stub,
                )
                self.assertEqual(
                    stub.count(
                        b"\xc7\x05"
                        + struct.pack("<I", scratch)
                        + struct.pack("<I", 0)
                    ),
                    2,
                )
                self.assertEqual(stub.count(b"\x8b\x4d\xdc\xe8"), 2)
                first = stub.index(b"\x8b\x4d\xdc\xe8")
                replay_only = stub.index(
                    b"\x8b\x4d\xdc\xe8",
                    first + 1,
                )
                displacement = struct.unpack(
                    "<i",
                    stub[replay_only + 4 : replay_only + 8],
                )[0]
                call_source = (
                    remote_base
                    + PROBE_STUB_OFFSET
                    + index * PROBE_STUB_STRIDE
                    + replay_only
                    + 3
                )
                self.assertEqual(
                    call_source + 5 + displacement,
                    0x00441770,
                )
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

    def test_event_stride_uses_non_sign_extending_immediate(self) -> None:
        stub = build_site_stub(0x02000000, HOOK_SITES[0])
        multiply = stub.index(b"\x69\xc9")
        immediate = struct.unpack("<i", stub[multiply + 2 : multiply + 6])[0]
        self.assertEqual(immediate, PROBE_EVENT_SIZE)
        self.assertGreaterEqual(PROBE_EVENT_SIZE, 0x80)
        self.assertNotIn(
            b"\x6b\xc9" + bytes((PROBE_EVENT_SIZE & 0xFF,)),
            stub,
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

    def test_enemy_damage_retains_exact_same_frame_hp_transaction(self) -> None:
        event = EnemyLifecycleEvent.decode(_damage_event(14))
        record = event.compact_record()
        self.assertTrue(event.is_damage_event)
        self.assertEqual(event.slot, 6)
        self.assertEqual(event.hp_before, 150)
        self.assertEqual(event.hp_after, 143)
        self.assertEqual(event.damage_resolved, 7)
        self.assertEqual(event.damage_route_id, 2)
        self.assertTrue(event.damage_alternate_hitbox_nonzero)
        self.assertEqual(event.damage_occupied_shot_count, 12)
        self.assertEqual(event.damage_eligible_shot_count, 9)
        self.assertEqual(record["resolved_damage"], 7)
        self.assertEqual(record["player_context"]["input_current"], 0x11)
        self.assertEqual(record["rng_before"]["calls"], 100)
        self.assertEqual(record["rng_after"]["calls"], 103)

    def test_enemy_damage_rejects_torn_or_impossible_transactions(self) -> None:
        with self.assertRaisesRegex(ValueError, "pointer identity"):
            EnemyLifecycleEvent.decode(
                _damage_event(15, commit_pointer=ENEMY_POOL_BASE)
            )
        with self.assertRaisesRegex(ValueError, "manager frame"):
            EnemyLifecycleEvent.decode(
                _damage_event(15, commit_frame=999)
            )
        with self.assertRaisesRegex(ValueError, "HP arithmetic"):
            EnemyLifecycleEvent.decode(
                _damage_event(15, hp_after=144)
            )
        with self.assertRaisesRegex(ValueError, "inactive"):
            EnemyLifecycleEvent.decode(
                _damage_event(15, flags=0x100)
            )
        with self.assertRaisesRegex(ValueError, "shot-pool counts"):
            EnemyLifecycleEvent.decode(
                _damage_event(15, occupied_shots=8, eligible_shots=9)
            )
        with self.assertRaisesRegex(ValueError, "reserved bits"):
            EnemyLifecycleEvent.decode(
                _damage_event(15, context_word=1 << 20)
            )

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

    def test_item_allocation_retains_pool_rng_and_caller_identity(self) -> None:
        caller = min(ITEM_ALLOCATION_RETURN_ADDRESSES)
        event = EnemyLifecycleEvent.decode(
            _item_event(
                11,
                kind=EnemyLifecycleKind.ITEM_ALLOCATE,
                slot=9,
                caller=caller,
                item_type=2,
                power_before=24.0,
                power_after=24.0,
            )
        )
        self.assertTrue(event.is_item_event)
        self.assertEqual(event.item_slot, 9)
        self.assertEqual(event.item_type, 2)
        self.assertEqual(event.power_before, 24.0)
        self.assertIsNone(event.rng_state_before)
        self.assertEqual(event.rng_state_after, 0x5678)
        self.assertEqual(
            event.compact_record()["caller_return_address"],
            caller,
        )
        defeat = EnemyLifecycleEvent.decode(
            _item_event(
                11,
                kind=EnemyLifecycleKind.ITEM_ALLOCATE,
                caller=0x0042BF0B,
                source_enemy_pointer=ENEMY_POOL_BASE + 5 * ENEMY_STRIDE,
            )
        )
        self.assertEqual(
            defeat.source_enemy_pointer,
            ENEMY_POOL_BASE + 5 * ENEMY_STRIDE,
        )
        with self.assertRaisesRegex(ValueError, "shipped caller"):
            EnemyLifecycleEvent.decode(
                _item_event(
                    11,
                    kind=EnemyLifecycleKind.ITEM_ALLOCATE,
                    caller=0x00401000,
                )
            )
        with self.assertRaisesRegex(ValueError, "source enemy"):
            EnemyLifecycleEvent.decode(
                _item_event(
                    11,
                    kind=EnemyLifecycleKind.ITEM_ALLOCATE,
                    caller=0x0042BF0B,
                )
            )

    def test_item_pickup_retains_same_update_resource_transaction(self) -> None:
        event = EnemyLifecycleEvent.decode(
            _item_event(
                12,
                kind=EnemyLifecycleKind.ITEM_PICKUP,
                item_type=0,
                power_before=7.0,
                power_after=8.0,
            )
        )
        record = event.compact_record()
        self.assertEqual(record["resources_before"]["power"], 7.0)
        self.assertEqual(record["resources_after"]["power"], 8.0)
        self.assertEqual(record["rng_before"]["calls"], 100)
        self.assertEqual(record["rng_after"]["calls"], 100)
        with self.assertRaisesRegex(ValueError, "pointer identity"):
            EnemyLifecycleEvent.decode(
                _item_event(
                    12,
                    kind=EnemyLifecycleKind.ITEM_PICKUP,
                    commit_pointer=ITEM_POOL_BASE,
                )
            )
        with self.assertRaisesRegex(ValueError, "manager frame"):
            EnemyLifecycleEvent.decode(
                _item_event(
                    12,
                    kind=EnemyLifecycleKind.ITEM_PICKUP,
                    commit_frame=999,
                )
            )

    def test_item_cull_retires_the_exact_pool_generation(self) -> None:
        event = EnemyLifecycleEvent.decode(
            _item_event(
                13,
                kind=EnemyLifecycleKind.ITEM_CULL,
                slot=17,
                power_before=8.0,
                power_after=8.0,
            )
        )
        self.assertEqual(event.item_slot, 17)
        self.assertIsNone(event.rng_state_before)
        self.assertIsNone(event.rng_state_after)
        self.assertEqual(event.power_before, event.power_after)
        self.assertEqual(event.compact_record()["kind"], "item_cull")

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
