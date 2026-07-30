from __future__ import annotations

import unittest

from th08_enemy_end_semantics import (
    MANAGER_HP_DEFEAT_MODE0_RETIRE,
    MANAGER_OFFSCREEN_RETIRE,
    OPCODE_5F_FORCED_HP_ZERO,
    EnemyForcedHpZeroEvidence,
    EnemyRetirementEvidence,
    PlayerShotDamageTransition,
    classify_enemy_retirement,
)
from th08_future_body_identity import (
    Route2SlotLifetimeLedger,
    advance_route2_slot_lifetimes,
)


class EnemyEndSemanticsTests(unittest.TestCase):
    def test_opcode_5f_forced_zero_is_not_a_retirement(self) -> None:
        evidence = EnemyForcedHpZeroEvidence(
            physical_update=101,
            sequence=0,
            slot=7,
            source=OPCODE_5F_FORCED_HP_ZERO,
            active_before=True,
            active_after=True,
            hp_after=0,
        )

        self.assertFalse(evidence.record()["retires_lifetime"])
        self.assertFalse(evidence.record()["verified_player_shot_kill"])
        with self.assertRaisesRegex(ValueError, "preserve"):
            EnemyForcedHpZeroEvidence(
                physical_update=101,
                sequence=0,
                slot=7,
                source=OPCODE_5F_FORCED_HP_ZERO,
                active_before=True,
                active_after=False,
                hp_after=0,
            )

    def test_mode0_clear_without_damage_edge_is_not_a_verified_kill(
        self,
    ) -> None:
        result = classify_enemy_retirement(
            EnemyRetirementEvidence(
                physical_update=101,
                sequence=0,
                slot=7,
                source=MANAGER_HP_DEFEAT_MODE0_RETIRE,
                active_bit_cleared=True,
                defeat_mode=0,
                post_current_health=0,
            )
        )

        self.assertEqual(result.reason, "hp_defeat_unattributed")
        self.assertFalse(result.verified_player_shot_kill)

    def test_exact_lethal_damage_and_mode0_clear_verify_player_shot_kill(
        self,
    ) -> None:
        result = classify_enemy_retirement(
            EnemyRetirementEvidence(
                physical_update=101,
                sequence=0,
                slot=7,
                source=MANAGER_HP_DEFEAT_MODE0_RETIRE,
                active_bit_cleared=True,
                defeat_mode=0,
                post_current_health=-3,
                damage_transition=PlayerShotDamageTransition(
                    hp_before_damage=5,
                    resolved_damage=8,
                    hp_after_damage=-3,
                ),
            )
        )

        self.assertEqual(result.reason, "player_shot_lethal_damage")
        self.assertTrue(result.verified_player_shot_kill)

        root = Route2SlotLifetimeLedger.from_root_active_slots(
            root_physical_update=100,
            active_slots=(7,),
        )
        step = advance_route2_slot_lifetimes(
            root,
            next_physical_update=101,
            events=(result.lifecycle_event,),
            observed_active_slots=(),
        )
        self.assertEqual(step.retired_identities[0].slot, 7)

    def test_preceding_forced_zero_prevents_kill_promotion(self) -> None:
        result = classify_enemy_retirement(
            EnemyRetirementEvidence(
                physical_update=101,
                sequence=1,
                slot=7,
                source=MANAGER_HP_DEFEAT_MODE0_RETIRE,
                active_bit_cleared=True,
                defeat_mode=0,
                post_current_health=0,
                preceding_forced_hp_zero_source=(
                    OPCODE_5F_FORCED_HP_ZERO
                ),
            )
        )

        self.assertEqual(result.reason, "forced_hp_zero_defeat")
        self.assertFalse(result.verified_player_shot_kill)

    def test_offscreen_control_edge_is_an_exact_nonkill_retirement(
        self,
    ) -> None:
        result = classify_enemy_retirement(
            EnemyRetirementEvidence(
                physical_update=101,
                sequence=0,
                slot=7,
                source=MANAGER_OFFSCREEN_RETIRE,
                active_bit_cleared=True,
            )
        )

        self.assertEqual(result.reason, "offscreen_cull")
        self.assertEqual(
            result.reason_authority,
            "observed_native_control_edge",
        )
        self.assertFalse(result.verified_player_shot_kill)

    def test_contradictory_damage_arithmetic_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "arithmetic"):
            PlayerShotDamageTransition(
                hp_before_damage=5,
                resolved_damage=8,
                hp_after_damage=0,
            )


if __name__ == "__main__":
    unittest.main()
