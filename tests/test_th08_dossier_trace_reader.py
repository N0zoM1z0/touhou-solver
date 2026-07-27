#!/usr/bin/env python3
"""Focused tests for shared offline dossier ingestion."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from analysis.dossier.statistics import percentiles
from analysis.dossier.trace_reader import read_practice_trace, read_trace


def _decision(frame: int) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": frame,
        "stage_route_index": 3,
        "resources": {"lives": 8.0, "bombs": 4.0, "power": 128.0},
        "player": {
            "x": 192.0,
            "y": 384.0,
            "phase": 0,
            "phase_at_action": 0,
            "predeath_at_action": 10,
        },
        "action": "stay",
        "mask": 5,
        "bomb": False,
        "hit_started": False,
    }


class DossierTraceReaderTests(unittest.TestCase):
    def test_readers_share_hash_and_parse_error_semantics(self) -> None:
        rows = [
            {"kind": "identity", "pid": 123},
            {"kind": "controller_config", "bomb_policy": "disabled"},
            _decision(100),
            {"kind": "auto_confirm_wall_pulse", "frame": 101},
            {"kind": "summary", "last_frame": 100},
        ]
        payload = b"".join(
            json.dumps(row, separators=(",", ":")).encode() + b"\n" for row in rows[:2]
        )
        payload += b"{invalid-json\n"
        payload += b"".join(
            json.dumps(row, separators=(",", ":")).encode() + b"\n" for row in rows[2:]
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "trace.jsonl"
            path.write_bytes(payload)

            practice = read_practice_trace(path)
            provenance, decisions = read_trace(path, trace_index=7)

        expected_digest = hashlib.sha256(payload).hexdigest()
        self.assertEqual(practice.sha256, expected_digest)
        self.assertEqual(provenance.sha256, expected_digest)
        self.assertEqual(practice.size_bytes, len(payload))
        self.assertEqual(provenance.size_bytes, len(payload))
        self.assertEqual(practice.parse_errors, 1)
        self.assertEqual(provenance.parse_errors, 1)
        self.assertEqual(practice.raw_kind_counts["decision"], 1)
        self.assertEqual(practice.end_event["reason"], "raw_trace_end")
        self.assertEqual(provenance.wall_auto_confirm_frames, (101,))
        self.assertEqual(provenance.decision_count, 1)
        self.assertEqual(decisions[0]["trace_index"], 7)

    def test_percentile_convention_remains_floor_indexed(self) -> None:
        self.assertEqual(
            percentiles(range(1, 21)),
            {"median": 10.5, "p95": 19.0, "max": 20.0},
        )
        self.assertIsNone(percentiles(()))


if __name__ == "__main__":
    unittest.main()
