from __future__ import annotations

import unittest

from th08_enemy_damage_model import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_BOMB_DAMAGE_IMMUNITY_FLAG,
    ENEMY_FLAGS2_UPDATE_BLOCKED,
    ENEMY_HP_SUBTRACTION_FLAG,
    ENEMY_PAUSE_DURING_BOMB_OR_TRANSITION_FLAG,
    ENEMY_PLAYER_SHOT_DAMAGE_FLAG,
    EnemyPlayerShotDamageContext,
    EnemyResolvedDamageContext,
    evaluate_enemy_player_shot_damage_gate,
    resolve_enemy_hp_damage,
)


_OPEN_FLAGS = (
    ENEMY_ACTIVE_FLAG
    | ENEMY_HP_SUBTRACTION_FLAG
    | ENEMY_PLAYER_SHOT_DAMAGE_FLAG
)


def _gate(
    *,
    flags: int = _OPEN_FLAGS,
    flags2: int = 0,
    bomb_active: bool = False,
    player_transition_state: int = 0,
    damage_tick_due: bool = True,
    spell_active: bool = False,
    active_spell_owner: bool = False,
):
    return evaluate_enemy_player_shot_damage_gate(
        EnemyPlayerShotDamageContext(
            flags=flags,
            flags2=flags2,
            bomb_active=bomb_active,
            player_transition_state=player_transition_state,
            damage_tick_due=damage_tick_due,
            spell_active=spell_active,
            active_spell_owner=active_spell_owner,
        )
    )


class EnemyDamageModelTests(unittest.TestCase):
    def test_resolved_damage_bonus_alternate_and_frame_cap(self) -> None:
        result = resolve_enemy_hp_damage(
            EnemyResolvedDamageContext(
                primary_return_damage=60,
                alternate_return_damage=34,
                alternate_enabled=True,
                route_id=0,
                player_damage_bonus_active=True,
            )
        )
        self.assertEqual(result.primary_after_player_bonus, 63)
        self.assertEqual(result.alternate_after_player_bonus, 36)
        self.assertEqual(result.after_alternate_combination, 84)
        self.assertEqual(result.after_frame_cap, 70)
        self.assertEqual(result.hp_damage, 70)

    def test_bomb_overlap_skips_alternate_and_selects_special_path(self) -> None:
        blocked = resolve_enemy_hp_damage(
            EnemyResolvedDamageContext(
                primary_return_damage=20,
                alternate_return_damage=70,
                alternate_enabled=True,
                bomb_region_overlap=True,
                special_enemy_damage_mode_active=True,
            )
        )
        self.assertEqual(blocked.after_alternate_combination, 20)
        self.assertEqual(blocked.hp_damage, 0)
        self.assertEqual(blocked.blocked_reason, "bomb_region_damage_blocked")

        allowed = resolve_enemy_hp_damage(
            EnemyResolvedDamageContext(
                primary_return_damage=20,
                bomb_region_overlap=True,
                special_enemy_damage_mode_active=True,
                bomb_region_damage_allowed=True,
            )
        )
        self.assertEqual(allowed.hp_damage, 8)

    def test_special_and_post_timer_integer_reductions(self) -> None:
        special = resolve_enemy_hp_damage(
            EnemyResolvedDamageContext(
                primary_return_damage=70,
                special_enemy_damage_mode_active=True,
            )
        )
        self.assertEqual(special.hp_damage, 10)

        timer = resolve_enemy_hp_damage(
            EnemyResolvedDamageContext(
                primary_return_damage=70,
                post_damage_timer_active=True,
                post_damage_timer_reduction_enabled=True,
            )
        )
        self.assertEqual(timer.hp_damage, 7)

        blocked = resolve_enemy_hp_damage(
            EnemyResolvedDamageContext(
                primary_return_damage=70,
                post_damage_timer_active=True,
            )
        )
        self.assertEqual(blocked.hp_damage, 0)
        self.assertEqual(
            blocked.blocked_reason,
            "post_damage_timer_blocks_damage",
        )

    def test_complete_native_gate_opens_only_with_hp_write_flag(self) -> None:
        gate = _gate()
        self.assertTrue(gate.manager_update_open)
        self.assertTrue(gate.damage_block_open)
        self.assertTrue(gate.shot_collision_open)
        self.assertTrue(gate.hp_subtraction_open)
        self.assertEqual(gate.blocked_reasons, ())

        gate = _gate(flags=_OPEN_FLAGS & ~ENEMY_HP_SUBTRACTION_FLAG)
        self.assertTrue(gate.shot_collision_open)
        self.assertFalse(gate.hp_subtraction_open)
        self.assertIn("hp_subtraction_disabled", gate.blocked_reasons)

    def test_flags2_and_local_blockers_are_distinct(self) -> None:
        flags2 = _gate(flags2=ENEMY_FLAGS2_UPDATE_BLOCKED)
        self.assertFalse(flags2.manager_update_open)
        self.assertIn("flags2_update_blocked", flags2.blocked_reasons)

        for blocker in (0x10, 0x20, 0x800):
            with self.subTest(blocker=blocker):
                gate = _gate(flags=_OPEN_FLAGS | blocker)
                self.assertTrue(gate.manager_update_open)
                self.assertFalse(gate.damage_block_open)
                self.assertIn(
                    f"damage_blocking_flags_{blocker:#x}",
                    gate.blocked_reasons,
                )

    def test_pause_flag_conditions_on_bomb_or_player_transition(self) -> None:
        flags = _OPEN_FLAGS | ENEMY_PAUSE_DURING_BOMB_OR_TRANSITION_FLAG
        self.assertTrue(_gate(flags=flags).hp_subtraction_open)

        bomb = _gate(flags=flags, bomb_active=True)
        self.assertFalse(bomb.manager_update_open)
        self.assertIn("pause_during_bomb", bomb.blocked_reasons)

        transition = _gate(flags=flags, player_transition_state=3)
        self.assertFalse(transition.manager_update_open)
        self.assertIn(
            "pause_during_player_transition",
            transition.blocked_reasons,
        )

    def test_bomb_immunity_is_narrower_than_update_pause(self) -> None:
        flags = _OPEN_FLAGS | ENEMY_BOMB_DAMAGE_IMMUNITY_FLAG
        self.assertTrue(_gate(flags=flags).hp_subtraction_open)
        bomb = _gate(flags=flags, bomb_active=True)
        self.assertTrue(bomb.manager_update_open)
        self.assertFalse(bomb.damage_block_open)
        self.assertIn("bomb_damage_immunity", bomb.blocked_reasons)

    def test_damage_tick_and_shot_flag_gate_collision_before_hp(self) -> None:
        tick = _gate(damage_tick_due=False)
        self.assertTrue(tick.damage_block_open)
        self.assertFalse(tick.shot_collision_open)
        self.assertIn("player_damage_tick_not_due", tick.blocked_reasons)

        disabled = _gate(flags=_OPEN_FLAGS & ~ENEMY_PLAYER_SHOT_DAMAGE_FLAG)
        self.assertFalse(disabled.shot_collision_open)
        self.assertIn("player_shot_damage_disabled", disabled.blocked_reasons)

    def test_active_spell_owner_has_separate_bomb_block(self) -> None:
        non_owner = _gate(
            bomb_active=True,
            spell_active=True,
            active_spell_owner=False,
        )
        self.assertTrue(non_owner.hp_subtraction_open)

        owner = _gate(
            bomb_active=True,
            spell_active=True,
            active_spell_owner=True,
        )
        self.assertTrue(owner.damage_block_open)
        self.assertFalse(owner.shot_collision_open)
        self.assertIn(
            "active_spell_owner_bomb_block",
            owner.blocked_reasons,
        )

    def test_inactive_enemy_retains_all_applicable_fail_closed_reasons(
        self,
    ) -> None:
        gate = _gate(flags=0)
        self.assertFalse(gate.hp_subtraction_open)
        self.assertIn("enemy_inactive", gate.blocked_reasons)
        self.assertIn("player_shot_damage_disabled", gate.blocked_reasons)
        self.assertIn("hp_subtraction_disabled", gate.blocked_reasons)

    def test_context_rejects_inconsistent_spell_owner(self) -> None:
        with self.assertRaisesRegex(ValueError, "active spell"):
            EnemyPlayerShotDamageContext(
                flags=_OPEN_FLAGS,
                flags2=0,
                bomb_active=False,
                player_transition_state=0,
                spell_active=False,
                active_spell_owner=True,
            )


if __name__ == "__main__":
    unittest.main()
