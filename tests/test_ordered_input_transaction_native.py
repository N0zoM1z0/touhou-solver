from __future__ import annotations

import unittest

from touhou_control.native.ordered_input import (
    async_ordered_input_native_available,
    issue_ordered_input_state_asynchronously_native,
)
from touhou_control.ordered_input_transaction_oracle import (
    OrderedInputBelief,
    OrderedInputExactState,
    issue_ordered_input_belief_asynchronously,
    ordered_mask_path,
)


SUPPORTED = 0xF7
FORBIDDEN = 0x02


def _signature(branch) -> tuple:
    return (
        branch.selected_mask,
        branch.write_required,
        branch.older_remaining,
        branch.new_delay,
        branch.active_masks_consumed_during_dispatch,
        branch.publications_during_dispatch,
        branch.successor_state,
    )


class NativeAsyncOrderedInputDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not async_ordered_input_native_available():
            raise unittest.SkipTest(
                "native asynchronous ordered-input differential is unavailable"
            )

    def assert_parity(
        self,
        state: OrderedInputExactState,
        *,
        selected_mask: int,
        delays: tuple[int, ...] = (1, 2),
        callback_counts: tuple[int, ...] = (0, 1, 2),
    ) -> None:
        scalar = issue_ordered_input_belief_asynchronously(
            OrderedInputBelief.from_states((state,)),
            selected_mask=selected_mask,
            post_dispatch_delay_support=delays,
            dispatch_callback_count_support=callback_counts,
            supported_mask=SUPPORTED,
            forbidden_mask=FORBIDDEN,
        )
        native = issue_ordered_input_state_asynchronously_native(
            state,
            selected_mask=selected_mask,
            post_dispatch_delay_support=delays,
            dispatch_callback_count_support=callback_counts,
            supported_mask=SUPPORTED,
            forbidden_mask=FORBIDDEN,
        )
        self.assertEqual(
            {_signature(branch) for branch in native},
            {_signature(branch) for branch in scalar},
        )
        self.assertEqual(len(native), len(scalar))

    def test_named_adversarial_histories_match_scalar(self) -> None:
        cases = (
            (OrderedInputExactState(0x65, 0x65), 0x41),
            (OrderedInputExactState(0x41, 0x41), 0x45),
            (OrderedInputExactState(0x84, 0x84), 0x41),
            (OrderedInputExactState(0x41, 0x41), 0x84),
            (
                OrderedInputExactState(
                    active_mask=0x65,
                    held_desired_mask=0x41,
                    queued_masks=(0x61, 0x41),
                    completion_remaining=2,
                ),
                0x84,
            ),
            (
                OrderedInputExactState(
                    active_mask=0x05,
                    held_desired_mask=0x04,
                    queued_masks=(0x04,),
                    completion_remaining=2,
                ),
                0x05,
            ),
        )
        for state, selected in cases:
            with self.subTest(state=state, selected=selected):
                self.assert_parity(state, selected_mask=selected)

    def test_complete_mask_no_write_preserves_pending_without_supports(
        self,
    ) -> None:
        pending = OrderedInputExactState(
            active_mask=0x61,
            held_desired_mask=0x41,
            queued_masks=(0x41,),
            completion_remaining=1,
        )
        self.assert_parity(
            pending,
            selected_mask=0x41,
            delays=(),
            callback_counts=(),
        )

    def test_small_complete_mask_action_matrix_matches_scalar(self) -> None:
        masks = (0x00, 0x01, 0x04, 0x05, 0x40, 0x41, 0x44, 0x45, 0x84)
        for active in masks:
            state = OrderedInputExactState(active, active)
            for selected in masks:
                with self.subTest(active=active, selected=selected):
                    self.assert_parity(
                        state,
                        selected_mask=selected,
                        delays=(() if selected == active else (1, 3)),
                        callback_counts=(
                            () if selected == active else (0, 1, 3)
                        ),
                    )

    def test_pending_suffix_matrix_matches_scalar(self) -> None:
        roots_and_targets = (
            (0x65, 0x41),
            (0x41, 0x84),
            (0x84, 0x05),
        )
        selected_masks = (0x00, 0x04, 0x41, 0x84)
        for root, held in roots_and_targets:
            path = ordered_mask_path(
                root,
                held,
                supported_mask=SUPPORTED,
                forbidden_mask=FORBIDDEN,
            )
            for prefix_count in range(len(path)):
                active = root if prefix_count == 0 else path[prefix_count - 1]
                remaining = path[prefix_count:]
                state = OrderedInputExactState(
                    active_mask=active,
                    held_desired_mask=held,
                    queued_masks=remaining,
                    completion_remaining=2,
                )
                for selected in selected_masks:
                    with self.subTest(
                        state=state,
                        selected=selected,
                    ):
                        self.assert_parity(
                            state,
                            selected_mask=selected,
                            delays=(() if selected == held else (1, 2)),
                            callback_counts=(
                                () if selected == held else (0, 2)
                            ),
                        )

    def test_native_rejects_invalid_support_contract(self) -> None:
        with self.assertRaisesRegex(ValueError, "measure returned 1"):
            issue_ordered_input_state_asynchronously_native(
                OrderedInputExactState(0x05, 0x05),
                selected_mask=0x04,
                post_dispatch_delay_support=(0,),
                dispatch_callback_count_support=(0,),
                supported_mask=SUPPORTED,
                forbidden_mask=FORBIDDEN,
            )
        with self.assertRaisesRegex(ValueError, "measure returned 1"):
            issue_ordered_input_state_asynchronously_native(
                OrderedInputExactState(0x05, 0x05),
                selected_mask=0x04,
                post_dispatch_delay_support=(1,),
                dispatch_callback_count_support=(17,),
                supported_mask=SUPPORTED,
                forbidden_mask=FORBIDDEN,
            )


if __name__ == "__main__":
    unittest.main()
