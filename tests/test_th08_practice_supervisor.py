#!/usr/bin/env python3
"""Tests for unattended original-game Practice Start automation."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import th08_practice_supervisor as supervisor
from th08_automation.practice_menu import (
    build_practice_menu_plan,
    forward_menu_steps,
    parse_practice_stage,
)
from th08_practice_supervisor import (
    ROOT,
    _progress_text,
    build_patch_batch_command,
    build_parser,
    practice_stage_available,
    read_last_json_record,
)


class PracticeSupervisorTests(unittest.TestCase):
    def test_stage_menu_order_matches_original_practice_screen(self) -> None:
        expected = {
            "1": (0, 0),
            "2": (1, 1),
            "3": (2, 2),
            "4a": (3, 3),
            "4b": (4, 4),
            "5": (5, 5),
            "6a": (6, 6),
            "6b": (7, 7),
        }
        for key, (menu_index, route_index) in expected.items():
            with self.subTest(stage=key):
                stage = parse_practice_stage(key)
                self.assertEqual(stage.menu_index, menu_index)
                self.assertEqual(stage.route_index, route_index)

    def test_plan_stops_before_final_stage_confirm(self) -> None:
        stage = parse_practice_stage("Stage-4B")
        plan = build_practice_menu_plan(
            stage,
            tap_gap_ms=180,
            screen_settle_ms=700,
        )
        self.assertEqual(
            [tap.key for tap in plan],
            [
                "down",
                "down",
                "down",
                "confirm",
                "confirm",
                "right",
                "right",
                "confirm",
            ]
            + ["down"] * 4,
        )
        self.assertEqual(plan[-1].wait_after_ms, 700)
        self.assertNotEqual(plan[-1].key, "confirm")

    def test_stage_one_waits_on_stage_screen_without_extra_direction(self) -> None:
        plan = build_practice_menu_plan(
            parse_practice_stage("1"),
            tap_gap_ms=180,
            screen_settle_ms=700,
        )
        self.assertEqual(
            [tap.key for tap in plan],
            [
                "down",
                "down",
                "down",
                "confirm",
                "confirm",
                "right",
                "right",
                "confirm",
            ],
        )
        self.assertEqual(plan[-1].wait_after_ms, 700)

    def test_ce_0052_fresh_team_menu_moves_to_third_sakuya_remilia(self) -> None:
        plan = build_practice_menu_plan(
            parse_practice_stage("1"),
            tap_gap_ms=180,
            screen_settle_ms=700,
        )
        self.assertEqual(
            [tap.key for tap in plan[5:8]],
            ["right", "right", "confirm"],
        )

    def test_native_cursor_navigation_is_bounded_and_wraps_forward(self) -> None:
        self.assertEqual(forward_menu_steps(3, 3, 4), 0)
        self.assertEqual(forward_menu_steps(0, 3, 4), 3)
        self.assertEqual(forward_menu_steps(3, 2, 4), 3)
        self.assertEqual(forward_menu_steps(0, 2, 4), 2)

    def test_final_a_is_bit_six_of_native_practice_availability(self) -> None:
        final_a = parse_practice_stage("6a")
        self.assertEqual(final_a.menu_index, 6)
        self.assertFalse(practice_stage_available(0xBF, final_a.menu_index))
        self.assertTrue(practice_stage_available(0xFF, final_a.menu_index))

    def test_parser_accepts_repeatable_stage_selection(self) -> None:
        args = build_parser().parse_args(
            [
                "--stage",
                "6a",
                "--repeat",
                "3",
                "--safety-value-horizon",
                "32",
                "--viability-audit",
                "--armed",
            ]
        )
        self.assertEqual(args.stage.key, "6a")
        self.assertEqual(args.stage.route_index, 6)
        self.assertEqual(args.repeat, 3)
        self.assertTrue(args.armed)
        self.assertTrue(args.kill_existing)
        self.assertEqual(args.safety_value_horizon, 32)
        self.assertTrue(args.viability_audit)

    def test_tail_reader_handles_a_record_larger_than_one_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trial.jsonl"
            records = [
                {"kind": "identity", "padding": "x" * 80_000},
                {
                    "kind": "decision",
                    "frame": 123,
                    "stage_route_index": 2,
                    "hit_count": 4,
                },
            ]
            path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(read_last_json_record(path), records[-1])

    def test_progress_text_is_bounded_and_operator_readable(self) -> None:
        text = _progress_text(
            {
                "kind": "decision",
                "frame": 500,
                "stage_route_index": 3,
                "spell_id": 99,
                "hit_count": 2,
                "active_bullets": 800,
                "active_lasers": 12,
                "unused_large_field": "x" * 1000,
            }
        )
        self.assertEqual(
            text,
            "kind=decision frame=500 stage=3 spell=99 hits=2 "
            "bullets=800 lasers=12",
        )

    def test_progress_text_reads_nested_live_spell_state(self) -> None:
        text = _progress_text(
            {
                "kind": "decision",
                "frame": 500,
                "stage_route_index": 3,
                "spell": {"active": True, "spell_id": 57},
                "hit_count": 2,
                "active_bullets": 800,
                "active_lasers": 0,
            }
        )
        self.assertIn("spell=57", text)

    def test_ce_0050_wrapper_does_not_use_dependency_free_ida_python(self) -> None:
        wrapper = (ROOT / "run_th08_practice_agent.bat").read_text(
            encoding="utf-8"
        )
        self.assertIn(r"%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe", wrapper)
        self.assertIn('-c "import numpy"', wrapper)
        self.assertNotIn(r"IDA Pro 9.3\python311\python.exe", wrapper)

    def test_ce_0051_patch_batch_path_is_not_nested_in_one_cmd_argument(
        self,
    ) -> None:
        path = Path(r"D:\Game Directory\run patch.bat")
        command = build_patch_batch_command(path)
        self.assertEqual(command[1:5], ("/d", "/c", "call", str(path)))
        self.assertNotIn("/s", tuple(part.lower() for part in command))
        self.assertNotIn('call "', command[-1])

    def test_completed_stage_selects_no_save_with_right_only(self) -> None:
        with (
            patch.object(supervisor, "focus_target_window"),
            patch.object(supervisor, "drive_menu_plan") as drive,
        ):
            result = supervisor.select_no_save_before_termination(
                object(),
                123,
                hold_ms=65,
                tap_gap_ms=180,
            )
        self.assertTrue(result["sent"])
        plan = drive.call_args.args[2]
        self.assertEqual([tap.key for tap in plan], ["right"])

    def test_killed_partial_is_not_accepted_as_completed_practice(self) -> None:
        self.assertTrue(
            supervisor.accepted_practice_termination(
                {"termination_reason": "route_complete"}
            )
        )
        self.assertFalse(
            supervisor.accepted_practice_termination(
                {"termination_reason": "process_unreadable"}
            )
        )
        self.assertFalse(supervisor.accepted_practice_termination(None))

    def test_comparison_skips_newer_discarded_partial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            accepted = root / (
                "lunatic_route2_stage5_unattended_20260724_010000"
                ".dossier.json"
            )
            discarded = root / (
                "lunatic_route2_stage5_unattended_20260724_020000"
                ".dossier.json"
            )
            current = root / (
                "lunatic_route2_stage5_unattended_20260724_030000"
                ".dossier.json"
            )
            for index, dossier in enumerate(
                (accepted, discarded, current), start=1
            ):
                dossier.write_text("{}\n", encoding="utf-8")
                os.utime(dossier, ns=(index, index))
            accepted.with_name(
                accepted.name.replace(".dossier.json", ".session.json")
            ).write_text(
                json.dumps(
                    {"status": "completed", "trial_accepted": True}
                ),
                encoding="utf-8",
            )
            discarded.with_name(
                discarded.name.replace(".dossier.json", ".session.json")
            ).write_text(
                json.dumps(
                    {"status": "discarded", "trial_accepted": False}
                ),
                encoding="utf-8",
            )
            with patch.object(supervisor, "RUNTIME_REPORT_DIR", root):
                baseline = supervisor._previous_dossier(
                    parse_practice_stage("5"),
                    current,
                )
            self.assertEqual(baseline, accepted)


if __name__ == "__main__":
    unittest.main()
