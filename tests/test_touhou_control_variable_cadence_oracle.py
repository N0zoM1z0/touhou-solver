#!/usr/bin/env python3
"""Semantic regressions for the variable-cadence belief-state oracle."""

from __future__ import annotations

import unittest

import numpy as np

from touhou_control.query_survival import (
    PendingCommand,
    SurvivalQueryProblem,
    scalar_query_local_survival,
)
from touhou_control.variable_cadence_oracle import (
    scalar_belief_cadence_survival,
    scalar_clairvoyant_recursive_cadence_survival,
)
from touhou_control.viability import ControlAction, ViabilityConfig


class VariableCadenceOracleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.x_axis = np.arange(3, dtype=np.float32)
        self.y_axis = np.arange(2, dtype=np.float32)

    def test_fixed_cadence_without_carried_delay_matches_hybrid(self) -> None:
        actions = (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        config = ViabilityConfig(
            frames_per_layer=2,
            required_clearance=0.0,
            clamp_to_bounds=True,
        )
        for seed in range(12):
            random = np.random.default_rng(seed)
            clearance = np.where(
                random.random((7, 2, 3)) < 0.2,
                -1.0,
                1.0,
            ).astype(np.float32)
            clearance[0, :, 1] = 1.0
            arguments = {
                "x_axis": self.x_axis,
                "y_axis": self.y_axis,
                "clearance_volume": clearance,
                "actions": actions,
                "delay_frames": (0, 1),
                "config": config,
                "start_frame": 0,
                "row": 0,
                "column": 1,
                "observed_action": "stay",
                "decision_frame_support": (2,),
            }
            expected = scalar_query_local_survival(**arguments)
            actual = scalar_belief_cadence_survival(**arguments)
            self.assertEqual(actual.action_labels, expected.action_labels)
            self.assertEqual(actual.best_actions, expected.best_actions)

    def test_selecting_same_pending_action_does_not_reset_delay(self) -> None:
        actions = (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
        )
        clearance = np.ones((4, 2, 3), dtype=np.float32)
        clearance[3, :, 1] = -1.0
        arguments = {
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "clearance_volume": clearance,
            "actions": actions,
            "delay_frames": (3,),
            "config": ViabilityConfig(
                frames_per_layer=1,
                required_clearance=0.0,
                clamp_to_bounds=True,
            ),
            "start_frame": 0,
            "row": 0,
            "column": 1,
            "observed_action": "stay",
            "pending_command": PendingCommand("left", (2,)),
            "decision_frame_support": (1,),
        }
        always_write = scalar_query_local_survival(**arguments)
        no_write = scalar_belief_cadence_survival(**arguments)
        self.assertFalse(always_write.winning)
        self.assertEqual(
            always_write.state_label.guaranteed_frames,
            2,
        )
        self.assertTrue(no_write.winning)
        self.assertEqual(no_write.best_actions, ("left",))
        self.assertEqual(
            no_write.action_label("left").guaranteed_frames,
            3,
        )
        problem = SurvivalQueryProblem(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(3,),
            nominal_delay=3,
            config=arguments["config"],
        )
        try:
            workspace = problem.build_belief_pipeline_workspace(
                policy_version="ce-0114",
                decision_frame_support=(1,),
            )
        except RuntimeError:
            return
        with workspace:
            native = workspace.query_cell(
                policy_version="ce-0114",
                frame=0,
                row=0,
                column=1,
                observed_action="stay",
                pending_command=PendingCommand("left", (2,)),
            )
        self.assertEqual(native.action_labels, no_write.action_labels)
        self.assertEqual(native.best_actions, no_write.best_actions)

    def test_hidden_remaining_delay_cannot_select_future_action(self) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        clearance = np.ones((5, 2, 3), dtype=np.float32)
        clearance[4, :, 1] = -1.0
        arguments = {
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "clearance_volume": clearance,
            "actions": actions,
            "delay_frames": (2, 3),
            "decision_frame_support": (1,),
            "config": ViabilityConfig(
                frames_per_layer=1,
                required_clearance=0.0,
                clamp_to_bounds=True,
            ),
            "start_frame": 0,
            "row": 0,
            "column": 0,
            "observed_action": "stay",
        }
        clairvoyant = (
            scalar_clairvoyant_recursive_cadence_survival(**arguments)
        )
        belief = scalar_belief_cadence_survival(**arguments)
        self.assertEqual(
            clairvoyant.action_label("right").guaranteed_frames,
            4,
        )
        self.assertEqual(
            belief.action_label("right").guaranteed_frames,
            3,
        )
        self.assertEqual(clairvoyant.best_actions, ("stay", "right"))
        self.assertEqual(belief.best_actions, ("stay",))

    def test_recursive_cadence_catches_phase_shifted_observation_gap(
        self,
    ) -> None:
        x_axis = np.arange(5, dtype=np.float32)
        clearance = np.ones((11, 2, 5), dtype=np.float32)
        for frame, column in ((5, 0), (7, 1), (9, 2), (10, 4)):
            clearance[frame, :, column] = -1.0
        arguments = {
            "x_axis": x_axis,
            "y_axis": self.y_axis,
            "clearance_volume": clearance,
            "actions": (
                ControlAction("left", -1.0, 0.0),
                ControlAction("stay", 0.0, 0.0),
                ControlAction("right", 1.0, 0.0),
            ),
            "delay_frames": (2, 3),
            "decision_frame_support": (1, 2),
            "config": ViabilityConfig(
                frames_per_layer=2,
                required_clearance=0.0,
                clamp_to_bounds=True,
            ),
            "start_frame": 0,
            "row": 0,
            "column": 2,
            "observed_action": "stay",
        }
        one_transition = scalar_belief_cadence_survival(
            **arguments,
            recursive_cadence=False,
        )
        recursive = scalar_belief_cadence_survival(**arguments)
        self.assertTrue(one_transition.winning)
        self.assertFalse(recursive.winning)
        self.assertEqual(
            recursive.state_label.guaranteed_frames,
            9,
        )

    def test_information_relaxation_never_lowers_random_action_value(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        config = ViabilityConfig(
            frames_per_layer=1,
            required_clearance=0.0,
            clamp_to_bounds=True,
        )
        for seed in range(12):
            random = np.random.default_rng(seed + 100)
            clearance = np.where(
                random.random((6, 2, 3)) < 0.2,
                -1.0,
                1.0,
            ).astype(np.float32)
            clearance[0, :, 0] = 1.0
            arguments = {
                "x_axis": self.x_axis,
                "y_axis": self.y_axis,
                "clearance_volume": clearance,
                "actions": actions,
                "delay_frames": (2, 3),
                "decision_frame_support": (1,),
                "config": config,
                "start_frame": 0,
                "row": 0,
                "column": 0,
                "observed_action": "stay",
            }
            clairvoyant = (
                scalar_clairvoyant_recursive_cadence_survival(**arguments)
            )
            belief = scalar_belief_cadence_survival(**arguments)
            for action in actions:
                self.assertLessEqual(
                    belief.action_label(action.name),
                    clairvoyant.action_label(action.name),
                )

    def test_native_belief_workspace_matches_independent_oracle(
        self,
    ) -> None:
        actions = (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        config = ViabilityConfig(
            frames_per_layer=2,
            required_clearance=0.0,
            clamp_to_bounds=True,
        )
        for seed in range(24):
            with self.subTest(seed=seed):
                random = np.random.default_rng(seed + 20_000)
                clearance = np.where(
                    random.random((7, 2, 3)) < 0.2,
                    -1.0,
                    random.choice(
                        (1.0, 2.0, 4.0),
                        size=(7, 2, 3),
                    ),
                ).astype(np.float32)
                clearance[0, :, 1] = 4.0
                pending = (
                    PendingCommand("right", (1, 2, 3))
                    if seed % 2
                    else None
                )
                continuation_actions = (
                    ("left", "stay")
                    if seed % 3 == 0
                    else None
                )
                arguments = {
                    "x_axis": self.x_axis,
                    "y_axis": self.y_axis,
                    "clearance_volume": clearance,
                    "actions": actions,
                    "delay_frames": (0, 1, 3),
                    "decision_frame_support": (1, 2),
                    "config": config,
                    "start_frame": 0,
                    "row": 0,
                    "column": 1,
                    "observed_action": "stay",
                    "pending_command": pending,
                    "continuation_actions": continuation_actions,
                }
                expected = scalar_belief_cadence_survival(**arguments)
                problem = SurvivalQueryProblem(
                    x_axis=self.x_axis,
                    y_axis=self.y_axis,
                    clearance_volume=clearance,
                    actions=actions,
                    delay_frames=(0, 1, 3),
                    nominal_delay=1,
                    config=config,
                )
                try:
                    workspace = problem.build_belief_pipeline_workspace(
                        policy_version=seed,
                        decision_frame_support=(1, 2),
                        continuation_actions=continuation_actions,
                    )
                except RuntimeError as error:
                    self.skipTest(str(error))
                with workspace:
                    actual = workspace.query_cell(
                        policy_version=seed,
                        frame=0,
                        row=0,
                        column=1,
                        observed_action="stay",
                        pending_command=pending,
                    )
                self.assertEqual(
                    actual.state_label.guaranteed_frames,
                    expected.state_label.guaranteed_frames,
                )
                self.assertAlmostEqual(
                    actual.state_label.bottleneck_margin,
                    expected.state_label.bottleneck_margin,
                    places=5,
                )
                self.assertEqual(actual.best_actions, expected.best_actions)
                for (_, actual_label), (_, expected_label) in zip(
                    actual.action_labels,
                    expected.action_labels,
                ):
                    self.assertEqual(
                        actual_label.guaranteed_frames,
                        expected_label.guaranteed_frames,
                    )
                    self.assertAlmostEqual(
                        actual_label.bottleneck_margin,
                        expected_label.bottleneck_margin,
                        places=5,
                    )


if __name__ == "__main__":
    unittest.main()
