from __future__ import annotations

import unittest

from analysis.th08_native_snapshot_causal_report import (
    _choose_maximin,
    _content_artifact,
)


def _branch(mask: int, clearances: tuple[float, ...], hit: int | None = None):
    return {
        "complete_mask": mask,
        "first_hit_manager_frame": hit,
        "ticks": [
            {
                "compact_state": {
                    "manager_frame": 2130 + index,
                    "player_phase": 0 if hit is None else 2,
                    "player_x": 10.0,
                    "player_y": 20.0,
                },
                "collision_control_summary": {
                    "nearest_bullets": [
                        {
                            "slot": 45,
                            "signed_box_separation": clearance,
                        }
                    ]
                },
            }
            for index, clearance in enumerate(clearances)
        ],
    }


class NativeSnapshotCausalReportTests(unittest.TestCase):
    def test_content_artifact_id_is_canonical_and_kind_sensitive(self) -> None:
        left = _content_artifact("ExactWitness", {"b": 2, "a": 1})
        right = _content_artifact("ExactWitness", {"a": 1, "b": 2})
        other = _content_artifact("ActionPortfolio", {"a": 1, "b": 2})

        self.assertEqual(left["artifact_id"], right["artifact_id"])
        self.assertNotEqual(left["artifact_id"], other["artifact_id"])

    def test_maximin_ignores_hits_and_uses_endpoint_then_lower_mask(self) -> None:
        selected = _choose_maximin(
            [
                _branch(0x10, (2.0, 4.0)),
                _branch(0x11, (2.0, 4.0)),
                _branch(0x44, (2.0, 5.0)),
                _branch(0xA4, (9.0, 9.0), hit=2130),
            ],
            mask_field="complete_mask",
        )

        self.assertEqual(selected["complete_mask"], 0x44)
        self.assertEqual(
            selected["minimum_clearance"]["signed_box_separation"],
            2.0,
        )


if __name__ == "__main__":
    unittest.main()
