#!/usr/bin/env python3
"""Selection and witness gates for the first-loss capsule experiment."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from analysis.first_loss_capsule import (
    audit,
    select_first_loss_bracket,
)
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


def _hazard_version() -> VersionIdentity:
    return _version(
        "hazard",
        available=True,
        snapshot_frame=0,
        source_frame=0,
    )


def _identity(
    *,
    query_frame: int,
    gameplay_epoch: int,
    stage_route_index: int,
) -> PipelineQueryIdentity:
    return PipelineQueryIdentity(
        observation=PipelineObservationIdentity.from_coordinates(
            gameplay_epoch=gameplay_epoch,
            stage_route_index=stage_route_index,
            spell_id=None,
            manager_frame=query_frame,
            query_frame=query_frame,
            target_frame=query_frame + 1,
            player_x=192.0,
            player_y=384.0,
        ),
        root=CanonicalPipelineRoot(
            supported_mask=0xF7,
            active_mask=0x05,
            held_desired_mask=0x05,
        ),
        observation_version=_version(
            "observation",
            precision="float32",
        ),
        hazard_version=_hazard_version(),
        policy_version=_version(
            "policy",
            available=True,
            snapshot_frame=0,
            source_frame=0,
        ),
        model_version=_version("model", complete_mask=True),
        clock_version=_version("clock", ce0120="open"),
    )


def _coverage(query_frame: int) -> dict[str, object]:
    return assess_hazard_coverage(
        root_frame=query_frame,
        horizon_frame=query_frame + 32,
        slabs=(
            HazardCoverageSlab(
                start_frame=query_frame + 1,
                end_frame=query_frame + 32,
                coverage_class=HazardCoverageClass.UNKNOWN,
                source="unseen_future_events",
                version=_hazard_version(),
                rationale="synthetic fail-closed coverage",
            ),
        ),
    ).record()


def _decision(
    *,
    decision_frame: int,
    query_frame: int,
    state_viable: bool,
    capsule: str | None,
    gameplay_epoch: int = 0,
    stage_route_index: int = 5,
    hit_started: bool = False,
) -> dict[str, object]:
    identity = _identity(
        query_frame=query_frame,
        gameplay_epoch=gameplay_epoch,
        stage_route_index=stage_route_index,
    )
    return {
        "kind": "decision",
        "frame": decision_frame,
        "gameplay_epoch": gameplay_epoch,
        "stage_route_index": stage_route_index,
        "hit_started": hit_started,
        "mask": 0x05,
        "control_delay_candidates": [1],
        "control_delay_frames": 1,
        "corridor": {
            "source_frame": 0,
            "audit_capsule": capsule,
            "viability": {
                "available": True,
                "query_frame": query_frame,
                "state_viable": state_viable,
            },
        },
        "local_pipeline_root": {
            "canonical_status": "available",
            "canonical_identity": identity.record(),
            "hazard_coverage": _coverage(query_frame),
        },
    }


def _write_trace(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_empty_capsule(path: Path) -> None:
    write_viability_audit_capsule(
        path,
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


class FirstLossCapsuleAuditTests(unittest.TestCase):
    def test_selects_first_uninterrupted_exact_bracket(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsules = root / "capsules"
            capsule = capsules / "policy_0_0.npz"
            _write_empty_capsule(capsule)
            trace = root / "trace.jsonl"
            _write_trace(
                trace,
                [
                    _decision(
                        decision_frame=1,
                        query_frame=0,
                        state_viable=True,
                        capsule=str(capsule),
                    ),
                    _decision(
                        decision_frame=2,
                        query_frame=1,
                        state_viable=False,
                        capsule=str(capsule),
                        hit_started=True,
                    ),
                ],
            )
            selection = select_first_loss_bracket(
                trace=trace,
                capsule_dir=capsules,
            )

        self.assertEqual(selection.status, "selected")
        self.assertIsNotNone(selection.bracket)
        assert selection.bracket is not None
        self.assertEqual(selection.bracket.last_viable.decision_frame, 1)
        self.assertEqual(selection.bracket.first_losing.decision_frame, 2)
        self.assertEqual(selection.root_validation_failures, ())

    def test_unavailable_query_breaks_bracket_continuity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsules = root / "capsules"
            capsule = capsules / "policy_0_0.npz"
            _write_empty_capsule(capsule)
            unavailable = {
                "kind": "decision",
                "frame": 2,
                "gameplay_epoch": 0,
                "stage_route_index": 5,
                "corridor": {
                    "viability": {
                        "available": False,
                        "state_viable": False,
                    },
                },
            }
            trace = root / "trace.jsonl"
            _write_trace(
                trace,
                [
                    _decision(
                        decision_frame=1,
                        query_frame=0,
                        state_viable=True,
                        capsule=str(capsule),
                    ),
                    unavailable,
                    _decision(
                        decision_frame=3,
                        query_frame=2,
                        state_viable=False,
                        capsule=str(capsule),
                        hit_started=True,
                    ),
                ],
            )
            selection = select_first_loss_bracket(
                trace=trace,
                capsule_dir=capsules,
            )

        self.assertEqual(selection.status, "unresolved_pre_hit_loss")
        self.assertEqual(
            selection.unresolved["reason"],
            "no_uninterrupted_exact_viable_predecessor",
        )
        self.assertEqual(
            dict(selection.interruption_counts)[
                "viability_query_unavailable"
            ],
            1,
        )

    def test_missing_capsule_leaves_first_loss_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trace = root / "trace.jsonl"
            _write_trace(
                trace,
                [
                    _decision(
                        decision_frame=1,
                        query_frame=0,
                        state_viable=True,
                        capsule=None,
                    ),
                    _decision(
                        decision_frame=2,
                        query_frame=1,
                        state_viable=False,
                        capsule=None,
                        hit_started=True,
                    ),
                ],
            )
            selection = select_first_loss_bracket(
                trace=trace,
                capsule_dir=root / "capsules",
            )

        self.assertEqual(selection.status, "unresolved_pre_hit_loss")
        self.assertEqual(
            selection.unresolved["reason"],
            "audit_capsule_missing",
        )
        self.assertIsNone(selection.bracket)

    def test_epoch_change_requires_a_new_viable_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsules = root / "capsules"
            capsule = capsules / "policy_0_0.npz"
            _write_empty_capsule(capsule)
            trace = root / "trace.jsonl"
            _write_trace(
                trace,
                [
                    _decision(
                        decision_frame=1,
                        query_frame=0,
                        state_viable=True,
                        capsule=str(capsule),
                    ),
                    _decision(
                        decision_frame=2,
                        query_frame=1,
                        state_viable=True,
                        capsule=str(capsule),
                        gameplay_epoch=1,
                    ),
                    _decision(
                        decision_frame=3,
                        query_frame=2,
                        state_viable=False,
                        capsule=str(capsule),
                        gameplay_epoch=1,
                        hit_started=True,
                    ),
                ],
            )
            selection = select_first_loss_bracket(
                trace=trace,
                capsule_dir=capsules,
            )

        self.assertEqual(selection.status, "selected")
        assert selection.bracket is not None
        self.assertEqual(
            selection.bracket.last_viable.identity.observation.gameplay_epoch,
            1,
        )
        self.assertEqual(
            dict(selection.interruption_counts)["physical_scope_changed"],
            1,
        )

    def test_malformed_losing_identity_cannot_be_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsules = root / "capsules"
            capsule = capsules / "policy_0_0.npz"
            _write_empty_capsule(capsule)
            losing = _decision(
                decision_frame=2,
                query_frame=1,
                state_viable=False,
                capsule=str(capsule),
                hit_started=True,
            )
            losing["local_pipeline_root"]["canonical_identity"][
                "sha256"
            ] = "0" * 64
            trace = root / "trace.jsonl"
            _write_trace(
                trace,
                [
                    _decision(
                        decision_frame=1,
                        query_frame=0,
                        state_viable=True,
                        capsule=str(capsule),
                    ),
                    losing,
                ],
            )
            selection = select_first_loss_bracket(
                trace=trace,
                capsule_dir=capsules,
            )

        self.assertEqual(selection.status, "unresolved_pre_hit_loss")
        self.assertEqual(
            selection.unresolved["reason"],
            "joined_root_invalid",
        )
        self.assertEqual(len(selection.root_validation_failures), 1)

    def test_report_completes_all_root_and_stationary_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsules = root / "capsules"
            capsule = capsules / "policy_0_0.npz"
            _write_empty_capsule(capsule)
            trace = root / "trace.jsonl"
            _write_trace(
                trace,
                [
                    _decision(
                        decision_frame=1,
                        query_frame=0,
                        state_viable=True,
                        capsule=str(capsule),
                    ),
                    _decision(
                        decision_frame=2,
                        query_frame=1,
                        state_viable=False,
                        capsule=str(capsule),
                        hit_started=True,
                    ),
                ],
            )
            first = audit(
                trace=trace,
                capsule_dir=capsules,
                horizon=2,
                decision_frame_support=(1,),
            )
            second = audit(
                trace=trace,
                capsule_dir=capsules,
                horizon=2,
                decision_frame_support=(1,),
            )

        self.assertTrue(first["passed"])
        self.assertEqual(first["report_digest"], second["report_digest"])
        self.assertTrue(
            first["conclusions"]["finite_model_audit_passed"]
        )
        self.assertFalse(
            first["conclusions"]["physical_survival_claim_available"]
        )
        self.assertFalse(
            first["conclusions"]["strategy_promotion_available"]
        )
        for role in ("g4_last_viable", "g3_first_losing"):
            observation = first["observations"][role]
            self.assertEqual(len(observation["complete_root_actions"]), 36)
            self.assertEqual(
                len(observation["continuation_candidates"]),
                36,
            )
            self.assertEqual(observation["continuation_mode"], "all_actions")
            self.assertEqual(
                observation["native_parity"]["mismatch_count"],
                0,
            )
            self.assertEqual(
                observation["physical_action_authority"],
                "none",
            )

    def test_recovered_loss_episode_is_skipped_before_target_hit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsules = root / "capsules"
            capsule = capsules / "policy_0_0.npz"
            _write_empty_capsule(capsule)
            trace = root / "trace.jsonl"
            _write_trace(
                trace,
                [
                    _decision(
                        decision_frame=1,
                        query_frame=0,
                        state_viable=True,
                        capsule=str(capsule),
                    ),
                    _decision(
                        decision_frame=2,
                        query_frame=1,
                        state_viable=False,
                        capsule=str(capsule),
                    ),
                    _decision(
                        decision_frame=3,
                        query_frame=2,
                        state_viable=True,
                        capsule=str(capsule),
                    ),
                    _decision(
                        decision_frame=4,
                        query_frame=3,
                        state_viable=False,
                        capsule=str(capsule),
                    ),
                    _decision(
                        decision_frame=5,
                        query_frame=4,
                        state_viable=False,
                        capsule=str(capsule),
                        hit_started=True,
                    ),
                ],
            )
            selection = select_first_loss_bracket(
                trace=trace,
                capsule_dir=capsules,
            )

        self.assertEqual(selection.status, "selected")
        self.assertEqual(selection.recovered_loss_episodes, 1)
        self.assertEqual(selection.target_hit_frame, 5)
        assert selection.bracket is not None
        self.assertEqual(selection.bracket.last_viable.decision_frame, 3)
        self.assertEqual(selection.bracket.first_losing.decision_frame, 4)


if __name__ == "__main__":
    unittest.main()
