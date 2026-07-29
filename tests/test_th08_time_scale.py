#!/usr/bin/env python3
"""Focused SEM-SCALE schedule and product/oracle regressions."""

import math
import unittest

from analysis.th08_scale_transition_raw_oracle import (
    RawLaserState,
    oracle_step_laser_raw,
    oracle_step_route2_movement_raw,
)
from movement_model import MovementBounds
from th08_ecl_vm_state import float32_bits
from th08_laser_model import (
    LaserPhase,
    laser_collision_geometry_frames,
    spawn_laser_state,
    step_laser,
)
from th08_laser_pool import (
    PLAYER_NORMAL,
    LaserPoolState,
    step_laser_pool,
)
from th08_movement_model import project_route2_movement_schedule
from th08_time_scale import (
    SCALE_COVERAGE_COMPLETE,
    SCALE_COVERAGE_ROOT_ONLY,
    TH08_UNIT_TIME_SCALE_BITS,
    Th08TimeScaleSchedule,
    canonical_time_scale_bits,
    validate_time_scale_bits,
)


_PHYSICAL_BOUNDS = MovementBounds(8.0, 16.0, 376.0, 432.0)


class TimeScaleScheduleTests(unittest.TestCase):
    def test_root_observation_proves_player_not_laser_phase(self) -> None:
        quarter = float32_bits(0.25)
        schedule = Th08TimeScaleSchedule.root_observation(
            quarter,
            source_frame=123,
        )
        self.assertEqual(schedule.coverage, SCALE_COVERAGE_ROOT_ONLY)
        self.assertEqual(schedule.require_player_horizon(1), (quarter,))
        with self.assertRaises(ValueError):
            schedule.require_laser_horizon(1)
        with self.assertRaises(ValueError):
            schedule.require_complete_horizon(1)

    def test_complete_schedule_keeps_phase_specific_transition(self) -> None:
        unit = TH08_UNIT_TIME_SCALE_BITS
        quarter = float32_bits(0.25)
        schedule = Th08TimeScaleSchedule.explicit(
            root_scale_bits=unit,
            player_scale_bits=(unit, quarter),
            laser_scale_bits=(quarter, quarter),
            complete=True,
            provenance="callback_18_between_player_and_laser",
        )
        self.assertEqual(schedule.coverage, SCALE_COVERAGE_COMPLETE)
        self.assertEqual(schedule.require_player_horizon(2), (unit, quarter))
        self.assertEqual(
            schedule.require_laser_horizon(2),
            (quarter, quarter),
        )

    def test_invalid_scale_fails_closed(self) -> None:
        for value in (-0.25, math.nan, math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    canonical_time_scale_bits(value)
        for bits in (True, -1, 0x1_0000_0000, 0x7F800000, 0x7FC00000):
            with self.subTest(bits=bits):
                with self.assertRaises(ValueError):
                    validate_time_scale_bits(bits)

    def test_schedule_identity_requires_immutable_strict_fields(self) -> None:
        with self.assertRaises(ValueError):
            Th08TimeScaleSchedule.explicit(
                root_scale_bits=TH08_UNIT_TIME_SCALE_BITS,
                player_scale_bits=[TH08_UNIT_TIME_SCALE_BITS],  # type: ignore[arg-type]
                laser_scale_bits=(TH08_UNIT_TIME_SCALE_BITS,),
                complete=True,
                provenance="mutable_player_schedule",
            )
        with self.assertRaises(ValueError):
            Th08TimeScaleSchedule.root_observation(
                TH08_UNIT_TIME_SCALE_BITS,
                source_frame=True,
            )


class ScaledMovementTests(unittest.TestCase):
    def test_finalb_quarter_scale_moves_four_units_in_four_frames(self) -> None:
        quarter = float32_bits(0.25)
        steps = project_route2_movement_schedule(
            x=192.0,
            y=400.0,
            input_masks=(0x80,) * 4,
            player_scale_bits=(quarter,) * 4,
            bounds=_PHYSICAL_BOUNDS,
        )
        self.assertEqual(steps[-1].x, 196.0)
        self.assertEqual(steps[-1].y, 400.0)

    def test_product_matches_independent_raw_oracle(self) -> None:
        scales = tuple(
            float32_bits(value)
            for value in (1.0, 0.0, 0.25, 1.0 / 3.0)
        )
        masks = (0x10, 0x90, 0x94, 0x64)
        steps = project_route2_movement_schedule(
            x=200.0,
            y=300.0,
            input_masks=masks,
            player_scale_bits=scales,
            bounds=_PHYSICAL_BOUNDS,
        )
        x_bits = float32_bits(200.0)
        y_bits = float32_bits(300.0)
        for step, mask, scale_bits in zip(steps, masks, scales):
            oracle = oracle_step_route2_movement_raw(
                x_bits=x_bits,
                y_bits=y_bits,
                input_mask=mask,
                axis_scale_x_bits=float32_bits(1.0),
                axis_scale_y_bits=float32_bits(1.0),
                time_scale_bits=scale_bits,
                left_bits=float32_bits(8.0),
                top_bits=float32_bits(16.0),
                right_bits=float32_bits(376.0),
                bottom_bits=float32_bits(432.0),
            )
            self.assertEqual(
                tuple(
                    float32_bits(value)
                    for value in (
                        step.x,
                        step.y,
                        step.velocity_x,
                        step.velocity_y,
                    )
                ),
                oracle,
            )
            x_bits, y_bits = oracle[:2]


class ScaledLaserTests(unittest.TestCase):
    def _laser(self):
        return spawn_laser_state(
            origin_x=0.0,
            origin_y=0.0,
            angle=0.0,
            speed=3.25,
            tail_distance=0.0,
            head_distance=10.125,
            maximum_length=12.5,
            width=16.0,
            warmup_frames=3,
            active_frames=4,
            fade_frames=3,
            collision_enable_frame=1,
            collision_disable_frame=2,
        )

    def test_projection_requires_complete_explicit_schedule(self) -> None:
        with self.assertRaises(ValueError):
            laser_collision_geometry_frames(
                self._laser(),
                frame_count=2,
                time_scale_schedule_bits=(float32_bits(0.25),),
            )

    def test_empty_pool_still_rejects_invalid_scale_identity(self) -> None:
        with self.assertRaises(ValueError):
            step_laser_pool(
                LaserPoolState(),
                player_x=0.0,
                player_y=0.0,
                player_half_width=2.0,
                player_half_height=2.0,
                player_state=PLAYER_NORMAL,
                time_scale_bits=0x7FC00000,
            )

    def test_stop_resume_matches_independent_raw_oracle(self) -> None:
        product = self._laser()
        raw = RawLaserState(
            tail_bits=float32_bits(product.tail_distance),
            head_bits=float32_bits(product.head_distance),
            maximum_length_bits=float32_bits(product.maximum_length),
            width_bits=float32_bits(product.width),
            current_width_bits=float32_bits(product.current_width),
            speed_bits=float32_bits(product.speed),
            warmup_frames=product.warmup_frames,
            active_frames=product.active_frames,
            fade_frames=product.fade_frames,
            collision_enable_frame=product.collision_enable_frame,
            collision_disable_frame=product.collision_disable_frame,
            flags=product.flags,
            phase=int(product.phase),
            timer=product.timer,
            timer_fraction_bits=float32_bits(product.timer_fraction),
            active=product.active,
        )
        for scale in (0.0, 0.5, 0.5, 1.0, 0.25):
            scale_bits = float32_bits(scale)
            product_result = step_laser(
                product,
                time_scale_bits=scale_bits,
            )
            oracle_result = oracle_step_laser_raw(
                raw,
                time_scale_bits=scale_bits,
            )
            self.assertEqual(
                (
                    float32_bits(product_result.laser.tail_distance),
                    float32_bits(product_result.laser.head_distance),
                    float32_bits(product_result.laser.current_width),
                    int(product_result.laser.phase),
                    product_result.laser.timer,
                    float32_bits(product_result.laser.timer_fraction),
                    product_result.laser.active,
                    tuple(
                        (int(check.phase), check.graze_enabled)
                        for check in product_result.checks
                    ),
                ),
                (
                    oracle_result.state.tail_bits,
                    oracle_result.state.head_bits,
                    oracle_result.state.current_width_bits,
                    oracle_result.state.phase,
                    oracle_result.state.timer,
                    oracle_result.state.timer_fraction_bits,
                    oracle_result.state.active,
                    oracle_result.checks,
                ),
            )
            product = product_result.laser
            raw = oracle_result.state
        self.assertIn(product.phase, tuple(LaserPhase))


if __name__ == "__main__":
    unittest.main()
