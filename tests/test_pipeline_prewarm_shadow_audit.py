#!/usr/bin/env python3
"""Tests for compact physical pipeline-prewarm shadow aggregation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analysis.pipeline_prewarm_shadow_audit import audit


class PipelinePrewarmShadowAuditTests(unittest.TestCase):
    def test_exact_hits_are_grouped_by_policy_ordinal_and_root_frame(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            rows = []
            for index, status in enumerate(("miss", "hit")):
                rows.append(
                    {
                        "kind": "decision",
                        "frame": 104 + index * 4,
                        "read_ms": 10.0 + index,
                        "action_lag": 2 + index,
                        "timing_ms": {
                            "previous_iteration": 40.0 + index,
                            "before_trace": 38.0 + index,
                            "corridor_bookkeeping": 2.0 + index,
                        },
                        "corridor": {
                            "source_frame": 100,
                            "age": 4 + index * 4,
                            "solve_ms": 90.0,
                            "forecast_lead_frames": 16,
                            "policy_status": "queryable",
                            "solver_timing_ms": {
                                "clearance": 12.0,
                                "viability": 70.0,
                                "pre_viability_hook": 0.5,
                            },
                            "pipeline_prewarm_shadow": {
                                "status": status,
                                "lookup_ms": 0.01,
                                "root": {
                                    "frame": 4 + index * 4,
                                },
                                "retarget": {
                                    "status": "queued",
                                    "elapsed_ms": 0.2,
                                    "root_count": 3,
                                },
                                "service": {
                                    "submitted_revision": index + 1,
                                    "completed_revision": 1,
                                    "ready_revision": 1,
                                    "target_replacement_count": 0,
                                    "latest_outcome": {
                                        "revision": 1,
                                        "status": "ready",
                                        "elapsed_ms": 100.0,
                                        "seed_ms": 95.0,
                                        "specialization_ms": 4.0,
                                    },
                                },
                            },
                        },
                    }
                )
            rows.append(
                {
                    "kind": "summary",
                    "termination_reason": "stage_complete",
                    "hit_count": 0,
                }
            )
            trace.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = audit(trace, baseline_dossier=None)

        self.assertEqual(report["hit_rate"]["attempts"], 2)
        self.assertEqual(report["hit_rate"]["hits"], 1)
        self.assertEqual(report["hit_rate"]["rate"], 0.5)
        self.assertEqual(
            report["hit_rate"]["by_decision_ordinal_within_policy"][
                "1"
            ]["hit_rate"],
            0.0,
        )
        self.assertEqual(
            report["hit_rate"]["by_decision_ordinal_within_policy"][
                "2"
            ]["hit_rate"],
            1.0,
        )
        self.assertEqual(
            report["counts"]["unique_target_outcome_count"],
            1,
        )
        self.assertEqual(
            report["policy_lifetime"]["query_decisions"]["median"],
            2.0,
        )


if __name__ == "__main__":
    unittest.main()
