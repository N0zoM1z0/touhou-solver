#!/usr/bin/env python3
"""Reusable numeric-store policies for deterministic simulation kernels."""

from __future__ import annotations

import struct
from collections.abc import Callable


StoreQuantizer = Callable[[float], float]


def identity_store(value: float) -> float:
    """Keep host precision when the target does not require store rounding."""

    return float(value)


def binary32_store(value: float) -> float:
    """Round once as an IEEE-754 binary32 memory store/load cycle."""

    return struct.unpack("<f", struct.pack("<f", value))[0]
