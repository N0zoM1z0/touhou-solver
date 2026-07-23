#!/usr/bin/env python3
"""Regression tests for replay frame extraction and run compression."""

from __future__ import annotations

import hashlib
import os
import struct
import unittest
from pathlib import Path

from th08_replay import compress_input_runs, decode_replay, extract_stage_inputs


REPLAY_DIR = (
    Path(
        r"D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)\replay"
    )
    if os.name == "nt"
    else Path(
        "/mnt/d/Entertainment/Game/Touhou/"
        "[th08] 东方永夜抄 (日文版)/replay"
    )
)


class ReplayTests(unittest.TestCase):
    def test_run_compression_round_trip(self) -> None:
        inputs = (0, 0, 1, 1, 1, 0x45)
        runs = compress_input_runs(inputs)
        restored = tuple(
            run.input_mask
            for run in runs
            for _ in range(run.start_frame, run.end_frame_exclusive)
        )
        self.assertEqual(restored, inputs)

    @unittest.skipUnless((REPLAY_DIR / "th8_06.rpy").is_file(), "local replay absent")
    def test_extra_route2_trace(self) -> None:
        metadata, decoded = decode_replay(REPLAY_DIR / "th8_06.rpy")
        self.assertEqual((metadata.route_id, metadata.difficulty_index), (2, 4))
        self.assertFalse(metadata.extended_input_records)
        self.assertEqual(len(metadata.stages), 1)
        stage = metadata.stages[0]
        self.assertEqual((stage.stage_index, stage.rng_seed), (8, 0xC0A4))
        self.assertEqual(stage.frame_count, 66386)
        self.assertEqual(stage.bomb_press_frames, (13041, 27305, 45553, 59744, 64086))

        inputs = extract_stage_inputs(decoded, stage)
        raw_words = b"".join(struct.pack("<H", value) for value in inputs)
        self.assertEqual(hashlib.sha256(raw_words).hexdigest(), stage.input_sha256)
        self.assertEqual(inputs[:32], (0,) * 32)


if __name__ == "__main__":
    unittest.main()
