#!/usr/bin/env python3
"""Tests for strict shipped runtime-ECL physical evidence audit."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from analysis.th08_runtime_ecl_identity_audit import (
    STAGE5_STATIC_LABEL,
    STAGE5_STATIC_LENGTH,
    STAGE5_STATIC_SHA256,
    RuntimeEclIdentityAuditError,
    audit,
)
from th08_runtime.game_state import EXPECTED_EXE_SHA256


def _identity_row() -> dict[str, object]:
    return {
        "schema": "th08-runtime-ecl-identity-observation-v1",
        "kind": "runtime_ecl_identity",
        "status": "exact_match",
        "authority": "trace_only_instruction_byte_identity",
        "pid": 1234,
        "executable_sha256": EXPECTED_EXE_SHA256,
        "route_id": 2,
        "difficulty_index": 3,
        "stage_route_index": 5,
        "gameplay_epoch": 0,
        "decision_frame": 102,
        "snapshot_frame": 101,
        "static_image": {
            "label": STAGE5_STATIC_LABEL,
            "length": STAGE5_STATIC_LENGTH,
            "sha256": STAGE5_STATIC_SHA256,
        },
        "capture": {
            "schema": "th08-runtime-ecl-image-capture-v1",
            "runtime_base": 0x02100000,
            "image_length": STAGE5_STATIC_LENGTH,
            "subroutine_count": 80,
            "timeline_count": 1,
            "relocated_sha256": "1" * 64,
            "normalized_sha256": STAGE5_STATIC_SHA256,
            "capture_ms": 0.75,
            "read_count": 4,
        },
        "identity": {
            "schema": "th08-runtime-ecl-image-identity-v1",
            "exact_match": True,
            "static_sha256": STAGE5_STATIC_SHA256,
            "normalized_runtime_sha256": STAGE5_STATIC_SHA256,
            "image_length": STAGE5_STATIC_LENGTH,
            "first_difference_offset": None,
        },
        "error": None,
        "transaction_ms": 0.9,
    }


class RuntimeEclIdentityAuditTests(unittest.TestCase):
    @staticmethod
    def _write_trace(rows: list[dict[str, object]]) -> Path:
        temporary = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".jsonl",
            delete=False,
        )
        with temporary:
            for row in rows:
                temporary.write(
                    json.dumps(row, allow_nan=False) + "\n"
                )
        return Path(temporary.name)

    def test_exact_one_shot_identity_passes_with_adjacent_cadence(
        self,
    ) -> None:
        trace = self._write_trace(
            [
                {
                    "kind": "decision",
                    "frame": 100,
                    "mask": 1,
                    "bomb": False,
                },
                _identity_row(),
                {
                    "kind": "decision",
                    "frame": 102,
                    "mask": 5,
                    "bomb": False,
                },
                {
                    "kind": "decision",
                    "frame": 105,
                    "mask": 4,
                    "bomb": False,
                },
                {
                    "kind": "summary",
                    "termination_reason": "route_complete",
                },
            ]
        )
        self.addCleanup(trace.unlink)
        result = audit(trace)
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["observation"]["normalized_sha256"],
            STAGE5_STATIC_SHA256,
        )
        self.assertEqual(
            result["adjacent_decision_cadence"],
            {
                "previous_frame": 100,
                "previous_delta": 2,
                "next_frame": 105,
                "next_delta": 3,
            },
        )
        self.assertEqual(
            result["authority"]["physical_action"],
            "none",
        )

    def test_duplicate_attempts_fail_closed(self) -> None:
        row = _identity_row()
        trace = self._write_trace(
            [
                row,
                row,
                {
                    "kind": "decision",
                    "frame": 102,
                    "mask": 0,
                    "bomb": False,
                },
                {
                    "kind": "summary",
                    "termination_reason": "route_complete",
                },
            ]
        )
        self.addCleanup(trace.unlink)
        with self.assertRaisesRegex(
            RuntimeEclIdentityAuditError,
            "exactly one",
        ):
            audit(trace)

    def test_nonexact_status_fails_closed(self) -> None:
        row = _identity_row()
        row["status"] = "byte_mismatch"
        identity = row["identity"]
        assert isinstance(identity, dict)
        identity["exact_match"] = False
        identity["first_difference_offset"] = 123
        trace = self._write_trace(
            [
                row,
                {
                    "kind": "decision",
                    "frame": 102,
                    "mask": 0,
                    "bomb": False,
                },
                {
                    "kind": "summary",
                    "termination_reason": "route_complete",
                },
            ]
        )
        self.addCleanup(trace.unlink)
        with self.assertRaisesRegex(
            RuntimeEclIdentityAuditError,
            "did not match",
        ):
            audit(trace)


if __name__ == "__main__":
    unittest.main()
