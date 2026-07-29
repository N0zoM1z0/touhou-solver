import dataclasses
import hashlib
import json
import unittest

import th08_live_dodge_agent as live


class PlannerPassDecisionParityTests(unittest.TestCase):
    """Freeze complete outputs with native-order float32 movement stores."""

    def test_five_complete_decisions_match_characterized_outputs(self) -> None:
        cases = {
            "open_field": {
                "arguments": {
                    "player_x": 192.0,
                    "player_y": 400.0,
                    "bullets": (),
                    "lasers": (),
                    "previous_direction": 0,
                    "can_bomb": False,
                },
                "action": "stay",
                "digest": (
                    "f9138d64812c81208f160fd8fac46e614a66d1e37aab4ed"
                    "21a44e64a993ef046"
                ),
            },
            "incoming_bullet": {
                "arguments": {
                    "player_x": 192.0,
                    "player_y": 400.0,
                    "bullets": (
                        live.Bullet(
                            192.0,
                            364.0,
                            0.0,
                            3.0,
                            3.0,
                            3.0,
                        ),
                    ),
                    "lasers": (),
                    "previous_direction": 0,
                    "can_bomb": False,
                },
                "action": "down_fast",
                "digest": (
                    "fc2ce312de18f2de7f41cad2b13483ba24406048739443a"
                    "03de4327dfadcc7cd"
                ),
            },
            "multi_delay": {
                "arguments": {
                    "player_x": 192.0,
                    "player_y": 400.0,
                    "bullets": (
                        live.Bullet(
                            192.0,
                            370.0,
                            0.0,
                            3.0,
                            3.0,
                            3.0,
                        ),
                    ),
                    "lasers": (),
                    "previous_direction": 0,
                    "previous_focus": True,
                    "can_bomb": False,
                    "control_delay_frames": 3,
                    "control_delay_candidates": (2, 3, 4),
                    "action_hold_frames": 3,
                },
                "action": "down_fast",
                "digest": (
                    "59befb361c824fad85d17716c97499fb6161ee76569d8936"
                    "de39e646cd686bef"
                ),
            },
            "viability_constraint": {
                "arguments": {
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
                "action": "left",
                "digest": (
                    "cc4deb10ba64725313af4ff3ab6077913793a2f8338b62559"
                    "1735ca42e84fd06"
                ),
            },
            "supplemental_lane": {
                "arguments": {
                    "player_x": 192.0,
                    "player_y": 300.0,
                    "bullets": (),
                    "lasers": (),
                    "previous_direction": live.LEFT,
                    "previous_focus": True,
                    "can_bomb": False,
                    "control_delay_frames": 2,
                    "control_delay_candidates": (1, 2, 3),
                    "action_hold_frames": 4,
                    "horizon": 4,
                    "threat_horizon": 4,
                    "beam_width": 1,
                    "allowed_first_actions": ("left", "right"),
                    "viability_repair_volumes": (
                        ("left", 1),
                        ("right", 9),
                    ),
                    "preloss_continuation_preference": True,
                    "preloss_supplemental_beam_width": 1,
                },
                "action": "right",
                "digest": (
                    "7a9f2438a3015b13bb549a1eedaa78b22a56dca6feea4f50"
                    "9f9bc1cbd49f3c73"
                ),
            },
        }
        original_hazard = live._LOCAL_HAZARD_BACKEND
        original_beam = live._LOCAL_BEAM_REDUCER
        original_supplemental = live._LOCAL_SUPPLEMENTAL_BACKEND
        try:
            live._configure_local_hazard_backend("numpy")
            live._configure_local_beam_reducer("python")
            live._configure_local_supplemental_backend("python")
            for name, case in cases.items():
                decision = live.choose_action(**case["arguments"])
                payload = dataclasses.asdict(decision)
                payload.pop("local_certificate_timing")
                encoded = json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=True,
                )
                digest = hashlib.sha256(encoded.encode()).hexdigest()
                self.assertEqual(decision.action, case["action"], msg=name)
                self.assertEqual(digest, case["digest"], msg=name)
        finally:
            live._configure_local_hazard_backend(original_hazard)
            live._configure_local_beam_reducer(original_beam)
            live._configure_local_supplemental_backend(
                original_supplemental
            )


if __name__ == "__main__":
    unittest.main()
