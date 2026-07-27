#!/usr/bin/env python3
"""Exact-root and finite-model checks for the G5 capsule audit."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from analysis.complete_mask_capsule import audit
from analysis.complete_mask_capsule.trace import (
    coverage_from_record,
    identity_from_record,
    read_complete_mask_roots,
)
from analysis.complete_mask_capsule.types import CompleteMaskWorkload
from touhou_control.hazard_coverage import (
    HazardCoverageClass,
    HazardCoverageSlab,
    assess_hazard_coverage,
)
from touhou_control.pipeline_identity import (
    CanonicalPipelineRoot,
    PipelineObservationIdentity,
    PipelineQueryIdentity,
    VersionIdentity,
)
from touhou_control.viability_audit_capsule import (
    write_viability_audit_capsule,
)


def _version(namespace: str, **components: object) -> VersionIdentity:
    return VersionIdentity.from_mapping(namespace, components)


def _identity() -> PipelineQueryIdentity:
    return PipelineQueryIdentity(
        observation=PipelineObservationIdentity.from_coordinates(
            gameplay_epoch=0,
            stage_route_index=3,
            spell_id=None,
            manager_frame=0,
            query_frame=0,
            target_frame=1,
            player_x=192.0,
            player_y=384.0,
        ),
        root=CanonicalPipelineRoot(
            supported_mask=0xF7,
            active_mask=0x05,
            held_desired_mask=0x05,
        ),
        observation_version=_version("observation", precision="float32"),
        hazard_version=_version(
            "hazard",
            available=True,
            snapshot_frame=0,
            source_frame=0,
        ),
        policy_version=_version(
            "policy",
            available=True,
            snapshot_frame=0,
            source_frame=0,
        ),
        model_version=_version("model", complete_mask=True),
        clock_version=_version("clock", ce0120="open"),
    )


def _coverage() -> dict[str, object]:
    version = _version(
        "hazard",
        available=True,
        snapshot_frame=0,
        source_frame=0,
    )
    return assess_hazard_coverage(
        root_frame=0,
        horizon_frame=32,
        slabs=(
            HazardCoverageSlab(
                start_frame=1,
                end_frame=32,
                coverage_class=HazardCoverageClass.UNKNOWN,
                source="unseen_future_events",
                version=version,
                rationale="synthetic fail-closed coverage",
            ),
        ),
    ).record()


def _decision(capsule: str) -> dict[str, object]:
    identity = _identity()
    return {
        "kind": "decision",
        "frame": 1,
        "mask": 0x05,
        "control_delay_candidates": [1],
        "control_delay_frames": 1,
        "corridor": {
            "source_frame": 0,
            "audit_capsule": capsule,
            "viability": {
                "available": True,
                "query_frame": 0,
                "state_viable": False,
            },
        },
        "local_pipeline_root": {
            "canonical_status": "available",
            "canonical_identity": identity.record(),
            "hazard_coverage": _coverage(),
        },
    }


class CompleteMaskCapsuleAuditTests(unittest.TestCase):
    def test_identity_digest_tamper_fails_closed(self) -> None:
        record = _identity().record()
        record["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            identity_from_record(record)

    def test_trace_join_replays_identity_and_unknown_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            trace.write_text(
                json.dumps(_decision("policy_0_0.npz")) + "\n",
                encoding="utf-8",
            )
            roots, failures = read_complete_mask_roots(trace)

        self.assertEqual(failures, [])
        self.assertEqual(len(roots), 1)
        root = roots[0]
        self.assertEqual(root.active_token, "th08_mask_05")
        self.assertEqual(root.held_token, "th08_mask_05")
        self.assertIsNone(root.pending_token)
        self.assertTrue(root.coverage.model_unknown)
        self.assertEqual(root.coverage.unknown_from_frame, 1)

    def test_malformed_coverage_slab_fails_closed(self) -> None:
        record = _coverage()
        record["slabs"].append("not-a-slab")
        with self.assertRaisesRegex(ValueError, "slab is malformed"):
            coverage_from_record(record)

    def test_trace_records_bad_json_and_bad_delay_support(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            bad_delay = _decision("policy_0_0.npz")
            bad_delay["control_delay_candidates"] = [2]
            trace.write_text(
                "{broken\n" + json.dumps(bad_delay) + "\n",
                encoding="utf-8",
            )
            roots, failures = read_complete_mask_roots(trace)

        self.assertEqual(roots, [])
        self.assertEqual(len(failures), 2)
        self.assertIn("line 1: JSONDecodeError", failures[0])
        self.assertIn(
            "nominal control delay is outside its support",
            failures[1],
        )

    def test_report_keeps_finite_witness_separate_from_model_unknown(self) -> None:
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
                    "horizon_frames": 80,
                },
                aabbs=(),
                piecewise_aabbs=(),
                segment_trajectories=(),
            )
            trace = root / "trace.jsonl"
            trace.write_text(
                json.dumps(_decision(str(capsule))) + "\n",
                encoding="utf-8",
            )
            report = audit(
                workloads=(
                    CompleteMaskWorkload(
                        name="synthetic",
                        stage="4A",
                        trace=trace,
                        capsule_dir=capsule_dir,
                        physical_interpretation="synthetic",
                    ),
                ),
                horizon=2,
                decision_frame_support=(1,),
                root_limit=1,
            )

        observation = report["workloads"][0]["observations"][0]
        self.assertEqual(observation["physical_model_status"], "model_unknown")
        self.assertEqual(observation["physical_action_authority"], "none")
        self.assertEqual(len(observation["complete_root_actions"]), 36)
        self.assertEqual(
            observation["continuation_candidates"],
            ("th08_mask_05",),
        )
        self.assertEqual(observation["native_parity"]["mismatch_count"], 0)
        self.assertEqual(
            observation["root_identity"]["sha256"],
            _identity().digest,
        )

    def test_report_records_missing_joined_capsule(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trace = root / "trace.jsonl"
            trace.write_text(
                "".join(
                    json.dumps(_decision("missing.npz")) + "\n"
                    for _index in range(8)
                ),
                encoding="utf-8",
            )
            report = audit(
                workloads=(
                    CompleteMaskWorkload(
                        name="missing",
                        stage="4A",
                        trace=trace,
                        capsule_dir=root,
                        physical_interpretation="synthetic",
                    ),
                ),
                horizon=2,
                decision_frame_support=(1,),
                root_limit=1,
            )

        workload = report["workloads"][0]
        self.assertEqual(workload["read_joined_root_count"], 8)
        self.assertEqual(workload["missing_capsule_count"], 8)
        self.assertEqual(workload["root_validation_failure_count"], 8)
        self.assertEqual(
            workload["root_validation_failure_counts"],
            {"joined capsule is absent: missing.npz": 8},
        )
        self.assertEqual(
            len(workload["root_validation_failure_samples"]),
            6,
        )
        self.assertEqual(workload["audited_root_count"], 0)
        self.assertIn(
            "joined capsule is absent: missing.npz",
            workload["root_validation_failure_samples"][0],
        )


if __name__ == "__main__":
    unittest.main()
