"""Focused tests for causal future-birth geometry lowering."""

from __future__ import annotations

import math
import unittest

from th08_future_birth_envelope import (
    FloatInterval,
    FutureDirectFire,
    lower_future_direct_fire,
    state2_position_coefficient,
)


def _h1_event(**updates: object) -> FutureDirectFire:
    fields: dict[str, object] = {
        "source": "root2129:singleton:aux0",
        "activation_frames": (1,),
        "origin_x": FloatInterval.point(60.05625534057617),
        "origin_y": FloatInterval.point(32.0),
        "mode": 1,
        "count1": 1,
        "count2": 1,
        "speed1": FloatInterval.point(0.9987534284591675),
        "speed2": FloatInterval.point(0.48124998807907104),
        "angle1": FloatInterval.point(-0.5760713815689087),
        "angle2": FloatInterval.point(0.0),
        "aim_angle": FloatInterval.point(0.0),
        "half_width": 2.0,
        "half_height": 2.0,
        "original_flags": 0x203,
        "transform_program_zero": True,
    }
    fields.update(updates)
    return FutureDirectFire(**fields)


class FutureBirthEnvelopeTests(unittest.TestCase):
    def test_native_state2_coefficients_retain_half_step_completion(self) -> None:
        self.assertEqual(state2_position_coefficient(1), -3.5)
        self.assertEqual(state2_position_coefficient(9), 0.5)
        self.assertEqual(state2_position_coefficient(10), 2.0)
        self.assertEqual(state2_position_coefficient(16), 8.0)

    def test_root2129_first_endpoint_matches_origin_minus_three_point_five_v(
        self,
    ) -> None:
        event = _h1_event()
        speed = event.speed1.lower
        angle = event.angle1.lower
        velocity_x = speed * math.cos(angle)
        velocity_y = speed * math.sin(angle)
        expected_x = event.origin_x.lower - 3.5 * velocity_x
        expected_y = event.origin_y.lower - 3.5 * velocity_y

        self.assertAlmostEqual(expected_x, 57.12478, places=4)
        self.assertAlmostEqual(expected_y, 33.90419, places=4)
        # State 2 is still in spawn ANM and therefore absent from the lethal
        # corridor hazard set at the first retained endpoint.
        result = lower_future_direct_fire(event, horizon_frames=16)
        self.assertIsNone(result[0].trajectory.sample(1))

    def test_state2_becomes_consumed_hazard_on_completion_update(self) -> None:
        result = lower_future_direct_fire(
            _h1_event(),
            horizon_frames=12,
        )
        trajectory = result[0].trajectory
        self.assertIsNone(trajectory.sample(9))
        sample = trajectory.sample(10)
        self.assertIsNotNone(sample)
        assert sample is not None
        speed = 0.9987534284591675
        angle = -0.5760713815689087
        self.assertAlmostEqual(
            sample.x,
            60.05625534057617 + 2.0 * speed * math.cos(angle),
            places=5,
        )
        self.assertAlmostEqual(
            sample.y,
            32.0 + 2.0 * speed * math.sin(angle),
            places=5,
        )

    def test_rng_angle_interval_is_a_bounded_envelope(self) -> None:
        event = _h1_event(
            mode=6,
            angle1=FloatInterval.point(-0.5),
            angle2=FloatInterval.point(0.5),
            original_flags=0x201,
        )
        result = lower_future_direct_fire(event, horizon_frames=1)
        sample = result[0].trajectory.sample(1)
        self.assertIsNotNone(sample)
        assert sample is not None
        for angle in (-0.5, 0.0, 0.5):
            x = event.origin_x.lower + event.speed1.lower * math.cos(angle)
            y = event.origin_y.lower + event.speed1.lower * math.sin(angle)
            self.assertLessEqual(abs(x - sample.x), sample.half_width)
            self.assertLessEqual(abs(y - sample.y), sample.half_height)

    def test_nonzero_transform_program_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "transform programs"):
            _h1_event(transform_program_zero=False)

    def test_unknown_native_flag_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported future bullet flags"):
            _h1_event(original_flags=0x40000203)


if __name__ == "__main__":
    unittest.main()
