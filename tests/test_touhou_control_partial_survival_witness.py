#!/usr/bin/env python3
"""Exact regressions for offline stationary partial-survival witnesses."""

from __future__ import annotations

from dataclasses import replace
import unittest

import numpy as np

from touhou_control.partial_survival_witness import (
    FINITE_MODEL_FEASIBILITY_WITNESS,
    NO_POSITIVE_ATTAINABLE_WITNESS,
    PARTIAL_WITNESS_ON_UNRESOLVED,
    POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS,
    build_stationary_policy_witness,
    build_stationary_witness_portfolio,
    replay_stationary_worst_branch,
    stationary_witness_problem_digest,
)
from touhou_control.query_survival import (
    PendingCommand,
    SurvivalQueryProblem,
)
from touhou_control.variable_cadence_oracle import (
    scalar_belief_cadence_survival,
)
from touhou_control.viability import ControlAction, ViabilityConfig


class PartialSurvivalWitnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        self.x_axis = np.arange(4, dtype=np.float32)
        self.y_axis = np.arange(2, dtype=np.float32)
        self.config = ViabilityConfig(
            frames_per_layer=2,
            required_clearance=0.0,
            clamp_to_bounds=True,
        )

    def problem(
        self,
        clearance: np.ndarray,
        *,
        actions: tuple[ControlAction, ...] | None = None,
        delay_frames: tuple[int, ...] = (0, 1),
        nominal_delay: int = 0,
        config: ViabilityConfig | None = None,
    ) -> SurvivalQueryProblem:
        return SurvivalQueryProblem(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=clearance,
            actions=self.actions if actions is None else actions,
            delay_frames=delay_frames,
            nominal_delay=nominal_delay,
            config=self.config if config is None else config,
        )

    def test_randomized_labels_match_scalar_and_native_oracle(self) -> None:
        for seed in range(4):
            with self.subTest(seed=seed):
                random = np.random.default_rng(seed)
                clearance = np.where(
                    random.random((8, 2, 4)) < 0.2,
                    -1.0,
                    1.0,
                ).astype(np.float32)
                clearance[0, :, 2] = 1.0
                problem = self.problem(clearance)
                arguments = {
                    "x_axis": problem.x_axis,
                    "y_axis": problem.y_axis,
                    "clearance_volume": problem.clearance_volume,
                    "actions": problem.actions,
                    "delay_frames": problem.delay_frames,
                    "decision_frame_support": (2, 3),
                    "config": problem.config,
                    "start_frame": 0,
                    "row": 0,
                    "column": 2,
                    "observed_action": "stay",
                    "continuation_actions": ("stay",),
                }
                scalar = scalar_belief_cadence_survival(**arguments)
                witnesses = tuple(
                    build_stationary_policy_witness(
                        problem=problem,
                        decision_frame_support=(2, 3),
                        frame=0,
                        row=0,
                        column=2,
                        observed_action="stay",
                        root_action=action.name,
                        continuation_action="stay",
                    )
                    for action in problem.actions
                )
                for witness in witnesses:
                    self.assertEqual(
                        witness.label,
                        scalar.action_label(witness.root_action),
                    )
                    self.assertEqual(
                        replay_stationary_worst_branch(witness),
                        witness.label,
                    )

                try:
                    workspace = problem.build_belief_pipeline_workspace(
                        policy_version=f"partial-witness-{seed}",
                        decision_frame_support=(2, 3),
                        continuation_actions=("stay",),
                    )
                except RuntimeError as error:
                    self.skipTest(f"native belief workspace unavailable: {error}")
                with workspace:
                    native = workspace.query_cell(
                        policy_version=f"partial-witness-{seed}",
                        frame=0,
                        row=0,
                        column=2,
                        observed_action="stay",
                    )
                for witness in witnesses:
                    self.assertEqual(
                        witness.label,
                        native.action_label(witness.root_action),
                    )

    def test_same_pending_action_is_no_write_in_worst_branch(self) -> None:
        actions = self.actions[:2]
        clearance = np.ones((4, 2, 4), dtype=np.float32)
        clearance[3, :, 2] = -1.0
        config = ViabilityConfig(
            frames_per_layer=1,
            required_clearance=0.0,
            clamp_to_bounds=True,
        )
        problem = self.problem(
            clearance,
            actions=actions,
            delay_frames=(3,),
            nominal_delay=3,
            config=config,
        )
        pending = PendingCommand("left", (2,))
        witness = build_stationary_policy_witness(
            problem=problem,
            decision_frame_support=(1,),
            frame=0,
            row=0,
            column=2,
            observed_action="stay",
            root_action="left",
            continuation_action="left",
            pending_command=pending,
        )
        scalar = scalar_belief_cadence_survival(
            x_axis=problem.x_axis,
            y_axis=problem.y_axis,
            clearance_volume=problem.clearance_volume,
            actions=problem.actions,
            delay_frames=problem.delay_frames,
            decision_frame_support=(1,),
            config=problem.config,
            start_frame=0,
            row=0,
            column=2,
            observed_action="stay",
            pending_command=pending,
            continuation_actions=("left",),
        )
        self.assertEqual(witness.label, scalar.action_label("left"))
        self.assertIsNone(witness.worst_branch[0].pickup_delay)
        self.assertEqual(
            witness.worst_branch[0].successor_remaining_delay_support,
            (1,),
        )

    def test_portfolio_is_complete_deterministic_and_mode_safe(self) -> None:
        clearance = np.ones((7, 2, 4), dtype=np.float32)
        clearance[4:, :, :] = -1.0
        problem = self.problem(clearance)
        arguments = {
            "problem": problem,
            "decision_frame_support": (1, 2),
            "continuation_candidates": ("left", "stay", "right"),
            "frame": 0,
            "row": 0,
            "column": 2,
            "observed_action": "stay",
            "unrestricted_status": "losing",
        }
        first = build_stationary_witness_portfolio(**arguments)
        second = build_stationary_witness_portfolio(**arguments)
        self.assertTrue(first.complete)
        self.assertEqual(
            first.complete_root_actions,
            tuple(action.name for action in problem.actions),
        )
        self.assertEqual(
            first.mode,
            POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS,
        )
        self.assertGreater(first.state_label.guaranteed_frames, 0)
        self.assertLess(
            first.state_label.guaranteed_frames,
            problem.horizon_frames,
        )
        self.assertEqual(first, second)
        for root_action, witness in zip(
            first.complete_root_actions,
            first.action_witnesses,
            strict=True,
        ):
            expected = max(
                scalar_belief_cadence_survival(
                    x_axis=problem.x_axis,
                    y_axis=problem.y_axis,
                    clearance_volume=problem.clearance_volume,
                    actions=problem.actions,
                    delay_frames=problem.delay_frames,
                    decision_frame_support=(1, 2),
                    config=problem.config,
                    start_frame=0,
                    row=0,
                    column=2,
                    observed_action="stay",
                    continuation_actions=(continuation,),
                ).action_label(root_action)
                for continuation in arguments["continuation_candidates"]
            )
            self.assertEqual(witness.label, expected)

        unresolved = build_stationary_witness_portfolio(
            **{**arguments, "unrestricted_status": "unresolved"}
        )
        self.assertEqual(
            unresolved.mode,
            PARTIAL_WITNESS_ON_UNRESOLVED,
        )

        safe_problem = self.problem(
            np.ones((7, 2, 4), dtype=np.float32)
        )
        feasible = build_stationary_witness_portfolio(
            **{
                **arguments,
                "problem": safe_problem,
            }
        )
        self.assertEqual(
            feasible.mode,
            FINITE_MODEL_FEASIBILITY_WITNESS,
        )

        unsafe_clearance = np.ones((7, 2, 4), dtype=np.float32)
        unsafe_clearance[0, 0, 2] = -1.0
        unsafe = build_stationary_witness_portfolio(
            **{
                **arguments,
                "problem": self.problem(unsafe_clearance),
            }
        )
        self.assertEqual(
            unsafe.mode,
            NO_POSITIVE_ATTAINABLE_WITNESS,
        )

    def test_digests_cover_problem_and_replay_rejects_tampering(self) -> None:
        clearance = np.ones((5, 2, 4), dtype=np.float32)
        problem = self.problem(clearance)
        base = stationary_witness_problem_digest(
            problem,
            decision_frame_support=(2,),
        )
        changed_clearance = clearance.copy()
        changed_clearance[3, 1, 3] = np.nextafter(
            np.float32(1.0),
            np.float32(2.0),
        )
        changed = stationary_witness_problem_digest(
            self.problem(changed_clearance),
            decision_frame_support=(2,),
        )
        changed_cadence = stationary_witness_problem_digest(
            problem,
            decision_frame_support=(2, 3),
        )
        self.assertNotEqual(base, changed)
        self.assertNotEqual(base, changed_cadence)

        witness = build_stationary_policy_witness(
            problem=problem,
            decision_frame_support=(2,),
            frame=0,
            row=0,
            column=2,
            observed_action="stay",
            root_action="left",
            continuation_action="stay",
        )
        with self.assertRaisesRegex(ValueError, "digest does not replay"):
            replay_stationary_worst_branch(
                replace(witness, continuation_action="right")
            )
        with self.assertRaisesRegex(
            ValueError,
            "does not match the supplied problem",
        ):
            build_stationary_policy_witness(
                problem=problem,
                decision_frame_support=(2,),
                frame=0,
                row=0,
                column=2,
                observed_action="stay",
                root_action="left",
                continuation_action="stay",
                problem_digest="0" * 64,
            )


if __name__ == "__main__":
    unittest.main()
