import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from analysis.th08_finalb_scale_root_capsule import (
    CAPSULE_SCHEMA,
    build_capsule,
)
from th08_live.movement import FOCUSED_CARDINAL_SPEED


def _decision(
    *,
    frame: int,
    scale: float,
    snapshot_lag: int = 1,
) -> dict[str, object]:
    x = 100.0
    y = 400.0
    control_delay = 4
    return {
        "kind": "decision",
        "frame": frame,
        "snapshot_frame": frame - 1,
        "snapshot_lag": snapshot_lag,
        "gameplay_epoch": 3,
        "stage_route_index": 7,
        "spell": {
            "active": True,
            "spell_id": 190,
            "name": "「永夜返し  -世明け-」",
        },
        "bullet_velocity_lookahead": {"time_scale": scale},
        "player": {
            "x": x,
            "y": y,
            "projected_x": x + FOCUSED_CARDINAL_SPEED * snapshot_lag,
            "projected_y": y,
            "control_origin_x": (
                x + FOCUSED_CARDINAL_SPEED * control_delay
            ),
            "control_origin_y": y,
        },
        "input_snapshot": {"current": 0x85, "previous": 0x05},
        "mask": 0x85,
        "action": "right",
        "control_delay_frames": control_delay,
        "active_bullets": 500,
        "active_lasers": 0,
        "hit_count": 17,
        "hit_started": False,
        "bomb": False,
        "resources": {"lives": 8.0, "bombs": 4.0, "power": 6.0},
    }


class FinalBScaleRootCapsuleTests(unittest.TestCase):
    def test_selects_quarter_scale_and_replays_corrected_player_step(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traces = []
            expected_source_hashes = []
            for index in range(3):
                path = root / f"physical_{index}.jsonl"
                records = [
                    {"kind": "start", "frame": 0},
                    _decision(frame=100 + index, scale=0.25),
                    _decision(frame=200 + index, scale=1.0),
                ]
                payload = "".join(
                    json.dumps(record, sort_keys=True) + "\n"
                    for record in records
                )
                path.write_text(payload, encoding="utf-8")
                traces.append(path)
                expected_source_hashes.append(
                    hashlib.sha256(path.read_bytes()).hexdigest()
                )

            capsule = build_capsule(traces)

        self.assertEqual(capsule["schema"], CAPSULE_SCHEMA)
        self.assertTrue(capsule["gate"]["passed"])
        self.assertEqual(capsule["aggregate"]["selected_record_count"], 3)
        self.assertEqual(
            capsule["aggregate"]["exact_root_covered_read_lag_rows"],
            3,
        )
        self.assertEqual(capsule["aggregate"]["physical_active_laser_rows"], 0)
        record = capsule["sessions"][0]["records"][0]
        self.assertEqual(
            record["legacy_held_input_reconstruction"]["actions"],
            ("right",),
        )
        comparison = record["read_lag_scale_comparison"]
        self.assertEqual(
            comparison["authority"],
            "scale_exact_for_same_legacy_input_assumption",
        )
        self.assertGreater(comparison["position_delta"], 1.7)
        self.assertLess(comparison["position_delta"], 1.8)
        self.assertIn(
            "noncausal",
            record["multi_frame_control_origin_diagnostic"]["authority"],
        )
        self.assertEqual(
            capsule["sessions"][0]["source"]["sha256"],
            expected_source_hashes[0],
        )

    def test_marks_root_schedule_incomplete_for_long_read_lag(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traces = []
            for index in range(3):
                path = root / f"physical_{index}.jsonl"
                path.write_text(
                    json.dumps(
                        _decision(
                            frame=300 + index,
                            scale=0.25,
                            snapshot_lag=2,
                        )
                    )
                    + "\n",
                    encoding="utf-8",
                )
                traces.append(path)

            capsule = build_capsule(traces)

        self.assertFalse(capsule["gate"]["passed"])
        self.assertEqual(capsule["aggregate"]["unknown_read_lag_rows"], 3)
        self.assertIsNone(
            capsule["sessions"][0]["records"][0][
                "read_lag_scale_comparison"
            ]["corrected_observed_scale_projection"]
        )


if __name__ == "__main__":
    unittest.main()
