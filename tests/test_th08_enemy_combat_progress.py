#!/usr/bin/env python3
"""Tests for trace-only ordinary-enemy combat progress."""

from __future__ import annotations

import struct
import unittest

from th08_boss_phase import (
    ENEMY_CURRENT_HEALTH_OFFSET,
    ENEMY_FLAGS2_OFFSET,
    ENEMY_FLAGS_OFFSET,
    ENEMY_FRAME_DAMAGE_OFFSET,
    ENEMY_MAXIMUM_HEALTH_OFFSET,
    ENEMY_PHASE_HEALTH_OFFSET,
)
from th08_live.enemy_combat_progress import (
    ENEMY_COMBAT_PROGRESS_LAYOUT,
    EnemyCombatProgressInventory,
    build_enemy_combat_progress_record,
    decode_enemy_combat_progress_inventory,
)
from th08_live.enemy_combat_progress_stage import (
    EnemyCombatProgressStageDependencies,
    EnemyCombatProgressStageRequest,
    run_enemy_combat_progress_stage,
)
from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_POOL_BASE,
    ENEMY_STRIDE,
    capture_enemy_pool_prefix_contiguous,
)


class _Reader:
    def __init__(self, blob: bytes) -> None:
        self.blob = blob
        self.calls: list[tuple[object, ...]] = []

    def u32(self, address: int) -> int:
        self.calls.append(("u32", address))
        return 200

    def read(self, address: int, size: int) -> bytes:
        self.calls.append(("read", address, size))
        if address != ENEMY_POOL_BASE:
            raise AssertionError(f"unexpected address {address:#x}")
        return self.blob[:size]


class _TraceSink:
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, object], bool, bool]] = []

    def emit(
        self,
        record: dict[str, object],
        *,
        flush: bool = False,
        measure: bool = False,
    ) -> float:
        self.calls.append((record, flush, measure))
        return 0.125


def _set_enemy(
    blob: bytearray,
    slot: int,
    *,
    flags: int,
    flags2: int,
    current: int,
    maximum: int,
    phase_start: int,
    frame_damage: int,
) -> None:
    base = slot * ENEMY_STRIDE
    struct.pack_into("<iii", blob, base + ENEMY_CURRENT_HEALTH_OFFSET, current, maximum, phase_start)
    struct.pack_into("<II", blob, base + ENEMY_FLAGS_OFFSET, flags, flags2)
    struct.pack_into("<i", blob, base + ENEMY_FRAME_DAMAGE_OFFSET, frame_damage)


def _scalar_combat_rows(
    blob: bytes,
    *,
    pool_size: int,
) -> list[list[int | bool]]:
    rows: list[list[int | bool]] = []
    for slot in range(pool_size):
        base = slot * ENEMY_STRIDE
        flags = struct.unpack_from("<I", blob, base + ENEMY_FLAGS_OFFSET)[0]
        if not flags & ENEMY_ACTIVE_FLAG:
            continue
        flags2 = struct.unpack_from("<I", blob, base + ENEMY_FLAGS2_OFFSET)[0]
        current = struct.unpack_from(
            "<i",
            blob,
            base + ENEMY_CURRENT_HEALTH_OFFSET,
        )[0]
        maximum = struct.unpack_from(
            "<i",
            blob,
            base + ENEMY_MAXIMUM_HEALTH_OFFSET,
        )[0]
        phase_start = struct.unpack_from(
            "<i",
            blob,
            base + ENEMY_PHASE_HEALTH_OFFSET,
        )[0]
        frame_damage = struct.unpack_from(
            "<i",
            blob,
            base + ENEMY_FRAME_DAMAGE_OFFSET,
        )[0]
        rows.append(
            [
                slot,
                ENEMY_POOL_BASE + base,
                flags,
                flags2,
                current,
                maximum,
                phase_start,
                frame_damage,
                bool(
                    flags & 0x40
                    and not flags & 0x830
                    and not flags2 & 0x80
                ),
                (flags >> 20) & 0x7,
            ]
        )
    return rows


class EnemyCombatProgressTests(unittest.TestCase):
    def test_decoder_preserves_raw_signed_health_gate_and_defeat_mode(
        self,
    ) -> None:
        blob = bytearray(3 * ENEMY_STRIDE)
        _set_enemy(
            blob,
            0,
            flags=ENEMY_ACTIVE_FLAG,
            flags2=0,
            current=99,
            maximum=120,
            phase_start=110,
            frame_damage=0,
        )
        _set_enemy(
            blob,
            1,
            flags=ENEMY_ACTIVE_FLAG | 0x40 | (3 << 20),
            flags2=0,
            current=-7,
            maximum=250,
            phase_start=200,
            frame_damage=13,
        )
        _set_enemy(
            blob,
            2,
            flags=0x40,
            flags2=0,
            current=50,
            maximum=50,
            phase_start=50,
            frame_damage=4,
        )
        ticks = iter((1.0, 1.00005))
        inventory = decode_enemy_combat_progress_inventory(
            bytes(blob),
            pool_base=ENEMY_POOL_BASE,
            pool_size=3,
            enemy_stride=ENEMY_STRIDE,
            enemy_active_flag=ENEMY_ACTIVE_FLAG,
            clock=lambda: next(ticks),
        )
        self.assertEqual(inventory.scanned_slots, 3)
        self.assertEqual(inventory.active_slots, 2)
        self.assertAlmostEqual(inventory.decode_ms, 0.05)
        first, second = inventory.observations
        self.assertFalse(first.local_damage_flags_open)
        self.assertEqual(second.current_health, -7)
        self.assertEqual(second.frame_damage, 13)
        self.assertTrue(second.local_damage_flags_open)
        self.assertEqual(second.defeat_mode, 3)
        self.assertEqual(
            second.enemy_pointer,
            ENEMY_POOL_BASE + ENEMY_STRIDE,
        )

    def test_each_local_blocking_bit_closes_only_the_local_gate(self) -> None:
        variants = (
            (ENEMY_ACTIVE_FLAG | 0x40 | 0x10, 0),
            (ENEMY_ACTIVE_FLAG | 0x40 | 0x20, 0),
            (ENEMY_ACTIVE_FLAG | 0x40 | 0x800, 0),
            (ENEMY_ACTIVE_FLAG | 0x40, 0x80),
        )
        blob = bytearray(len(variants) * ENEMY_STRIDE)
        for slot, (flags, flags2) in enumerate(variants):
            _set_enemy(
                blob,
                slot,
                flags=flags,
                flags2=flags2,
                current=1,
                maximum=2,
                phase_start=2,
                frame_damage=0,
            )
        inventory = decode_enemy_combat_progress_inventory(
            bytes(blob),
            pool_base=ENEMY_POOL_BASE,
            pool_size=len(variants),
            enemy_stride=ENEMY_STRIDE,
            enemy_active_flag=ENEMY_ACTIVE_FLAG,
        )
        self.assertTrue(inventory.observations)
        self.assertTrue(
            all(
                not observation.local_damage_flags_open
                for observation in inventory.observations
            )
        )

    def test_dense_64_slot_decode_matches_independent_scalar_oracle(
        self,
    ) -> None:
        blob = bytearray(64 * ENEMY_STRIDE)
        for slot in range(64):
            flags = ENEMY_ACTIVE_FLAG | 0x40 | ((slot % 8) << 20)
            flags2 = 0
            if slot % 5 == 1:
                flags |= 0x10
            elif slot % 5 == 2:
                flags |= 0x20
            elif slot % 5 == 3:
                flags |= 0x800
            elif slot % 5 == 4:
                flags2 |= 0x80
            _set_enemy(
                blob,
                slot,
                flags=flags,
                flags2=flags2,
                current=slot - 32,
                maximum=64 + slot,
                phase_start=96 + slot,
                frame_damage=slot % 17,
            )
        inventory = decode_enemy_combat_progress_inventory(
            bytes(blob),
            pool_base=ENEMY_POOL_BASE,
            pool_size=64,
            enemy_stride=ENEMY_STRIDE,
            enemy_active_flag=ENEMY_ACTIVE_FLAG,
        )
        self.assertEqual(
            [observation.record() for observation in inventory.observations],
            _scalar_combat_rows(bytes(blob), pool_size=64),
        )

    def test_truncated_blob_fails_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires"):
            decode_enemy_combat_progress_inventory(
                b"\0" * (ENEMY_STRIDE - 1),
                pool_base=ENEMY_POOL_BASE,
                pool_size=1,
                enemy_stride=ENEMY_STRIDE,
                enemy_active_flag=ENEMY_ACTIVE_FLAG,
            )

    def test_nonfinite_or_reversed_timing_fails_loudly(self) -> None:
        decode_ticks = iter((1.0, float("nan")))
        with self.assertRaisesRegex(ValueError, "decode timing"):
            decode_enemy_combat_progress_inventory(
                b"\0" * ENEMY_STRIDE,
                pool_base=ENEMY_POOL_BASE,
                pool_size=1,
                enemy_stride=ENEMY_STRIDE,
                enemy_active_flag=ENEMY_ACTIVE_FLAG,
                clock=lambda: next(decode_ticks),
            )
        inventory = EnemyCombatProgressInventory(64, 0, (), 0.0)
        record_ticks = iter((2.0, 1.0))
        with self.assertRaisesRegex(ValueError, "record timing"):
            build_enemy_combat_progress_record(
                inventory,
                clock=lambda: next(record_ticks),
            )

    def test_record_declares_offsets_masks_and_no_lifecycle_authority(
        self,
    ) -> None:
        inventory = EnemyCombatProgressInventory(
            scanned_slots=64,
            active_slots=0,
            observations=(),
            decode_ms=0.025,
        )
        ticks = iter((2.0, 2.00001))
        record = build_enemy_combat_progress_record(
            inventory,
            clock=lambda: next(ticks),
        )
        self.assertEqual(record["layout"], ENEMY_COMBAT_PROGRESS_LAYOUT)
        self.assertEqual(record["authority"], "trace_only")
        self.assertEqual(record["generation_authority"], "none")
        self.assertEqual(record["end_reason_authority"], "none")
        self.assertEqual(
            record["damageability_authority"],
            "local_flags_only",
        )
        self.assertAlmostEqual(record["record_ms"], 0.01)

    def test_capture_option_reuses_exact_blob_and_preserves_bodies(
        self,
    ) -> None:
        blob = bytearray(2 * ENEMY_STRIDE)
        _set_enemy(
            blob,
            0,
            flags=ENEMY_ACTIVE_FLAG | 0x40,
            flags2=0,
            current=80,
            maximum=100,
            phase_start=100,
            frame_damage=2,
        )
        plain_reader = _Reader(bytes(blob))
        traced_reader = _Reader(bytes(blob))
        plain = capture_enemy_pool_prefix_contiguous(
            plain_reader,  # type: ignore[arg-type]
            pool_size=2,
        )
        traced = capture_enemy_pool_prefix_contiguous(
            traced_reader,  # type: ignore[arg-type]
            pool_size=2,
            include_combat_progress=True,
        )
        self.assertEqual(plain.bodies, traced.bodies)
        self.assertIsNone(plain.combat_progress_inventory)
        self.assertIsNotNone(traced.combat_progress_inventory)
        self.assertEqual(plain_reader.calls, traced_reader.calls)
        self.assertEqual(
            [call[0] for call in traced_reader.calls],
            ["u32", "read", "u32"],
        )

    def test_post_issue_stage_preserves_capture_identity_and_emit_policy(
        self,
    ) -> None:
        inventory = EnemyCombatProgressInventory(64, 0, (), 0.02)
        sink = _TraceSink()
        built = {
            "layout": ENEMY_COMBAT_PROGRESS_LAYOUT,
            "authority": "trace_only",
        }
        ticks = iter((3.0, 3.00002))
        result = run_enemy_combat_progress_stage(
            EnemyCombatProgressStageRequest(
                trace_sink=sink,  # type: ignore[arg-type]
                inventory=inventory,
                route_id=2,
                difficulty_index=3,
                stage_route_index=5,
                gameplay_epoch=4,
                decision_frame=900,
                frame_before=899,
                frame_after=899,
                capture_attempts=1,
            ),
            dependencies=EnemyCombatProgressStageDependencies(
                build_record=lambda observed: (
                    built
                    if observed is inventory
                    else self.fail("inventory identity changed")
                )
            ),
            clock=lambda: next(ticks),
        )
        self.assertEqual(result.record["inventory"], built)
        self.assertTrue(result.record["stable"])
        self.assertAlmostEqual(result.stage_ms, 0.02)
        self.assertEqual(result.emit_ms, 0.125)
        self.assertEqual(sink.calls[0][1:], (False, True))


if __name__ == "__main__":
    unittest.main()
