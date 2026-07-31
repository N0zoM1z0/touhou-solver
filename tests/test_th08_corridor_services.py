#!/usr/bin/env python3
"""Tests for corridor audit lifecycle ownership."""

from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from th08_corridor_adapter import LoweredCorridorHazards
from th08_corridor_audit import submit_corridor_audit


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

if __name__ == "__main__":
    unittest.main()
