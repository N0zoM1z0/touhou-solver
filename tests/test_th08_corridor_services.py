#!/usr/bin/env python3
"""Tests for corridor audit and prewarm lifecycle ownership."""

from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from th08_corridor_adapter import LoweredCorridorHazards
from th08_corridor_audit import submit_corridor_audit
from th08_corridor_prewarm import (
    close_pipeline_prewarm_owner,
    close_retired_pipeline_prewarm_owners,
    corridor_pipeline_prewarm_query,
    corridor_pipeline_prewarm_retarget,
)
from touhou_control.query_survival import ReachablePipelineRoot


EMPTY_HAZARDS = LoweredCorridorHazards((), (), ())


def submit_arguments(root: Path) -> dict[str, object]:
    return {
        "audit_capsule_dir": root,
        "audit_executor": None,
        "source_frame": 120,
        "snapshot_frame": 100,
        "forecast_lead_frames": 20,
        "player_x": 192.0,
        "player_y": 400.0,
        "snapshot_lag": 2,
        "control_delay_candidates": (1, 2),
        "observed_control_delay_candidates": (2,),
        "nominal_control_delay": 1,
        "active_action": "stay",
        "required_gate_lane": "left",
        "context_key": (0, 3, 57),
        "grid_step": 16.0,
        "frames_per_layer": 8,
        "horizon_frames": 80,
        "bullet_slots": (1, 4),
        "laser_slots": (2,),
        "enemy_pointers": (0x1234,),
        "plan_reachable": True,
        "hazards": EMPTY_HAZARDS,
    }


@dataclass
class Owner:
    pipeline_prewarm_service: object | None


@dataclass
class VersionedOwner(Owner):
    source_frame: int = 100
    snapshot_frame: int | None = 90
    context_key: tuple[int, int, int | None] | None = (0, 3, 57)


class Th08CorridorServicesTests(unittest.TestCase):
    def test_sync_audit_submission_owns_metadata_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch(
                "th08_corridor_audit._write_corridor_audit_capsule",
                return_value=(1.25, None),
            ) as writer:
                submission = submit_corridor_audit(
                    **submit_arguments(root)
                )

        self.assertEqual(
            submission.capsule,
            str(root / "policy_100_120.npz"),
        )
        self.assertEqual(submission.write_ms, 1.25)
        self.assertIsNone(submission.error)
        self.assertIsNone(submission.future)
        metadata = writer.call_args.kwargs["metadata"]
        self.assertEqual(metadata["control_delay_candidates"], (1, 2))
        self.assertEqual(
            metadata["observed_control_delay_candidates"],
            (2,),
        )
        self.assertEqual(metadata["bullet_slots"], [1, 4])
        self.assertEqual(metadata["enemy_pointers"], [0x1234])

    def test_async_audit_future_is_a_separate_handle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                patch(
                    "th08_corridor_audit."
                    "_write_corridor_audit_capsule",
                    return_value=(2.5, "test"),
                ),
                ThreadPoolExecutor(max_workers=1) as executor,
            ):
                arguments = submit_arguments(root)
                arguments["audit_executor"] = executor
                submission = submit_corridor_audit(**arguments)
                self.assertIsNotNone(submission.future)
                assert submission.future is not None
                self.assertEqual(
                    submission.future.result(timeout=2.0),
                    (2.5, "test"),
                )
        self.assertIsNone(submission.write_ms)
        self.assertIsNone(submission.error)

    def test_prewarm_lifecycle_closes_each_unretained_service_once(
        self,
    ) -> None:
        retained_service = Mock()
        retired_service = Mock()
        retained = Owner(retained_service)
        retired = Owner(retired_service)

        close_retired_pipeline_prewarm_owners(
            (retired, retired, retained, None),
            (retained,),
        )
        retained_service.close.assert_not_called()
        retired_service.close.assert_called_once_with()

        close_pipeline_prewarm_owner(retained)
        retained_service.close.assert_called_once_with()

    def test_prewarm_query_keeps_exact_version_and_root_identity(
        self,
    ) -> None:
        result = object()
        snapshot = object()
        problem = Mock(horizon_frames=80)
        problem.project_to_lattice.return_value = (5, 6, 0.25)
        service = Mock(
            policy_version=(100, 90, (0, 3, 57)),
            problem=problem,
        )
        service.lookup.return_value = result
        service.snapshot.return_value = snapshot
        owner = VersionedOwner(service)

        query = corridor_pipeline_prewarm_query(
            owner,
            current_frame=104,
            player_x=192.0,
            player_y=400.0,
            observed_action="stay",
            pending_command=None,
            max_age_frames=79,
        )

        self.assertEqual(query.status, "hit")
        self.assertEqual(
            query.root,
            ReachablePipelineRoot(4, 5, 6, "stay", None),
        )
        self.assertIs(query.result, result)
        self.assertIs(query.service, snapshot)
        service.lookup.assert_called_once_with(query.root)

    def test_prewarm_retarget_preserves_bounded_schedule(self) -> None:
        root = ReachablePipelineRoot(4, 5, 6, "stay", None)
        next_root = ReachablePipelineRoot(8, 7, 8, "left", None)
        service = Mock(
            policy_version=(100, 90, (0, 3, 57)),
            problem=object(),
        )
        service.retarget.return_value = 9
        owner = VersionedOwner(service)
        schedule = SimpleNamespace(
            roots=(next_root,),
            candidate_count=3,
        )

        with patch(
            "th08_corridor_prewarm.schedule_pipeline_frontier",
            return_value=schedule,
        ) as scheduler:
            retarget = corridor_pipeline_prewarm_retarget(
                owner,
                root=root,
                selected_action="left",
                physical_x=188.0,
                physical_y=396.0,
                command_issue_offset=1,
                preferred_decision_frame=5,
            )

        self.assertEqual(retarget.status, "queued")
        self.assertEqual(retarget.revision, 9)
        self.assertEqual(retarget.root_count, 1)
        self.assertEqual(retarget.candidate_root_count, 3)
        self.assertEqual(
            scheduler.call_args.kwargs[
                "scheduling_frame_support"
            ],
            (2, 3, 4, 5, 6, 7, 8, 9),
        )
        self.assertEqual(scheduler.call_args.kwargs["root_limit"], 2)
        service.retarget.assert_called_once_with((next_root,))


if __name__ == "__main__":
    unittest.main()
