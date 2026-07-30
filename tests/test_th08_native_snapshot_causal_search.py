from __future__ import annotations

import unittest

from tools.th08_native_snapshot_causal_search import (
    DEFAULT_PREFIX_MASKS,
    PORTFOLIO_NO_BOMB_MASKS,
    _first_hit_manager_frame,
    _parse_masks,
    build_parser,
)


class NativeSnapshotCausalSearchTests(unittest.TestCase):
    def test_defaults_cover_six_prefixes_and_all_secondary_masks(self) -> None:
        arguments = build_parser().parse_args(["--output", "causal.json"])

        self.assertEqual(arguments.prefix_masks, DEFAULT_PREFIX_MASKS)
        self.assertIsNone(arguments.prefix_action_schedule)
        self.assertEqual(
            arguments.secondary_masks,
            PORTFOLIO_NO_BOMB_MASKS,
        )
        self.assertEqual(arguments.prefix_horizon, 8)
        self.assertEqual(arguments.secondary_horizon, 8)
        self.assertEqual(arguments.hold_frames, 3)

    def test_mask_parser_is_hex_unique_and_no_bomb(self) -> None:
        self.assertEqual(_parse_masks("0x14, 0x95"), (0x14, 0x95))

        with self.assertRaises(Exception):
            _parse_masks("0x14,0x14")
        with self.assertRaises(Exception):
            _parse_masks("0x02")

    def test_parser_accepts_one_exact_prefix_schedule(self) -> None:
        arguments = build_parser().parse_args(
            [
                "--output",
                "causal.json",
                "--prefix-action-schedule",
                "0x94,0x94,0x94,r,r,0x44",
            ]
        )

        self.assertEqual(
            arguments.prefix_action_schedule,
            (0x94, 0x94, 0x94, None, None, 0x44),
        )

    def test_first_hit_uses_first_phase_two_frame(self) -> None:
        history = (
            {"manager_frame": 2138, "player_phase": 0},
            {"manager_frame": 2139, "player_phase": 2},
            {"manager_frame": 2140, "player_phase": 2},
        )

        self.assertEqual(_first_hit_manager_frame(history), 2139)
        self.assertIsNone(
            _first_hit_manager_frame(({"manager_frame": 2138, "player_phase": 0},))
        )


if __name__ == "__main__":
    unittest.main()
