"""Native float32 timer-step reproduction for optional frame offsets."""

from __future__ import annotations

from th08_ecl_vm_state import float32_bits, float32_from_bits

from .constants import NATIVE_DIRECT_TIMER_THRESHOLD


def float32(value: float) -> float:
    return float32_from_bits(float32_bits(value))


def physical_wait(
    *,
    elapsed: int,
    target: int,
    fraction: float,
    time_scale: float,
    used_steps: int,
    maximum_steps: int,
) -> tuple[int, float, int] | None:
    while elapsed < target:
        if used_steps >= maximum_steps:
            return None
        if time_scale > NATIVE_DIRECT_TIMER_THRESHOLD:
            elapsed += 1
        else:
            fraction = float32(fraction + time_scale)
            if fraction >= 1.0:
                elapsed += 1
                fraction = float32(fraction - 1.0)
        used_steps += 1
    return elapsed, fraction, used_steps
