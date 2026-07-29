#!/usr/bin/env python3
"""Tests for the exact ECL VM-local shadow benchmark gates."""

from __future__ import annotations

import unittest
from pathlib import Path

from benchmarks.th08_ecl_vm_local_shadow_benchmark import run_benchmark


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "artifacts"
    / "ecl_reports"
    / "stage4a_vm_local_op05_cases_sem_timer_v2_20260729.json"
)


class EclVmLocalShadowBenchmarkTests(unittest.TestCase):
    def test_small_benchmark_preserves_all_exact_cases(self) -> None:
        report = run_benchmark(
            fixture_path=FIXTURE,
            batches=1,
            iterations_per_batch=1,
        )

        self.assertTrue(report["passed"])
        self.assertEqual(report["input"]["unique_cases"], 108)
        self.assertEqual(
            report["logical_work"]["vm_instructions_per_transition"],
            1,
        )
        self.assertGreater(
            report["logical_work"]["python_bytecode_ops_per_transition"]["p50"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
