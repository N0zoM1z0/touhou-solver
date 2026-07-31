from __future__ import annotations

import unittest

import th08_live_dodge_agent as live


class NativeLocalBeamTests(unittest.TestCase):
    def test_native_reducer_matches_python_decision(self) -> None:
        if live.native_backend._load_local_beam_reduce_function() is None:
            self.skipTest("native local beam reducer unavailable")
        arguments = {
            "player_x": 192.0,
            "player_y": 360.0,
            "bullets": (
                live.Bullet(192.0, 330.0, 0.0, 2.5, 3.0, 3.0),
                live.Bullet(210.0, 350.0, -1.0, 1.0, 2.0, 2.0),
            ),
            "lasers": (),
            "previous_direction": live.LEFT,
            "previous_focus": True,
            "can_bomb": False,
            "control_delay_frames": 2,
            "control_delay_candidates": (1, 2, 3),
            "action_hold_frames": 3,
            "horizon": 8,
            "threat_horizon": 12,
            "beam_width": 24,
        }
        try:
            live._configure_local_beam_reducer("python")
            reference = live.choose_action(**arguments)
            live._configure_local_beam_reducer("native")
            actual = live.choose_action(**arguments)
        finally:
            live._configure_local_beam_reducer("python")

        self.assertEqual(actual.action, reference.action)
        self.assertEqual(actual.mask, reference.mask)
        self.assertEqual(actual.robust_collisions, reference.robust_collisions)
        self.assertEqual(actual.local_collisions, reference.local_collisions)


if __name__ == "__main__":
    unittest.main()
