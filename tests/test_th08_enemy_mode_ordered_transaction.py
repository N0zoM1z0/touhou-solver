from __future__ import annotations

import unittest

from th08_enemy_mode import (
    merge_route2_ordered_mode_decision_observation_classes,
    project_route2_ordered_mode_decision_branches,
)
from touhou_control.ordered_input_transaction_oracle import (
    OrderedInputBelief,
    OrderedInputExactState,
)


SUPPORTED = 0xF7
ACTION_MASKS = {
    "shot": 0x01,
    "focus_shot": 0x05,
    "left_down_focus_shot": 0x65,
    "left_down_shot": 0x61,
    "left_shot": 0x41,
}


def _settled(mask: int) -> OrderedInputBelief:
    return OrderedInputBelief.from_states((OrderedInputExactState(mask, mask),))


class OrderedEnemyModeDecisionTests(unittest.TestCase):
    def test_priority9_consumes_current_before_priority17_publication(self) -> None:
        branches = project_route2_ordered_mode_decision_branches(
            input_belief=_settled(0x01),
            selected_action="focus_shot",
            action_masks=ACTION_MASKS,
            supported_mask=SUPPORTED,
            delay_frames=(1,),
            decision_frame_support=(1,),
            initial_mode_state=(0, False, 4),
            enemy_flag_frames=((),),
        )

        self.assertEqual(len(branches), 1)
        branch = branches[0]
        self.assertEqual(branch.hazard_branch.frames[0].active_mask, 0x01)
        self.assertEqual(
            branch.hazard_branch.frames[0].mode_state_after,
            (0, False, 5),
        )
        self.assertEqual(branch.successor_input_state.active_mask, 0x05)

    def test_ce0193_partial_mask_changes_next_priority9_mode_state(self) -> None:
        branches = project_route2_ordered_mode_decision_branches(
            input_belief=_settled(0x65),
            selected_action="left_shot",
            action_masks=ACTION_MASKS,
            supported_mask=SUPPORTED,
            delay_frames=(2,),
            decision_frame_support=(2,),
            initial_mode_state=(0, False, 4),
            enemy_flag_frames=((), ()),
        )

        self.assertEqual(len(branches), 2)
        self.assertEqual(
            {
                tuple(frame.active_mask for frame in branch.hazard_branch.frames)
                for branch in branches
            },
            {(0x65, 0x65), (0x65, 0x61)},
        )
        self.assertEqual(
            {branch.successor_input_state.active_mask for branch in branches},
            {0x41},
        )
        self.assertEqual(
            {branch.successor_mode_state for branch in branches},
            {(1, False, 1), (0, False, 0)},
        )

        classes = merge_route2_ordered_mode_decision_observation_classes(
            branches,
            base_observation=lambda _branch, _frame: "same_base",
        )
        self.assertEqual(len(classes), 2)
        self.assertEqual(
            {mode_class.key.active_mask for mode_class in classes},
            {0x41},
        )
        self.assertEqual(
            {mode_class.key.mode_state for mode_class in classes},
            {(1, False, 1), (0, False, 0)},
        )

    def test_no_write_preserves_hidden_ordered_queue_and_deadline(self) -> None:
        input_belief = OrderedInputBelief.from_states(
            (
                OrderedInputExactState(
                    active_mask=0x65,
                    held_desired_mask=0x41,
                    queued_masks=(0x61, 0x41),
                    completion_remaining=2,
                ),
                OrderedInputExactState(
                    active_mask=0x65,
                    held_desired_mask=0x41,
                    queued_masks=(0x61, 0x41),
                    completion_remaining=3,
                ),
            )
        )

        branches = project_route2_ordered_mode_decision_branches(
            input_belief=input_belief,
            selected_action="left_shot",
            action_masks=ACTION_MASKS,
            supported_mask=SUPPORTED,
            delay_frames=(),
            decision_frame_support=(1,),
            initial_mode_state=(0, False, 0),
            enemy_flag_frames=((),),
        )

        self.assertEqual(len(branches), 4)
        self.assertTrue(
            all(
                not branch.hazard_branch.issue_branch.write_required
                for branch in branches
            )
        )
        self.assertTrue(
            all(
                branch.hazard_branch.issue_branch.new_delay is None
                for branch in branches
            )
        )
        unchanged = tuple(
            branch
            for branch in branches
            if branch.successor_input_state.active_mask == 0x65
        )
        self.assertEqual(len(unchanged), 2)
        classes = merge_route2_ordered_mode_decision_observation_classes(
            unchanged,
            base_observation=lambda _branch, _frame: "same_base",
        )
        self.assertEqual(len(classes), 1)
        self.assertEqual(
            {
                state.completion_remaining
                for state in classes[0].successor_input_belief.states
            },
            {1, 2},
        )

    def test_missing_intermediate_action_identity_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "without action identities"):
            project_route2_ordered_mode_decision_branches(
                input_belief=_settled(0x65),
                selected_action="left_shot",
                action_masks={
                    "left_down_focus_shot": 0x65,
                    "left_shot": 0x41,
                },
                supported_mask=SUPPORTED,
                delay_frames=(2,),
                decision_frame_support=(1,),
                initial_mode_state=(0, False, 0),
                enemy_flag_frames=((),),
            )


if __name__ == "__main__":
    unittest.main()
