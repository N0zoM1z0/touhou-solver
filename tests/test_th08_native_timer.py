#!/usr/bin/env python3
"""Differential tests for the revalidated TH08 native timer primitive."""

from __future__ import annotations

import math
import random
import unittest

from analysis.th08_ecl_timer_raw_oracle import (
    oracle_advance_timer_raw,
    oracle_preserve_fraction_on_branch,
    oracle_reset_timer_components,
)
from th08_ecl_vm_state import float32_bits, float32_from_bits
from th08_native_timer import (
    TH08_NATIVE_TIMER_SEMANTICS_VERSION,
    TH08_TIMER_FAST_SCALE_THRESHOLD_BITS,
    Th08TimerState,
    advance_scaled_timer,
    advance_until_elapsed,
    reset_timer_elapsed,
)


class Th08NativeTimerTests(unittest.TestCase):
    def _assert_transition(
        self,
        *,
        elapsed: int,
        fraction: float,
        scale: float,
        expected_elapsed: int,
        expected_fraction: float,
    ) -> None:
        fraction_bits = float32_bits(fraction)
        scale_bits = float32_bits(scale)
        product = advance_scaled_timer(
            Th08TimerState(elapsed, fraction_bits),
            time_scale_bits=scale_bits,
        )
        oracle = oracle_advance_timer_raw(
            elapsed,
            fraction_bits,
            scale_bits,
        )
        self.assertEqual(
            (product.elapsed, product.fraction_bits),
            oracle,
        )
        self.assertEqual(product.elapsed, expected_elapsed)
        self.assertEqual(
            product.fraction_bits,
            float32_bits(expected_fraction),
        )

    def test_nonunit_scale_rounds_before_carry(self) -> None:
        self._assert_transition(
            elapsed=10,
            fraction=0.75,
            scale=0.5,
            expected_elapsed=11,
            expected_fraction=0.25,
        )
        self._assert_transition(
            elapsed=-10,
            fraction=0.125,
            scale=0.25,
            expected_elapsed=-10,
            expected_fraction=0.375,
        )

    def test_fast_path_preserves_fraction(self) -> None:
        self._assert_transition(
            elapsed=10,
            fraction=0.75,
            scale=1.0,
            expected_elapsed=11,
            expected_fraction=0.75,
        )
        self._assert_transition(
            elapsed=10,
            fraction=-0.25,
            scale=2.0,
            expected_elapsed=11,
            expected_fraction=-0.25,
        )

    def test_threshold_bit_and_next_float_take_different_paths(self) -> None:
        fraction_bits = float32_bits(0.125)
        at_threshold = advance_scaled_timer(
            Th08TimerState(7, fraction_bits),
            time_scale_bits=TH08_TIMER_FAST_SCALE_THRESHOLD_BITS,
        )
        above_threshold = advance_scaled_timer(
            Th08TimerState(7, fraction_bits),
            time_scale_bits=TH08_TIMER_FAST_SCALE_THRESHOLD_BITS + 1,
        )
        self.assertEqual(at_threshold.elapsed, 8)
        self.assertNotEqual(at_threshold.fraction_bits, fraction_bits)
        self.assertEqual(above_threshold.elapsed, 8)
        self.assertEqual(above_threshold.fraction_bits, fraction_bits)

    def test_negative_scale_and_signed_wrap_are_explicit(self) -> None:
        self._assert_transition(
            elapsed=4,
            fraction=0.75,
            scale=-0.5,
            expected_elapsed=4,
            expected_fraction=0.25,
        )
        self._assert_transition(
            elapsed=(1 << 31) - 1,
            fraction=0.5,
            scale=1.0,
            expected_elapsed=-(1 << 31),
            expected_fraction=0.5,
        )

    def test_branch_preserves_fraction_and_reset_zeros_it(self) -> None:
        state = Th08TimerState(10, float32_bits(0.75))
        product_branch = state.with_elapsed_preserving_fraction(-4)
        oracle_branch = oracle_preserve_fraction_on_branch(
            -4,
            state.fraction_bits,
        )
        self.assertEqual(
            (product_branch.elapsed, product_branch.fraction_bits),
            oracle_branch,
        )
        product_reset = reset_timer_elapsed(0xFFFFFFFF)
        oracle_reset = oracle_reset_timer_components(0xFFFFFFFF)
        self.assertEqual(
            (product_reset.elapsed, product_reset.fraction_bits),
            oracle_reset,
        )
        self.assertEqual(oracle_reset, (-1, 0))

    def test_component_identity_does_not_alias_equal_sums(self) -> None:
        first = Th08TimerState(10, float32_bits(0.75))
        second = Th08TimerState(11, float32_bits(-0.25))
        self.assertEqual(first.diagnostic_value, second.diagnostic_value)
        self.assertNotEqual(
            first.serialized_identity,
            second.serialized_identity,
        )
        self.assertEqual(
            first.serialized_identity[0],
            TH08_NATIVE_TIMER_SEMANTICS_VERSION,
        )

    def test_wait_uses_integer_equality_and_preserves_component_state(self) -> None:
        state, frames, reached = advance_until_elapsed(
            Th08TimerState(3, float32_bits(0.5)),
            target_elapsed=4,
            time_scale_bits=float32_bits(0.75),
            max_physical_frames=4,
        )
        self.assertTrue(reached)
        self.assertEqual(frames, 1)
        self.assertEqual(
            (state.elapsed, state.fraction_bits),
            (4, float32_bits(0.25)),
        )

        past, frames, reached = advance_until_elapsed(
            Th08TimerState(5, 0),
            target_elapsed=4,
            time_scale_bits=float32_bits(1.0),
            max_physical_frames=3,
        )
        self.assertFalse(reached)
        self.assertEqual(frames, 3)
        self.assertEqual(past.elapsed, 8)

    def test_nonfinite_inputs_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            Th08TimerState(0, float32_bits(math.inf))
        with self.assertRaises(ValueError):
            advance_scaled_timer(
                Th08TimerState(0, 0),
                time_scale_bits=float32_bits(math.nan),
            )
        with self.assertRaises(ValueError):
            advance_scaled_timer(
                Th08TimerState(0, 0xFF7FFFFF),
                time_scale_bits=0xFF7FFFFF,
            )
        self.assertTrue(
            math.isfinite(float32_from_bits(TH08_TIMER_FAST_SCALE_THRESHOLD_BITS))
        )

    def test_exact_integer_oracle_matches_product_over_raw_bit_edges(self) -> None:
        generator = random.Random(0x447421)
        checked = 0
        while checked < 4096:
            fraction_bits = generator.getrandbits(32)
            scale_bits = generator.getrandbits(32)
            if fraction_bits >> 23 & 0xFF == 0xFF or scale_bits >> 23 & 0xFF == 0xFF:
                continue
            elapsed = generator.randint(-(1 << 31), (1 << 31) - 1)
            state = Th08TimerState(elapsed, fraction_bits)
            try:
                product = advance_scaled_timer(
                    state,
                    time_scale_bits=scale_bits,
                )
            except ValueError:
                with self.assertRaises(ValueError):
                    oracle_advance_timer_raw(
                        elapsed,
                        fraction_bits,
                        scale_bits,
                    )
            else:
                self.assertEqual(
                    (product.elapsed, product.fraction_bits),
                    oracle_advance_timer_raw(
                        elapsed,
                        fraction_bits,
                        scale_bits,
                    ),
                )
            checked += 1


if __name__ == "__main__":
    unittest.main()
