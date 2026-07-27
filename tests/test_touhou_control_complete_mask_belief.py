from __future__ import annotations

import unittest

import numpy as np

from th08_pipeline_actions import TH08_COMPLETE_MASK_ACTION_SPACE
from touhou_control.query_survival import PendingCommand, SurvivalQueryProblem
from touhou_control.reachability_oracle import SurvivalLabel
from touhou_control.variable_cadence_oracle import (
    scalar_belief_cadence_survival,
)
from touhou_control.viability import ViabilityConfig


class CompleteMaskBeliefWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.space = TH08_COMPLETE_MASK_ACTION_SPACE
        self.actions = self.space.control_actions
        self.x_axis = np.arange(3, dtype=np.float32)
        self.y_axis = np.arange(2, dtype=np.float32)
        self.clearance = np.ones((3, 2, 3), dtype=np.float32)
        self.config = ViabilityConfig(
            frames_per_layer=1,
            required_clearance=0.0,
            clamp_to_bounds=True,
        )
        self.observed = self.space.token_for_mask(0x05)
        self.pending = PendingCommand(
            self.space.token_for_mask(0x85),
            (1, 2),
        )

    def _problem(self) -> SurvivalQueryProblem:
        return SurvivalQueryProblem(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=self.clearance,
            actions=self.actions,
            delay_frames=(1, 2),
            nominal_delay=1,
            config=self.config,
        )

    def test_36_action_ce_0134_root_matches_independent_scalar(self) -> None:
        scalar = scalar_belief_cadence_survival(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=self.clearance,
            actions=self.actions,
            delay_frames=(1, 2),
            decision_frame_support=(1,),
            config=self.config,
            start_frame=0,
            row=0,
            column=1,
            observed_action=self.observed,
            pending_command=self.pending,
        )

        with self._problem().build_belief_pipeline_workspace(
            policy_version="ce-0134-complete-mask",
            decision_frame_support=(1,),
        ) as workspace:
            native = workspace.query_cell(
                policy_version="ce-0134-complete-mask",
                frame=0,
                row=0,
                column=1,
                observed_action=self.observed,
                pending_command=self.pending,
            )

        self.assertEqual(len(native.action_labels), 36)
        self.assertEqual(native.state_label, scalar.state_label)
        self.assertEqual(native.action_labels, scalar.action_labels)
        self.assertEqual(native.best_actions, scalar.best_actions)
        self.assertEqual(len(native.best_actions), 36)
        self.assertIn(self.space.token_for_mask(0xA5), native.best_actions)

    def test_64_bit_upper_mask_retains_actions_above_bit_31(self) -> None:
        with self._problem().build_belief_pipeline_workspace(
            policy_version="complete-mask-upper",
            decision_frame_support=(1,),
            reveal_remaining_delay=True,
        ) as workspace:
            certification = workspace.certify_upper_bound(
                policy_version="complete-mask-upper",
                frame=0,
                row=0,
                column=1,
                observed_action=self.observed,
                pending_command=self.pending,
                lower_bound=SurvivalLabel(0, -float("inf")),
            )

        self.assertFalse(certification.certified)
        self.assertFalse(certification.deadline_expired)
        self.assertEqual(
            certification.unresolved_actions,
            tuple(action.name for action in self.actions),
        )
        self.assertEqual(len(certification.unresolved_actions), 36)

    def test_equal_velocity_pending_identity_changes_no_write_value(self) -> None:
        row_clearance = np.asarray(
            [
                [1, 1, 1, -1, 1],
                [1, -1, 1, -1, 1],
                [-1, -1, 1, 1, 1],
                [1, 1, -1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, -1, 1, -1, 1],
            ],
            dtype=np.float32,
        )
        clearance = np.repeat(row_clearance[:, None, :], 2, axis=1)
        x_axis = np.arange(5, dtype=np.float32)
        continuation = tuple(
            self.space.token_for_mask(mask)
            for mask in (0x05, 0x45, 0x85)
        )
        problem = SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=self.y_axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(1, 3),
            nominal_delay=1,
            config=self.config,
        )
        scalar_results = {}
        native_results = {}

        with problem.build_belief_pipeline_workspace(
            policy_version="ce-0134-identity-value",
            decision_frame_support=(1, 2),
            continuation_actions=continuation,
        ) as workspace:
            for pending_mask in (0x85, 0x84):
                pending = PendingCommand(
                    self.space.token_for_mask(pending_mask),
                    (1, 2),
                )
                scalar_results[pending_mask] = (
                    scalar_belief_cadence_survival(
                        x_axis=x_axis,
                        y_axis=self.y_axis,
                        clearance_volume=clearance,
                        actions=self.actions,
                        delay_frames=(1, 3),
                        decision_frame_support=(1, 2),
                        config=self.config,
                        start_frame=0,
                        row=0,
                        column=2,
                        observed_action=self.observed,
                        pending_command=pending,
                        continuation_actions=continuation,
                    )
                )
                native_results[pending_mask] = workspace.query_cell(
                    policy_version="ce-0134-identity-value",
                    frame=0,
                    row=0,
                    column=2,
                    observed_action=self.observed,
                    pending_command=pending,
                )

        for pending_mask in (0x85, 0x84):
            self.assertEqual(
                native_results[pending_mask].action_labels,
                scalar_results[pending_mask].action_labels,
            )
        shot = self.space.token_for_mask(0x85)
        no_shot = self.space.token_for_mask(0x84)
        self.assertEqual(
            scalar_results[0x85].action_label(shot),
            SurvivalLabel(5, 1.0),
        )
        self.assertEqual(
            scalar_results[0x85].action_label(no_shot),
            SurvivalLabel(2, -1.0),
        )
        self.assertEqual(
            scalar_results[0x84].action_label(no_shot),
            SurvivalLabel(5, 1.0),
        )
        self.assertEqual(
            scalar_results[0x84].action_label(shot),
            SurvivalLabel(2, -1.0),
        )


if __name__ == "__main__":
    unittest.main()
