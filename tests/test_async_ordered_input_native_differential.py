from __future__ import annotations

import unittest

from analysis.async_ordered_input_native_differential import build_report
from touhou_control.native.ordered_input import (
    async_ordered_input_native_available,
)


class AsyncOrderedInputNativeDifferentialReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not async_ordered_input_native_available():
            raise unittest.SkipTest(
                "native asynchronous ordered-input differential is unavailable"
            )

    def test_report_is_complete_and_deterministic(self) -> None:
        first = build_report()
        second = build_report()

        self.assertEqual(first, second)
        self.assertTrue(first["integrity"]["passed"])
        self.assertEqual(first["integrity"]["mismatch_count"], 0)
        self.assertEqual(first["scope"]["case_count"], 115)
        self.assertEqual(first["scope"]["physical_witness_count"], 2)
        self.assertEqual(
            first["scope"]["scalar_branch_count"],
            first["scope"]["native_branch_count"],
        )
        self.assertFalse(first["authority"]["live_action_authority"])
        self.assertFalse(first["authority"]["physical_support_upper_bound"])

    def test_physical_witnesses_retain_exact_branch_histories(self) -> None:
        report = build_report()
        witnesses = {
            witness["identity"]: witness
            for witness in report["physical_witnesses"]
        }

        self.assertEqual(
            set(witnesses),
            {
                "physical_ce0193_0x65_to_0x41",
                "physical_superseded_0x04_target_to_0x05",
            },
        )
        self.assertTrue(
            all(
                witness["exact_branches"]
                for witness in witnesses.values()
            )
        )
        ce0193 = witnesses["physical_ce0193_0x65_to_0x41"]
        self.assertTrue(
            any(
                branch["publications_during_dispatch"] == [0x61]
                for branch in ce0193["exact_branches"]
            )
        )


if __name__ == "__main__":
    unittest.main()
