from __future__ import annotations

import unittest

from touhou_control.local_pipeline_oracle import (
    LocalPipelineRoot,
    enumerate_local_pipeline_branches,
    scalar_local_pipeline_certificates,
)


class LocalPipelineOracleTests(unittest.TestCase):
    def test_pending_hold_is_no_write_and_does_not_reset_delay(self) -> None:
        root = LocalPipelineRoot(
            active_action="stay",
            held_desired_action="left",
            pending_action="left",
            remaining_delay_support=(2,),
        )

        branches = enumerate_local_pipeline_branches(
            root=root,
            selected_action="left",
            delay_frames=(3,),
            horizon_frames=5,
        )

        self.assertEqual(len(branches), 1)
        self.assertFalse(branches[0].write_required)
        self.assertIsNone(branches[0].new_delay)
        self.assertEqual(
            branches[0].active_actions,
            ("stay", "stay", "left", "left", "left"),
        )

    def test_new_write_preserves_older_pending_until_new_pickup(self) -> None:
        root = LocalPipelineRoot(
            active_action="stay",
            held_desired_action="left",
            pending_action="left",
            remaining_delay_support=(2,),
        )

        branches = enumerate_local_pipeline_branches(
            root=root,
            selected_action="right",
            delay_frames=(3,),
            horizon_frames=5,
        )

        self.assertEqual(len(branches), 1)
        self.assertTrue(branches[0].write_required)
        self.assertEqual(
            branches[0].active_actions,
            ("stay", "stay", "left", "right", "right"),
        )

    def test_hidden_remaining_and_new_delay_form_universal_branches(
        self,
    ) -> None:
        root = LocalPipelineRoot(
            active_action="stay",
            held_desired_action="left",
            pending_action="left",
            remaining_delay_support=(1, 2),
        )

        branches = enumerate_local_pipeline_branches(
            root=root,
            selected_action="right",
            delay_frames=(2, 3),
            horizon_frames=4,
        )

        self.assertEqual(len(branches), 4)
        self.assertEqual(
            {
                (
                    branch.older_remaining,
                    branch.new_delay,
                    branch.active_actions,
                )
                for branch in branches
            },
            {
                (1, 2, ("stay", "left", "right", "right")),
                (1, 3, ("stay", "left", "left", "right")),
                (2, 2, ("stay", "stay", "right", "right")),
                (2, 3, ("stay", "stay", "left", "right")),
            },
        )

    def test_scalar_certificate_finds_pending_prefix_collision(self) -> None:
        root = LocalPipelineRoot(
            active_action="stay",
            held_desired_action="left",
            pending_action="left",
            remaining_delay_support=(1, 2),
        )

        def sample(
            x: float,
            _y: float,
            step: int,
        ) -> tuple[float, int, float]:
            clearance = -1.0 if step == 2 and x < 0.0 else 2.0
            return (0.0, int(clearance < 0.0), clearance)

        certificates = scalar_local_pipeline_certificates(
            root=root,
            selected_actions=("left", "right"),
            action_velocities={
                "stay": (0.0, 0.0),
                "left": (-1.0, 0.0),
                "right": (1.0, 0.0),
            },
            delay_frames=(2, 3),
            horizon_frames=4,
            start_x=0.0,
            start_y=0.0,
            bounds=(-10.0, 10.0, -10.0, 10.0),
            hazard_sample=sample,
            boundary_risk=lambda _x, _y: 0.0,
        )

        self.assertFalse(certificates["left"].write_required)
        self.assertEqual(certificates["left"].branch_count, 2)
        self.assertEqual(certificates["left"].worst_collisions, 1)
        self.assertTrue(certificates["right"].write_required)
        self.assertEqual(certificates["right"].branch_count, 4)
        self.assertEqual(certificates["right"].worst_collisions, 1)

    def test_rejects_inconsistent_one_pending_root(self) -> None:
        with self.assertRaisesRegex(ValueError, "held desired"):
            LocalPipelineRoot(
                active_action="stay",
                held_desired_action="right",
            )
        with self.assertRaisesRegex(ValueError, "held desired"):
            LocalPipelineRoot(
                active_action="stay",
                held_desired_action="left",
                pending_action="right",
                remaining_delay_support=(1,),
            )


if __name__ == "__main__":
    unittest.main()
