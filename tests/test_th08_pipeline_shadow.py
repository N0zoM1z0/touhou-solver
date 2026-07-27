from __future__ import annotations

import unittest
from dataclasses import dataclass

from th08_live.pipeline_shadow import build_pipeline_shadow_snapshot
from touhou_control.delay import PendingCommandEstimate


@dataclass(frozen=True)
class _Solution:
    source_frame: int = 90
    snapshot_frame: int = 88
    context_key: tuple[int, int, int | None] = (3, 1, 42)


def _action(mask: int) -> str:
    return f"mask_{mask:02x}"


class Th08PipelineShadowTests(unittest.TestCase):
    def test_pending_multikey_root_retains_complete_masks(self) -> None:
        snapshot = build_pipeline_shadow_snapshot(
            supported_mask=0xF7,
            native_active_mask=0x81,
            held_desired_mask=0x55,
            pending_estimate=PendingCommandEstimate(
                expected_mask=0x55,
                remaining_frames=(1, 2),
                snapshot_age=2,
                issue_age=1,
                overdue=False,
            ),
            action_from_mask=_action,
            gameplay_epoch=3,
            stage_route_index=1,
            spell_id=42,
            manager_frame=100,
            query_frame=102,
            target_frame=105,
            player_x=192.0,
            player_y=384.0,
            hazard_horizon_frames=32,
            corridor_solution=_Solution(),
        )

        self.assertIsNotNone(snapshot.local_root)
        self.assertIsNotNone(snapshot.canonical_identity)
        self.assertEqual(snapshot.record["pending_mask"], 0x55)
        self.assertEqual(
            snapshot.record["canonical_identity"]["root"]["pending_mask"],
            0x55,
        )
        self.assertEqual(
            snapshot.record["hazard_coverage"]["status"],
            "model_unknown",
        )
        self.assertEqual(
            snapshot.record["hazard_coverage"]["root_frame"],
            102,
        )
        self.assertEqual(
            snapshot.record["hazard_coverage"]["unknown_from_frame"],
            103,
        )
        self.assertEqual(
            snapshot.record["clock_authority"],
            "shadow_no_reset_authority",
        )

    def test_no_pending_root_requires_native_pickup(self) -> None:
        snapshot = build_pipeline_shadow_snapshot(
            supported_mask=0xF7,
            native_active_mask=0x81,
            held_desired_mask=0x41,
            pending_estimate=None,
            action_from_mask=_action,
            gameplay_epoch=3,
            stage_route_index=1,
            spell_id=None,
            manager_frame=100,
            query_frame=100,
            target_frame=103,
            player_x=192.0,
            player_y=384.0,
            hazard_horizon_frames=10,
            corridor_solution=None,
        )

        self.assertIsNone(snapshot.local_root)
        self.assertIsNone(snapshot.canonical_identity)
        self.assertFalse(snapshot.record["estimator_consistent"])
        self.assertEqual(
            snapshot.record["canonical_status"],
            "estimator_inconsistent",
        )

    def test_identity_changes_with_corridor_version(self) -> None:
        arguments = {
            "supported_mask": 0xF7,
            "native_active_mask": 0x81,
            "held_desired_mask": 0x81,
            "pending_estimate": None,
            "action_from_mask": _action,
            "gameplay_epoch": 3,
            "stage_route_index": 1,
            "spell_id": 42,
            "manager_frame": 100,
            "query_frame": 102,
            "target_frame": 105,
            "player_x": 192.0,
            "player_y": 384.0,
            "hazard_horizon_frames": 32,
        }
        first = build_pipeline_shadow_snapshot(
            **arguments,
            corridor_solution=_Solution(source_frame=90),
        )
        second = build_pipeline_shadow_snapshot(
            **arguments,
            corridor_solution=_Solution(source_frame=91),
        )

        assert first.canonical_identity is not None
        assert second.canonical_identity is not None
        self.assertNotEqual(
            first.canonical_identity.digest,
            second.canonical_identity.digest,
        )


if __name__ == "__main__":
    unittest.main()
