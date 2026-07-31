from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_ordinary_future_source_retained_gate_20260731.json"
)


class OrdinaryFutureSourceRetainedGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.points = {
            int(point["decision_frame"]): point
            for point in cls.report["chain"]
        }

    def test_complete_future_geometry_hard_gate_passes(self) -> None:
        gate = self.report["deterministic_gate"]
        self.assertTrue(gate["hard_gate_passed"])
        self.assertEqual(gate["blockers"], [])
        self.assertTrue(
            gate["complete_future_birth_ecl_timeline_coverage"]
        )
        self.assertTrue(
            gate["future_geometry_consumed_across_publication_lead"]
        )
        self.assertTrue(gate["signed_per_action_terminal_values"])
        self.assertTrue(gate["coverage_version_exact_authority_all_roots"])

    def test_first_retained_root_has_directional_exact_authority(self) -> None:
        point = self.points[817]
        predecessor = point["causal_predecessor"]
        self.assertTrue(predecessor["authority_eligible"])
        self.assertTrue(predecessor["applicable"])
        self.assertEqual(
            predecessor["allowed_actions"],
            [
                "stay",
                "left",
                "down",
                "down_left",
                "down_right",
                "left_fast",
                "down_fast",
                "down_left_fast",
            ],
        )
        self.assertFalse(
            point["directional_summary"]["active_action_allowed"]
        )
        self.assertFalse(
            point["directional_summary"]["issued_action_allowed"]
        )
        self.assertGreater(
            point["directional_summary"]["best_margin"],
            0.0,
        )

    def test_pending_root_preserves_no_write_branch_cardinality(self) -> None:
        point = self.points[850]
        self.assertEqual(
            point["pipeline_root"]["remaining_delay_support"],
            [1, 2, 3, 4],
        )
        branch_counts = {
            action["branch_count"]
            for action in point["causal_predecessor"]["actions"]
        }
        self.assertEqual(branch_counts, {4, 28})
        self.assertTrue(
            all(
                action["unavailable_branch_count"] == 0
                for action in point["causal_predecessor"]["actions"]
            )
        )

    def test_late_roots_remain_fail_closed_when_predecessor_is_empty(
        self,
    ) -> None:
        for frame in (850, 910):
            predecessor = self.points[frame]["causal_predecessor"]
            self.assertTrue(predecessor["authority_eligible"])
            self.assertFalse(predecessor["applicable"])
            self.assertEqual(predecessor["allowed_actions"], [])
            self.assertEqual(
                predecessor["reason"],
                "prepublication_viable_predecessor_empty",
            )


if __name__ == "__main__":
    unittest.main()
