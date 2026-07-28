from __future__ import annotations

import json
import unittest

from analysis.derived_pattern_source_join import (
    build_derived_pattern_source_join,
)


def _source_audit() -> dict[str, object]:
    candidates = []
    for slot, position in ((10, (100.0, 200.0)), (11, (300.0, 50.0))):
        candidates.append(
            {
                "slot": slot,
                "position": list(position),
                "pattern": {"predicted_child_count": 3},
            }
        )
    return {
        "frame": 100,
        "gameplay_epoch": 2,
        "stage_route_index": 5,
        "derived_source_observation": {
            "frame_after": 99,
            "candidates": candidates,
        },
        "observation": {
            "frame_after": 99,
            "previous_frame_after": 97,
            "evidence_count": 0,
            "evidence": {
                "format": "columnar_v1",
                "slot": [],
                "code": [],
                "age": [],
                "geometry": [],
                "geometry_finite": [],
            },
        },
    }


def _activation_audit() -> dict[str, object]:
    slots = [20, 21, 22, 23, 24, 25]
    velocities = [
        (-1.0, 0.0),
        (0.0, 1.0),
        (1.0, 0.0),
        (0.5, 0.0),
        (0.0, -0.5),
        (-0.5, 0.0),
    ]
    origins = [(100.0, 200.0)] * 3 + [(302.0, 50.0)] * 3
    ages = [2] * 6
    geometry = []
    for origin, velocity, age in zip(origins, velocities, ages):
        geometry.append(
            [
                origin[0] + velocity[0] * age,
                origin[1] + velocity[1] * age,
                velocity[0],
                velocity[1],
                10.0,
                10.0,
            ]
        )
    return {
        "frame": 102,
        "gameplay_epoch": 2,
        "stage_route_index": 5,
        "derived_source_observation": {
            "frame_after": 101,
            "candidates": [],
        },
        "observation": {
            "frame_after": 101,
            "previous_frame_after": 99,
            "evidence_count": 6,
            "evidence": {
                "format": "columnar_v1",
                "slot": slots,
                "code": [3] * 6,
                "age": ages,
                "geometry": geometry,
                "geometry_finite": [True] * 6,
            },
        },
    }


class DerivedPatternSourceJoinTests(unittest.TestCase):
    def test_join_retains_count_matches_but_limits_stationary_proxy(self) -> None:
        report = build_derived_pattern_source_join(
            [_source_audit(), _activation_audit()]
        )
        self.assertEqual(report["source_sightings"], 2)
        self.assertEqual(report["activation_groups_after_source_rows"], 2)
        self.assertEqual(report["activation_group_sizes"], {"3": 2})
        self.assertEqual(report["groups_with_count_candidates"], 2)
        self.assertEqual(
            report["groups_with_unique_stationary_geometry_candidate"],
            1,
        )
        self.assertEqual(report["unmatched_source_sightings"], 1)
        self.assertFalse(report["semantics"]["hit_outcome_used"])
        json.dumps(report, allow_nan=False)

    def test_digest_is_stable_and_scope_discontinuity_fails_closed(self) -> None:
        audits = [_source_audit(), _activation_audit()]
        first = build_derived_pattern_source_join(audits)
        second = build_derived_pattern_source_join(audits)
        self.assertEqual(
            first["complete_edge_digest"],
            second["complete_edge_digest"],
        )
        audits[1]["gameplay_epoch"] = 3
        rejected = build_derived_pattern_source_join(audits)
        self.assertEqual(rejected["next_observation_discontinuities"], 1)
        self.assertEqual(rejected["activation_groups_after_source_rows"], 0)
        self.assertEqual(rejected["unmatched_source_sightings"], 2)


if __name__ == "__main__":
    unittest.main()
