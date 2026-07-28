#!/usr/bin/env python3
"""Tests for the strict live JSONL publication boundary."""

from __future__ import annotations

import io
import math
import unittest

from th08_live.trace import TraceSink


class TraceSinkTests(unittest.TestCase):
    def test_emits_standard_json(self) -> None:
        output = io.StringIO()

        TraceSink(output).emit({"value": None}, flush=True)

        self.assertEqual(output.getvalue(), '{"value": null}\n')

    def test_rejects_nonfinite_values(self) -> None:
        output = io.StringIO()

        with self.assertRaises(ValueError):
            TraceSink(output).emit({"value": -math.inf})

        self.assertEqual(output.getvalue(), "")

    def test_emit_many_stops_before_invalid_record(self) -> None:
        output = io.StringIO()

        with self.assertRaises(ValueError):
            TraceSink(output).emit_many(
                (
                    {"value": 1.0},
                    {"value": math.nan},
                    {"value": 2.0},
                )
            )

        self.assertEqual(output.getvalue(), '{"value": 1.0}\n')


if __name__ == "__main__":
    unittest.main()
