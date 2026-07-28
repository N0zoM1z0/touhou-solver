from __future__ import annotations

import math
import struct
import unittest

import numpy as np

from th08_live.bullet_birth import (
    BIRTH_KIND_ACTIVATION_EDGE,
    BIRTH_KIND_BOOTSTRAP_RECENT,
    BIRTH_KIND_INVALID_TIMER,
    BIRTH_KIND_TIMER_REGRESSION,
    BULLET_TIMER_CURRENT_OFFSET,
    BulletBirthEvidenceBatch,
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
    def test_columnar_batch_retains_validation_and_read_only_columns(
        self,
    ) -> None:
        arguments = {
            "slots": np.array([7], dtype=np.int32),
            "codes": np.array([3], dtype=np.uint8),
            "states": np.array([2], dtype=np.uint16),
            "ages": np.array([4], dtype=np.int32),
            "previous_states": np.array([0], dtype=np.uint16),
            "previous_ages": np.array([9], dtype=np.int32),
            "support_start": 100,
            "support_end": 104,
            "geometry": np.array(
                [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]],
                dtype=np.float32,
            ),
            "transform_flags": np.array([11], dtype=np.uint32),
            "geometry_finite": np.array([True], dtype=np.bool_),
        }
        batch = BulletBirthEvidenceBatch(**arguments)
        self.assertEqual(batch[0].slot, 7)
        self.assertEqual(batch[0].activation_support_start, 100)
        self.assertEqual(
            batch.record()["geometry_finite"],
            [True],
        )
        for column in (
            batch._slots,
            batch._codes,
            batch._states,
            batch._ages,
            batch._previous_states,
            batch._previous_ages,
            batch._geometry,
            batch._transform_flags,
            batch._geometry_finite,
        ):
            self.assertFalse(column.flags.writeable)

        invalid_cases = {
            "length": {
                **arguments,
                "codes": np.array([], dtype=np.uint8),
            },
            "previous_pair": {
                **arguments,
                "previous_states": None,
            },
            "geometry_shape": {
                **arguments,
                "geometry": np.zeros((1, 5), dtype=np.float32),
            },
            "code": {
                **arguments,
                "codes": np.array([5], dtype=np.uint8),
            },
        }
        for name, invalid in invalid_cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                BulletBirthEvidenceBatch(**invalid)

    def test_compact_double_buffer_matches_independent_scalar_transitions(
        self,
    ) -> None:
        blob = _pool()
        tracker = BulletBirthTracker(maximum_bootstrap_age=3)
        previous_states: list[int] | None = None
        previous_ages: list[int] | None = None
        previous_frame_before: int | None = None

        for generation in range(16):
            for slot in range(48):
                state = int((generation * 7 + slot * 3) % 5 != 0)
                age = (
                    -1
                    if state and (generation * 11 + slot) % 37 == 0
                    else (generation * 3 + slot * 5) % 17
                )
                _set_slot(
                    blob,
                    slot,
                    state=state,
                    age=age,
                    x=(
                        math.nan
                        if (generation + slot) % 41 == 0
                        else generation + slot * 0.25
                    ),
                    y=slot * 0.5,
                    velocity_x=generation * -0.125,
                    velocity_y=slot * 0.0625,
                    width=6.0 + (slot % 3),
                    height=8.0 + (generation % 2),
                    transform_flags=(generation << 8) | slot,
                )

            frame_before = generation * 2
            frame_after = frame_before + int(generation % 4 == 0)
            observation = tracker.observe(
                blob,
                frame_before=frame_before,
                frame_after=frame_after,
            )
            states = [
                struct.unpack_from(
                    "<H",
                    blob,
                    slot * BULLET_STRIDE + BULLET_STATE_OFFSET,
                )[0]
                for slot in range(BULLET_POOL_SIZE)
            ]
            ages = [
                struct.unpack_from(
                    "<i",
                    blob,
                    slot * BULLET_STRIDE + BULLET_TIMER_CURRENT_OFFSET,
                )[0]
                for slot in range(BULLET_POOL_SIZE)
            ]
            expected: list[
                tuple[int, str, str, int | None, int | None, int | None]
            ] = []
            for slot, (state, age) in enumerate(zip(states, ages)):
                if state and age < 0:
                    expected.append(
                        (
                            slot,
                            BIRTH_KIND_INVALID_TIMER,
                            OBSERVATION_INVALID_TIMER,
                            (
                                previous_states[slot]
                                if previous_states is not None
                                else None
                            ),
                            (
                                previous_ages[slot]
                                if previous_ages is not None
                                else None
                            ),
                            None,
                        )
                    )
                elif state and previous_states is None and age <= 3:
                    expected.append(
                        (
                            slot,
                            BIRTH_KIND_BOOTSTRAP_RECENT,
                            OBSERVATION_CAPTURE_SPANNED,
                            None,
                            None,
                            None,
                        )
                    )
                elif (
                    state
                    and previous_states is not None
                    and previous_ages is not None
                    and not previous_states[slot]
                ):
                    expected.append(
                        (
                            slot,
                            BIRTH_KIND_ACTIVATION_EDGE,
                            OBSERVATION_CAPTURE_SPANNED,
                            previous_states[slot],
                            previous_ages[slot],
                            previous_frame_before,
                        )
                    )
                elif (
                    state
                    and previous_states is not None
                    and previous_ages is not None
                    and previous_states[slot]
                    and age < previous_ages[slot]
                ):
                    expected.append(
                        (
                            slot,
                            BIRTH_KIND_TIMER_REGRESSION,
                            OBSERVATION_SLOT_REUSE_AMBIGUOUS,
                            previous_states[slot],
                            previous_ages[slot],
                            previous_frame_before,
                        )
                    )
            actual = [
                (
                    item.slot,
                    item.kind,
                    item.observation_status,
                    item.previous_state,
                    item.previous_age,
                    item.activation_support_start,
                )
                for item in observation.evidence
            ]
            self.assertEqual(actual, expected)
            self.assertEqual(
                observation.active_count,
                sum(state != 0 for state in states),
            )
            self.assertEqual(
                [item.slot for item in observation.evidence],
                sorted(item.slot for item in observation.evidence),
            )
            previous_states = states
            previous_ages = ages
            previous_frame_before = frame_before

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
            first_record["evidence"]["geometry"][0],
            [None, 20.0, 1.0, -2.0, 6.0, 8.0],
        )

        tracker.reset()
        second = tracker.observe(blob, frame_before=8, frame_after=8)
        second_record = second.record()
        self.assertEqual(
            first_record.keys(),
            second_record.keys(),
        )
        self.assertEqual(
            first_record["evidence"]["slot"][0],
            second_record["evidence"]["slot"][0],
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
