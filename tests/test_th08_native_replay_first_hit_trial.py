from __future__ import annotations

import unittest

from tools.th08_native_replay_first_hit_trial import (
    _input_alignment,
    build_parser,
)


class NativeReplayFirstHitTrialTests(unittest.TestCase):
    def test_parser_exposes_explicit_fast_forward(self) -> None:
        args = build_parser().parse_args(
            ["--output", "report.json", "--fast-forward"]
        )
        self.assertTrue(args.fast_forward)

    def test_input_alignment_recovers_manager_to_replay_offset(self) -> None:
        replay = (0, 0, 1, 1, 0x45, 0x45, 5, 5)
        frames = tuple(
            {
                "manager_frame": manager_frame,
                "input_current": replay[manager_frame - 2],
            }
            for manager_frame in range(2, 8)
        )
        alignment = _input_alignment(frames, replay, radius=4)
        self.assertEqual(alignment[0]["manager_to_replay_offset"], -2)
        self.assertEqual(alignment[0]["match_fraction"], 1.0)
        self.assertTrue(alignment[0]["exact_consecutive_suffix_match"])

    def test_input_alignment_handles_large_native_clock_origin(self) -> None:
        replay = (5, 5, 33, 33, 5, 5, 5, 5, 5, 5, 17, 17)
        frames = tuple(
            {
                "manager_frame": 12_311 + index,
                "input_current": value,
            }
            for index, value in enumerate(replay)
        )
        alignment = _input_alignment(frames, replay, radius=4)
        self.assertEqual(
            alignment[0]["manager_to_replay_offset"],
            -12_311,
        )
        self.assertEqual(alignment[0]["match_fraction"], 1.0)
        self.assertTrue(alignment[0]["exact_consecutive_suffix_match"])


if __name__ == "__main__":
    unittest.main()
