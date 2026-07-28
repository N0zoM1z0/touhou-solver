#!/usr/bin/env python3
"""Regression for the unattended full-route completion boundary."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from th08_automation.practice_menu import parse_practice_difficulty
from th08_full_route_supervisor import (
    _terminal_scene_record,
    build_parser,
    retain_game_after_trial,
    validate_team_selection,
)


class FullRouteSupervisorTests(unittest.TestCase):
    def test_parser_preserves_lunatic_default_and_accepts_hard(self) -> None:
        self.assertEqual(build_parser().parse_args([]).difficulty.key, "lunatic")
        args = build_parser().parse_args(
            ["--difficulty", "hard", "--leave-game-running"]
        )
        self.assertEqual(args.difficulty.menu_index, 2)
        self.assertTrue(args.leave_game_running)

    def test_corridor_background_priority_is_explicitly_opt_in(self) -> None:
        default_args = build_parser().parse_args([])
        enabled_args = build_parser().parse_args(
            ["--corridor-background-low-priority"]
        )

        self.assertFalse(default_args.corridor_background_low_priority)
        self.assertTrue(enabled_args.corridor_background_low_priority)

    def test_enemy_combat_progress_is_explicitly_opt_in(self) -> None:
        default_args = build_parser().parse_args([])
        enabled_args = build_parser().parse_args(
            ["--trace-enemy-combat-progress"]
        )

        self.assertFalse(default_args.trace_enemy_combat_progress)
        self.assertTrue(enabled_args.trace_enemy_combat_progress)

    def test_team_preconfirm_uses_selected_difficulty_cursor(self) -> None:
        import th08_full_route_supervisor as supervisor
        from unittest.mock import patch

        state = {
            "mode": supervisor.TITLE_MODE_GAME_TEAM,
            "substate": 1,
            "cursor": 2,
            "difficulty_cursor": 2,
        }
        with patch.object(
            supervisor,
            "_read_title_menu_state",
            return_value=state,
        ):
            selected = validate_team_selection(
                object(),
                1234,
                difficulty=parse_practice_difficulty("hard"),
            )
        self.assertIs(selected, state)

    def test_only_accepted_opt_in_route_survives_final_cleanup(self) -> None:
        self.assertTrue(
            retain_game_after_trial(
                accepted=True,
                leave_game_running=True,
            )
        )
        for accepted, requested in (
            (False, False),
            (False, True),
            (True, False),
        ):
            with self.subTest(accepted=accepted, requested=requested):
                self.assertFalse(
                    retain_game_after_trial(
                        accepted=accepted,
                        leave_game_running=requested,
                    )
                )

    def test_terminal_unload_precedes_route_complete_summary(self) -> None:
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trial.jsonl"
            rows = [
                {
                    "kind": "scene_inactive",
                    "frame": 226864,
                    "engine_flags": 109072,
                    "stage_route_index": 7,
                    "transition_from_stage": 7,
                    "expected_stage": None,
                    "status": "terminal_unload",
                },
                {
                    "kind": "summary",
                    "last_frame": 226864,
                    "termination_reason": "route_complete",
                },
            ]
            trace.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            completion = _terminal_scene_record(trace)
        self.assertEqual(completion["frame"], 226864)
        self.assertEqual(completion["engine_flags"], 109072)


if __name__ == "__main__":
    unittest.main()
