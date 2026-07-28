#!/usr/bin/env python3
"""Tests for the TH08 ECL VM-local projection benchmark gates."""

from __future__ import annotations

import unittest

from benchmarks.th08_ecl_vm_projection_benchmark import run_benchmark


class EclVmProjectionBenchmarkTests(unittest.TestCase):
    def test_small_benchmark_preserves_compatibility_and_payload_gates(
        self,
    ) -> None:
        report = run_benchmark(batches=2, iterations_per_batch=4)

        self.assertTrue(report["passed"])
        self.assertEqual(report["payload"]["projection_vm_read_bytes"], 104)
        self.assertEqual(report["payload"]["vm_read_growth_bytes"], 40)
        self.assertGreater(
            report["payload"]["compact_projection_trace_bytes"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
