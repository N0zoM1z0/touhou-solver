from __future__ import annotations

import gc
import math
import random
import struct
import time
import unittest
from unittest import mock

import numpy as np

from th08_live.bullet_birth import (
    BULLET_TIMER_CURRENT_OFFSET,
    BulletBirthTracker,
)
from th08_live.bullet_birth_native import (
    NATIVE_CALL_MODE_GIL_HELD,
    NATIVE_CALL_MODE_GIL_RELEASED,
    NativeBulletBirthTracker,
    native_bullet_birth_available,
)
from th08_live import bullet_birth_native as native_module
from th08_live.bullet_decode import (
    BULLET_GEOMETRY_OFFSET,
    BULLET_POOL_SIZE,
    BULLET_POSITION_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_VELOCITY_OFFSET,
)


def _pool() -> bytearray:
    return bytearray(BULLET_POOL_SIZE * BULLET_STRIDE)


def _set_slot(
    blob: bytearray,
    slot: int,
    *,
    state: int,
    age: int,
    geometry: tuple[float, float, float, float, float, float],
    transform_flags: int,
) -> None:
    base = slot * BULLET_STRIDE
    struct.pack_into("<H", blob, base + BULLET_STATE_OFFSET, state)
    struct.pack_into("<i", blob, base + BULLET_TIMER_CURRENT_OFFSET, age)
    struct.pack_into(
        "<2f",
        blob,
        base + BULLET_POSITION_OFFSET,
        *geometry[:2],
    )
    struct.pack_into(
        "<2f",
        blob,
        base + BULLET_VELOCITY_OFFSET,
        *geometry[2:4],
    )
    struct.pack_into(
        "<2f",
        blob,
        base + BULLET_GEOMETRY_OFFSET,
        *geometry[4:],
    )
    struct.pack_into(
        "<I",
        blob,
        base + BULLET_TRANSFORM_FLAGS_OFFSET,
        transform_flags,
    )


class NativeBulletBirthLoaderTests(unittest.TestCase):
    def test_call_modes_select_distinct_ctypes_boundaries(self) -> None:
        class FakeFunction:
            pass

        class FakeLibrary:
            def __init__(self) -> None:
                self.touhou_trace_bullet_births_v1 = FakeFunction()

        released_library = FakeLibrary()
        held_library = FakeLibrary()
        with (
            mock.patch.dict(native_module._LIBRARIES, {}, clear=True),
            mock.patch.dict(native_module._LOAD_ERRORS, {}, clear=True),
            mock.patch.dict(native_module._FUNCTIONS, {}, clear=True),
            mock.patch.object(
                native_module.ctypes,
                "CDLL",
                return_value=released_library,
            ) as cdll,
            mock.patch.object(
                native_module.ctypes,
                "PyDLL",
                return_value=held_library,
            ) as pydll,
        ):
            released = native_module._load_function(
                NATIVE_CALL_MODE_GIL_RELEASED
            )
            held = native_module._load_function(NATIVE_CALL_MODE_GIL_HELD)
            self.assertIs(
                released,
                released_library.touhou_trace_bullet_births_v1,
            )
            self.assertIs(
                held,
                held_library.touhou_trace_bullet_births_v1,
            )
            self.assertIsNot(released, held)
            cdll.assert_called_once_with(
                str(native_module.native_bullet_birth_library_path())
            )
            pydll.assert_called_once_with(
                str(native_module.native_bullet_birth_library_path())
            )
            self.assertIs(
                native_module._load_function(
                    NATIVE_CALL_MODE_GIL_RELEASED
                ),
                released,
            )
            self.assertIs(
                native_module._load_function(NATIVE_CALL_MODE_GIL_HELD),
                held,
            )

    def test_unknown_call_mode_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "call mode"):
            native_module._load_function("unknown")


@unittest.skipUnless(
    native_bullet_birth_available()
    and native_bullet_birth_available(NATIVE_CALL_MODE_GIL_HELD),
    "native bullet-birth trace library is unavailable",
)
class NativeBulletBirthTrackerTests(unittest.TestCase):
    def assert_observations_equal(self, expected, actual) -> None:
        self.assertEqual(expected.record(), actual.record())
        self.assertEqual(len(expected.evidence), len(actual.evidence))
        for expected_item, actual_item in zip(
            expected.evidence,
            actual.evidence,
        ):
            self.assertEqual(expected_item.slot, actual_item.slot)
            self.assertEqual(expected_item.kind, actual_item.kind)
            self.assertEqual(
                expected_item.observation_status,
                actual_item.observation_status,
            )
            self.assertEqual(expected_item.state, actual_item.state)
            self.assertEqual(expected_item.age, actual_item.age)
            self.assertEqual(
                expected_item.previous_state,
                actual_item.previous_state,
            )
            self.assertEqual(
                expected_item.previous_age,
                actual_item.previous_age,
            )
            self.assertEqual(
                expected_item.transform_flags,
                actual_item.transform_flags,
            )
            self.assertEqual(
                expected_item.geometry_finite,
                actual_item.geometry_finite,
            )
            for expected_value, actual_value in zip(
                (
                    expected_item.x,
                    expected_item.y,
                    expected_item.velocity_x,
                    expected_item.velocity_y,
                    expected_item.width,
                    expected_item.height,
                ),
                (
                    actual_item.x,
                    actual_item.y,
                    actual_item.velocity_x,
                    actual_item.velocity_y,
                    actual_item.width,
                    actual_item.height,
                ),
            ):
                if math.isnan(expected_value):
                    self.assertTrue(math.isnan(actual_value))
                else:
                    self.assertEqual(
                        struct.pack("<f", expected_value),
                        struct.pack("<f", actual_value),
                    )

    def test_matches_python_on_boundary_and_nonfinite_cases(self) -> None:
        blob = _pool()
        special = (
            (1, -1, (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)),
            (2, 0, (math.nan, 2.0, 3.0, 4.0, 5.0, 6.0)),
            (65535, 8, (1.0, math.inf, 3.0, 4.0, 5.0, 6.0)),
            (3, 9, (1.0, 2.0, -math.inf, 4.0, 5.0, 6.0)),
            (4, 2**31 - 1, (1.0, 2.0, 3.0, 4.0, -0.0, 6.0)),
        )
        for slot, (state, age, geometry) in enumerate(special):
            _set_slot(
                blob,
                slot,
                state=state,
                age=age,
                geometry=geometry,
                transform_flags=0xFFFFFFFF - slot,
            )
        python = BulletBirthTracker()
        native = NativeBulletBirthTracker()
        self.assert_observations_equal(
            python.observe(blob, frame_before=10, frame_after=11),
            native.observe(blob, frame_before=10, frame_after=11),
        )
        diagnostics = native.diagnostics()
        self.assertGreaterEqual(diagnostics.prepare_ms, 0.0)
        self.assertGreaterEqual(diagnostics.native_call_ms, 0.0)
        self.assertGreaterEqual(diagnostics.materialize_ms, 0.0)

        _set_slot(
            blob,
            0,
            state=1,
            age=0,
            geometry=(10.0, 20.0, 1.0, -2.0, 6.0, 8.0),
            transform_flags=7,
        )
        _set_slot(
            blob,
            2,
            state=0,
            age=-123,
            geometry=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            transform_flags=0,
        )
        _set_slot(
            blob,
            100,
            state=5,
            age=0,
            geometry=(30.0, 40.0, -1.0, 2.0, 3.0, 4.0),
            transform_flags=0x80000000,
        )
        self.assert_observations_equal(
            python.observe(blob, frame_before=12, frame_after=12),
            native.observe(blob, frame_before=12, frame_after=12),
        )

    def test_randomized_multi_generation_full_pool_parity(self) -> None:
        rng = random.Random(0xB17A)
        blob = _pool()
        python = BulletBirthTracker()
        natives = (
            NativeBulletBirthTracker(
                native_call_mode=NATIVE_CALL_MODE_GIL_RELEASED
            ),
            NativeBulletBirthTracker(
                native_call_mode=NATIVE_CALL_MODE_GIL_HELD
            ),
        )
        states = [0] * BULLET_POOL_SIZE
        ages = [0] * BULLET_POOL_SIZE
        for generation in range(16):
            for slot in range(BULLET_POOL_SIZE):
                draw = rng.random()
                if draw < 0.18:
                    states[slot] = 0
                    ages[slot] = rng.randint(-(2**31), 2**31 - 1)
                elif draw < 0.42 or states[slot] == 0:
                    states[slot] = rng.randint(1, 65535)
                    ages[slot] = rng.choice(
                        (-1, 0, 1, 8, 9, rng.randint(0, 5000))
                    )
                else:
                    ages[slot] = min(2**31 - 1, ages[slot] + 1)
                geometry = (
                    rng.uniform(-256.0, 640.0),
                    rng.uniform(-64.0, 512.0),
                    rng.uniform(-16.0, 16.0),
                    rng.uniform(-16.0, 16.0),
                    rng.uniform(-32.0, 32.0),
                    rng.uniform(-32.0, 32.0),
                )
                _set_slot(
                    blob,
                    slot,
                    state=states[slot],
                    age=ages[slot],
                    geometry=geometry,
                    transform_flags=rng.getrandbits(32),
                )
            frame_before = generation * 3
            frame_after = frame_before + generation % 2
            expected = python.observe(
                blob,
                frame_before=frame_before,
                frame_after=frame_after,
            )
            for native in natives:
                self.assert_observations_equal(
                    expected,
                    native.observe(
                        blob,
                        frame_before=frame_before,
                        frame_after=frame_after,
                    ),
                )

    def test_reset_and_validation_match_python(self) -> None:
        blob = _pool()
        python = BulletBirthTracker()
        natives = (
            NativeBulletBirthTracker(
                native_call_mode=NATIVE_CALL_MODE_GIL_RELEASED
            ),
            NativeBulletBirthTracker(
                native_call_mode=NATIVE_CALL_MODE_GIL_HELD
            ),
        )
        for tracker in (python, *natives):
            with self.assertRaisesRegex(ValueError, "requires"):
                tracker.observe(
                    blob[:-1],
                    frame_before=0,
                    frame_after=0,
                )
            with self.assertRaisesRegex(ValueError, "invalid"):
                tracker.observe(blob, frame_before=2, frame_after=1)
            tracker.observe(blob, frame_before=3, frame_after=3)
            with self.assertRaisesRegex(ValueError, "regressed"):
                tracker.observe(blob, frame_before=2, frame_after=3)
            tracker.reset()
        expected = python.observe(blob, frame_before=0, frame_after=0)
        for native in natives:
            self.assert_observations_equal(
                expected,
                native.observe(blob, frame_before=0, frame_after=0),
            )

    def test_call_modes_report_identity_and_match_exactly(self) -> None:
        blob = _pool()
        _set_slot(
            blob,
            17,
            state=5,
            age=0,
            geometry=(10.0, 20.0, 1.0, -2.0, 6.0, 8.0),
            transform_flags=7,
        )
        released = NativeBulletBirthTracker(
            native_call_mode=NATIVE_CALL_MODE_GIL_RELEASED
        )
        held = NativeBulletBirthTracker(
            native_call_mode=NATIVE_CALL_MODE_GIL_HELD
        )
        self.assertEqual(
            released.native_call_mode,
            NATIVE_CALL_MODE_GIL_RELEASED,
        )
        self.assertEqual(held.native_call_mode, NATIVE_CALL_MODE_GIL_HELD)
        self.assert_observations_equal(
            released.observe(blob, frame_before=1, frame_after=1),
            held.observe(blob, frame_before=1, frame_after=1),
        )

    def test_capacity_error_does_not_advance_native_history(self) -> None:
        blob = _pool()
        tracker = NativeBulletBirthTracker()
        tracker._previous_states[:] = np.arange(
            BULLET_POOL_SIZE,
            dtype=np.uint16,
        )
        tracker._previous_ages[:] = np.arange(
            BULLET_POOL_SIZE,
            dtype=np.int32,
        )
        before_states = tracker._previous_states.copy()
        before_ages = tracker._previous_ages.copy()
        required_size = BULLET_POOL_SIZE * BULLET_STRIDE
        pointer = tracker._raw_pointer_for(
            blob,
            required_size=required_size,
        )
        self.assertEqual(
            tracker._invoke(
                pointer,
                required_size=required_size,
                output_capacity=BULLET_POOL_SIZE - 1,
            ),
            -1,
        )
        np.testing.assert_array_equal(
            tracker._previous_states,
            before_states,
        )
        np.testing.assert_array_equal(
            tracker._previous_ages,
            before_ages,
        )

    def test_diagnostics_reconcile_and_count_native_phase_gc(self) -> None:
        blob = _pool()
        tracker = NativeBulletBirthTracker()
        original_invoke = tracker._invoke

        def invoke_with_collection(*args, **kwargs):
            result = original_invoke(*args, **kwargs)
            gc.collect(0)
            return result

        tracker._invoke = invoke_with_collection
        started = time.perf_counter()
        tracker.observe(blob, frame_before=0, frame_after=0)
        observation_ms = (time.perf_counter() - started) * 1000.0
        diagnostics = tracker.diagnostics()
        record = diagnostics.record(observation_ms=observation_ms)
        segments = record["native_segments_ms"]
        completed = record["gc_completed"]
        self.assertIsInstance(segments, dict)
        self.assertIsInstance(completed, dict)
        self.assertAlmostEqual(
            sum(segments.values()),
            observation_ms,
            places=6,
        )
        self.assertEqual(completed["prepare"], [0, 0, 0])
        self.assertEqual(completed["native_call"], [1, 0, 0])
        self.assertEqual(completed["materialize"], [0, 0, 0])

        gc.collect(0)
        tracker._invoke = original_invoke
        tracker.observe(blob, frame_before=1, frame_after=1)
        self.assertEqual(
            tracker.diagnostics().gc_completed,
            ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
        )


if __name__ == "__main__":
    unittest.main()
