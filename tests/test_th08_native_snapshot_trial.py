from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from th08_runtime.native_snapshot import (
    NativeReplayActionCarrier,
    NativeSnapshotUnknownError,
)
from tools.th08_native_snapshot_trial import (
    DEFAULT_ACTION_B,
    DEFAULT_COMPACT_CORPUS,
    DEFAULT_COMPACT_CORPUS_TICKS,
    DEFAULT_HOLD_FRAMES,
    DEFAULT_HORIZON,
    DEFAULT_PORTFOLIO_CORPUS,
    DEFAULT_STAGE5_SHA256,
    DEFAULT_TARGET_MANAGER_FRAME,
    PORTFOLIO_NO_BOMB_MASKS,
    _assert_action_carrier_epoch,
    _assert_mapping_epoch,
    _compact_corpus_comparison,
    _compare_portfolio_branch_to_corpus,
    _load_portfolio_corpus,
    _validate_action_schedule,
    build_parser,
)


class NativeSnapshotTrialCliTests(unittest.TestCase):
    def test_parser_pins_canonical_stage5_root_and_distinct_action(self) -> None:
        arguments = build_parser().parse_args(["--output", "native_snapshot.json"])

        self.assertEqual(
            arguments.target_manager_frame,
            DEFAULT_TARGET_MANAGER_FRAME,
        )
        self.assertEqual(arguments.action_b, DEFAULT_ACTION_B)
        self.assertIsNone(arguments.action_schedule)
        self.assertEqual(arguments.horizon, DEFAULT_HORIZON)
        self.assertEqual(arguments.hold_frames, DEFAULT_HOLD_FRAMES)
        self.assertEqual(arguments.natural_reference, "a")
        self.assertFalse(arguments.retain_collision_control_payload)
        self.assertFalse(arguments.portfolio_all36)
        self.assertEqual(
            arguments.portfolio_corpus,
            DEFAULT_PORTFOLIO_CORPUS,
        )
        self.assertEqual(arguments.compact_corpus, DEFAULT_COMPACT_CORPUS)
        self.assertEqual(
            arguments.compact_corpus_ticks,
            DEFAULT_COMPACT_CORPUS_TICKS,
        )
        self.assertEqual(
            arguments.expected_replay_sha256,
            DEFAULT_STAGE5_SHA256,
        )

    def test_action_mask_accepts_hexadecimal(self) -> None:
        arguments = build_parser().parse_args(
            [
                "--output",
                "native_snapshot.json",
                "--action-b",
                "0x15",
            ]
        )

        self.assertEqual(arguments.action_b, 0x15)

    def test_parser_accepts_explicit_horizon_and_natural_branch(self) -> None:
        arguments = build_parser().parse_args(
            [
                "--output",
                "native_snapshot.json",
                "--horizon",
                "8",
                "--hold-frames",
                "3",
                "--natural-reference",
                "b",
            ]
        )

        self.assertEqual(arguments.horizon, 8)
        self.assertEqual(arguments.hold_frames, 3)
        self.assertEqual(arguments.natural_reference, "b")

    def test_parser_accepts_explicit_model_payload_retention(self) -> None:
        arguments = build_parser().parse_args(
            [
                "--output",
                "native_snapshot.json",
                "--retain-collision-control-payload",
            ]
        )

        self.assertTrue(arguments.retain_collision_control_payload)

    def test_parser_accepts_exact_action_schedule_with_recorded_ticks(self) -> None:
        arguments = build_parser().parse_args(
            [
                "--output",
                "native_snapshot.json",
                "--action-schedule",
                "0x94,0x94,recorded,r,-,0x44",
            ]
        )

        self.assertEqual(
            arguments.action_schedule,
            (0x94, 0x94, None, None, None, 0x44),
        )

    def test_action_carrier_epoch_requires_exact_per_tick_cursor(self) -> None:
        root = NativeReplayActionCarrier(1, 2, 0x1000, 2129, 0x05)
        second = NativeReplayActionCarrier(1, 2, 0x1002, 2130, 0x15)

        _assert_action_carrier_epoch(root, second, tick_index=1)

        wrong_cursor = NativeReplayActionCarrier(1, 2, 0x1004, 2130, 0x15)
        with self.assertRaises(NativeSnapshotUnknownError):
            _assert_action_carrier_epoch(root, wrong_cursor, tick_index=1)

    def test_mapping_epoch_error_retains_bounded_region_differences(self) -> None:
        with self.assertRaisesRegex(
            NativeSnapshotUnknownError,
            r"removed=.*4096.*added=.*8192",
        ):
            _assert_mapping_epoch(
                ((4096, 4096, 4096, 4, 4096, 4, 131072),),
                ((8192, 4096, 8192, 4, 4096, 4, 131072),),
                context="mapping changed",
            )

    def test_compact_corpus_comparison_is_field_exact(self) -> None:
        expected = {
            "manager_frame": 2130,
            "input_current": 5,
            "player_x": 376.0,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "fixture",
                        "result": {
                            "status": "fixture",
                            "history": [expected],
                        },
                    }
                ),
                encoding="utf-8",
            )
            exact = _compact_corpus_comparison(
                path,
                target_manager_frame=2129,
                branch={"ticks": [{"compact_state": dict(expected)}]},
            )
            mismatch = _compact_corpus_comparison(
                path,
                target_manager_frame=2129,
                branch={
                    "ticks": [
                        {
                            "compact_state": {
                                **expected,
                                "player_x": 375.0,
                            }
                        }
                    ]
                },
            )

        self.assertTrue(exact["exact"])
        self.assertEqual(exact["compared_frames"], [2130])
        self.assertFalse(mismatch["exact"])
        self.assertEqual(
            mismatch["ticks"][0]["field_changes"][0]["field"],
            "player_x",
        )

    def test_portfolio_mask_order_is_complete_and_no_bomb(self) -> None:
        self.assertEqual(len(PORTFOLIO_NO_BOMB_MASKS), 36)
        self.assertEqual(len(set(PORTFOLIO_NO_BOMB_MASKS)), 36)
        self.assertTrue(all(mask & 0x02 == 0 for mask in PORTFOLIO_NO_BOMB_MASKS))
        self.assertEqual(
            PORTFOLIO_NO_BOMB_MASKS[:8],
            (0x00, 0x01, 0x04, 0x05, 0x10, 0x11, 0x14, 0x15),
        )

    def test_action_schedule_is_exact_horizon_and_no_bomb(self) -> None:
        _validate_action_schedule(
            (0x14, 0x14, 0x14, None, 0x90),
            horizon=5,
        )

        with self.assertRaises(ValueError):
            _validate_action_schedule((0x14,), horizon=2)
        with self.assertRaises(ValueError):
            _validate_action_schedule((0x14, 0x02), horizon=2)

    def test_portfolio_branch_comparison_uses_first_hit_state(self) -> None:
        expected = {
            "complete_mask": 0x05,
            "status": "first_hit_observed",
            "first_hit_manager_frame": 2131,
            "stop_manager_frame": None,
            "endpoint": {
                "manager_frame": 2131,
                "player_phase": 2,
                "player_x": 376.0,
            },
        }
        branch = {
            "ticks": [
                {
                    "compact_state": {
                        "manager_frame": 2130,
                        "player_phase": 0,
                        "player_x": 376.0,
                    }
                },
                {
                    "compact_state": {
                        "manager_frame": 2131,
                        "player_phase": 2,
                        "player_x": 376.0,
                    }
                },
                {
                    "compact_state": {
                        "manager_frame": 2132,
                        "player_phase": 2,
                        "player_x": 370.0,
                    }
                },
            ]
        }

        comparison = _compare_portfolio_branch_to_corpus(
            expected,
            branch,
        )

        self.assertTrue(comparison["exact"])
        self.assertTrue(comparison["outcome_class_exact"])
        self.assertEqual(
            comparison["observed_first_hit_manager_frame"],
            2131,
        )
        self.assertEqual(comparison["first_hit_frame_delta"], 0)

    def test_portfolio_corpus_requires_exact_root_horizon_and_masks(
        self,
    ) -> None:
        branches = [
            {
                "complete_mask": mask,
                "status": "stop_frame_reached_without_hit",
                "first_hit_manager_frame": None,
                "stop_manager_frame": 2137,
                "endpoint": {
                    "manager_frame": 2137,
                    "player_phase": 0,
                },
            }
            for mask in PORTFOLIO_NO_BOMB_MASKS
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "all36.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "fixture",
                        "root_frame": 2129,
                        "stop_manager_frame": 2137,
                        "hold_frames": 3,
                        "branches": branches,
                    }
                ),
                encoding="utf-8",
            )
            by_mask, record = _load_portfolio_corpus(
                path,
                target_manager_frame=2129,
                horizon=8,
                hold_frames=3,
            )

        self.assertEqual(tuple(by_mask), PORTFOLIO_NO_BOMB_MASKS)
        self.assertEqual(record["mask_count"], 36)


if __name__ == "__main__":
    unittest.main()
