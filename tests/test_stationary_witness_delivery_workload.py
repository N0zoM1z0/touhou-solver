#!/usr/bin/env python3
"""Deterministic reservoir and fail-closed gate tests."""

from __future__ import annotations

from types import SimpleNamespace
import unittest

from benchmarks.stationary_witness_delivery.gate import evaluate_gate
from benchmarks.stationary_witness_delivery.workload import (
    select_physical_roots,
)


def _root(frame: int, viable: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        decision_frame=frame,
        trace_state_viable=viable,
        identity=SimpleNamespace(digest=f"root-{frame}"),
    )


class StationaryWitnessDeliveryWorkloadTests(unittest.TestCase):
    def test_fixed_reservoir_keeps_first_eight_and_last_before_hits(self) -> None:
        roots = [_root(frame) for frame in range(1, 21)]
        selected = select_physical_roots(
            roots,
            hit_frames=(12, 17),
        )
        self.assertEqual(
            tuple(root.decision_frame for root in selected),
            (1, 2, 3, 4, 5, 6, 7, 8, 11, 16),
        )

    def test_missing_prehit_root_fails_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "precedes hit"):
            select_physical_roots(
                [_root(frame) for frame in range(10, 20)],
                hit_frames=(5,),
            )

    def test_gate_reports_missing_completion_samples_as_failure(self) -> None:
        variant = {
            "completion_ratio": 0.0,
            "complete_publication": None,
            "partial_publication_count": 0,
            "lookup_failure_count": 0,
            "errors": [],
            "worker_priority_lowered": True,
        }
        workers = {
            **variant,
            "background_viability": {
                "worker_limit_applied": True,
                "priority_lowered": False,
                "throughput_per_second": 0.0,
                "solve": None,
            },
        }
        result = evaluate_gate(
            preparation={"selected_root_count": 18},
            measurements={
                "idle": variant,
                "workers4": workers,
                "workers4_idle_witness_control": {
                    "throughput_per_second": 0.0,
                    "solve": None,
                },
                "rapid_replacement": {
                    "active_cancellation_count": 0,
                    "cancellation_ack": None,
                    "stale_lookup_count": 0,
                    "partial_publication_count": 0,
                },
            },
            abi={"passed": True},
            authoritative_windows_run=True,
        )
        self.assertFalse(result["passed"])
        self.assertFalse(
            result["conditions"][
                "workers4_publication_p95_at_most_8_ms"
            ]
        )


if __name__ == "__main__":
    unittest.main()
