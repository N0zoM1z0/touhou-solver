#!/usr/bin/env python3
"""Tests for the game-neutral fail-closed runtime-control handshake."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime_agent import (
    FrameSynchronizedPlayback,
    input_transitions,
    load_input_masks,
)


class RuntimeAgentTests(unittest.TestCase):
    def test_releases_precede_presses(self) -> None:
        changes = input_transitions(0x41, 0x82, supported_mask=0xF7)
        self.assertEqual(
            [(item.bit, item.pressed) for item in changes],
            [(0x01, False), (0x40, False), (0x02, True), (0x80, True)],
        )

    def test_one_frame_ahead_handshake(self) -> None:
        playback = FrameSynchronizedPlayback((0x01, 0x41), supported_mask=0xF7)
        self.assertEqual([(item.bit, item.pressed) for item in playback.arm(100)], [(1, True)])
        first = playback.observe(101, 0x01)
        self.assertFalse(first.finished)
        self.assertEqual([(item.bit, item.pressed) for item in first.transitions], [(0x40, True)])
        second = playback.observe(102, 0x41)
        self.assertTrue(second.finished)
        self.assertEqual(
            [(item.bit, item.pressed) for item in second.transitions],
            [(0x01, False), (0x40, False)],
        )

    def test_frame_skip_and_readback_mismatch_abort(self) -> None:
        playback = FrameSynchronizedPlayback((0x01,), supported_mask=0xF7)
        playback.arm(7)
        with self.assertRaisesRegex(RuntimeError, "discontinuity"):
            playback.observe(9, 0x01)

        playback = FrameSynchronizedPlayback((0x01,), supported_mask=0xF7)
        playback.arm(7)
        with self.assertRaisesRegex(RuntimeError, "readback mismatch"):
            playback.observe(8, 0x00)

    def test_load_compact_runs(self) -> None:
        payload = {
            "frame_count": 4,
            "runs": [
                {"start_frame": 0, "end_frame_exclusive": 2, "input_mask": 1},
                {"start_frame": 2, "end_frame_exclusive": 4, "input_mask": 5},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(load_input_masks(path), (1, 1, 5, 5))


if __name__ == "__main__":
    unittest.main()
