"""Structurally independent raw oracle for the TH08 timer transition.

This module intentionally does not import the product timer representation,
float helpers, or transition. State is carried as two plain integers and every
binary32 store is performed locally through ``struct``.
"""

from __future__ import annotations

import math
import struct


ORACLE_SEMANTICS_VERSION = "th08-ecl-timer-raw-oracle-v2-exact-integer-rounding"
_FAST_THRESHOLD_BITS = 0x3F7D70A4


def _float_from_bits(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def _signed_dword(value: int) -> int:
    raw = value & 0xFFFFFFFF
    return raw - (1 << 32) if raw & 0x80000000 else raw


def _finite_components(bits: int) -> tuple[bool, int, int]:
    """Return sign, integer significand, and base-two exponent."""

    sign = bool(bits & 0x80000000)
    exponent_field = (bits >> 23) & 0xFF
    fraction = bits & 0x007FFFFF
    if exponent_field == 0xFF:
        raise ValueError("oracle supports finite float32 inputs only")
    if exponent_field == 0:
        return sign, fraction, -149
    return sign, (1 << 23) | fraction, exponent_field - 127 - 23


def _round_divide_power_of_two(value: int, shift: int) -> int:
    """Round a nonnegative integer division to nearest, ties to even."""

    if shift <= 0:
        return value << -shift
    quotient, remainder = divmod(value, 1 << shift)
    half = 1 << (shift - 1)
    if remainder > half or (remainder == half and quotient & 1):
        quotient += 1
    return quotient


def _encode_exact_binary32(
    signed_significand: int,
    exponent: int,
    *,
    negative_exact_zero: bool,
) -> int:
    """Round ``signed_significand * 2**exponent`` to binary32."""

    if signed_significand == 0:
        return 0x80000000 if negative_exact_zero else 0

    sign_bit = 0x80000000 if signed_significand < 0 else 0
    magnitude = abs(signed_significand)
    leading_exponent = magnitude.bit_length() - 1 + exponent

    if leading_exponent >= -126:
        precision_exponent = leading_exponent - 23
        significand = _round_divide_power_of_two(
            magnitude,
            precision_exponent - exponent,
        )
        if significand == 1 << 24:
            significand >>= 1
            leading_exponent += 1
        if leading_exponent > 127:
            raise ValueError("oracle transition rounded outside finite float32")
        exponent_field = leading_exponent + 127
        return sign_bit | (exponent_field << 23) | (significand - (1 << 23))

    subnormal = _round_divide_power_of_two(
        magnitude,
        -149 - exponent,
    )
    if subnormal == 0:
        return sign_bit
    if subnormal >= 1 << 23:
        return sign_bit | (1 << 23)
    return sign_bit | subnormal


def _add_binary32_bits(lhs_bits: int, rhs_bits: int) -> int:
    lhs_sign, lhs_significand, lhs_exponent = _finite_components(lhs_bits)
    rhs_sign, rhs_significand, rhs_exponent = _finite_components(rhs_bits)
    common_exponent = min(lhs_exponent, rhs_exponent)
    lhs_integer = lhs_significand << (lhs_exponent - common_exponent)
    rhs_integer = rhs_significand << (rhs_exponent - common_exponent)
    if lhs_sign:
        lhs_integer = -lhs_integer
    if rhs_sign:
        rhs_integer = -rhs_integer
    return _encode_exact_binary32(
        lhs_integer + rhs_integer,
        common_exponent,
        negative_exact_zero=(
            lhs_sign and rhs_sign and lhs_significand == 0 and rhs_significand == 0
        ),
    )


def oracle_advance_timer_raw(
    elapsed: int,
    fraction_bits: int,
    time_scale_bits: int,
) -> tuple[int, int]:
    """Return one raw finite-input transition without product dependencies."""

    if not -(1 << 31) <= elapsed < (1 << 31):
        raise ValueError("oracle elapsed is outside signed int32")
    if not 0 <= fraction_bits <= 0xFFFFFFFF:
        raise ValueError("oracle fraction bits are outside uint32")
    if not 0 <= time_scale_bits <= 0xFFFFFFFF:
        raise ValueError("oracle scale bits are outside uint32")
    fraction = _float_from_bits(fraction_bits)
    scale = _float_from_bits(time_scale_bits)
    if not math.isfinite(fraction) or not math.isfinite(scale):
        raise ValueError("oracle supports finite float32 inputs only")

    if scale > _float_from_bits(_FAST_THRESHOLD_BITS):
        return _signed_dword(elapsed + 1), fraction_bits

    stored_bits = _add_binary32_bits(fraction_bits, time_scale_bits)
    stored = _float_from_bits(stored_bits)
    if stored >= 1.0:
        return (
            _signed_dword(elapsed + 1),
            _add_binary32_bits(stored_bits, 0xBF800000),
        )
    return elapsed, stored_bits


def oracle_preserve_fraction_on_branch(
    target_elapsed: int,
    fraction_bits: int,
) -> tuple[int, int]:
    if not 0 <= fraction_bits <= 0xFFFFFFFF:
        raise ValueError("oracle fraction bits are outside uint32")
    if not math.isfinite(_float_from_bits(fraction_bits)):
        raise ValueError("oracle supports finite float32 fractions only")
    return _signed_dword(target_elapsed), fraction_bits


def oracle_reset_timer_components(target_elapsed: int) -> tuple[int, int]:
    return _signed_dword(target_elapsed), 0


__all__ = [
    "ORACLE_SEMANTICS_VERSION",
    "oracle_advance_timer_raw",
    "oracle_preserve_fraction_on_branch",
    "oracle_reset_timer_components",
]
