"""Structurally independent raw-bit oracle for TH08 SEM-SCALE.

This module deliberately does not import the product movement, laser, numeric
store, or scale-schedule implementations.  Finite float32 operations are
performed as exact rational arithmetic followed by local
round-to-nearest-even encoding.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, replace
from fractions import Fraction

from analysis.th08_ecl_timer_raw_oracle import oracle_advance_timer_raw


ORACLE_SEMANTICS_VERSION = "th08-scale-transition-raw-oracle-v1"

_UNIT_BITS = 0x3F800000
_ZERO_BITS = 0
_ONE_POINT_TWO_BITS = 0x3F99999A
_TAIL_CULL_BITS = 0x44200000

_FOCUSED_CARDINAL_BITS = 0x40133333
_FOCUSED_DIAGONAL_BITS = 0x3FD02C18
_UNFOCUSED_CARDINAL_BITS = 0x40800000
_UNFOCUSED_DIAGONAL_BITS = 0x403504F3

_INPUT_FOCUS = 0x04
_INPUT_UP = 0x10
_INPUT_DOWN = 0x20
_INPUT_LEFT = 0x40
_INPUT_RIGHT = 0x80


def _float_from_bits(bits: int) -> float:
    if not 0 <= bits <= 0xFFFFFFFF:
        raise ValueError("oracle float32 bits must be uint32")
    value = struct.unpack("<f", struct.pack("<I", bits))[0]
    if not math.isfinite(value):
        raise ValueError("oracle supports finite float32 inputs only")
    return value


def _fraction_from_bits(bits: int) -> Fraction:
    _float_from_bits(bits)
    sign = -1 if bits & 0x80000000 else 1
    exponent_field = (bits >> 23) & 0xFF
    fraction_field = bits & 0x007FFFFF
    if exponent_field == 0:
        significand = fraction_field
        exponent = -149
    else:
        significand = (1 << 23) | fraction_field
        exponent = exponent_field - 127 - 23
    value = Fraction(sign * significand, 1)
    return value * (1 << exponent) if exponent >= 0 else value / (1 << -exponent)


def _round_ratio_nearest_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient & 1):
        quotient += 1
    return quotient


def _floor_binary_exponent(value: Fraction) -> int:
    numerator = value.numerator
    denominator = value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        if numerator < denominator << exponent:
            exponent -= 1
    elif numerator << -exponent < denominator:
        exponent -= 1
    return exponent


def _fraction_to_bits(
    value: Fraction,
    *,
    negative_zero: bool = False,
) -> int:
    if value == 0:
        return 0x80000000 if negative_zero else 0
    sign_bit = 0x80000000 if value < 0 else 0
    magnitude = abs(value)
    exponent = _floor_binary_exponent(magnitude)
    if exponent > 127:
        raise ValueError("oracle result is outside finite float32")

    if exponent >= -126:
        shift = 23 - exponent
        if shift >= 0:
            numerator = magnitude.numerator << shift
            denominator = magnitude.denominator
        else:
            numerator = magnitude.numerator
            denominator = magnitude.denominator << -shift
        significand = _round_ratio_nearest_even(numerator, denominator)
        if significand == 1 << 24:
            significand >>= 1
            exponent += 1
        if exponent > 127:
            raise ValueError("oracle result rounded outside finite float32")
        return sign_bit | ((exponent + 127) << 23) | (
            significand - (1 << 23)
        )

    subnormal = _round_ratio_nearest_even(
        magnitude.numerator << 149,
        magnitude.denominator,
    )
    if subnormal == 0:
        return sign_bit
    if subnormal >= 1 << 23:
        return sign_bit | (1 << 23)
    return sign_bit | subnormal


def _add_bits(lhs_bits: int, rhs_bits: int) -> int:
    return _fraction_to_bits(
        _fraction_from_bits(lhs_bits) + _fraction_from_bits(rhs_bits),
        negative_zero=(
            bool(lhs_bits & 0x80000000)
            and bool(rhs_bits & 0x80000000)
            and not (lhs_bits & 0x7FFFFFFF)
            and not (rhs_bits & 0x7FFFFFFF)
        ),
    )


def _multiply_bits(lhs_bits: int, rhs_bits: int) -> int:
    return _fraction_to_bits(
        _fraction_from_bits(lhs_bits) * _fraction_from_bits(rhs_bits),
        negative_zero=bool((lhs_bits ^ rhs_bits) & 0x80000000),
    )


def _multiply_add_bits(
    lhs_bits: int,
    rhs_bits: int,
    addend_bits: int,
) -> int:
    """Round the physical-domain x87 multiply/add at its final dword store."""

    return _fraction_to_bits(
        _fraction_from_bits(lhs_bits) * _fraction_from_bits(rhs_bits)
        + _fraction_from_bits(addend_bits)
    )


def _divide_fraction_to_bits(numerator: Fraction, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("oracle integer divisor must be positive")
    return _fraction_to_bits(numerator / denominator)


def _negate_bits(bits: int) -> int:
    return bits ^ 0x80000000


def _decode_direction(input_mask: int) -> tuple[int, int]:
    mask = input_mask & 0xFFFF
    if mask & (_INPUT_UP | _INPUT_LEFT) == _INPUT_UP | _INPUT_LEFT:
        return -1, -1
    if mask & (_INPUT_DOWN | _INPUT_LEFT) == _INPUT_DOWN | _INPUT_LEFT:
        return -1, 1
    if mask & (_INPUT_UP | _INPUT_RIGHT) == _INPUT_UP | _INPUT_RIGHT:
        return 1, -1
    if mask & (_INPUT_DOWN | _INPUT_RIGHT) == _INPUT_DOWN | _INPUT_RIGHT:
        return 1, 1
    if mask & _INPUT_DOWN:
        return 0, 1
    if mask & _INPUT_UP:
        return 0, -1
    if mask & _INPUT_LEFT:
        return -1, 0
    if mask & _INPUT_RIGHT:
        return 1, 0
    return 0, 0


def oracle_step_route2_movement_raw(
    *,
    x_bits: int,
    y_bits: int,
    input_mask: int,
    axis_scale_x_bits: int,
    axis_scale_y_bits: int,
    time_scale_bits: int,
    left_bits: int,
    top_bits: int,
    right_bits: int,
    bottom_bits: int,
) -> tuple[int, int, int, int]:
    """Return raw ``x, y, delta_x, delta_y`` after one player update."""

    values = tuple(
        _float_from_bits(bits)
        for bits in (
            x_bits,
            y_bits,
            axis_scale_x_bits,
            axis_scale_y_bits,
            time_scale_bits,
            left_bits,
            top_bits,
            right_bits,
            bottom_bits,
        )
    )
    if min(values[2:5]) < 0.0:
        raise ValueError("oracle movement scales must be nonnegative")
    if values[5] > values[7] or values[6] > values[8]:
        raise ValueError("oracle movement bounds must be ordered")

    axis_x, axis_y = _decode_direction(input_mask)
    diagonal = axis_x != 0 and axis_y != 0
    focused = bool(input_mask & _INPUT_FOCUS)
    speed_bits = (
        _FOCUSED_DIAGONAL_BITS
        if focused and diagonal
        else (
            _FOCUSED_CARDINAL_BITS
            if focused
            else (
                _UNFOCUSED_DIAGONAL_BITS
                if diagonal
                else _UNFOCUSED_CARDINAL_BITS
            )
        )
    )

    def signed_speed(axis: int) -> int:
        if axis == 0:
            return _ZERO_BITS
        return speed_bits if axis > 0 else _negate_bits(speed_bits)

    scaled_x_bits = _multiply_bits(
        signed_speed(axis_x),
        axis_scale_x_bits,
    )
    scaled_y_bits = _multiply_bits(
        signed_speed(axis_y),
        axis_scale_y_bits,
    )
    velocity_x_bits = _multiply_bits(scaled_x_bits, time_scale_bits)
    velocity_y_bits = _multiply_bits(scaled_y_bits, time_scale_bits)
    raw_x_bits = _add_bits(x_bits, velocity_x_bits)
    raw_y_bits = _add_bits(y_bits, velocity_y_bits)
    raw_x = _float_from_bits(raw_x_bits)
    raw_y = _float_from_bits(raw_y_bits)
    next_x_bits = (
        left_bits
        if raw_x < values[5]
        else right_bits if raw_x > values[7] else raw_x_bits
    )
    next_y_bits = (
        top_bits
        if raw_y < values[6]
        else bottom_bits if raw_y > values[8] else raw_y_bits
    )
    return next_x_bits, next_y_bits, velocity_x_bits, velocity_y_bits


@dataclass(frozen=True)
class RawLaserState:
    tail_bits: int
    head_bits: int
    maximum_length_bits: int
    width_bits: int
    current_width_bits: int
    speed_bits: int
    warmup_frames: int
    active_frames: int
    fade_frames: int
    collision_enable_frame: int
    collision_disable_frame: int
    flags: int
    phase: int
    timer: int
    timer_fraction_bits: int
    active: bool = True

    def __post_init__(self) -> None:
        for bits in (
            self.tail_bits,
            self.head_bits,
            self.maximum_length_bits,
            self.width_bits,
            self.current_width_bits,
            self.speed_bits,
            self.timer_fraction_bits,
        ):
            _float_from_bits(bits)
        if self.phase not in (0, 1, 2):
            raise ValueError("oracle laser phase must be 0, 1, or 2")


@dataclass(frozen=True)
class RawLaserStep:
    state: RawLaserState
    checks: tuple[tuple[int, bool], ...]


def _advance_raw_laser_timer(
    state: RawLaserState,
    *,
    time_scale_bits: int,
) -> RawLaserState:
    timer, fraction_bits = oracle_advance_timer_raw(
        state.timer,
        state.timer_fraction_bits,
        time_scale_bits,
    )
    return replace(
        state,
        timer=timer,
        timer_fraction_bits=fraction_bits,
    )


def oracle_step_laser_raw(
    state: RawLaserState,
    *,
    time_scale_bits: int,
) -> RawLaserStep:
    """Advance laser motion/lifecycle fields and collision-call order."""

    scale = _float_from_bits(time_scale_bits)
    if scale < 0.0:
        raise ValueError("oracle laser scale must be nonnegative")
    if not state.active:
        return RawLaserStep(state, ())

    head_bits = _multiply_add_bits(
        state.speed_bits,
        time_scale_bits,
        state.head_bits,
    )
    tail_bits = state.tail_bits
    if (
        _float_from_bits(head_bits) - _float_from_bits(tail_bits)
        > _float_from_bits(state.maximum_length_bits)
    ):
        tail_bits = _add_bits(
            head_bits,
            _negate_bits(state.maximum_length_bits),
        )
    if _float_from_bits(tail_bits) < 0.0:
        tail_bits = _ZERO_BITS
    current = replace(
        state,
        head_bits=head_bits,
        tail_bits=tail_bits,
    )
    checks: list[tuple[int, bool]] = []

    if current.phase == 0:
        if not current.flags & 1:
            ramp_frames = min(current.warmup_frames, 30)
            ramp_start = current.warmup_frames - ramp_frames
            if ramp_start >= current.timer:
                current_width_bits = _ONE_POINT_TWO_BITS
            elif current.warmup_frames:
                elapsed = Fraction(current.timer, 1) + _fraction_from_bits(
                    current.timer_fraction_bits
                )
                current_width_bits = _divide_fraction_to_bits(
                    elapsed * _fraction_from_bits(current.width_bits),
                    current.warmup_frames,
                )
            else:
                current_width_bits = current.width_bits
            current = replace(
                current,
                current_width_bits=current_width_bits,
            )
        if current.timer >= current.collision_enable_frame:
            checks.append((0, False))
        if current.timer < current.warmup_frames:
            current = _advance_raw_laser_timer(
                current,
                time_scale_bits=time_scale_bits,
            )
            if (
                _float_from_bits(current.tail_bits)
                >= _float_from_bits(_TAIL_CULL_BITS)
            ):
                current = replace(current, active=False)
            return RawLaserStep(current, tuple(checks))
        current = replace(
            current,
            phase=1,
            timer=0,
            timer_fraction_bits=0,
            current_width_bits=current.width_bits,
        )

    if current.phase == 1:
        checks.append((1, current.timer % 20 == 0))
        if current.timer < current.active_frames:
            current = _advance_raw_laser_timer(
                current,
                time_scale_bits=time_scale_bits,
            )
            if (
                _float_from_bits(current.tail_bits)
                >= _float_from_bits(_TAIL_CULL_BITS)
            ):
                current = replace(current, active=False)
            return RawLaserStep(current, tuple(checks))
        current = replace(
            current,
            phase=2,
            timer=0,
            timer_fraction_bits=0,
        )
        if current.fade_frames == 0:
            return RawLaserStep(
                replace(current, active=False),
                tuple(checks),
            )

    if not current.flags & 1:
        if current.fade_frames > 0:
            elapsed = Fraction(current.timer, 1) + _fraction_from_bits(
                current.timer_fraction_bits
            )
            width = _fraction_from_bits(current.width_bits)
            current_width_bits = _fraction_to_bits(
                width - elapsed * width / current.fade_frames
            )
        else:
            current_width_bits = 0
        if _float_from_bits(current_width_bits) < 0.0:
            current_width_bits = 0
        current = replace(
            current,
            current_width_bits=current_width_bits,
        )
    if current.timer < current.collision_disable_frame:
        checks.append((2, False))
    if current.timer >= current.fade_frames:
        return RawLaserStep(
            replace(current, active=False),
            tuple(checks),
        )
    current = _advance_raw_laser_timer(
        current,
        time_scale_bits=time_scale_bits,
    )
    if (
        _float_from_bits(current.tail_bits)
        >= _float_from_bits(_TAIL_CULL_BITS)
    ):
        current = replace(current, active=False)
    return RawLaserStep(current, tuple(checks))


__all__ = [
    "ORACLE_SEMANTICS_VERSION",
    "RawLaserState",
    "RawLaserStep",
    "oracle_step_laser_raw",
    "oracle_step_route2_movement_raw",
]
