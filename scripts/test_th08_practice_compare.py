#!/usr/bin/env python3
"""Focused tests for TH08 practice-run comparisons."""

from __future__ import annotations

import unittest

from th08_practice_compare import compare_dossiers


def _dossier(run_id: str, *, hits: int, solve_ms: float) -> dict[str, object]:
    death = {
        "spell_attribution": {"spell_id": 50},
    }
    return {
        "schema": "th08-practice-dossier-v1",
        "run_id": run_id,
        "control_policy": {"verification": {"passed": True}},
        "deaths": [death] * hits,
        "totals": {
            "death_count": hits,
            "latency_ms": {
                "corridor_solver": {
                    "active_spell_50": {
                        "solve_ms": {
                            "median": solve_ms,
                            "p95": solve_ms,
                            "max": solve_ms,
                        },
                        "age_frames": {
                            "median": solve_ms,
                            "p95": solve_ms,
                            "max": solve_ms,
                        },
                        "stale_solution_count": hits,
                    }
                }
            },
            "decision_cadence_frames": {"median": 3.0},
            "behavior_context": {},
            "hit_contact_epoch": {},
            "primary_cause_counts": {},
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
            comparison["spell_50_corridor"]["solve_ms"]["p95"][
                "reduction_fraction"
            ],
            0.75,
        )


if __name__ == "__main__":
    unittest.main()
