from __future__ import annotations

import unittest

from benchmarks.benchmark_preloss_continuation_reserve import (
    _comparison,
    _eligible,
)


class PrelossContinuationBenchmarkTests(unittest.TestCase):
    def test_eligibility_requires_complete_current_viable_repairs(self) -> None:
        row = {
            "corridor": {
                "viability": {
                    "support_covers_current": True,
                    "safe_actions": ["left", "right"],
                    "repair_volumes": {"left": 3, "right": 5},
                }
            }
        }
        self.assertTrue(_eligible(row))

        row["corridor"]["viability"]["repair_volumes"].pop("right")
        self.assertFalse(_eligible(row))
        row["corridor"]["viability"]["repair_volumes"]["right"] = 5
        row["corridor"]["viability"]["support_covers_current"] = False
        self.assertFalse(_eligible(row))
        row["corridor"]["viability"]["support_covers_current"] = True
        row["corridor"]["viability"]["safe_actions"] = []
        self.assertFalse(_eligible(row))

    def test_comparison_uses_lower_is_better_orientation(self) -> None:
        self.assertEqual(_comparison(1, 2), "improved")
        self.assertEqual(_comparison(2, 2), "equal")
        self.assertEqual(_comparison(3, 2), "regressed")


if __name__ == "__main__":
    unittest.main()
