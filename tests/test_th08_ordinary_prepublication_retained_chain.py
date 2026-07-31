from __future__ import annotations

import json
from pathlib import Path
import unittest


REPORT = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "runtime_reports"
    / "th08_ordinary_prepublication_retained_gate_20260731.json"
)


class OrdinaryPrepublicationRetainedChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.rows = {
            row["decision_frame"]: row
            for row in cls.report["chain"]
        }

    def test_exact_retained_chain_and_phase_semantics(self) -> None:
        self.assertEqual(
            tuple(self.rows),
            (817, 833, 835, 850, 910),
        )
        self.assertTrue(
            all(
                row["player_phase"] not in (1, 2)
                for row in self.rows.values()
            )
        )
        self.assertEqual(
            {
                row["retained_predeath_limit"]
                for row in self.rows.values()
            },
            {10},
        )
        self.assertEqual(
            self.rows[833]["pending_policy_source_frame"]
            - self.rows[833]["observation_frame"],
            3,
        )

    def test_scalar_alias_and_directional_recovery_are_both_retained(self) -> None:
        self.assertTrue(
            self.rows[835][
                "scalar_counterfactual_issued_action_allowed"
            ]
        )
        self.assertEqual(
            self.rows[835]["scalar_counterfactual_issued_action"],
            "down_left",
        )
        for frame in (850, 910):
            row = self.rows[frame]
            self.assertEqual(
                row["scalar_counterfactual_allowed_action_count"],
                17,
            )
            self.assertEqual(
                row["scalar_counterfactual_all_action_value"],
                0.0,
            )
            self.assertGreater(
                len(set(row["recovery_distances"].values())),
                1,
            )
        self.assertEqual(
            min(
                self.rows[835]["recovery_distances"],
                key=self.rows[835]["recovery_distances"].get,
            ),
            "left_fast",
        )
        self.assertEqual(
            min(
                self.rows[910]["recovery_distances"],
                key=self.rows[910]["recovery_distances"].get,
            ),
            "left_fast",
        )

    def test_missing_birth_coverage_keeps_physical_gate_closed(self) -> None:
        self.assertEqual(
            {
                row["future_hazard_coverage"]
                for row in self.rows.values()
            },
            {"model_unknown"},
        )
        gate = self.report["deterministic_gate"]
        self.assertTrue(gate["directional_hazard_space_recovery_retained"])
        self.assertFalse(gate["complete_future_birth_event_coverage"])
        self.assertIsNone(
            gate["nontrivial_exact_allowed_set_before_exhaustion"]
        )
        self.assertFalse(gate["hard_gate_passed"])
        self.assertEqual(
            gate["physical_disposition"],
            "do_not_run_until_hard_gate_passes",
        )


if __name__ == "__main__":
    unittest.main()
