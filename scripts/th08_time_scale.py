"""Immutable TH08 player/laser global time-scale schedules.

The shipped player update runs before enemy ECL callbacks, while the laser
manager runs after them.  A callback can therefore make the two consumers see
different values in one physical update.  This module keeps those phase
observations separate and never turns a root observation into an unbounded
constant schedule.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from th08_ecl_vm_state import float32_bits, float32_from_bits


TH08_GLOBAL_TIME_SCALE_ADDRESS = 0x017CE8E0
TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION = (
    "th08-player-laser-phase-scale-v1-0044ba67-00431bc9"
)
TH08_UNIT_TIME_SCALE_BITS = 0x3F800000

SCALE_COVERAGE_COMPLETE = "complete"
SCALE_COVERAGE_PARTIAL = "partial"
SCALE_COVERAGE_ROOT_ONLY = "root_only"
_COVERAGE_VALUES = frozenset(
    {
        SCALE_COVERAGE_COMPLETE,
        SCALE_COVERAGE_PARTIAL,
        SCALE_COVERAGE_ROOT_ONLY,
    }
)


def validate_time_scale_bits(bits: int, *, field: str = "time scale") -> float:
    """Decode one finite, nonnegative native float32 scale."""

    if type(bits) is not int or not 0 <= bits <= 0xFFFFFFFF:
        raise ValueError(f"{field} bits must be an unsigned dword")
    value = float32_from_bits(bits)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{field} must be finite and nonnegative")
    return value


def canonical_time_scale_bits(value: float) -> int:
    """Round a supported host value to the native float32 representation."""

    if not math.isfinite(value) or value < 0.0:
        raise ValueError("time scale must be finite and nonnegative")
    try:
        bits = float32_bits(value)
    except OverflowError as exc:
        raise ValueError("time scale is outside finite float32") from exc
    validate_time_scale_bits(bits)
    return bits


def _validate_horizon(horizon: int, *, field: str) -> None:
    if type(horizon) is not int or horizon < 0:
        raise ValueError(f"{field} horizon must be a nonnegative integer")


@dataclass(frozen=True)
class Th08TimeScaleSchedule:
    """Causal phase-specific scale support for a future physical horizon.

    ``player_scale_bits[t]`` and ``laser_scale_bits[t]`` are the values used
    by future update ``t + 1``.  The tuples are exact prefixes, not values to
    repeat after exhaustion.
    """

    root_scale_bits: int
    player_scale_bits: tuple[int, ...]
    laser_scale_bits: tuple[int, ...]
    coverage: str
    provenance: str
    source_frame: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.player_scale_bits, tuple) or not isinstance(
            self.laser_scale_bits,
            tuple,
        ):
            raise ValueError("time-scale phase schedules must be immutable tuples")
        validate_time_scale_bits(
            self.root_scale_bits,
            field="root time scale",
        )
        for index, bits in enumerate(self.player_scale_bits):
            validate_time_scale_bits(
                bits,
                field=f"player time scale {index}",
            )
        for index, bits in enumerate(self.laser_scale_bits):
            validate_time_scale_bits(
                bits,
                field=f"laser time scale {index}",
            )
        if self.coverage not in _COVERAGE_VALUES:
            raise ValueError("unknown time-scale coverage status")
        if type(self.provenance) is not str or not self.provenance:
            raise ValueError("time-scale schedule provenance cannot be empty")
        if self.source_frame is not None and (
            type(self.source_frame) is not int or self.source_frame < 0
        ):
            raise ValueError(
                "time-scale source frame must be a nonnegative integer"
            )
        if (
            self.player_scale_bits
            and self.player_scale_bits[0] != self.root_scale_bits
        ):
            raise ValueError(
                "first future player scale must equal the post-update root"
            )
        if self.coverage == SCALE_COVERAGE_COMPLETE and (
            len(self.player_scale_bits) != len(self.laser_scale_bits)
        ):
            raise ValueError(
                "complete phase schedule must cover equal player/laser horizons"
            )
        if self.coverage == SCALE_COVERAGE_ROOT_ONLY and (
            self.player_scale_bits != (self.root_scale_bits,)
            or self.laser_scale_bits
        ):
            raise ValueError(
                "root-only coverage proves one player phase and no laser phase"
            )

    @classmethod
    def constant(
        cls,
        scale_bits: int,
        *,
        horizon: int,
        provenance: str = "declared_constant",
        source_frame: int | None = None,
    ) -> Th08TimeScaleSchedule:
        """Construct an explicitly declared complete constant schedule."""

        validate_time_scale_bits(scale_bits)
        _validate_horizon(horizon, field="time-scale")
        values = (scale_bits,) * horizon
        return cls(
            root_scale_bits=scale_bits,
            player_scale_bits=values,
            laser_scale_bits=values,
            coverage=SCALE_COVERAGE_COMPLETE,
            provenance=provenance,
            source_frame=source_frame,
        )

    @classmethod
    def explicit(
        cls,
        *,
        root_scale_bits: int,
        player_scale_bits: tuple[int, ...],
        laser_scale_bits: tuple[int, ...],
        complete: bool,
        provenance: str,
        source_frame: int | None = None,
    ) -> Th08TimeScaleSchedule:
        """Construct a supplied phase schedule without filling missing frames."""

        return cls(
            root_scale_bits=root_scale_bits,
            player_scale_bits=player_scale_bits,
            laser_scale_bits=laser_scale_bits,
            coverage=(
                SCALE_COVERAGE_COMPLETE
                if complete
                else SCALE_COVERAGE_PARTIAL
            ),
            provenance=provenance,
            source_frame=source_frame,
        )

    @classmethod
    def root_observation(
        cls,
        scale_bits: int,
        *,
        source_frame: int,
        provenance: str = "live_post_update_root",
    ) -> Th08TimeScaleSchedule:
        """Retain exactly what one post-update root observation proves.

        The next player update precedes enemy ECL writers and therefore sees
        the root.  The next laser update can see a later callback write, so no
        laser frame is certified by the root alone.
        """

        return cls(
            root_scale_bits=scale_bits,
            player_scale_bits=(scale_bits,),
            laser_scale_bits=(),
            coverage=SCALE_COVERAGE_ROOT_ONLY,
            provenance=provenance,
            source_frame=source_frame,
        )

    @property
    def complete_horizon(self) -> int:
        if self.coverage != SCALE_COVERAGE_COMPLETE:
            return 0
        return len(self.player_scale_bits)

    def require_player_horizon(self, horizon: int) -> tuple[int, ...]:
        _validate_horizon(horizon, field="player scale")
        if len(self.player_scale_bits) < horizon:
            raise ValueError(
                "player time-scale schedule does not cover the requested horizon"
            )
        return self.player_scale_bits[:horizon]

    def require_laser_horizon(self, horizon: int) -> tuple[int, ...]:
        _validate_horizon(horizon, field="laser scale")
        if len(self.laser_scale_bits) < horizon:
            raise ValueError(
                "laser time-scale schedule does not cover the requested horizon"
            )
        return self.laser_scale_bits[:horizon]

    def require_complete_horizon(self, horizon: int) -> None:
        _validate_horizon(horizon, field="time-scale")
        if (
            self.coverage != SCALE_COVERAGE_COMPLETE
            or self.complete_horizon < horizon
        ):
            raise ValueError(
                "phase time-scale schedule is incomplete for the requested horizon"
            )

    @property
    def serialized_identity(self) -> tuple[object, ...]:
        return (
            TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
            self.root_scale_bits,
            self.player_scale_bits,
            self.laser_scale_bits,
            self.coverage,
            self.provenance,
            self.source_frame,
        )


__all__ = [
    "SCALE_COVERAGE_COMPLETE",
    "SCALE_COVERAGE_PARTIAL",
    "SCALE_COVERAGE_ROOT_ONLY",
    "TH08_GLOBAL_TIME_SCALE_ADDRESS",
    "TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION",
    "TH08_UNIT_TIME_SCALE_BITS",
    "Th08TimeScaleSchedule",
    "canonical_time_scale_bits",
    "validate_time_scale_bits",
]
