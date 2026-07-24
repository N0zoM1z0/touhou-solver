#!/usr/bin/env python3
"""Tests for the pure global-to-local policy boundary."""

from __future__ import annotations

import unittest

from touhou_control.policy_guidance import (
    assemble_local_policy_guidance,
)
from touhou_control.viability import SafetyValueQuery, ViabilityQuery


class LocalPolicyGuidanceTests(unittest.TestCase):
    def test_winning_query_is_the_only_hard_action_constraint(self) -> None:
        query = ViabilityQuery(
            available=True,
            layer=0,
            row=1,
            column=2,
            active_action="stay",
            state_viable=True,
            safe_actions=("left",),
            repair_volumes=(("left", 7),),
            position_error=1.25,
            reason="winning",
            survival_frames=80,
            survival_bottleneck_margin=3.0,
            survival_best_actions=("right",),
        )
        guidance = assemble_local_policy_guidance(
            viability_query=query,
            safety_value_query=None,
            policy_delay_frames=(1, 2, 3),
            current_delay_frames=(2, 3),
        )
        self.assertEqual(guidance.allowed_first_actions, ("left",))
        self.assertEqual(guidance.repair_volumes, (("left", 7),))
        self.assertEqual(guidance.position_error, 1.25)
        self.assertEqual(guidance.survival_actions, ())

    def test_losing_query_orders_survival_before_soft_fallbacks(self) -> None:
        query = ViabilityQuery(
            available=True,
            layer=0,
            row=1,
            column=2,
            active_action="stay",
            state_viable=False,
            safe_actions=(),
            repair_volumes=(("right", 3),),
            position_error=4.0,
            reason="losing",
            recovery_distances=(("right", 12.0),),
            survival_frames=10,
            survival_bottleneck_margin=-1.5,
            survival_best_actions=("left",),
        )
        safety = SafetyValueQuery(
            available=True,
            layer=0,
            row=1,
            column=2,
            active_action="stay",
            state_value=-2.0,
            action_values=(),
            best_actions=("up",),
            position_error=4.0,
            reason="fallback",
        )
        guidance = assemble_local_policy_guidance(
            viability_query=query,
            safety_value_query=safety,
            policy_delay_frames=(1, 2, 3),
            current_delay_frames=(1, 3),
        )
        self.assertIsNone(guidance.allowed_first_actions)
        self.assertEqual(guidance.survival_actions, ("left",))
        self.assertEqual(guidance.survival_frames, 10)
        self.assertEqual(guidance.safety_actions, ("up",))
        self.assertEqual(guidance.recovery_distances, (("right", 12.0),))
        self.assertEqual(guidance.position_error, 0.0)

    def test_uncovered_delay_support_disables_all_policy_guidance(self) -> None:
        query = ViabilityQuery(
            available=True,
            layer=0,
            row=0,
            column=0,
            active_action="stay",
            state_viable=True,
            safe_actions=("stay",),
            repair_volumes=(("stay", 1),),
            position_error=0.0,
            reason="stale support",
        )
        guidance = assemble_local_policy_guidance(
            viability_query=query,
            safety_value_query=None,
            policy_delay_frames=(1, 2),
            current_delay_frames=(2, 3),
        )
        self.assertFalse(guidance.support_covers_current)
        self.assertIsNone(guidance.allowed_first_actions)
        self.assertEqual(guidance.repair_volumes, ())


if __name__ == "__main__":
    unittest.main()
