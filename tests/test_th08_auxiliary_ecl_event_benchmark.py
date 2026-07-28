from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from benchmarks.auxiliary_ecl_event.runner import (
    BATCH_WORKLOAD,
    REPORT_AUTHORITY,
    REPORT_SCHEMA,
    run_benchmark,
)
from benchmarks.auxiliary_ecl_event.workload import (
    EXPECTED_ECL_SHA256,
    load_fixture,
)


class AuxiliaryEclEventBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = (
            Path(__file__).resolve().parents[1]
            / "artifacts"
            / "decoded"
            / "ecldata5.ecl"
        )

    def test_fixed_workload_identity_and_distribution(self) -> None:
        fixture = load_fixture(self.path)
        self.assertEqual(fixture.ecl_sha256, EXPECTED_ECL_SHA256)
        self.assertEqual(
            hashlib.sha256(self.path.read_bytes()).hexdigest(),
            EXPECTED_ECL_SHA256,
        )
        batch = fixture.workloads[BATCH_WORKLOAD]
        self.assertEqual(len(batch), 34)
        self.assertEqual(
            {
                subroutine: sum(
                    context.subroutine_index == subroutine
                    for context in batch
                )
                for subroutine in (69, 72, 73)
            },
            {69: 8, 72: 9, 73: 17},
        )

    def test_report_schema_and_gate(self) -> None:
        report = run_benchmark(self.path, iterations=8, warmup=1)
        self.assertEqual(report["schema"], REPORT_SCHEMA)
        self.assertEqual(report["authority"], REPORT_AUTHORITY)
        self.assertEqual(report["fixture"]["batch_workload"], BATCH_WORKLOAD)
        self.assertTrue(report["gate"]["passed"])
        batch = report["workloads"][BATCH_WORKLOAD]
        self.assertEqual(batch["context_count"], 34)
        self.assertEqual(batch["intent_count"], 102)
        self.assertGreater(batch["serialized_bytes"], 0)
        combined = batch["timing"]["lower_and_serialize"]
        self.assertIn("gc_overlap_sample_count", combined)
        self.assertIn("non_gc_max_ms", combined)


if __name__ == "__main__":
    unittest.main()
