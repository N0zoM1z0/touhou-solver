#!/usr/bin/env python3
"""Tests for the mandatory-stage symbolic ECL event atlas."""

from __future__ import annotations

import unittest
from pathlib import Path

from analysis.th08_mandatory_event_atlas import (
    _callback_detail,
    _event_classes,
    build_event_atlas,
)
from th08_ecl import SubInstruction


ROOT = Path(__file__).resolve().parents[1]


class MandatoryEventAtlasTests(unittest.TestCase):
    def test_event_classes_keep_overlapping_resource_cleanup(self) -> None:
        self.assertEqual(
            _event_classes("subroutine", 0x5F),
            ("global_enemy_cleanup", "item_resource"),
        )
        self.assertEqual(
            _event_classes("subroutine", 0x6F),
            ("bullet_transform",),
        )
        self.assertEqual(
            _event_classes("timeline", 0x00),
            ("timeline_enemy_birth",),
        )
        self.assertEqual(
            _event_classes("timeline", 0x06),
            ("timeline_unknown",),
        )

    def test_callback_detail_separates_literal_and_dynamic_indices(self) -> None:
        literal = SubInstruction(
            0,
            0,
            0x89,
            20,
            0,
            0xFF,
            0,
            (7, 0),
        )
        detail = _callback_detail(literal)
        self.assertEqual(detail["action"], "install_per_frame")
        self.assertEqual(detail["callback_index"], 7)
        self.assertEqual(
            detail["callback_name"],
            "update_barrier_portal_center_y_224",
        )

        dynamic = SubInstruction(
            0,
            0,
            0x88,
            20,
            0,
            0xFF,
            1,
            (10036, 0),
        )
        self.assertEqual(
            _callback_detail(dynamic),
            {
                "action": "invoke",
                "callback_index": None,
                "callback_index_dynamic": True,
            },
        )

    def test_retained_atlas_keeps_static_and_runtime_authority_separate(self) -> None:
        report = build_event_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=(
                ROOT
                / "artifacts"
                / "runtime_reports"
                / "th08_immutable_content_manifest_20260731.json"
            ),
        )
        self.assertEqual(report["stage_count"], 4)
        self.assertTrue(
            report["classification"][
                "mandatory_static_event_classes_inventoried"
            ]
        )
        self.assertFalse(
            report["classification"]["content_02_exit_gate_passed"]
        )
        self.assertFalse(report["authority"]["runtime_execution_authority"])
        self.assertGreater(
            report["event_class_matrix"]["hostile_fire"][
                "conservative_route_reachable"
            ],
            0,
        )
        self.assertTrue(
            all(
                not stage["flow"]["unresolved_dynamic_subroutine_edges"]
                for stage in report["stages"]
            )
        )


if __name__ == "__main__":
    unittest.main()
