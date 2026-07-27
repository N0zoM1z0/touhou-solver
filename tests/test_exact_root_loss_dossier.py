#!/usr/bin/env python3
"""Focused tests for exact-root loss completion and dossier semantics."""

from __future__ import annotations

import unittest

from analysis.exact_root_loss.model import (
    EMPTY,
    INCOMPLETE,
    NOT_RUN,
    UNRESOLVED,
    minimal_rescue_combinations,
    solve_result,
    validate_dossier,
)
from analysis.exact_root_loss.replay import compare_query_results
from analysis.exact_root_loss.source import (
    KernelSample,
    TraceEvidence,
    capsule_basename,
    transition_evidence,
)


class ExactRootLossDossierTests(unittest.TestCase):
    def test_incomplete_and_unvisited_results_are_never_empty(self) -> None:
        unavailable = solve_result({"available": False, "reason": "timeout"})
        self.assertEqual(unavailable["completion"], INCOMPLETE)
        self.assertEqual(unavailable["outcome"], UNRESOLVED)
        unvisited = solve_result(
            {
                "available": False,
                "reason": "query age exceeds short horizon",
            }
        )
        self.assertEqual(unvisited["completion"], NOT_RUN)
        self.assertEqual(unvisited["outcome"], UNRESOLVED)
        complete = solve_result(
            {"available": True, "state_viable": False}
        )
        self.assertEqual(complete["outcome"], EMPTY)

    def test_rescue_combinations_are_observed_singletons(self) -> None:
        combinations = minimal_rescue_combinations(
            ("spatial_quantization", "finite_horizon_requirement")
        )
        self.assertEqual(
            [entry["factors"] for entry in combinations],
            [["SPATIAL_AMBIGUITY"], ["SHORT_HORIZON_ONLY"]],
        )
        self.assertTrue(
            all(entry["evidence_level"] == "observed" for entry in combinations)
        )

    def test_capsule_basename_accepts_windows_unc(self) -> None:
        self.assertEqual(
            capsule_basename(
                r"\\wsl.localhost\ubuntu\repo\raw\policy_1_17.npz"
            ),
            "policy_1_17.npz",
        )

    def test_transition_uses_latest_same_epoch_boundary(self) -> None:
        def sample(frame: int, viable: bool, epoch: int = 2) -> KernelSample:
            return KernelSample(
                decision_frame=frame,
                query_frame=frame - 1,
                state_viable=viable,
                capsule=f"policy_{frame}.npz",
                capsule_source_frame=frame - 8,
                projected_x=1.0,
                projected_y=2.0,
                active_action="stay",
                current_delay_support=(1, 2),
                gameplay_epoch=epoch,
                stage_route_index=3,
                spell_id=10,
                policy_status="ready",
            )

        trace = TraceEvidence(
            hit_frames=(400,),
            samples=(
                sample(100, True, epoch=1),
                sample(120, False, epoch=1),
                sample(200, True),
                sample(220, False),
                sample(300, True),
                sample(320, False),
                sample(390, False),
            ),
            target_samples={},
        )
        result = transition_evidence(
            trace,
            minimum_pre_hit_frames=240,
        )[0]
        boundary = result["nonempty_to_empty"]
        self.assertEqual(boundary["nonempty"]["decision_frame"], 300)
        self.assertEqual(boundary["first_empty"]["decision_frame"], 320)
        self.assertEqual(result["window_start_frame"], 160)

    def test_transition_window_expands_past_240_frames(self) -> None:
        def sample(frame: int, viable: bool) -> KernelSample:
            return KernelSample(
                decision_frame=frame,
                query_frame=frame - 1,
                state_viable=viable,
                capsule=f"policy_{frame}.npz",
                capsule_source_frame=frame - 8,
                projected_x=1.0,
                projected_y=2.0,
                active_action="stay",
                current_delay_support=(1, 2),
                gameplay_epoch=3,
                stage_route_index=3,
                spell_id=10,
                policy_status="ready",
            )

        trace = TraceEvidence(
            hit_frames=(500,),
            samples=(
                sample(100, True),
                sample(120, False),
                sample(490, False),
            ),
            target_samples={},
        )
        result = transition_evidence(
            trace,
            minimum_pre_hit_frames=240,
        )[0]
        self.assertEqual(result["window_start_frame"], 100)
        self.assertEqual(result["window_span_frames"], 400)
        self.assertEqual(
            result["nonempty_to_empty"]["lead_frames"],
            380,
        )

    def test_query_comparison_reports_field_mismatch(self) -> None:
        expected = {
            "available": True,
            "state_viable": False,
            "safe_action_count": 0,
            "layer": 1,
            "row": 2,
            "column": 3,
            "position_error": 0.25,
        }
        self.assertEqual(compare_query_results(expected, dict(expected)), [])
        actual = dict(expected)
        actual["row"] = 4
        self.assertEqual(
            compare_query_results(expected, actual),
            ["row: expected 2, got 4"],
        )

    def test_gate_rejects_incomplete_empty_label(self) -> None:
        roots = []
        classes = (
            ["SPATIAL_AMBIGUITY"] * 6
            + ["SHORT_HORIZON_ONLY"] * 8
            + ["MODELED_LOSING_UNRESOLVED"] * 47
        )
        for index, classification in enumerate(classes):
            roots.append(
                {
                    "root_id": f"root-{index}",
                    "primary_classification": {"code": classification},
                    "capsule": {
                        "sha256": "a",
                        "bytes": 1,
                        "decoded": True,
                    },
                    "variants": {
                        "base": {
                            "completion": "complete",
                            "outcome": "empty",
                        }
                    },
                    "pipeline_comparison": {"base_matches_trace": True},
                    "conclusions": (
                        [
                            {
                                "code": "FUTURE_BIRTH_GAP",
                                "evidence_level": "observed",
                            }
                        ]
                        if index < 7
                        else []
                    ),
                }
            )
        dossier = {
            "scope": {"hit_count": 0},
            "roots": roots,
            "transitions": [],
        }
        self.assertTrue(validate_dossier(dossier)["passed"])
        roots[0]["variants"]["base"] = {
            "completion": "incomplete",
            "outcome": "empty",
        }
        gate = validate_dossier(dossier)
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["incomplete_labeled_empty_count"], 1)


if __name__ == "__main__":
    unittest.main()
