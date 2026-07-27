from __future__ import annotations

import unittest

from th08_corridor_adapter import TH08_VIABILITY_ACTIONS
from th08_movement_model import INPUT_BOMB
from th08_pipeline_actions import (
    TH08_COMPLETE_MASK_ACTION_SPACE,
    th08_complete_mask_token,
)


class Th08CompleteMaskActionTests(unittest.TestCase):
    def test_action_space_is_complete_injective_and_no_bomb(self) -> None:
        space = TH08_COMPLETE_MASK_ACTION_SPACE

        self.assertEqual(len(space.actions), 36)
        self.assertEqual(len({action.token for action in space.actions}), 36)
        self.assertEqual(
            len({action.complete_mask for action in space.actions}),
            36,
        )
        self.assertTrue(
            all(not action.complete_mask & INPUT_BOMB for action in space.actions)
        )
        for action in space.actions:
            self.assertEqual(
                space.mask_for_token(
                    space.token_for_mask(action.complete_mask)
                ),
                action.complete_mask,
            )

    def test_ce_0134_distinguishes_complete_write_with_same_velocity(self) -> None:
        space = TH08_COMPLETE_MASK_ACTION_SPACE
        active = space.action_for_mask(0x05)
        held_pending = space.action_for_mask(0x85)
        selected = space.action_for_mask(0x84)

        self.assertNotEqual(active.token, held_pending.token)
        self.assertNotEqual(held_pending.token, selected.token)
        self.assertEqual(
            (held_pending.velocity_x, held_pending.velocity_y),
            (selected.velocity_x, selected.velocity_y),
        )
        self.assertFalse(
            space.is_no_write(
                held_mask=held_pending.complete_mask,
                selected_token=selected.token,
            )
        )

    def test_movement_projection_matches_existing_viability_actions(self) -> None:
        projected = {
            action.movement_label: (action.velocity_x, action.velocity_y)
            for action in TH08_COMPLETE_MASK_ACTION_SPACE.actions
            if action.movement_label != "stay_unfocused"
        }

        self.assertEqual(
            projected,
            {
                action.name: (action.velocity_x, action.velocity_y)
                for action in TH08_VIABILITY_ACTIONS
            },
        )

    def test_rejects_bomb_and_noncanonical_direction_masks(self) -> None:
        with self.assertRaisesRegex(ValueError, "Bomb"):
            th08_complete_mask_token(0x02)
        with self.assertRaisesRegex(ValueError, "outside the action alphabet"):
            th08_complete_mask_token(0xC0)


if __name__ == "__main__":
    unittest.main()
