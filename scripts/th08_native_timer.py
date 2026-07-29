"""Bit-exact supported-domain model of the shipped TH08 timer transition."""

from __future__ import annotations

import math
from dataclasses import dataclass

from th08_ecl_vm_state import float32_bits, float32_from_bits


TH08_NATIVE_TIMER_SEMANTICS_VERSION = "th08-native-timer-components-v1-00447421"
TH08_TIMER_FAST_SCALE_THRESHOLD_BITS = 0x3F7D70A4
TH08_TIMER_FAST_SCALE_THRESHOLD = float32_from_bits(
    TH08_TIMER_FAST_SCALE_THRESHOLD_BITS
)


def _signed_int32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


def _finite_float32_from_bits(bits: int, *, field: str) -> float:
    if not 0 <= bits <= 0xFFFFFFFF:
        raise ValueError(f"{field} bits must be an unsigned dword")
    value = float32_from_bits(bits)
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float32")
    return value


@dataclass(frozen=True)
class Th08TimerState:
    """Control-relevant current components of one native ``Th08Timer``.

    The shipped object also stores the previous integer at +0x00. The narrow
    ECL shadow never reads that field, so it is deliberately excluded instead
    of being guessed or silently merged into current elapsed time.
    """

    elapsed: int
    fraction_bits: int

    def __post_init__(self) -> None:
        if not -(1 << 31) <= self.elapsed < (1 << 31):
            raise ValueError("timer elapsed must be a signed int32")
        _finite_float32_from_bits(
            self.fraction_bits,
            field="timer fraction",
        )

    @classmethod
    def from_float(cls, elapsed: int, fraction: float) -> Th08TimerState:
        return cls(elapsed, float32_bits(fraction))

    @property
    def fraction(self) -> float:
        return float32_from_bits(self.fraction_bits)

    @property
    def diagnostic_value(self) -> float:
        """Human-readable sum; never use this value as state identity."""

        return self.elapsed + self.fraction

    @property
    def serialized_identity(self) -> tuple[str, int, int]:
        return (
            TH08_NATIVE_TIMER_SEMANTICS_VERSION,
            self.elapsed,
            self.fraction_bits,
        )

    def with_elapsed_preserving_fraction(self, elapsed: int) -> Th08TimerState:
        """Opcode 0x04/taken 0x05 behavior at 0x004186F1."""

        return Th08TimerState(_signed_int32(elapsed), self.fraction_bits)


def reset_timer_elapsed(elapsed: int) -> Th08TimerState:
    """Component result of the native setter at 0x00406610.

    The full native setter additionally writes previous=-999. Callers whose
    behavior depends on previous remain outside this component-only model.
    """

    return Th08TimerState(_signed_int32(elapsed), 0)


def advance_scaled_timer(
    state: Th08TimerState,
    *,
    time_scale_bits: int,
) -> Th08TimerState:
    """Apply one finite-input transition from 0x00447421.

    The slow path explicitly rounds the addition to float32 before testing
    carry, exactly matching the intervening ``fstp dword``. The native helper
    performs at most one carry and all elapsed increments are dword wraps.
    Non-finite inputs are excluded from exactness authority.
    """

    time_scale = _finite_float32_from_bits(
        time_scale_bits,
        field="gameplay time scale",
    )
    if time_scale > TH08_TIMER_FAST_SCALE_THRESHOLD:
        return Th08TimerState(
            _signed_int32(state.elapsed + 1),
            state.fraction_bits,
        )

    try:
        rounded_fraction_bits = float32_bits(state.fraction + time_scale)
    except OverflowError as exc:
        raise ValueError("advanced timer fraction is outside float32") from exc
    rounded_fraction = _finite_float32_from_bits(
        rounded_fraction_bits,
        field="advanced timer fraction",
    )
    elapsed = state.elapsed
    if rounded_fraction >= 1.0:
        elapsed = _signed_int32(elapsed + 1)
        rounded_fraction_bits = float32_bits(rounded_fraction - 1.0)
    return Th08TimerState(elapsed, rounded_fraction_bits)


def advance_until_elapsed(
    state: Th08TimerState,
    *,
    target_elapsed: int,
    time_scale_bits: int,
    max_physical_frames: int,
) -> tuple[Th08TimerState, int, bool]:
    """Advance until native integer-timer equality or a frame budget expires.

    ECL scheduling at 0x004185AF compares only the signed integer component
    for equality. A timer already past ``target_elapsed`` is therefore not
    eligible and must keep advancing; treating the condition as ``>=`` is an
    optimistic semantic change.
    """

    if not -(1 << 31) <= target_elapsed < (1 << 31):
        raise ValueError("target elapsed must be a signed int32")
    if max_physical_frames < 0:
        raise ValueError("timer frame budget cannot be negative")
    _finite_float32_from_bits(
        time_scale_bits,
        field="gameplay time scale",
    )

    current = state
    frames = 0
    while current.elapsed != target_elapsed and frames < max_physical_frames:
        current = advance_scaled_timer(
            current,
            time_scale_bits=time_scale_bits,
        )
        frames += 1
    return current, frames, current.elapsed == target_elapsed


__all__ = [
    "TH08_NATIVE_TIMER_SEMANTICS_VERSION",
    "TH08_TIMER_FAST_SCALE_THRESHOLD",
    "TH08_TIMER_FAST_SCALE_THRESHOLD_BITS",
    "Th08TimerState",
    "advance_scaled_timer",
    "advance_until_elapsed",
    "reset_timer_elapsed",
]
