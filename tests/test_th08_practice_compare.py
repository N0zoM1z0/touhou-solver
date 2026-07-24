#!/usr/bin/env python3
"""Focused tests for TH08 practice-run comparisons."""

from __future__ import annotations

import unittest

from analysis.th08_practice_compare import compare_dossiers


def _dossier(run_id: str, *, hits: int, solve_ms: float) -> dict[str, object]:
    return {
        "schema": "th08-practice-dossier-v1",
        "run_id": run_id,
        "practice_scope": {
            "stage_route_index": 7,
            "raw_summary_is_scope_valid": True,
            "accepted_completion": True,
        },
        "control_policy": {"verification": {"passed": True}},
        "deaths": [],
        "totals": {
            "death_count": hits,
            "robust_viability": {
                "policy_decision_count": 10,
                "query_count": 8,
                "empty_action_set_count": hits,
                "solve_ms": {
                    "median": solve_ms,
                    "p95": solve_ms,
                    "max": solve_ms,
                },
                "policy_status_counts": {"queryable": 8, "expired": 2},
            },
            "behavior_context": {},
            "input_visibility": {},
            "hit_contact_epoch": {},
            "primary_cause_counts": {},
            "per_spell": [
                {
                    "phase_key": "166",
                    "spell_name": "fixture",
                    "hit_count": hits,
                    "decision_count": 20,
                    "decision_cadence_frames": {
                        "median": solve_ms / 10.0,
                        "p95": solve_ms / 10.0,
                        "max": solve_ms / 10.0,
                    },
                    "runtime_timing_ms": {
                        "decode_pools": {
                            "median": solve_ms / 20.0,
                            "p95": solve_ms / 20.0,
                            "max": solve_ms / 20.0,
                        },
                    },
                    "robust_viability": {
                        "query_count": 8,
                        "empty_action_set_count": hits,
                        "solve_ms": {
                            "median": solve_ms,
                            "p95": solve_ms,
                            "max": solve_ms,
                        },
                    },
                }
            ],
        },
    }


class Th08PracticeCompareTests(unittest.TestCase):
    def test_comparison_retains_directional_reductions(self) -> None:
        comparison = compare_dossiers(
            _dossier("before", hits=4, solve_ms=100.0),
            _dossier("after", hits=3, solve_ms=25.0),
        )
        self.assertEqual(
            comparison["death_count"]["reduction_fraction"],
            0.25,
        )
        self.assertEqual(
            comparison["robust_viability"]["solve_ms"]["p95"][
                "reduction_fraction"
            ],
            0.75,
        )
        self.assertEqual(
            comparison["per_phase"]["166"]["hit_count"]["delta"],
            -1,
        )
        self.assertEqual(
            comparison["per_phase"]["166"]["runtime_timing_ms"][
                "decode_pools"
            ]["p95"]["reduction_fraction"],
            0.75,
        )
        self.assertTrue(
            comparison["scope_compatibility"][
                "candidate_accepted_completion"
            ]
        )


if __name__ == "__main__":
    unittest.main()
