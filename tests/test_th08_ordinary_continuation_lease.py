from __future__ import annotations

import unittest

from th08_live.ordinary_continuation_lease import (
    OrdinaryContinuationLease,
    check_continuation_lease_capture,
    check_continuation_lease_issue,
)
from touhou_control.local_pipeline_oracle import (
    LocalPipelineRoot,
    enumerate_delayed_issue_pipeline_branches,
)
from touhou_control.pipeline_identity import VersionIdentity


class OrdinaryContinuationLeaseTests(unittest.TestCase):
    def _lease(self) -> OrdinaryContinuationLease:
        root = LocalPipelineRoot("stay", "stay")
        branches = enumerate_delayed_issue_pipeline_branches(
            root=root,
            selected_action="right_fast",
            issue_delay_frames=(2,),
            pickup_delay_frames=(0, 2),
            horizon_frames=10,
        )
        positions = tuple(
            tuple(
                (100.0 + branch_index * 10.0 + step, 200.0)
                for branch_index in range(len(branches))
            )
            for step in range(11)
        )
        return OrdinaryContinuationLease(
            lease_id="lease-test",
            gameplay_epoch=4,
            stage_route_index=3,
            action="right_fast",
            mask=0x51,
            root_frame=100,
            issue_frame=102,
            horizon_frames=10,
            projection_digest="projection-test",
            projection_source="unit-test",
            projection_version=VersionIdentity.from_mapping(
                "projection-test-v1",
                {"root_frame": 100},
            ),
            pipeline_root=root,
            issue_delay=2,
            pickup_delay_support=(0, 2),
            branches=branches,
            positions_by_step=positions,
            minimum_clearance=3.0,
            fresh_geometry_frame=102,
            fresh_geometry_changed=False,
        )

    def test_active_pickup_conditions_to_matching_branch(self) -> None:
        lease = self._lease()
        # At age four, delay-zero has picked up while delay-two remains old.
        check = check_continuation_lease_capture(
            lease,
            gameplay_epoch=4,
            stage_route_index=3,
            spell_active=False,
            player_phase=0,
            unit_time_scale=True,
            current_frame=104,
            player_x=104.0,
            player_y=200.0,
            pipeline_root=LocalPipelineRoot("right_fast", "right_fast"),
            minimum_remaining_frames=2,
        )

        self.assertTrue(check.valid)
        self.assertEqual(check.matched_branch_count, 1)

    def test_pending_support_must_be_covered_by_old_pickup_branches(self) -> None:
        lease = self._lease()
        valid = check_continuation_lease_capture(
            lease,
            gameplay_epoch=4,
            stage_route_index=3,
            spell_active=False,
            player_phase=0,
            unit_time_scale=True,
            current_frame=103,
            player_x=113.0,
            player_y=200.0,
            pipeline_root=LocalPipelineRoot(
                "stay",
                "right_fast",
                pending_action="right_fast",
                remaining_delay_support=(1,),
            ),
            minimum_remaining_frames=2,
        )
        uncovered = check_continuation_lease_capture(
            lease,
            gameplay_epoch=4,
            stage_route_index=3,
            spell_active=False,
            player_phase=0,
            unit_time_scale=True,
            current_frame=103,
            player_x=113.0,
            player_y=200.0,
            pipeline_root=LocalPipelineRoot(
                "stay",
                "right_fast",
                pending_action="right_fast",
                remaining_delay_support=(0, 1),
            ),
            minimum_remaining_frames=2,
        )

        self.assertTrue(valid.valid)
        self.assertFalse(uncovered.valid)
        self.assertEqual(uncovered.reason, "pending_support_not_covered")

    def test_position_context_and_expiry_revoke_fail_closed(self) -> None:
        lease = self._lease()
        wrong_position = check_continuation_lease_capture(
            lease,
            gameplay_epoch=4,
            stage_route_index=3,
            spell_active=False,
            player_phase=0,
            unit_time_scale=True,
            current_frame=104,
            player_x=104.25,
            player_y=200.0,
            pipeline_root=LocalPipelineRoot("right_fast", "right_fast"),
            minimum_remaining_frames=2,
        )
        wrong_stage = check_continuation_lease_capture(
            lease,
            gameplay_epoch=4,
            stage_route_index=5,
            spell_active=False,
            player_phase=0,
            unit_time_scale=True,
            current_frame=104,
            player_x=104.0,
            player_y=200.0,
            pipeline_root=LocalPipelineRoot("right_fast", "right_fast"),
            minimum_remaining_frames=2,
        )
        expired = check_continuation_lease_capture(
            lease,
            gameplay_epoch=4,
            stage_route_index=3,
            spell_active=False,
            player_phase=0,
            unit_time_scale=True,
            current_frame=109,
            player_x=109.0,
            player_y=200.0,
            pipeline_root=LocalPipelineRoot("right_fast", "right_fast"),
            minimum_remaining_frames=2,
        )

        self.assertEqual(
            wrong_position.reason,
            "pipeline_branch_or_position_mismatch",
        )
        self.assertEqual(wrong_stage.reason, "stage_route_mismatch")
        self.assertEqual(expired.reason, "terminal_continuation_expired")

    def test_issue_cannot_change_direction_without_new_predecessor(self) -> None:
        lease = self._lease()
        retained = check_continuation_lease_issue(
            lease,
            gameplay_epoch=4,
            stage_route_index=3,
            spell_active=False,
            player_phase=0,
            issue_frame=105,
            selected_action="right_fast",
            selected_mask=0x51,
            minimum_remaining_frames=2,
        )
        switched = check_continuation_lease_issue(
            lease,
            gameplay_epoch=4,
            stage_route_index=3,
            spell_active=False,
            player_phase=0,
            issue_frame=105,
            selected_action="left_fast",
            selected_mask=0x41,
            minimum_remaining_frames=2,
        )

        self.assertTrue(retained.valid)
        self.assertFalse(switched.valid)
        self.assertEqual(
            switched.reason,
            "selected_action_changed_without_predecessor",
        )


if __name__ == "__main__":
    unittest.main()
