"""Trace-only hostile-bullet birth evidence from one captured TH08 pool blob."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

import numpy as np

from .bullet_decode import (
    BULLET_GEOMETRY_OFFSET,
    BULLET_POSITION_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_VELOCITY_OFFSET,
)
from .sensor import BULLET_POOL_SIZE, BULLET_STRIDE


# IDA: bullet_manager_update passes bullet + 0xD8C to timer_current(), whose
# accessor returns the int32 at timer + 0x08.
BULLET_TIMER_BASE_OFFSET = 0x0D8C
BULLET_TIMER_CURRENT_OFFSET = BULLET_TIMER_BASE_OFFSET + 0x08

BIRTH_KIND_ACTIVATION_EDGE = "activation_edge"
BIRTH_KIND_BOOTSTRAP_RECENT = "bootstrap_recent"
BIRTH_KIND_TIMER_REGRESSION = "timer_regression"
BIRTH_KIND_INVALID_TIMER = "invalid_timer"

OBSERVATION_COMPLETE = "complete"
OBSERVATION_CAPTURE_SPANNED = "capture_spanned"
OBSERVATION_INVALID_TIMER = "invalid_timer"
OBSERVATION_SLOT_REUSE_AMBIGUOUS = "slot_reuse_ambiguous"


@dataclass(frozen=True)
class BulletBirthEvidence:
    """One compact slot-level activation or timer anomaly."""

    slot: int
    kind: str
    observation_status: str
    state: int
    age: int
    previous_state: int | None
    previous_age: int | None
    activation_support_start: int | None
    activation_support_end: int
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    width: float
    height: float
    transform_flags: int
    geometry_finite: bool

    def record(self) -> dict[str, object]:
        position: list[float | None]
        velocity: list[float | None]
        geometry: list[float | None]
        if self.geometry_finite:
            position = [self.x, self.y]
            velocity = [self.velocity_x, self.velocity_y]
            geometry = [self.width, self.height]
        else:
            position = [
                self.x if math.isfinite(self.x) else None,
                self.y if math.isfinite(self.y) else None,
            ]
            velocity = [
                (
                    self.velocity_x
                    if math.isfinite(self.velocity_x)
                    else None
                ),
                (
                    self.velocity_y
                    if math.isfinite(self.velocity_y)
                    else None
                ),
            ]
            geometry = [
                self.width if math.isfinite(self.width) else None,
                self.height if math.isfinite(self.height) else None,
            ]
        return {
            "slot": self.slot,
            "kind": self.kind,
            "observation_status": self.observation_status,
            "state": self.state,
            "age": self.age,
            "previous_state": self.previous_state,
            "previous_age": self.previous_age,
            "activation_support": [
                self.activation_support_start,
                self.activation_support_end,
            ],
            "position": position,
            "velocity": velocity,
            "geometry": geometry,
            "transform_flags": self.transform_flags,
            "geometry_finite": self.geometry_finite,
        }


@dataclass(frozen=True)
class BulletBirthObservation:
    """Birth evidence and provenance for one persistent-buffer capture."""

    frame_before: int
    frame_after: int
    previous_frame_before: int | None
    previous_frame_after: int | None
    active_count: int
    evidence: tuple[BulletBirthEvidence, ...]

    @property
    def capture_span(self) -> int:
        return self.frame_after - self.frame_before

    def record(self) -> dict[str, object]:
        return {
            "role": "trace_only_no_action_authority",
            "frame_before": self.frame_before,
            "frame_after": self.frame_after,
            "capture_span": self.capture_span,
            "previous_frame_before": self.previous_frame_before,
            "previous_frame_after": self.previous_frame_after,
            "active_count": self.active_count,
            "evidence_count": len(self.evidence),
            "evidence": [item.record() for item in self.evidence],
        }


def _pool_field(
    blob: bytes | bytearray | memoryview,
    *,
    offset: int,
    dtype: str,
) -> np.ndarray:
    return np.ndarray(
        (BULLET_POOL_SIZE,),
        dtype=dtype,
        buffer=blob,
        offset=offset,
        strides=(BULLET_STRIDE,),
    )


def _validate_pool_blob(blob: bytes | bytearray | memoryview) -> None:
    required_size = BULLET_POOL_SIZE * BULLET_STRIDE
    if len(blob) < required_size:
        raise ValueError(f"bullet pool requires {required_size} bytes")


def _slot_evidence(
    blob: bytes | bytearray | memoryview,
    *,
    slot: int,
    kind: str,
    observation_status: str,
    state: int,
    age: int,
    previous_state: int | None,
    previous_age: int | None,
    activation_support_start: int | None,
    activation_support_end: int,
) -> BulletBirthEvidence:
    base = slot * BULLET_STRIDE
    width, height = struct.unpack_from(
        "<ff",
        blob,
        base + BULLET_GEOMETRY_OFFSET,
    )
    x, y = struct.unpack_from(
        "<ff",
        blob,
        base + BULLET_POSITION_OFFSET,
    )
    velocity_x, velocity_y = struct.unpack_from(
        "<ff",
        blob,
        base + BULLET_VELOCITY_OFFSET,
    )
    transform_flags = struct.unpack_from(
        "<I",
        blob,
        base + BULLET_TRANSFORM_FLAGS_OFFSET,
    )[0]
    geometry_finite = all(
        math.isfinite(value)
        for value in (x, y, velocity_x, velocity_y, width, height)
    )
    return BulletBirthEvidence(
        slot=slot,
        kind=kind,
        observation_status=observation_status,
        state=state,
        age=age,
        previous_state=previous_state,
        previous_age=previous_age,
        activation_support_start=activation_support_start,
        activation_support_end=activation_support_end,
        x=x,
        y=y,
        velocity_x=velocity_x,
        velocity_y=velocity_y,
        width=width,
        height=height,
        transform_flags=transform_flags,
        geometry_finite=geometry_finite,
    )


class BulletBirthTracker:
    """Compare captured pool generations without retaining another pool blob."""

    def __init__(self, *, maximum_bootstrap_age: int = 8) -> None:
        if type(maximum_bootstrap_age) is not int or maximum_bootstrap_age < 0:
            raise ValueError("maximum bootstrap age must be a non-negative int")
        self._maximum_bootstrap_age = maximum_bootstrap_age
        self._previous_states: np.ndarray | None = None
        self._previous_ages: np.ndarray | None = None
        self._previous_frame_before: int | None = None
        self._previous_frame_after: int | None = None

    def reset(self) -> None:
        self._previous_states = None
        self._previous_ages = None
        self._previous_frame_before = None
        self._previous_frame_after = None

    def observe(
        self,
        blob: bytes | bytearray | memoryview,
        *,
        frame_before: int,
        frame_after: int,
    ) -> BulletBirthObservation:
        _validate_pool_blob(blob)
        if (
            type(frame_before) is not int
            or type(frame_after) is not int
            or frame_before < 0
            or frame_after < frame_before
        ):
            raise ValueError("invalid bullet capture frame interval")
        if (
            self._previous_frame_before is not None
            and frame_before < self._previous_frame_before
        ):
            raise ValueError("bullet capture frame regressed")

        states_view = _pool_field(
            blob,
            offset=BULLET_STATE_OFFSET,
            dtype="<u2",
        )
        ages_view = _pool_field(
            blob,
            offset=BULLET_TIMER_CURRENT_OFFSET,
            dtype="<i4",
        )
        active = states_view != 0
        invalid_timer = active & (ages_view < 0)
        valid_active = active & ~invalid_timer

        previous_states = self._previous_states
        previous_ages = self._previous_ages
        evidence_specs: list[
            tuple[int, str, str, int | None, int | None, int | None]
        ] = []

        for slot in np.flatnonzero(invalid_timer):
            index = int(slot)
            evidence_specs.append(
                (
                    index,
                    BIRTH_KIND_INVALID_TIMER,
                    OBSERVATION_INVALID_TIMER,
                    (
                        int(previous_states[index])
                        if previous_states is not None
                        else None
                    ),
                    (
                        int(previous_ages[index])
                        if previous_ages is not None
                        else None
                    ),
                    None,
                )
            )

        if previous_states is None or previous_ages is None:
            bootstrap = (
                valid_active
                & (ages_view <= self._maximum_bootstrap_age)
            )
            for slot in np.flatnonzero(bootstrap):
                evidence_specs.append(
                    (
                        int(slot),
                        BIRTH_KIND_BOOTSTRAP_RECENT,
                        OBSERVATION_CAPTURE_SPANNED,
                        None,
                        None,
                        None,
                    )
                )
        else:
            previous_active = previous_states != 0
            activated = valid_active & ~previous_active
            regressed = (
                valid_active
                & previous_active
                & (ages_view < previous_ages)
            )
            support_start = self._previous_frame_before
            for slot in np.flatnonzero(activated):
                index = int(slot)
                evidence_specs.append(
                    (
                        index,
                        BIRTH_KIND_ACTIVATION_EDGE,
                        OBSERVATION_CAPTURE_SPANNED,
                        int(previous_states[index]),
                        int(previous_ages[index]),
                        support_start,
                    )
                )
            for slot in np.flatnonzero(regressed):
                index = int(slot)
                evidence_specs.append(
                    (
                        index,
                        BIRTH_KIND_TIMER_REGRESSION,
                        OBSERVATION_SLOT_REUSE_AMBIGUOUS,
                        int(previous_states[index]),
                        int(previous_ages[index]),
                        support_start,
                    )
                )

        evidence_specs.sort(key=lambda item: (item[0], item[1]))
        evidence = tuple(
            _slot_evidence(
                blob,
                slot=slot,
                kind=kind,
                observation_status=status,
                state=int(states_view[slot]),
                age=int(ages_view[slot]),
                previous_state=previous_state,
                previous_age=previous_age,
                activation_support_start=support_start,
                activation_support_end=frame_after,
            )
            for (
                slot,
                kind,
                status,
                previous_state,
                previous_age,
                support_start,
            ) in evidence_specs
        )
        result = BulletBirthObservation(
            frame_before=frame_before,
            frame_after=frame_after,
            previous_frame_before=self._previous_frame_before,
            previous_frame_after=self._previous_frame_after,
            active_count=int(np.count_nonzero(active)),
            evidence=evidence,
        )

        # Copy only two compact strided fields. The 6.3 MiB pool destination
        # remains sensor-owned and is overwritten by the next RPM capture.
        self._previous_states = states_view.copy()
        self._previous_ages = ages_view.copy()
        self._previous_frame_before = frame_before
        self._previous_frame_after = frame_after
        return result


__all__ = [
    "BIRTH_KIND_ACTIVATION_EDGE",
    "BIRTH_KIND_BOOTSTRAP_RECENT",
    "BIRTH_KIND_INVALID_TIMER",
    "BIRTH_KIND_TIMER_REGRESSION",
    "BULLET_TIMER_BASE_OFFSET",
    "BULLET_TIMER_CURRENT_OFFSET",
    "BulletBirthEvidence",
    "BulletBirthObservation",
    "BulletBirthTracker",
    "OBSERVATION_CAPTURE_SPANNED",
    "OBSERVATION_COMPLETE",
    "OBSERVATION_INVALID_TIMER",
    "OBSERVATION_SLOT_REUSE_AMBIGUOUS",
]
