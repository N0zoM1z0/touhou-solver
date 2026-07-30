from __future__ import annotations

import struct
import unittest
from types import SimpleNamespace

from th08_live.enemy_sensor import (
    ENEMY_FLAGS_OFFSET,
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
)
from th08_runtime.game_state import (
    ADDR_PLAYER,
    ADDR_SPELL_CARD_STATE,
    PLAYER_BOMB_ACTIVE_OFFSET,
    PLAYER_DAMAGE_TIMER_OFFSET,
    PLAYER_SHOT_POOL_OFFSET,
    PLAYER_SHOT_SLOT_ANGLE_OFFSET,
    PLAYER_SHOT_SLOT_DAMAGE_OFFSET,
    PLAYER_SHOT_SLOT_FOCUS_OFFSET,
    PLAYER_SHOT_SLOT_HITBOX_OFFSET,
    PLAYER_SHOT_SLOT_HIT_CALLBACK_OFFSET,
    PLAYER_SHOT_SLOT_POSITION_OFFSET,
    PLAYER_SHOT_SLOT_SOURCE_RECORD_OFFSET,
    PLAYER_SHOT_SLOT_SPEED_OFFSET,
    PLAYER_SHOT_SLOT_STRIDE,
    PLAYER_SHOT_SLOT_TIMER_OFFSET,
    PLAYER_SHOT_SLOT_UPDATE_CALLBACK_OFFSET,
    PLAYER_SHOT_SLOT_VELOCITY_OFFSET,
    PLAYER_SHOT_TIMER_OFFSET,
    SPELL_STATE_CAPTURE_SIZE,
)
from th08_runtime.native_combat_projection import (
    ENEMY_ALTERNATE_HITBOX_OFFSET,
    ENEMY_DAMAGE_HITBOX_OFFSET,
    ENEMY_FLAGS2_OFFSET,
    ENEMY_FRAME_DAMAGE_OFFSET,
    ENEMY_HITPOINTS_OFFSET,
    ENEMY_MAIN_VM_OFFSET,
    ENEMY_MAIN_VM_TIMER_CURRENT_OFFSET,
    ENEMY_POSITION_OFFSET,
    NATIVE_COMBAT_PROJECTION_SCHEMA,
    PLAYER_SHOT_COMBAT_STATE_SCHEMA,
    PLAYER_SHOT_POOL_BYTES,
    capture_native_combat_projection,
    capture_player_shot_combat_state,
    decode_player_shot_pool,
)


def _install_shot(
    pool: bytearray,
    slot: int,
    *,
    state: int = 1,
    shot_type: int = 0,
    damage: int = 20,
    hit_callback: int = 0,
) -> None:
    base = slot * PLAYER_SHOT_SLOT_STRIDE
    struct.pack_into(
        "<ff",
        pool,
        base + PLAYER_SHOT_SLOT_POSITION_OFFSET,
        100.0,
        50.0,
    )
    struct.pack_into(
        "<ff",
        pool,
        base + PLAYER_SHOT_SLOT_HITBOX_OFFSET,
        8.0,
        8.0,
    )
    struct.pack_into(
        "<ff",
        pool,
        base + PLAYER_SHOT_SLOT_VELOCITY_OFFSET,
        0.0,
        -12.0,
    )
    struct.pack_into(
        "<f",
        pool,
        base + PLAYER_SHOT_SLOT_SPEED_OFFSET,
        12.0,
    )
    struct.pack_into(
        "<f",
        pool,
        base + PLAYER_SHOT_SLOT_ANGLE_OFFSET,
        -1.5707964,
    )
    struct.pack_into(
        "<iIi",
        pool,
        base + PLAYER_SHOT_SLOT_TIMER_OFFSET,
        3,
        0x3F000000,
        4,
    )
    struct.pack_into(
        "<hhh",
        pool,
        base + PLAYER_SHOT_SLOT_DAMAGE_OFFSET,
        damage,
        state,
        shot_type,
    )
    pool[base + PLAYER_SHOT_SLOT_FOCUS_OFFSET] = 1
    struct.pack_into(
        "<I",
        pool,
        base + PLAYER_SHOT_SLOT_UPDATE_CALLBACK_OFFSET,
        0,
    )
    struct.pack_into(
        "<I",
        pool,
        base + PLAYER_SHOT_SLOT_HIT_CALLBACK_OFFSET,
        hit_callback,
    )
    struct.pack_into(
        "<I",
        pool,
        base + PLAYER_SHOT_SLOT_SOURCE_RECORD_OFFSET,
        0x00610000 + slot * 0x38,
    )


def _native_root(enemy_component: bytes) -> object:
    return SimpleNamespace(
        components=(
            SimpleNamespace(
                spec=SimpleNamespace(
                    name="ordinary_enemy_template_and_pool",
                    address=ENEMY_POOL_BASE - ENEMY_STRIDE,
                ),
                data=enemy_component,
            ),
        )
    )


class _Reader:
    def __init__(
        self,
        *,
        pool: bytes,
        emission_timer: bytes,
        damage_timer: bytes,
        spell: bytes,
        player_context: bytes,
    ) -> None:
        self._memory = {
            (ADDR_PLAYER + PLAYER_SHOT_POOL_OFFSET, len(pool)): pool,
            (
                ADDR_PLAYER + PLAYER_SHOT_TIMER_OFFSET,
                len(emission_timer),
            ): emission_timer,
            (
                ADDR_PLAYER + PLAYER_DAMAGE_TIMER_OFFSET,
                len(damage_timer),
            ): damage_timer,
            (ADDR_SPELL_CARD_STATE, len(spell)): spell,
            (ADDR_PLAYER, len(player_context)): player_context,
        }

    def read(self, address: int, size: int) -> bytes:
        try:
            return self._memory[(address, size)]
        except KeyError as exc:
            raise AssertionError(f"unexpected read {address:#x}/{size:#x}") from exc


class NativeCombatProjectionTests(unittest.TestCase):
    def test_full_player_shot_pool_retains_causal_and_decoded_identity(
        self,
    ) -> None:
        pool = bytearray(PLAYER_SHOT_POOL_BYTES)
        _install_shot(pool, 7, state=2, shot_type=3, damage=11)
        state = capture_player_shot_combat_state(
            _Reader(
                pool=bytes(pool),
                emission_timer=struct.pack("<iIi", 4, 0, 5),
                damage_timer=struct.pack("<iIi", 8, 0x3F000000, 9),
                spell=bytes(SPELL_STATE_CAPTURE_SIZE),
                player_context=bytes(PLAYER_BOMB_ACTIVE_OFFSET + 4),
            )
        )

        self.assertTrue(state.emission_timer.integer_changed)
        self.assertTrue(state.damage_timer.integer_changed)
        self.assertEqual(state.occupied_slot_indices, (7,))
        self.assertEqual(state.damage_eligible_slot_indices, (7,))
        slot = state.slots[0]
        self.assertEqual(slot.damage, 11)
        self.assertEqual(slot.shot_type, 3)
        self.assertEqual(slot.focus_logic_at_birth, 1)
        self.assertEqual(slot.source_record_pointer, 0x00610000 + 7 * 0x38)
        record = state.record()
        self.assertEqual(record["schema"], PLAYER_SHOT_COMBAT_STATE_SCHEMA)
        self.assertEqual(record["pool"]["occupied_count"], 1)
        self.assertEqual(len(record["pool"]["sha256"]), 64)
        self.assertEqual(len(record["pool"]["active_slots"][0]["raw_sha256"]), 64)

    def test_inactive_stale_bytes_change_pool_identity_without_inventing_shot(
        self,
    ) -> None:
        left = bytearray(PLAYER_SHOT_POOL_BYTES)
        right = bytearray(left)
        right[PLAYER_SHOT_SLOT_STRIDE + 17] = 1

        left_slots = decode_player_shot_pool(bytes(left))
        right_slots = decode_player_shot_pool(bytes(right))

        self.assertEqual(left_slots, ())
        self.assertEqual(right_slots, ())
        self.assertNotEqual(bytes(left), bytes(right))

    def test_projection_exposes_supported_and_unresolved_native_passes(
        self,
    ) -> None:
        pool = bytearray(PLAYER_SHOT_POOL_BYTES)
        _install_shot(pool, 0, damage=20)
        _install_shot(pool, 1, state=2, shot_type=3, damage=10)
        _install_shot(pool, 2, shot_type=4, damage=7)
        _install_shot(pool, 3, damage=9, hit_callback=0x00450100)

        enemy_component = bytearray((ENEMY_POOL_SIZE + 1) * ENEMY_STRIDE)
        base = ENEMY_STRIDE
        struct.pack_into("<I", enemy_component, base + ENEMY_FLAGS_OFFSET, 0x49)
        struct.pack_into("<I", enemy_component, base + ENEMY_FLAGS2_OFFSET, 0)
        struct.pack_into(
            "<ff",
            enemy_component,
            base + ENEMY_POSITION_OFFSET,
            100.0,
            50.0,
        )
        struct.pack_into(
            "<ff",
            enemy_component,
            base + ENEMY_DAMAGE_HITBOX_OFFSET,
            24.0,
            16.0,
        )
        struct.pack_into(
            "<ff",
            enemy_component,
            base + ENEMY_ALTERNATE_HITBOX_OFFSET,
            12.0,
            12.0,
        )
        struct.pack_into(
            "<iii",
            enemy_component,
            base + ENEMY_HITPOINTS_OFFSET,
            100,
            120,
            0,
        )
        struct.pack_into(
            "<i",
            enemy_component,
            base + ENEMY_FRAME_DAMAGE_OFFSET,
            0,
        )
        struct.pack_into(
            "<I",
            enemy_component,
            base + ENEMY_MAIN_VM_OFFSET,
            0x00600000,
        )
        struct.pack_into(
            "<i",
            enemy_component,
            base + ENEMY_MAIN_VM_TIMER_CURRENT_OFFSET,
            77,
        )

        spell = bytearray(SPELL_STATE_CAPTURE_SIZE)
        player_context = bytearray(PLAYER_BOMB_ACTIVE_OFFSET + 4)
        projection = capture_native_combat_projection(
            _Reader(
                pool=bytes(pool),
                emission_timer=struct.pack("<iIi", 4, 0, 5),
                damage_timer=struct.pack("<iIi", 8, 0, 9),
                spell=bytes(spell),
                player_context=bytes(player_context),
            ),
            native_root_projection=_native_root(bytes(enemy_component)),
            compact_state={
                "manager_frame": 100,
                "input_current": 0x05,
                "focus_logic": 1,
            },
        )

        self.assertEqual(projection.record()["schema"], NATIVE_COMBAT_PROJECTION_SCHEMA)
        self.assertEqual(projection.summary["active_shot_count"], 4)
        self.assertEqual(projection.summary["damage_eligible_shot_count"], 4)
        self.assertEqual(projection.summary["active_enemy_target_count"], 1)
        self.assertEqual(projection.summary["open_hp_gate_target_count"], 1)
        self.assertEqual(projection.summary["positive_hp_sum"], 100)
        self.assertEqual(
            projection.summary["supported_primary_contribution_sum"],
            30,
        )
        self.assertEqual(
            projection.summary[
                "open_gate_supported_primary_contribution_sum"
            ],
            30,
        )
        self.assertEqual(
            projection.summary["supported_alternate_contribution_sum"],
            10,
        )
        self.assertEqual(
            projection.summary["supported_primary_overlap_target_count"],
            1,
        )
        self.assertEqual(projection.summary["unresolved_overlap_target_count"], 1)
        target = projection.payload["enemy_targets"][0]
        self.assertEqual(target["hitpoints"], 100)
        self.assertTrue(target["alternate_hitbox"]["enabled"])
        self.assertTrue(target["damage_gate"]["hp_subtraction_open"])
        primary = target["ordinary_shot_passes"]["primary"]
        alternate = target["ordinary_shot_passes"]["alternate"]
        self.assertEqual(primary["supported_hit_slots"], [0, 1])
        self.assertEqual(primary["supported_contribution_after_cap"], 30)
        self.assertEqual(primary["type45_mode_dependent_overlap_slots"], [2])
        self.assertEqual(primary["callback_dependent_overlap_slots"], [3])
        self.assertEqual(alternate["supported_hit_slots"], [1])
        self.assertEqual(alternate["supported_contribution_after_cap"], 10)

    def test_nonfinite_active_shot_fails_closed(self) -> None:
        pool = bytearray(PLAYER_SHOT_POOL_BYTES)
        _install_shot(pool, 0)
        struct.pack_into(
            "<f",
            pool,
            PLAYER_SHOT_SLOT_POSITION_OFFSET,
            float("nan"),
        )

        with self.assertRaisesRegex(ValueError, "not finite"):
            decode_player_shot_pool(bytes(pool))


if __name__ == "__main__":
    unittest.main()
