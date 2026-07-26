from __future__ import annotations

import unittest
from types import SimpleNamespace

from benchmarks.benchmark_supplemental_direct_root_contention import (
    FRAME_MS,
    _deadline_proxy,
    _evaluate_gate,
    _finite_contract_checks,
)


class SupplementalDirectRootContentionGateTests(unittest.TestCase):
    def test_inactive_lane_does_not_claim_historical_or_global_contract(
        self,
    ) -> None:
        shared = {
            "robust_collisions": 0,
            "robust_min_clearance": 1.0,
            "local_collisions": 0,
            "min_clearance": 1.0,
            "terminal_threat_collisions": 0,
            "terminal_threat_min_clearance": 1.0,
            "planned_route_gate_deficit": 0.0,
            "viability_repair_volume": 0,
            "viability_control_reserve_deficit": 0.0,
            "bomb": False,
        }
        baseline = SimpleNamespace(action="left", **shared)
        inactive = SimpleNamespace(
            action="left",
            preloss_continuation_preference_active=False,
            preloss_historical_action=None,
            preloss_supplemental_failure=None,
            **shared,
        )
        issue = SimpleNamespace(
            action="left",
            bomb=False,
            issue_recertification=SimpleNamespace(
                global_constraint_relaxed=True,
            ),
        )

        checks = _finite_contract_checks(
            baseline,
            inactive,
            issue,
            safe_actions={"stay"},
        )

        self.assertFalse(checks["historical_action_mismatch"])
        self.assertFalse(checks["global_membership"])
        self.assertFalse(any(checks.values()))

    def test_deadline_proxy_distinguishes_new_and_existing_miss(self) -> None:
        new_miss = _deadline_proxy(
            recorded_observe_to_input_ms=2.0 * FRAME_MS - 1.0,
            compute_delta_ms=2.0,
            support_high=2,
            post_capture_advance=1,
        )
        self.assertFalse(new_miss["historical_miss"])
        self.assertTrue(new_miss["supplemental_miss"])
        self.assertTrue(new_miss["new_miss"])
        self.assertFalse(new_miss["strict_worst_phase_miss"])

        existing = _deadline_proxy(
            recorded_observe_to_input_ms=2.0 * FRAME_MS + 1.0,
            compute_delta_ms=-5.0,
            support_high=2,
            post_capture_advance=2,
        )
        self.assertTrue(existing["historical_miss"])
        self.assertFalse(existing["supplemental_miss"])
        self.assertFalse(existing["new_miss"])

    def test_fixed_gate_accepts_exact_inclusive_p95_boundary(self) -> None:
        gate = _evaluate_gate(
            violation_counts={"hard": 0},
            invalid_measured_root_count=0,
            worker_limit_applied=True,
            workers4_deltas_ms=[5.0] * 20 + [16.0],
            historical_background={
                "solve_p95_ms": 100.0,
                "solves_per_second": 10.0,
            },
            supplemental_background={
                "solve_p95_ms": 110.0,
                "solves_per_second": 9.0,
            },
            new_deadline_miss_count=0,
            completion_ratio=0.95,
            action_change_retention_ratio=0.90,
            completed_native_reference_mismatch_count=0,
            historical_fallback_mismatch_count=0,
        )
        self.assertTrue(gate["passed"], gate["reasons"])

    def test_fixed_gate_rejects_exclusive_frame_and_contract_failure(
        self,
    ) -> None:
        gate = _evaluate_gate(
            violation_counts={"hard": 1},
            invalid_measured_root_count=0,
            worker_limit_applied=True,
            workers4_deltas_ms=[FRAME_MS],
            historical_background={
                "solve_p95_ms": 100.0,
                "solves_per_second": 10.0,
            },
            supplemental_background={
                "solve_p95_ms": 100.0,
                "solves_per_second": 10.0,
            },
            new_deadline_miss_count=0,
            completion_ratio=0.94,
            action_change_retention_ratio=0.89,
            completed_native_reference_mismatch_count=1,
            historical_fallback_mismatch_count=1,
        )
        self.assertFalse(gate["passed"])
        self.assertTrue(
            any(
                reason.startswith("finite_contract_violations")
                for reason in gate["reasons"]
            )
        )
        self.assertTrue(
            any(
                reason.startswith("workers4_delta_max_ms")
                for reason in gate["reasons"]
            )
        )


if __name__ == "__main__":
    unittest.main()
