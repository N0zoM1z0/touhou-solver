#!/usr/bin/env python3
"""Focused tests for issue-time input override ordering."""

from __future__ import annotations

import unittest

from th08_live.issue_overrides import (
    apply_deadline_hold,
    apply_post_hit_input_overrides,
)
from th08_local_planner import Decision


BOMB = 0x02
FOCUS = 0x04


def _decision(*, mask: int = FOCUS, bomb: bool = False) -> Decision:
    return Decision(
        mask=mask,
        action="stay",
        min_clearance=12.0,
        immediate_clearance=12.0,
        score=0.0,
        bomb=bomb,
    )


class IssueOverrideTests(unittest.TestCase):
    def test_deadline_hold_preserves_the_active_command(self) -> None:
        decision = apply_deadline_hold(
            _decision(mask=0x44),
            deadline_missed=True,
            previous_mask=0x85,
            focus_bit=FOCUS,
            action_name_from_mask=lambda mask: f"mask_{mask:02x}",
        )
        self.assertEqual(decision.mask, 0x85)
        self.assertEqual(decision.action, "mask_85+deadline_hold")
        self.assertFalse(decision.bomb)
        self.assertTrue(decision.planned_focus)

    def test_no_deadline_miss_returns_the_original_decision(self) -> None:
        original = _decision(mask=0x44)
        self.assertIs(
            apply_deadline_hold(
                original,
                deadline_missed=False,
                previous_mask=0x85,
                focus_bit=FOCUS,
                action_name_from_mask=str,
            ),
            original,
        )

    def test_deathbomb_precedes_auto_confirm(self) -> None:
        observed_masks: list[int] = []

        def apply_confirm(**values: object) -> tuple[int, object | None]:
            observed_masks.append(int(values["mask"]))
            return int(values["mask"]) | 0x01, {"kind": "confirm"}

        result = apply_post_hit_input_overrides(
            _decision(),
            no_bomb=False,
            phase_now=2,
            predeath_now=10,
            bomb_stock=3.0,
            counter_at_action=100,
            last_bomb_counter=60,
            bomb_bit=BOMB,
            auto_confirm_eligible=True,
            auto_confirm_apply=apply_confirm,
        )
        self.assertEqual(observed_masks, [FOCUS | BOMB])
        self.assertEqual(result.decision.mask, FOCUS | BOMB | 0x01)
        self.assertEqual(result.decision.action, "stay+deathbomb")
        self.assertTrue(result.decision.bomb)
        self.assertTrue(result.can_deathbomb)
        self.assertEqual(result.last_bomb_counter, 100)
        self.assertEqual(result.auto_confirm_event, {"kind": "confirm"})

    def test_no_bomb_guard_checks_the_final_confirm_mask(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "no-bomb policy produced a Bomb input",
        ):
            apply_post_hit_input_overrides(
                _decision(),
                no_bomb=True,
                phase_now=0,
                predeath_now=0,
                bomb_stock=0.0,
                counter_at_action=100,
                last_bomb_counter=0,
                bomb_bit=BOMB,
                auto_confirm_eligible=True,
                auto_confirm_apply=lambda **values: (
                    int(values["mask"]) | BOMB,
                    {"kind": "invalid"},
                ),
            )


if __name__ == "__main__":
    unittest.main()
