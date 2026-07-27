#!/usr/bin/env python3
"""Tests for independently retained ECL snapshot and lookahead outcomes."""

from __future__ import annotations

import unittest

from th08_ecl_runtime import (
    EclInstructionCache,
    EclLookaheadResult,
    EclVmSnapshot,
)
from th08_live.ecl_capture import (
    ENEMY_MANAGER_FRAME_ADDRESS,
    capture_main_ecl,
)


class _Reader:
    def __init__(self) -> None:
        self.frames = iter((100, 101))

    def u32(self, address: int) -> int:
        if address != ENEMY_MANAGER_FRAME_ADDRESS:
            raise AssertionError(f"unexpected address {address:#x}")
        return next(self.frames)

    def read(self, _address: int, _size: int) -> bytes:
        return b""


def _snapshot(_reader: object, _pointer: int) -> EclVmSnapshot:
    return EclVmSnapshot(
        instruction_pointer=0x401000,
        timer_fraction=0.0,
        timer_elapsed=10,
        tag_mask=0,
        callback_angle=0.0,
        callback_speed=0.0,
        time_scale=1.0,
    )


class MainEclCaptureTests(unittest.TestCase):
    def test_lookahead_failure_keeps_observed_vm_snapshot(self) -> None:
        def reject_lookahead(*_args: object, **_kwargs: object) -> object:
            raise ValueError("unsupported control flow")

        capture = capture_main_ecl(
            _Reader(),
            enemy_pointer=0x500000,
            instruction_cache=EclInstructionCache(),
            horizon_frames=80,
            active_difficulty_mask=8,
            clock=iter((1.0, 1.002)).__next__,
            snapshot_reader=_snapshot,
            lookahead_analyzer=reject_lookahead,
        )
        self.assertIsNotNone(capture.snapshot)
        self.assertIsNone(capture.lookahead)
        self.assertEqual(capture.tagged_velocity_toggles, ())
        self.assertEqual(
            capture.error,
            "ValueError: unsupported control flow",
        )
        self.assertEqual((capture.frame_before, capture.frame_after), (100, 101))
        self.assertAlmostEqual(capture.elapsed_ms, 2.0)

    def test_snapshot_failure_remains_fail_closed(self) -> None:
        def reject_snapshot(_reader: object, _pointer: int) -> object:
            raise OSError("unreadable VM")

        capture = capture_main_ecl(
            _Reader(),
            enemy_pointer=0x500000,
            instruction_cache=EclInstructionCache(),
            horizon_frames=80,
            active_difficulty_mask=8,
            clock=iter((1.0, 1.001)).__next__,
            snapshot_reader=reject_snapshot,
        )
        self.assertIsNone(capture.snapshot)
        self.assertIsNone(capture.lookahead)
        self.assertEqual(capture.error, "OSError: unreadable VM")

    def test_success_retains_callback_result(self) -> None:
        result = EclLookaheadResult(
            events=(),
            instructions_scanned=3,
            stop_reason="horizon",
            horizon_covered=True,
        )
        capture = capture_main_ecl(
            _Reader(),
            enemy_pointer=0x500000,
            instruction_cache=EclInstructionCache(),
            horizon_frames=80,
            active_difficulty_mask=8,
            clock=iter((1.0, 1.001)).__next__,
            snapshot_reader=_snapshot,
            lookahead_analyzer=lambda *_args, **_kwargs: result,
        )
        self.assertIsNotNone(capture.snapshot)
        self.assertIs(capture.lookahead, result)
        self.assertIsNone(capture.error)


if __name__ == "__main__":
    unittest.main()
