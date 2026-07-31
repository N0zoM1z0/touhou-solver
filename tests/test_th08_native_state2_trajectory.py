from __future__ import annotations

import json
from pathlib import Path
import unittest

REPORT = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "runtime_reports"
    / "th08_native_state2_lifecycle_root2129_h8_20260730.json"
)


class NativeState2TrajectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_production_and_independent_lifecycle_are_exact(self) -> None:
        result = self.report["result"]
        self.assertEqual(
            result["production_root_active_state2_h8"],
            "exact",
        )
        self.assertEqual(result["production_position_exact"], "223/223")
        self.assertEqual(result["independent_lifecycle_exact"], "223/223")
        self.assertEqual(result["headless_natural_exact_ticks"], 8)

    def test_timer_groups_transition_without_future_native_state(self) -> None:
        differential = self.report["artifacts"]["production_differential"][
            "payload"
        ]
        self.assertEqual(
            differential["transition_frames"],
            {
                "2131": list(range(1192, 1199)),
                "2133": list(range(1199, 1206)),
                "2135": list(range(1206, 1213)),
                "2137": [1213, 1214, 1215, 1216, 1218, 1219],
            },
        )
        self.assertIsNone(differential["production_first_mismatch"])
        self.assertIsNone(
            differential["independent_lifecycle_first_mismatch"]
        )

    def test_payload_retention_elides_duplicate_same_action_branches(self) -> None:
        self.assertFalse(
            self.report["result"][
                "a1_a2_duplicate_model_payloads_retained"
            ]
        )

    def test_scope_remains_narrow_and_nonphysical(self) -> None:
        self.assertEqual(self.report["result"]["physical_trials_used"], 0)
        self.assertIn(
            "causal birth/removal generation",
            self.report["authority"]["not_accepted_for"],
        )


if __name__ == "__main__":
    unittest.main()
