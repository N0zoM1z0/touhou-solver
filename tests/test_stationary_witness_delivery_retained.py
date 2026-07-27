#!/usr/bin/env python3
"""Contract checks for retained Windows delivery evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "benchmarks"


def _read(name: str) -> tuple[dict[str, object], str]:
    payload = (ARTIFACTS / name).read_bytes()
    return json.loads(payload), hashlib.sha256(payload).hexdigest()


class RetainedStationaryWitnessDeliveryTests(unittest.TestCase):
    def test_two_pcore_gates_and_rejected_variants_remain_explicit(self) -> None:
        expected = (
            (
                "stationary_witness_windows_delivery_pcore_affinity_"
                "20260728.json",
                "ed9f60d8ce46c834bca54263d2c1ce03"
                "d3c9ddb377f597a91864ba896e71e11f",
                "fda6a1a0997e30cf5bbe73b58c18cfe7"
                "ca7a9cfc464566b12a68f6d8eb8acd88",
            ),
            (
                "stationary_witness_windows_delivery_pcore_affinity_"
                "repeat2_20260728.json",
                "8e6c03a0b6221b5bf984b070762c2578"
                "9ce8275940d93e83ebb248cac23ddb0b",
                "10868c9595804bf7b4c4f39d9ee9223a"
                "bd14e8816b83356dd202e1cbdc5556f7",
            ),
        )
        for name, report_digest, file_digest in expected:
            with self.subTest(name=name):
                report, observed_file_digest = _read(name)
                self.assertEqual(observed_file_digest, file_digest)
                self.assertEqual(report["report_sha256"], report_digest)
                self.assertTrue(report["gate"]["passed"])
                self.assertTrue(all(
                    report["gate"]["conditions"].values()
                ))
                self.assertEqual(report["physical_action_authority"], "none")
                self.assertEqual(
                    report["preparation"]["selected_root_count"],
                    18,
                )
                self.assertEqual(
                    report["measurements"]["workers4"][
                        "worker_affinity_cpu"
                    ],
                    11,
                )
                self.assertEqual(
                    report["production_abi"]["manifest_symbol_count"],
                    46,
                )
        unpinned, _ = _read(
            "stationary_witness_windows_delivery_optimized_"
            "repeat2_20260728.json"
        )
        self.assertFalse(unpinned["gate"]["passed"])
        self.assertFalse(
            unpinned["gate"]["conditions"][
                "viability_p95_ratio_at_most_1_10"
            ]
        )
        ecore, _ = _read(
            "stationary_witness_windows_delivery_affinity_20260728.json"
        )
        self.assertFalse(ecore["gate"]["passed"])
        self.assertFalse(
            ecore["gate"]["conditions"][
                "workers4_publication_p95_at_most_8_ms"
            ]
        )


if __name__ == "__main__":
    unittest.main()
