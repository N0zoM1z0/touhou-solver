import unittest

import th08_live_dodge_agent as live


class PlannerPassDecisionTests(unittest.TestCase):
    def test_characterized_actions_remain_stable(self) -> None:
        cases = (
            (
                {
                    "player_x": 192.0,
                    "player_y": 400.0,
                    "bullets": (),
                    "lasers": (),
                    "previous_direction": 0,
                    "can_bomb": False,
                },
                "stay",
            ),
            (
                {
                    "player_x": 192.0,
                    "player_y": 400.0,
                    "bullets": (
                        live.Bullet(192.0, 364.0, 0.0, 3.0, 3.0, 3.0),
                    ),
                    "lasers": (),
                    "previous_direction": 0,
                    "can_bomb": False,
                },
                "down_fast",
            ),
            (
                {
                    "player_x": 192.0,
                    "player_y": 400.0,
                    "bullets": (),
                    "lasers": (),
                    "previous_direction": 0,
                    "previous_focus": True,
                    "can_bomb": False,
                    "target_x": 300.0,
                    "target_y": 400.0,
                    "target_deadline": 8,
                    "allowed_first_actions": ("left",),
                    "viability_repair_volumes": (("left", 5),),
                },
                "left",
            ),
        )
        original_hazard = live._LOCAL_HAZARD_BACKEND
        original_beam = live._LOCAL_BEAM_REDUCER
        try:
            live._configure_local_hazard_backend("numpy")
            live._configure_local_beam_reducer("python")
            for arguments, expected in cases:
                self.assertEqual(
                    live.choose_action(**arguments).action,
                    expected,
                )
        finally:
            live._configure_local_hazard_backend(original_hazard)
            live._configure_local_beam_reducer(original_beam)


if __name__ == "__main__":
    unittest.main()
