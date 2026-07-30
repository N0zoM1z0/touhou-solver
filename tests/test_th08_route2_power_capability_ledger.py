from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ANALYSIS = SCRIPTS / "analysis"
for path in (SCRIPTS, ANALYSIS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from th08_route2_power_capability_ledger import build_report  # noqa: E402


class Route2PowerCapabilityLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = build_report(
            primary_path=ROOT / "artifacts/decoded/ply02a.sht",
            secondary_path=ROOT / "artifacts/decoded/ply02as.sht",
        )

    def test_covers_complete_power_and_pickup_domain(self) -> None:
        transitions = self.report["pickup_transitions"]
        self.assertEqual(len(transitions), 129 * 3)
        self.assertEqual(
            self.report["inputs"]["normal_power_thresholds"],
            [8, 24, 48, 80, 128],
        )
        self.assertEqual(len(self.report["power_bands"]), 6)
        self.assertEqual(
            (
                self.report["power_bands"][-1]["power_lower_inclusive"],
                self.report["power_bands"][-1]["power_upper_inclusive"],
            ),
            (128, 128),
        )

    def test_large_pickup_saturates_instead_of_retaining_132(self) -> None:
        transition = self.report["summary"]["large_pickup_124"]
        self.assertEqual(transition["power_after"], 128)
        self.assertEqual(transition["power_delta"], 4)
        self.assertEqual(transition["thresholds_crossed"], [128])
        self.assertTrue(transition["converted_other_active_power_items"])

    def test_full_power_spawn_converts_later_power_drops(self) -> None:
        transition = next(
            item
            for item in self.report["pickup_transitions"]
            if item["power_before"] == 128
            and item["requested_pickup"] == "small_power"
        )
        self.assertEqual(transition["effective_item_type"], 8)
        self.assertTrue(transition["spawn_converted_to_overflow"])
        self.assertEqual(transition["power_delta"], 0)
        self.assertFalse(transition["profile_changed"])

    def test_threshold_marginals_preserve_action_conditioning(self) -> None:
        rows = self.report["threshold_marginals"]
        self.assertEqual([row["threshold"] for row in rows], [8, 24, 48, 80, 128])
        at_128 = rows[-1]["small_pickup_transition"]["capability_delta"]
        self.assertEqual(
            at_128["unfocused_primary"][
                "nominal_base_damage_per_20_tick_cycle"
            ],
            80,
        )
        self.assertEqual(
            at_128["focused_secondary"][
                "nominal_base_damage_per_20_tick_cycle"
            ],
            185,
        )

    def test_report_retains_no_policy_authority(self) -> None:
        self.assertFalse(self.report["authority"]["planner_action_authority"])
        self.assertFalse(self.report["authority"]["causal_collection_authority"])


if __name__ == "__main__":
    unittest.main()
