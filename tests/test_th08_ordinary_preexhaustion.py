from __future__ import annotations

import unittest

from th08_live.controller import (
    _ordinary_nonspell_preexhaustion_filter,
)
from th08_time_scale import TH08_UNIT_TIME_SCALE_BITS
from touhou_control.local_pipeline_oracle import LocalPipelineRoot


class OrdinaryNonspellPreexhaustionTests(unittest.TestCase):
    def _build(self, **overrides):
        arguments = {
            "enabled": True,
            "spell_active": False,
            "player_phase": 0,
            "predeath_counter": 0,
            "root_scale_bits": TH08_UNIT_TIME_SCALE_BITS,
            "root": LocalPipelineRoot("stay", "stay"),
            "action_hold_frames": 3,
            "player_x": 21.4,
            "player_y": 409.1,
        }
        arguments.update(overrides)
        return _ordinary_nonspell_preexhaustion_filter(**arguments)

    def test_stage4a_witness_corner_rejects_down_left(self) -> None:
        result = self._build()

        self.assertTrue(result.authority_eligible)
        self.assertTrue(result.applicable)
        self.assertIn("stay", result.allowed_actions or ())
        self.assertIn("up", result.allowed_actions or ())
        self.assertNotIn("down_left", result.allowed_actions or ())
        self.assertNotIn("down_left_fast", result.allowed_actions or ())
        self.assertEqual(result.pickup_delay_frames, (0, 1, 2, 3))

    def test_pending_pickup_uses_every_physical_order_in_lease(
        self,
    ) -> None:
        result = self._build(
            root=LocalPipelineRoot(
                active_action="down_left",
                held_desired_action="up_right",
                pending_action="up_right",
                remaining_delay_support=(1,),
            )
        )

        by_action = {action.action: action for action in result.actions}
        self.assertEqual(by_action["up_right"].branch_count, 4)
        self.assertEqual(by_action["right"].branch_count, 16)
        self.assertEqual(
            result.record()["pickup_clock_authority"],
            "every_physical_pickup_order_within_lease_including_"
            "no_pickup_not_enemy_manager_frame",
        )

    def test_spell_phase_has_no_authority(self) -> None:
        result = self._build(spell_active=True)

        self.assertFalse(result.authority_eligible)
        self.assertEqual(result.reason, "spell_active")

    def test_nonunit_root_scale_fails_closed(self) -> None:
        result = self._build(root_scale_bits=0x3F000000)

        self.assertFalse(result.authority_eligible)
        self.assertEqual(result.reason, "nonunit_root_time_scale")

    def test_player_transition_fails_closed(self) -> None:
        result = self._build(player_phase=2)

        self.assertFalse(result.authority_eligible)
        self.assertEqual(
            result.reason,
            "player_transition_or_predeath",
        )


if __name__ == "__main__":
    unittest.main()
