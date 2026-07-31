from __future__ import annotations

import unittest

from touhou_control.local_pipeline_oracle import LocalPipelineRoot
from touhou_control.preexhaustion import (
    build_causal_preexhaustion_filter,
)


BOUNDS = (8.0, 376.0, 16.0, 432.0)
VELOCITIES = {
    "stay": (0.0, 0.0),
    "left": (-2.3, 0.0),
    "right": (2.3, 0.0),
    "up": (0.0, -2.3),
    "down": (0.0, 2.3),
    "up_right": (1.626, -1.626),
    "down_left": (-1.626, 1.626),
    "up_right_fast": (2.828, -2.828),
    "down_left_fast": (-2.828, 2.828),
}
ACTIONS = tuple(VELOCITIES)


class CausalPreexhaustionFilterTests(unittest.TestCase):
    def _build(self, **overrides):
        arguments = {
            "enabled": True,
            "root": LocalPipelineRoot("stay", "stay"),
            "selected_actions": ACTIONS,
            "action_velocities": VELOCITIES,
            "delay_frames": (2, 3, 4),
            "action_hold_frames": 3,
            "start_x": 21.0,
            "start_y": 409.0,
            "bounds": BOUNDS,
            "player_radius": 2.0,
            "hostile_birth_uncertainty_frames": 3,
            "movement_scale_bounds": (0.0, 1.0),
        }
        arguments.update(overrides)
        return build_causal_preexhaustion_filter(**arguments)

    def test_near_corner_excludes_actions_that_spend_control_reserve(self):
        result = self._build()

        self.assertTrue(result.authority_eligible)
        self.assertTrue(result.applicable)
        self.assertIn("stay", result.allowed_actions or ())
        self.assertIn("up", result.allowed_actions or ())
        self.assertIn("right", result.allowed_actions or ())
        self.assertNotIn("left", result.allowed_actions or ())
        self.assertNotIn("down", result.allowed_actions or ())
        self.assertNotIn("down_left", result.allowed_actions or ())
        self.assertNotIn("down_left_fast", result.allowed_actions or ())

    def test_interior_state_does_not_constrain_actions(self):
        result = self._build(start_x=192.0, start_y=300.0)

        self.assertTrue(result.authority_eligible)
        self.assertFalse(result.applicable)
        self.assertIsNone(result.allowed_actions)
        self.assertEqual(result.reason, "interior_reserve_sufficient")

    def test_hostile_birth_uncertainty_activates_one_lease_earlier(self):
        without_birth_reserve = self._build(
            start_x=38.0,
            start_y=300.0,
            hostile_birth_uncertainty_frames=0,
        )
        with_birth_reserve = self._build(
            start_x=38.0,
            start_y=300.0,
            hostile_birth_uncertainty_frames=3,
        )

        self.assertFalse(without_birth_reserve.applicable)
        self.assertTrue(with_birth_reserve.applicable)
        self.assertEqual(
            with_birth_reserve.record()["hazard_authority"],
            "none_reaction_reserve_only_no_future_birth_geometry_claim",
        )

    def test_pending_root_enumerates_old_and_new_pickup_uncertainty(self):
        result = self._build(
            root=LocalPipelineRoot(
                active_action="down_left",
                held_desired_action="up_right",
                pending_action="up_right",
                remaining_delay_support=(1, 2),
            )
        )

        by_action = {action.action: action for action in result.actions}
        self.assertEqual(by_action["up_right"].branch_count, 2)
        self.assertEqual(by_action["right"].branch_count, 6)
        self.assertNotIn("down_left", result.allowed_actions or ())

    def test_pending_motion_cannot_hide_an_intermediate_reserve_loss(self):
        result = self._build(
            root=LocalPipelineRoot(
                active_action="left",
                held_desired_action="right",
                pending_action="right",
                remaining_delay_support=(2,),
            ),
            delay_frames=(2,),
        )

        self.assertEqual(
            result.reason,
            "pending_motion_forces_reserve_loss_choose_maximum",
        )
        by_action = {action.action: action for action in result.actions}
        self.assertLess(
            max(
                by_action[action].worst_lease_reserve
                for action in result.allowed_actions or ()
            ),
            result.current_reserve,
        )

    def test_missing_pipeline_root_fails_closed_without_authority(self):
        result = self._build(root=None)

        self.assertFalse(result.authority_eligible)
        self.assertFalse(result.applicable)
        self.assertIsNone(result.allowed_actions)
        self.assertEqual(result.reason, "pipeline_root_unavailable")

    def test_disabled_filter_has_no_action_authority(self):
        result = self._build(enabled=False)

        self.assertFalse(result.enabled)
        self.assertFalse(result.authority_eligible)
        self.assertIsNone(result.allowed_actions)


if __name__ == "__main__":
    unittest.main()
