#!/usr/bin/env python3
"""Exact TH08 gameplay RNG recovered from th08.exe at 0x0043ECC0."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Th08Rng:
    """The game's shared 16-bit RNG state and its consumption counter."""

    state: int
    calls: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.state <= 0xFFFF:
            raise ValueError("TH08 RNG seed must fit in 16 bits")
        if self.calls < 0:
            raise ValueError("TH08 RNG call count cannot be negative")

    def next_u16(self) -> int:
        mixed = ((self.state ^ 0x9630) - 0x6553) & 0xFFFF
        self.state = ((mixed << 2) + ((mixed & 0xC000) >> 14)) & 0xFFFF
        self.calls += 1
        return self.state

    def next_u32(self) -> int:
        return (self.next_u16() << 16) | self.next_u16()

    def next_unit(self) -> float:
        """Match 0x0043ED50: a value in [0, 1)."""

        return self.next_u32() / 4294967296.0

    def next_signed_unit(self) -> float:
        """Match 0x0043ED80: a value in [-1, 1)."""

        return self.next_u32() / 2147483648.0 - 1.0

    def next_scaled(self, span: float) -> float:
        """Match 0x0040D390: a uniform value in [0, span)."""

        return self.next_unit() * span

    def next_mod(self, modulus: int) -> int:
        """Match 0x00406EF0, including its zero-modulus result."""

        return self.next_u32() % modulus if modulus else 0
