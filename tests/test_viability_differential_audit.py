#!/usr/bin/env python3
"""Tests for the retained-capsule differential audit."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from touhou_control.viability_audit_capsule import (
    write_viability_audit_capsule,
)
from touhou_control.packed_hazards import PackedSegmentFrames
from analysis.viability_differential_audit import (
    _classify_empty_query,
    _empty_rescue_factors,
    _packed_horizon_prefix,
    _select_query_rows,
    audit,
)


class ViabilityDifferentialAuditTests(unittest.TestCase):
    def test_stratified_selection_covers_both_warning_boundaries(self) -> None:
        rows = [{"frame": frame} for frame in range(9)]
        selected = _select_query_rows(
            rows,
            limit=3,
            mode="stratified",
        )
        self.assertEqual(
            tuple(row["frame"] for row in selected),
            (0, 4, 8),
        )

    def test_short_horizon_slices_packed_laser_frames(self) -> None:
        packed = PackedSegmentFrames.from_frame_rows(
            tuple(
                ((float(frame), 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0),)
                for frame in range(5)
            )
        )
        prefix = _packed_horizon_prefix(packed, frame_count=3)
        self.assertIsNotNone(prefix)
        assert prefix is not None
        self.assertEqual(prefix.frame_count, 3)
        self.assertEqual(prefix.sample_count, 3)
        self.assertEqual(tuple(prefix.origin_x), (0.0, 1.0, 2.0))

    def test_empty_rescue_factors_remain_independent(self) -> None:
        self.assertEqual(
            _empty_rescue_factors(
                trace_empty=True,
                current_delay_viable=True,
                spatial_variant_viable=True,
                uncertainty_no_growth_viable=False,
                uncertainty_none_viable=True,
                short_horizon_viable=True,
            ),
            (
                "full_async_delay_envelope",
                "spatial_quantization",
                "base_or_forecast_uncertainty",
                "finite_horizon_requirement",
            ),
        )

    def test_future_birth_is_evidence_not_the_cause_of_an_empty_kernel(
        self,
    ) -> None:
        classification, evidence = _classify_empty_query(
            trace_empty=True,
            base_matches_trace=True,
            base_viable=False,
            spatial_variant_viable=False,
            fresh_policy_differs=False,
            fresh_viable=False,
            short_horizon_viable=False,
            collision_hazard_absent_at_source=True,
        )
        self.assertEqual(classification, "modeled_losing_unresolved")
        self.assertEqual(evidence, ("hazard_model_future_birth_gap",))

    def test_recomputed_base_disagreement_is_not_called_coarse_empty(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsule_dir = root / "capsules"
            capsule = capsule_dir / "policy_0_0.npz"
            write_viability_audit_capsule(
                capsule,
                metadata={
                    "source_frame": 0,
                    "snapshot_frame": 0,
                    "forecast_lead_frames": 0,
                    "player_x": 192.0,
                    "player_y": 384.0,
                    "snapshot_lag": 0,
                    "control_delay_candidates": [1, 2, 3, 4, 5, 6],
                    "nominal_control_delay": 2,
                    "active_action": "stay",
                    "required_gate_lane": None,
                    "context_key": [0, 5, None],
                    "grid_step": 16.0,
                    "frames_per_layer": 8,
                    "horizon_frames": 80,
                    "bullet_slots": [],
                    "laser_slots": [],
                    "enemy_pointers": [],
                    "plan_reachable": True,
                },
                aabbs=(),
                piecewise_aabbs=(),
                segment_trajectories=(),
            )
            trace = root / "trace.jsonl"
            rows = [
                {
                    "kind": "decision",
                    "frame": 10,
                    "hit_started": False,
                    "spell": {"spell_id": 0},
                    "player": {
                        "projected_x": 192.0,
                        "projected_y": 384.0,
                    },
                    "corridor": {
                        "source_frame": 0,
                        "snapshot_frame": 0,
                        "audit_capsule": (
                            r"\\wsl.localhost\ubuntu\tmp\policy_0_0.npz"
                        ),
                        "viability": {
                            "available": True,
                            "state_viable": False,
                            "query_frame": 10,
                            "layer": 1,
                            "active_action": "stay",
                            "position_error": 0.0,
                        },
                    },
                },
                {
                    "kind": "decision",
                    "frame": 20,
                    "hit_started": True,
                },
            ]
            trace.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            # This is a classification/wiring regression, not a performance
            # benchmark.  The old test recomputed every 16/8/4-pixel audit
            # variant and spent ~8.6 seconds proving a one-bit disagreement.
            # Full native solves belong in retained capsule experiments.
            recomputed = {
                "available": True,
                "state_viable": True,
                "safe_action_count": 1,
                "layer": 1,
                "row": 0,
                "column": 0,
                "position_error": 0.0,
            }
            with (
                patch(
                    "analysis.viability_differential_audit.AuditSolver.solve",
                    return_value=object(),
                ),
                patch(
                    "analysis.viability_differential_audit._query_payload",
                    return_value=recomputed,
                ),
            ):
                report = audit(
                    trace_path=trace,
                    capsule_dir=capsule_dir,
                    regressions_path=None,
                    pre_hit_frames=16,
                    max_queries_per_hit=8,
                )
        self.assertEqual(report["scope"]["audited_empty_queries"], 1)
        labels = report["observations"][0]["labels"]
        self.assertIn(
            "policy_reconstruction_or_version_mismatch",
            labels,
        )
        self.assertNotIn("spatial_coarse_false_empty", labels)
        self.assertEqual(
            report["model_constraints"]["diagnostic_only_variants"],
            ["space8_time4_h80_delay_clipped"],
        )


if __name__ == "__main__":
    unittest.main()
