from __future__ import annotations

import unittest

from touhou_control.issue_actions import (
    CompleteMaskAction,
    CompleteMaskActionSpace,
)


class CompleteMaskActionSpaceTests(unittest.TestCase):
    def test_rejects_duplicate_masks_even_when_tokens_differ(self) -> None:
        with self.assertRaisesRegex(ValueError, "injective"):
            CompleteMaskActionSpace(
                supported_mask=0x03,
                actions=(
                    CompleteMaskAction("first", 0x01, "left", -1.0, 0.0),
                    CompleteMaskAction("second", 0x01, "left", -1.0, 0.0),
                ),
            )

    def test_equal_velocity_tokens_keep_distinct_issue_identity(self) -> None:
        space = CompleteMaskActionSpace(
            supported_mask=0x03,
            actions=(
                CompleteMaskAction("held", 0x01, "right", 1.0, 0.0),
                CompleteMaskAction("selected", 0x03, "right", 1.0, 0.0),
            ),
        )

        self.assertEqual(
            space.action_for_token("held").velocity_x,
            space.action_for_token("selected").velocity_x,
        )
        self.assertFalse(
            space.is_no_write(held_mask=0x01, selected_token="selected")
        )
        self.assertTrue(
            space.is_no_write(held_mask=0x01, selected_token="held")
        )
        self.assertEqual(
            tuple(action.name for action in space.control_actions),
            ("held", "selected"),
        )


if __name__ == "__main__":
    unittest.main()
