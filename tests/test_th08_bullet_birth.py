from __future__ import annotations

import math
import struct
import unittest

from th08_live.bullet_birth import (
    BIRTH_KIND_ACTIVATION_EDGE,
    BIRTH_KIND_BOOTSTRAP_RECENT,
    BIRTH_KIND_INVALID_TIMER,
    BIRTH_KIND_TIMER_REGRESSION,
    BULLET_TIMER_CURRENT_OFFSET,
    BulletBirthTracker,
    OBSERVATION_CAPTURE_SPANNED,
    OBSERVATION_INVALID_TIMER,
    OBSERVATION_SLOT_REUSE_AMBIGUOUS,
)
from th08_live.bullet_decode import (
    BULLET_ANGLE_OFFSET,
    BULLET_GEOMETRY_OFFSET,
    BULLET_POSITION_OFFSET,
    BULLET_SPEED_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_VELOCITY_OFFSET,
    decode_planning_bullets,
)
from th08_live.sensor import BULLET_POOL_SIZE, BULLET_STRIDE


def _pool() -> bytearray:
    return bytearray(BULLET_POOL_SIZE * BULLET_STRIDE)


def _set_slot(
    blob: bytearray,
    slot: int,
    *,
    state: int,
    age: int,
    x: float = 10.0,
    y: float = 20.0,
    velocity_x: float = 1.0,
    velocity_y: float = -2.0,
    width: float = 6.0,
    height: float = 8.0,
    transform_flags: int = 0,
) -> None:
    base = slot * BULLET_STRIDE
    struct.pack_into("<H", blob, base + BULLET_STATE_OFFSET, state)
    struct.pack_into("<i", blob, base + BULLET_TIMER_CURRENT_OFFSET, age)
    struct.pack_into(
        "<ff",
        blob,
        base + BULLET_GEOMETRY_OFFSET,
        width,
        height,
    )
    struct.pack_into(
        "<ff",
        blob,
        base + BULLET_POSITION_OFFSET,
        x,
        y,
    )
    struct.pack_into(
        "<ff",
        blob,
        base + BULLET_VELOCITY_OFFSET,
        velocity_x,
        velocity_y,
    )
    struct.pack_into(
        "<I",
        blob,
        base + BULLET_TRANSFORM_FLAGS_OFFSET,
        transform_flags,
    )
    struct.pack_into("<f", blob, base + BULLET_SPEED_OFFSET, 2.0)
    struct.pack_into("<f", blob, base + BULLET_ANGLE_OFFSET, 0.0)


class BulletBirthTrackerTests(unittest.TestCase):
    def test_rejects_short_pool_blob(self) -> None:
        with self.assertRaisesRegex(ValueError, "bullet pool requires"):
            BulletBirthTracker().observe(
                bytearray(64),
                frame_before=1,
                frame_after=1,
            )

    def test_rejects_invalid_or_regressing_capture_interval(self) -> None:
        tracker = BulletBirthTracker()
        blob = _pool()
        with self.assertRaisesRegex(ValueError, "invalid bullet capture"):
            tracker.observe(blob, frame_before=3, frame_after=2)
        tracker.observe(blob, frame_before=10, frame_after=11)
        with self.assertRaisesRegex(ValueError, "capture frame regressed"):
            tracker.observe(blob, frame_before=9, frame_after=12)

    def test_first_capture_keeps_only_recent_bootstrap_evidence(self) -> None:
        blob = _pool()
        _set_slot(blob, 5, state=1, age=8)
        _set_slot(blob, 6, state=1, age=9)
        result = BulletBirthTracker(maximum_bootstrap_age=8).observe(
            blob,
            frame_before=100,
            frame_after=101,
        )
        self.assertEqual(result.active_count, 2)
        self.assertEqual(len(result.evidence), 1)
        evidence = result.evidence[0]
        self.assertEqual(evidence.slot, 5)
        self.assertEqual(evidence.kind, BIRTH_KIND_BOOTSTRAP_RECENT)
        self.assertEqual(
            evidence.observation_status,
            OBSERVATION_CAPTURE_SPANNED,
        )
        self.assertIsNone(evidence.activation_support_start)
        self.assertEqual(evidence.activation_support_end, 101)

    def test_activation_edge_retains_geometry_and_capture_support(self) -> None:
        tracker = BulletBirthTracker()
        blob = _pool()
        tracker.observe(blob, frame_before=40, frame_after=41)
        _set_slot(
            blob,
            17,
            state=1,
            age=1,
            x=123.5,
            y=77.25,
            velocity_x=-0.5,
            velocity_y=3.25,
            width=12.0,
            height=14.0,
            transform_flags=0x40,
        )
        result = tracker.observe(blob, frame_before=43, frame_after=44)
        self.assertEqual(len(result.evidence), 1)
        evidence = result.evidence[0]
        self.assertEqual(evidence.slot, 17)
        self.assertEqual(evidence.kind, BIRTH_KIND_ACTIVATION_EDGE)
        self.assertEqual(evidence.previous_state, 0)
        self.assertEqual(evidence.previous_age, 0)
        self.assertEqual(evidence.activation_support_start, 40)
        self.assertEqual(evidence.activation_support_end, 44)
        self.assertEqual((evidence.x, evidence.y), (123.5, 77.25))
        self.assertEqual(
            (evidence.velocity_x, evidence.velocity_y),
            (-0.5, 3.25),
        )
        self.assertEqual((evidence.width, evidence.height), (12.0, 14.0))
        self.assertEqual(evidence.transform_flags, 0x40)
        self.assertTrue(evidence.geometry_finite)

    def test_timer_regression_is_slot_reuse_ambiguity(self) -> None:
        tracker = BulletBirthTracker()
        blob = _pool()
        _set_slot(blob, 3, state=1, age=100)
        tracker.observe(blob, frame_before=10, frame_after=10)
        _set_slot(blob, 3, state=1, age=2)
        result = tracker.observe(blob, frame_before=13, frame_after=13)
        self.assertEqual(len(result.evidence), 1)
        evidence = result.evidence[0]
        self.assertEqual(evidence.kind, BIRTH_KIND_TIMER_REGRESSION)
        self.assertEqual(
            evidence.observation_status,
            OBSERVATION_SLOT_REUSE_AMBIGUOUS,
        )
        self.assertEqual(evidence.previous_age, 100)

    def test_release_then_reactivation_is_an_activation_edge(self) -> None:
        tracker = BulletBirthTracker()
        blob = _pool()
        _set_slot(blob, 9, state=1, age=20)
        tracker.observe(blob, frame_before=1, frame_after=1)
        _set_slot(blob, 9, state=0, age=20)
        empty = tracker.observe(blob, frame_before=2, frame_after=2)
        self.assertEqual(empty.evidence, ())
        _set_slot(blob, 9, state=1, age=0)
        result = tracker.observe(blob, frame_before=3, frame_after=3)
        self.assertEqual(result.evidence[0].kind, BIRTH_KIND_ACTIVATION_EDGE)
        self.assertEqual(result.evidence[0].previous_state, 0)

    def test_inactive_stale_timer_is_ignored(self) -> None:
        blob = _pool()
        _set_slot(blob, 11, state=0, age=-999)
        result = BulletBirthTracker().observe(
            blob,
            frame_before=1,
            frame_after=1,
        )
        self.assertEqual(result.active_count, 0)
        self.assertEqual(result.evidence, ())

    def test_active_negative_timer_is_retained_as_invalid(self) -> None:
        blob = _pool()
        _set_slot(blob, 12, state=1, age=-1)
        result = BulletBirthTracker().observe(
            blob,
            frame_before=1,
            frame_after=2,
        )
        self.assertEqual(len(result.evidence), 1)
        evidence = result.evidence[0]
        self.assertEqual(evidence.kind, BIRTH_KIND_INVALID_TIMER)
        self.assertEqual(
            evidence.observation_status,
            OBSERVATION_INVALID_TIMER,
        )

    def test_nonfinite_geometry_is_explicit_and_deterministic(self) -> None:
        blob = _pool()
        _set_slot(blob, 2, state=1, age=0, x=math.nan)
        tracker = BulletBirthTracker()
        first = tracker.observe(blob, frame_before=8, frame_after=8)
        self.assertFalse(first.evidence[0].geometry_finite)
        self.assertTrue(math.isnan(first.evidence[0].x))
        first_record = first.record()
        self.assertEqual(
            first_record["evidence"][0]["position"],
            [None, 20.0],
        )

        tracker.reset()
        second = tracker.observe(blob, frame_before=8, frame_after=8)
        second_record = second.record()
        self.assertEqual(
            first_record.keys(),
            second_record.keys(),
        )
        self.assertEqual(
            first_record["evidence"][0]["slot"],
            second_record["evidence"][0]["slot"],
        )

    def test_observer_does_not_mutate_existing_planning_decode(self) -> None:
        blob = _pool()
        _set_slot(blob, 100, state=1, age=3, transform_flags=0)
        before_blob = bytes(blob)
        expected = decode_planning_bullets(blob)
        BulletBirthTracker().observe(
            blob,
            frame_before=20,
            frame_after=21,
        )
        actual = decode_planning_bullets(blob)
        self.assertEqual(bytes(blob), before_blob)
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
