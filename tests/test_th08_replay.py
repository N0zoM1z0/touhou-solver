#!/usr/bin/env python3
"""Regression tests for replay frame extraction and run compression."""

from __future__ import annotations

import hashlib
import os
import struct
import unittest
from pathlib import Path

from th08_pbgz import lzss_compress_literals, lzss_decompress
from th08_replay import (
    compress_input_runs,
    decode_replay,
    encode_replay,
    extract_stage_inputs,
    replace_stage_inputs,
)


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
    def test_literal_lzss_round_trip(self) -> None:
        for payload in (b"", b"\x00", b"replay root\x00\xff" * 19):
            encoded = lzss_compress_literals(payload)
            self.assertEqual(lzss_decompress(encoded, len(payload)), payload)

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

    @unittest.skipUnless(
        (REPLAY_DIR / "th8_15.rpy").is_file(),
        "local Stage-5 replay absent",
    )
    def test_replay_encode_and_input_mutation_round_trip(self) -> None:
        path = REPLAY_DIR / "th8_15.rpy"
        metadata, decoded = decode_replay(path)
        stage = metadata.stages[0]
        source_inputs = extract_stage_inputs(decoded, stage)

        reencoded_path = Path(self.id().replace(".", "_") + ".rpy")
        try:
            reencoded_path.write_bytes(encode_replay(decoded))
            round_trip_metadata, round_trip_decoded = decode_replay(
                reencoded_path
            )
            normalized_source = bytearray(decoded)
            normalized_round_trip = bytearray(round_trip_decoded)
            for offset, size in ((12, 8), (24, 4)):
                normalized_source[offset : offset + size] = b"\x00" * size
                normalized_round_trip[offset : offset + size] = (
                    b"\x00" * size
                )
            self.assertEqual(normalized_round_trip, normalized_source)
            self.assertEqual(
                round_trip_metadata.stages[0].input_sha256,
                stage.input_sha256,
            )

            replacement = (0x00, 0x01, 0xF5)
            mutated = replace_stage_inputs(
                decoded,
                stage,
                start_frame=100,
                input_masks=replacement,
            )
            reencoded_path.write_bytes(encode_replay(mutated))
            mutated_metadata, mutated_decoded = decode_replay(reencoded_path)
            mutated_stage = mutated_metadata.stages[0]
            mutated_inputs = extract_stage_inputs(
                mutated_decoded,
                mutated_stage,
            )
            self.assertEqual(mutated_inputs[:100], source_inputs[:100])
            self.assertEqual(mutated_inputs[100:103], replacement)
            self.assertEqual(mutated_inputs[103:], source_inputs[103:])
        finally:
            reencoded_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
