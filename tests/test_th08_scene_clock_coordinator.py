from __future__ import annotations

import unittest

from th08_live import SceneClockCoordinator


class SceneClockCoordinatorTests(unittest.TestCase):
    def test_coordinator_owns_scene_confirm_and_optional_clock_state(
        self,
    ) -> None:
        coordinator = SceneClockCoordinator.create(
            auto_confirm_interval_frames=15,
            auto_confirm_idle_frames=20,
            stage_successors={1: 2},
            transition_timeout_seconds=90.0,
            terminal_grace_seconds=5.0,
            input_clock_shadow=True,
        )

        self.assertEqual(coordinator.auto_confirm.interval_frames, 15)
        self.assertEqual(coordinator.auto_confirm.idle_frames, 20)
        self.assertEqual(coordinator.scene_guard.stage_successors, {1: 2})
        self.assertIsNotNone(coordinator.input_clock_tracker)

        disabled = SceneClockCoordinator.create(
            auto_confirm_interval_frames=0,
            auto_confirm_idle_frames=0,
            stage_successors={},
            transition_timeout_seconds=90.0,
            terminal_grace_seconds=5.0,
            input_clock_shadow=False,
        )
        self.assertIsNone(disabled.input_clock_tracker)


if __name__ == "__main__":
    unittest.main()
