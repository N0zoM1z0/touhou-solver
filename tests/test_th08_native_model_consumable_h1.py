from __future__ import annotations

import unittest

from analysis.th08_native_model_consumable_h1 import (
    DEFAULT_WITNESS,
    DEFAULT_WITNESS_SHA256,
    _f32_bits,
    _predict_state_local_step,
    build_report,
)


class NativeModelConsumableH1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = build_report(
            DEFAULT_WITNESS,
            expected_witness_sha256=DEFAULT_WITNESS_SHA256,
        )

    def test_state2_uses_native_half_velocity_with_binary32_store(self) -> None:
        predicted = _predict_state_local_step(
            60.0562629699707,
            0.7221736907958984,
            2,
        )
        self.assertEqual(_f32_bits(predicted), "0x4271AB5E")

    def test_lifecycle_field_closes_all_root_active_h1_mismatches(self) -> None:
        result = self.report["result"]
        self.assertEqual(result["legacy_exact_common_slots"], 664)
        self.assertEqual(result["corrected_exact_common_slots"], 692)
        self.assertEqual(result["common_slot_count"], 692)

        model = self.report["artifacts"]["model_trajectory"]["payload"]
        self.assertEqual(model["status"], "exact")
        self.assertEqual(
            model["legacy_full_velocity"]["mismatch_slots"],
            list(range(1192, 1220)),
        )
        self.assertIsNone(model["state_local_h1"]["first_mismatch"])

    def test_integrated_layer_stops_at_observed_unpredicted_events(self) -> None:
        result = self.report["result"]
        self.assertEqual(result["birth_count"], 7)
        self.assertEqual(result["removal_count"], 4)
        self.assertEqual(result["integrated_hazard_inventory_h1"], "UNKNOWN")

        mismatch = self.report["artifacts"]["first_mismatch_report"]["payload"]
        gap = mismatch["integrated_hazard_inventory_h1"]
        self.assertEqual(gap["status"], "UNKNOWN")
        self.assertEqual(
            gap["first_missing_transition"]["birth_slots"],
            list(range(1220, 1227)),
        )
        self.assertEqual(
            gap["first_missing_transition"]["removal_slots"],
            [87, 120, 545, 710],
        )

    def test_root_is_content_addressed_and_keeps_all_lifecycle_fields(self) -> None:
        root = self.report["artifacts"]["native_hazard_root"]
        self.assertTrue(root["artifact_id"].startswith("sha256:"))
        payload = root["payload"]
        self.assertEqual(payload["state_counts"], {"1": 668, "2": 28})
        self.assertEqual(len(payload["bullets"]), 696)
        state2 = [
            bullet for bullet in payload["bullets"] if bullet["state"] == 2
        ]
        self.assertEqual([bullet["slot"] for bullet in state2], list(range(1192, 1220)))
        self.assertEqual(
            sorted({bullet["timer_d80_elapsed"] for bullet in state2}),
            [2, 4, 6, 8],
        )

    def test_no_physical_evidence_is_claimed(self) -> None:
        self.assertEqual(self.report["result"]["physical_trials_used"], 0)
        self.assertIn(
            "physical promotion",
            self.report["authority"]["not_accepted_for"],
        )


if __name__ == "__main__":
    unittest.main()
