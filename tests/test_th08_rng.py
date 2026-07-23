#!/usr/bin/env python3
"""Regression tests for the recovered TH08 RNG."""

from __future__ import annotations

import unittest

from th08_rng import Th08Rng


class RngTests(unittest.TestCase):
    def test_seed_c0a4_vector(self) -> None:
        rng = Th08Rng(0xC0A4)
        self.assertEqual(
            [rng.next_u16() for _ in range(8)],
            [0xC507, 0xB793, 0xF142, 0x087C, 0xE3E4, 0x4204, 0xBB85, 0x218B],
        )
        self.assertEqual(rng.calls, 8)

    def test_u32_consumes_two_states(self) -> None:
        rng = Th08Rng(0xFFFF)
        self.assertEqual(rng.next_u32(), 0x11F089B4)
        self.assertEqual(rng.state, 0x89B4)
        self.assertEqual(rng.calls, 2)

    def test_transition_is_one_full_16_bit_cycle(self) -> None:
        rng = Th08Rng(0xC0A4)
        seen = {rng.state}
        for _ in range(0xFFFF):
            self.assertNotIn(rng.next_u16(), seen)
            seen.add(rng.state)
        self.assertEqual(rng.next_u16(), 0xC0A4)
        self.assertEqual(len(seen), 0x10000)

    def test_modulus_zero_does_not_consume_rng(self) -> None:
        rng = Th08Rng(0x1234)
        self.assertEqual(rng.next_mod(0), 0)
        self.assertEqual((rng.state, rng.calls), (0x1234, 0))


if __name__ == "__main__":
    unittest.main()
