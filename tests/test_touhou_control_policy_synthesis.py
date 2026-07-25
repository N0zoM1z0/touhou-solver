#!/usr/bin/env python3
"""Bound and parity regressions for candidate-policy synthesis."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from touhou_control.policy_synthesis import (
    evaluate_candidate_policy_portfolio,
    prioritize_candidates_from_previous_version,
    refine_candidate_policy_gap,
    singleton_continuation_candidates,
)
from touhou_control.query_survival import SurvivalQueryProblem
from touhou_control.variable_cadence_oracle import (
    scalar_belief_cadence_survival,
)
from touhou_control.viability import ControlAction, ViabilityConfig


class PolicySynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.x_axis = np.arange(4, dtype=np.float32)
        self.y_axis = np.arange(2, dtype=np.float32)
        self.actions = (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        self.config = ViabilityConfig(
            frames_per_layer=1,
            required_clearance=0.0,
            clamp_to_bounds=True,
        )

    def problem(self, seed: int, horizon: int = 8):
        random = np.random.default_rng(90_000 + seed)
        clearance = np.where(
            random.random((horizon + 1, 2, 4)) < 0.22,
            -1.0,
            random.choice(
                (1.0, 2.0, 4.0),
                size=(horizon + 1, 2, 4),
            ),
        ).astype(np.float32)
        clearance[0, :, 1] = 4.0
        return SurvivalQueryProblem(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(1, 2, 3),
            nominal_delay=2,
            config=self.config,
        )

    def scalar(self, problem, **extra):
        return scalar_belief_cadence_survival(
            x_axis=problem.x_axis,
            y_axis=problem.y_axis,
            clearance_volume=problem.clearance_volume,
            actions=problem.actions,
            delay_frames=problem.delay_frames,
            decision_frame_support=(1, 2),
            config=problem.config,
            start_frame=0,
            row=0,
            column=1,
            observed_action="stay",
            **extra,
        )

    def test_greedy_prefix_widths_are_nested_verified_lower_bounds(
        self,
    ) -> None:
        problem = self.problem(7)
        exact = self.scalar(problem)
        scalar_widths = [
            self.scalar(
                problem,
                continuation_policy="greedy_prefix",
                candidate_policy_width=width,
            )
            for width in (1, 2)
        ]
        native_widths = []
        for width in (1, 2):
            version = ("candidate-width", width)
            with problem.build_belief_pipeline_workspace(
                policy_version=version,
                decision_frame_support=(1, 2),
                continuation_policy="greedy_prefix",
                candidate_policy_width=width,
            ) as workspace:
                native_widths.append(
                    workspace.query_cell(
                        policy_version=version,
                        frame=0,
                        row=0,
                        column=1,
                        observed_action="stay",
                    )
                )
        for native, scalar in zip(native_widths, scalar_widths):
            self.assertEqual(native.action_labels, scalar.action_labels)
        for action_index in range(len(self.actions)):
            self.assertLessEqual(
                scalar_widths[0].action_labels[action_index][1],
                scalar_widths[1].action_labels[action_index][1],
            )
            self.assertLessEqual(
                scalar_widths[1].action_labels[action_index][1],
                exact.action_labels[action_index][1],
            )

    def test_dual_bound_refinement_closes_retained_seed_30_gap(
        self,
    ) -> None:
        problem = self.problem(30)
        exact = self.scalar(problem)
        candidates = singleton_continuation_candidates(problem)
        portfolio = evaluate_candidate_policy_portfolio(
            problem=problem,
            policy_version="portfolio-seed-30",
            decision_frame_support=(1, 2),
            candidates=candidates,
            frame=0,
            row=0,
            column=1,
            observed_action="stay",
            stop_on_feasibility=False,
        )
        self.assertLess(portfolio.result.state_label, exact.state_label)
        refined = refine_candidate_policy_gap(
            problem=problem,
            policy_version="dual-seed-30",
            decision_frame_support=(1, 2),
            candidates=candidates,
            frame=0,
            row=0,
            column=1,
            observed_action="stay",
            max_columns=3,
        )
        self.assertTrue(refined.optimality_certified)
        self.assertEqual(
            refined.final_lower_result.state_label,
            exact.state_label,
        )

    def test_cross_version_reuse_changes_order_not_certificates(
        self,
    ) -> None:
        previous_problem = self.problem(7)
        candidates = singleton_continuation_candidates(previous_problem)
        previous = evaluate_candidate_policy_portfolio(
            problem=previous_problem,
            policy_version="previous-version",
            decision_frame_support=(1, 2),
            candidates=candidates,
            frame=0,
            row=0,
            column=1,
            observed_action="stay",
            stop_on_feasibility=False,
        )
        prioritized = prioritize_candidates_from_previous_version(
            candidates=candidates,
            previous=previous,
        )
        prior_best = max(
            previous.candidate_evaluations,
            key=lambda evaluation: evaluation.state_label,
        )
        self.assertEqual(
            prioritized[0].name,
            prior_best.candidate_policy,
        )

        current_problem = self.problem(8)
        common = {
            "problem": current_problem,
            "decision_frame_support": (1, 2),
            "frame": 0,
            "row": 0,
            "column": 1,
            "observed_action": "stay",
            "stop_on_feasibility": False,
        }
        default = evaluate_candidate_policy_portfolio(
            policy_version="current-default",
            candidates=candidates,
            **common,
        )
        reordered = evaluate_candidate_policy_portfolio(
            policy_version="current-reordered",
            candidates=prioritized,
            **common,
        )
        self.assertEqual(
            reordered.result.action_labels,
            default.result.action_labels,
        )
        self.assertEqual(
            set(reordered.completed_candidates),
            set(default.completed_candidates),
        )

    def test_total_budget_keeps_completed_lower_and_marks_unvisited(
        self,
    ) -> None:
        problem = self.problem(30)
        candidates = singleton_continuation_candidates(problem)
        with patch(
            "touhou_control.policy_synthesis.time.perf_counter",
            side_effect=(0.0, 0.0, 0.002),
        ):
            portfolio = evaluate_candidate_policy_portfolio(
                problem=problem,
                policy_version="budgeted",
                decision_frame_support=(1, 2),
                candidates=candidates,
                frame=0,
                row=0,
                column=1,
                observed_action="stay",
                total_timeout_ms=1,
                stop_on_feasibility=False,
            )
        self.assertEqual(len(portfolio.completed_candidates), 1)
        self.assertEqual(len(portfolio.unvisited_candidates), 2)
        self.assertTrue(portfolio.budget_exhausted)


if __name__ == "__main__":
    unittest.main()
