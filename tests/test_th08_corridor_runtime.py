#!/usr/bin/env python3
"""Tests for the extracted asynchronous corridor runtime boundary."""

from __future__ import annotations

import math
import unittest

import numpy as np

from corridor_planner import CorridorPlan
from th08_corridor_runtime import (
    CorridorSolution,
    LIVE_REFINEMENT_GRID_STEPS,
    LIVE_SURVIVAL_LABELS,
    SHADOW_REFINEMENT_GRID_STEPS,
    SHADOW_SURVIVAL_LABELS,
    corridor_viability_query,
)
from touhou_control.viability import (
    ControlAction,
    RobustViabilityPolicy,
    ViabilityConfig,
)


class Th08CorridorRuntimeTests(unittest.TestCase):
    def test_rejected_fine_and_survival_strategies_remain_shadow_only(self) -> None:
        self.assertEqual(LIVE_REFINEMENT_GRID_STEPS, ())
        self.assertFalse(LIVE_SURVIVAL_LABELS)
        self.assertEqual(SHADOW_REFINEMENT_GRID_STEPS, (8.0,))
        self.assertTrue(SHADOW_SURVIVAL_LABELS)

    def test_fine_boolean_query_inherits_only_coarse_losing_label(self) -> None:
        axis = np.asarray([0.0, 1.0], dtype=np.float32)
        actions = (ControlAction("stay", 0.0, 0.0),)
        config = ViabilityConfig(frames_per_layer=1)
        viable = np.zeros((2, 1, 2, 2), dtype=np.bool_)
        masks = np.zeros((1, 1, 2, 2), dtype=np.uint32)
        primary = RobustViabilityPolicy(
            x_axis=axis,
            y_axis=axis,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=config,
            viable=viable,
            safe_action_masks=masks,
            backend="native",
        )
        survival = RobustViabilityPolicy(
            x_axis=axis,
            y_axis=axis,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=config,
            viable=viable.copy(),
            safe_action_masks=masks.copy(),
            backend="native_fused_survival",
            survival_frames=np.full(
                viable.shape,
                7,
                dtype=np.uint16,
            ),
            survival_bottleneck_margins=np.full(
                viable.shape,
                -1.5,
                dtype=np.float32,
            ),
            survival_best_action_masks=np.ones(
                masks.shape,
                dtype=np.uint32,
            ),
        )
        plan = CorridorPlan(
            reachable=False,
            path=(),
            bottleneck_clearance=-math.inf,
            terminal_clearance=-math.inf,
            lane="none",
            gate=None,
            reason="test",
            viability_policy=primary,
            survival_policy=survival,
        )
        query = corridor_viability_query(
            CorridorSolution(100, plan, 1.0),
            current_frame=100,
            player_x=0.0,
            player_y=0.0,
            active_action="stay",
            max_age_frames=1,
        )
        self.assertIsNotNone(query)
        assert query is not None
        self.assertFalse(query.state_viable)
        self.assertEqual(query.survival_frames, 7)
        self.assertEqual(query.survival_bottleneck_margin, -1.5)
        self.assertEqual(query.survival_best_actions, ("stay",))


if __name__ == "__main__":
    unittest.main()
