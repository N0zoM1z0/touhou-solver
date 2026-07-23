#!/usr/bin/env python3
"""Focused tests for TH08 stitched run dossiers."""

from __future__ import annotations

import unittest

from th08_run_dossier import (
    _classify_death,
    _death_clusters,
    _nearest_bullet,
    _nearest_laser,
    _spell_attribution,
)


def _row(
    frame: int,
    *,
    bullets: int = 1,
    pipeline: float = 5.0,
    slack: float = 2.0,
) -> dict[str, object]:
    return {
        "frame": frame,
        "player": {"x": 192.0, "y": 400.0},
        "nearby_bullets": [
            [17, 192.0, 400.0, 0.0, 0.0, 2.0, 2.0, 0]
        ]
        if bullets
        else [],
        "active_bullets": bullets,
        "active_lasers": 0,
        "pipeline_clearance": pipeline,
        "corridor_slack": slack,
        "action_lag": 1,
        "action": "stay",
    }


class Th08RunDossierTests(unittest.TestCase):
    def test_native_overlap_outranks_positive_pipeline_model(self) -> None:
        row = _row(100)
        primary, contributing, nearest, laser = _classify_death(
            row,
            window=[row],
        )
        self.assertEqual(primary, "observed_bullet_overlap")
        self.assertEqual(nearest["slot"], 17)
        self.assertIsNone(laser)
        self.assertEqual(contributing, [])

    def test_missing_witness_stays_explicitly_unmodeled(self) -> None:
        row = _row(100, bullets=0, pipeline=8.0, slack=-2.0)
        primary, contributing, nearest, laser = _classify_death(
            row,
            window=[row],
        )
        self.assertEqual(primary, "sensor_gap_or_unmodeled_hazard")
        self.assertIsNone(nearest)
        self.assertIsNone(laser)
        self.assertIn("corridor_deadline_miss", contributing)

    def test_overlap_witness_outranks_closer_nonoverlapping_center(self) -> None:
        row = _row(100)
        row["nearby_bullets"] = [
            [1, 195.0, 405.0, 0.0, 0.0, 1.0, 1.0, 0],
            [2, 200.0, 400.0, 0.0, 0.0, 8.0, 2.0, 0],
        ]
        nearest = _nearest_bullet(row)
        self.assertEqual(nearest["slot"], 2)
        self.assertLessEqual(nearest["aabb_clearance"], 0.0)

    def test_native_laser_overlap_uses_exact_segment_geometry(self) -> None:
        row = _row(100, bullets=0)
        row["active_lasers"] = 1
        row["lasers"] = [[100.0, 400.0, 0.0, 0.0, 200.0, 5.0]]
        nearest = _nearest_laser(row)
        self.assertLessEqual(nearest["clearance"], 0.0)
        primary, _, _, _ = _classify_death(row, window=[row])
        self.assertEqual(primary, "observed_laser_overlap")

    def test_live_spell_attribution_is_gated_by_active_flag(self) -> None:
        row = {
            "spell": {
                "active": True,
                "flags": 5,
                "enemy_pointer": 0x1234,
                "spell_id": 145,
                "name": "禁薬「蓬莱の薬」",
            }
        }
        self.assertEqual(_spell_attribution(row)["spell_id"], 145)
        row["spell"]["active"] = False
        attribution = _spell_attribution(row)
        self.assertEqual(attribution["status"], "no_active_spell_at_hit")
        self.assertIsNone(attribution["spell_id"])

    def test_death_clusters_do_not_cross_stages(self) -> None:
        deaths = [
            {
                "frame": 100,
                "stage_route_index": 0,
                "stage_label": "Stage 1",
                "resources_at_hit": {"power": 10.0},
                "active_bullets": 20,
                "primary_cause_class": "sensor_gap_or_unmodeled_hazard",
            },
            {
                "frame": 500,
                "stage_route_index": 0,
                "stage_label": "Stage 1",
                "resources_at_hit": {"power": 8.0},
                "active_bullets": 30,
                "primary_cause_class": "sensor_gap_or_unmodeled_hazard",
            },
            {
                "frame": 550,
                "stage_route_index": 1,
                "stage_label": "Stage 2",
                "resources_at_hit": {"power": 7.0},
                "active_bullets": 40,
                "primary_cause_class": "observed_bullet_overlap",
            },
        ]
        clusters = _death_clusters(deaths)
        self.assertEqual([cluster["death_count"] for cluster in clusters], [2, 1])
        self.assertEqual(clusters[0]["minimum_power"], 8.0)


if __name__ == "__main__":
    unittest.main()
