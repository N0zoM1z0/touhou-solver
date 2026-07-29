from __future__ import annotations

import unittest

from touhou_control.ordered_input_transaction_oracle import (
    OrderedInputBelief,
    OrderedInputExactState,
    advance_ordered_input_belief,
    advance_ordered_input_state,
    belief_after_issue,
    enumerate_ordered_input_histories,
    issue_ordered_input_belief,
    merge_observation_equivalent_states,
    ordered_mask_path,
)


SUPPORTED = 0xF7
FORBIDDEN = 0x02


def _settled(mask: int) -> OrderedInputBelief:
    return OrderedInputBelief.from_states((OrderedInputExactState(mask, mask),))


class OrderedInputTransactionOracleTests(unittest.TestCase):
    def test_path_releases_then_presses_in_ascending_bit_order(self) -> None:
        self.assertEqual(
            ordered_mask_path(
                0x41,
                0x84,
                supported_mask=SUPPORTED,
                forbidden_mask=FORBIDDEN,
            ),
            (0x40, 0x00, 0x04, 0x84),
        )

    def test_ce0193_exposes_ordered_partial_mask_before_final(self) -> None:
        branches = issue_ordered_input_belief(
            _settled(0x65),
            selected_mask=0x41,
            delay_support=(2,),
            supported_mask=SUPPORTED,
            forbidden_mask=FORBIDDEN,
        )

        self.assertEqual(len(branches), 1)
        issued = branches[0].successor_state
        self.assertEqual(issued.queued_masks, (0x61, 0x41))
        self.assertEqual(issued.completion_remaining, 2)

        first_groups = advance_ordered_input_belief(belief_after_issue(branches))
        self.assertEqual(
            {group.observation.active_mask for group in first_groups},
            {0x65, 0x61},
        )
        self.assertNotIn(
            0x41,
            {group.observation.active_mask for group in first_groups},
        )

        first_states = tuple(state for group in first_groups for state in group.states)
        second_states = tuple(
            successor
            for state in first_states
            for successor in advance_ordered_input_state(state)
        )
        self.assertEqual(
            {state.active_mask for state in second_states},
            {0x41},
        )
        self.assertTrue(all(state.settled for state in second_states))

    def test_single_edge_reduces_to_atomic_old_then_final(self) -> None:
        branches = issue_ordered_input_belief(
            _settled(0x41),
            selected_mask=0x40,
            delay_support=(2,),
            supported_mask=SUPPORTED,
            forbidden_mask=FORBIDDEN,
        )
        issued = branches[0].successor_state

        histories = enumerate_ordered_input_histories(
            issued,
            publication_steps=2,
        )

        self.assertEqual(len(histories), 1)
        self.assertEqual(
            histories[0].active_masks_after_publication,
            (0x41, 0x40),
        )
        self.assertTrue(histories[0].successor_state.settled)

    def test_same_held_mask_is_no_write_and_preserves_pending(self) -> None:
        pending = OrderedInputExactState(
            active_mask=0x61,
            held_desired_mask=0x41,
            queued_masks=(0x41,),
            completion_remaining=1,
        )
        belief = OrderedInputBelief.from_states((pending,))

        branches = issue_ordered_input_belief(
            belief,
            selected_mask=0x41,
            delay_support=(),
            supported_mask=SUPPORTED,
            forbidden_mask=FORBIDDEN,
        )

        self.assertEqual(len(branches), 1)
        self.assertFalse(branches[0].write_required)
        self.assertIsNone(branches[0].new_delay)
        self.assertEqual(branches[0].older_remaining, 1)
        self.assertEqual(branches[0].successor_state, pending)

    def test_overwrite_appends_after_older_unobserved_suffix(self) -> None:
        pending = OrderedInputExactState(
            active_mask=0x65,
            held_desired_mask=0x41,
            queued_masks=(0x61, 0x41),
            completion_remaining=2,
        )

        branches = issue_ordered_input_belief(
            OrderedInputBelief.from_states((pending,)),
            selected_mask=0x84,
            delay_support=(3,),
            supported_mask=SUPPORTED,
            forbidden_mask=FORBIDDEN,
        )

        self.assertEqual(len(branches), 1)
        self.assertEqual(branches[0].older_remaining, 2)
        self.assertEqual(branches[0].new_delay, 3)
        self.assertEqual(
            branches[0].successor_state.queued_masks,
            (0x61, 0x41, 0x40, 0x00, 0x04, 0x84),
        )
        self.assertEqual(
            branches[0].successor_state.completion_remaining,
            3,
        )

    def test_final_is_forbidden_early_and_forced_at_deadline(self) -> None:
        issued = issue_ordered_input_belief(
            _settled(0x41),
            selected_mask=0x84,
            delay_support=(3,),
            supported_mask=SUPPORTED,
            forbidden_mask=FORBIDDEN,
        )[0].successor_state

        first = advance_ordered_input_state(issued)
        self.assertTrue(all(state.active_mask != 0x84 for state in first))
        second = tuple(
            successor
            for state in first
            for successor in advance_ordered_input_state(state)
        )
        self.assertTrue(all(state.active_mask != 0x84 for state in second))
        third = tuple(
            successor
            for state in second
            for successor in advance_ordered_input_state(state)
        )
        self.assertEqual({state.active_mask for state in third}, {0x84})
        self.assertTrue(all(state.settled for state in third))

    def test_hidden_deadlines_merge_before_next_controller_choice(self) -> None:
        slow = OrderedInputExactState(
            active_mask=0x65,
            held_desired_mask=0x41,
            queued_masks=(0x61, 0x41),
            completion_remaining=3,
        )
        fast = OrderedInputExactState(
            active_mask=0x65,
            held_desired_mask=0x41,
            queued_masks=(0x61, 0x41),
            completion_remaining=2,
        )

        groups = merge_observation_equivalent_states((slow, fast))

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].states, (fast, slow))
        self.assertEqual(groups[0].observation.active_mask, 0x65)
        self.assertEqual(groups[0].observation.held_desired_mask, 0x41)

    def test_unsupported_and_bomb_masks_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            ordered_mask_path(
                0x01,
                0x09,
                supported_mask=SUPPORTED,
                forbidden_mask=FORBIDDEN,
            )
        with self.assertRaisesRegex(ValueError, "forbidden"):
            issue_ordered_input_belief(
                _settled(0x01),
                selected_mask=0x03,
                delay_support=(1,),
                supported_mask=SUPPORTED,
                forbidden_mask=FORBIDDEN,
            )

    def test_one_action_is_applied_uniformly_across_hidden_states(self) -> None:
        states = (
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
        belief = OrderedInputBelief.from_states(states)

        branches = issue_ordered_input_belief(
            belief,
            selected_mask=0x44,
            delay_support=(1, 2),
            supported_mask=SUPPORTED,
            forbidden_mask=FORBIDDEN,
        )

        self.assertEqual(len(branches), 4)
        self.assertEqual(
            {branch.source_state for branch in branches},
            set(states),
        )
        self.assertEqual(
            {branch.selected_mask for branch in branches},
            {0x44},
        )
        self.assertEqual(
            {branch.new_delay for branch in branches},
            {1, 2},
        )
        self.assertTrue(all(branch.write_required for branch in branches))
        self.assertTrue(
            all(branch.successor_state.held_desired_mask == 0x44 for branch in branches)
        )


if __name__ == "__main__":
    unittest.main()
