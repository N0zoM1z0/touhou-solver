#!/usr/bin/env python3
"""Authority and integrity checks for the retained G3 capsule report."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from analysis.partial_witness_capsule.serialization import canonical_sha256
from touhou_control.partial_survival_witness import (
    FINITE_MODEL_FEASIBILITY_WITNESS,
    NO_POSITIVE_ATTAINABLE_WITNESS,
    PARTIAL_WITNESS_ON_UNRESOLVED,
    POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS,
)


REPORT = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "viability_audit"
    / "g3_stationary_partial_witness_capsule_audit_20260727.json"
)
EXPECTED_REPORT_DIGEST = (
    "82ae76afac47f556d01865cba4a0342db6c5b1da44e537e6af7b7a9f28d881f8"
)


class G3PartialSurvivalCapsuleReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_report_digest_and_authority_are_fixed(self) -> None:
        report = dict(self.report)
        digest = report.pop("report_digest")
        self.assertEqual(digest, EXPECTED_REPORT_DIGEST)
        self.assertEqual(canonical_sha256(report), digest)
        self.assertEqual(
            self.report["scope"]["authority"],
            "offline restricted attainable lower witness only",
        )
        self.assertIn(
            "unresolved",
            self.report["scope"]["unrestricted_contract"],
        )

    def test_each_workload_retains_all_three_distinct_modes(self) -> None:
        expected_modes = (
            FINITE_MODEL_FEASIBILITY_WITNESS,
            PARTIAL_WITNESS_ON_UNRESOLVED,
            NO_POSITIVE_ATTAINABLE_WITNESS,
        )
        self.assertEqual(
            [workload["stage"] for workload in self.report["workloads"]],
            ["4A", "6B"],
        )
        for workload in self.report["workloads"]:
            with self.subTest(workload=workload["workload"]):
                self.assertEqual(
                    tuple(workload["retained_modes"]),
                    expected_modes,
                )
                self.assertEqual(workload["missing_modes"], [])
                observations = {
                    observation["mode"]: observation
                    for observation in workload["observations"]
                }
                self.assertNotIn(
                    POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS,
                    observations,
                )
                full = observations[FINITE_MODEL_FEASIBILITY_WITNESS]
                partial = observations[PARTIAL_WITNESS_ON_UNRESOLVED]
                empty = observations[NO_POSITIVE_ATTAINABLE_WITNESS]
                self.assertEqual(
                    full["state_label"]["guaranteed_frames"],
                    self.report["scope"]["horizon_frames"],
                )
                self.assertGreater(
                    float.fromhex(
                        full["state_label"]["bottleneck_margin_hex"]
                    ),
                    0.0,
                )
                self.assertGreater(
                    partial["state_label"]["guaranteed_frames"],
                    0,
                )
                self.assertLess(
                    partial["state_label"]["guaranteed_frames"],
                    self.report["scope"]["horizon_frames"],
                )
                self.assertEqual(
                    empty["state_label"]["guaranteed_frames"],
                    0,
                )

    def test_portfolios_are_complete_and_native_checked(self) -> None:
        for workload in self.report["workloads"]:
            for observation in workload["observations"]:
                with self.subTest(
                    workload=workload["workload"],
                    mode=observation["mode"],
                ):
                    self.assertEqual(
                        observation["unrestricted_status"],
                        "unresolved",
                    )
                    complete_actions = observation[
                        "complete_root_actions"
                    ]
                    witnesses = observation["action_witnesses"]
                    self.assertEqual(len(complete_actions), 17)
                    self.assertEqual(len(witnesses), 17)
                    self.assertEqual(
                        [witness["root_action"] for witness in witnesses],
                        complete_actions,
                    )
                    parity = observation[
                        "native_selected_witness_parity"
                    ]
                    self.assertEqual(
                        parity["checked_selected_witness_count"],
                        17,
                    )
                    self.assertEqual(parity["mismatch_count"], 0)
                    self.assertEqual(parity["mismatches"], [])


if __name__ == "__main__":
    unittest.main()
