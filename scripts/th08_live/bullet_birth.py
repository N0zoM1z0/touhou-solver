"""Trace-only hostile-bullet birth evidence from one captured TH08 pool blob."""

from __future__ import annotations

import math
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


def _candidate_geometry(
    blob: bytes | bytearray | memoryview,
    *,
    slots: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Gather candidate-only geometry into compact contiguous arrays."""

    values = np.empty((len(slots), 6), dtype=np.float32)
    for column, offset in enumerate(
        (
            BULLET_POSITION_OFFSET,
            BULLET_POSITION_OFFSET + 4,
            BULLET_VELOCITY_OFFSET,
            BULLET_VELOCITY_OFFSET + 4,
            BULLET_GEOMETRY_OFFSET,
            BULLET_GEOMETRY_OFFSET + 4,
        )
    ):
        np.take(
            _pool_field(blob, offset=offset, dtype="<f4"),
            slots,
            out=values[:, column],
        )
    transform_flags = np.take(
        _pool_field(
            blob,
            offset=BULLET_TRANSFORM_FLAGS_OFFSET,
            dtype="<u4",
        ),
        slots,
    )
    geometry_finite = np.isfinite(values).all(axis=1)
    return values, transform_flags, geometry_finite


class BulletBirthTracker:
    """Compare captured pool generations without retaining another pool blob."""

    def __init__(self, *, maximum_bootstrap_age: int = 8) -> None:
        if type(maximum_bootstrap_age) is not int or maximum_bootstrap_age < 0:
            raise ValueError("maximum bootstrap age must be a non-negative int")
        self._maximum_bootstrap_age = maximum_bootstrap_age
        self._current_states = np.empty(BULLET_POOL_SIZE, dtype=np.uint16)
        self._current_ages = np.empty(BULLET_POOL_SIZE, dtype=np.int32)
        self._previous_states = np.empty(BULLET_POOL_SIZE, dtype=np.uint16)
        self._previous_ages = np.empty(BULLET_POOL_SIZE, dtype=np.int32)
        self._active = np.empty(BULLET_POOL_SIZE, dtype=np.bool_)
        self._valid_active = np.empty(BULLET_POOL_SIZE, dtype=np.bool_)
        self._work = np.empty(BULLET_POOL_SIZE, dtype=np.bool_)
        self._previous_active = np.empty(BULLET_POOL_SIZE, dtype=np.bool_)
        self._candidate_kind = np.empty(BULLET_POOL_SIZE, dtype=np.uint8)
        self._has_previous = False
        self._previous_frame_before: int | None = None
        self._previous_frame_after: int | None = None

    def reset(self) -> None:
        self._has_previous = False
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
        # Copy each sparse 6.3-MiB pool field once. All comparisons below use
        # compact contiguous double buffers and fixed scratch arrays.
        np.copyto(self._current_states, states_view)
        np.copyto(self._current_ages, ages_view)
        states = self._current_states
        ages = self._current_ages
        active = self._active
        valid_active = self._valid_active
        work = self._work
        candidate_kind = self._candidate_kind
        np.not_equal(states, 0, out=active)
        np.less(ages, 0, out=work)
        np.logical_not(work, out=valid_active)
        np.logical_and(active, valid_active, out=valid_active)
        candidate_kind.fill(0)
        np.logical_and(active, work, out=work)
        candidate_kind[work] = 1

        previous_states = self._previous_states if self._has_previous else None
        previous_ages = self._previous_ages if self._has_previous else None
        if not self._has_previous:
            np.less_equal(
                ages,
                self._maximum_bootstrap_age,
                out=work,
            )
            np.logical_and(valid_active, work, out=work)
            candidate_kind[work] = 2
        else:
            previous_active = self._previous_active
            np.not_equal(previous_states, 0, out=previous_active)
            np.logical_not(previous_active, out=work)
            np.logical_and(valid_active, work, out=work)
            candidate_kind[work] = 3
            np.less(ages, previous_ages, out=work)
            np.logical_and(work, previous_active, out=work)
            np.logical_and(work, valid_active, out=work)
            candidate_kind[work] = 4

        candidate_slots = np.flatnonzero(candidate_kind)
        evidence: list[BulletBirthEvidence] = []
        if candidate_slots.size:
            geometry, transform_flags, geometry_finite = _candidate_geometry(
                blob,
                slots=candidate_slots,
            )
            support_start = self._previous_frame_before
            for evidence_index, slot in enumerate(candidate_slots):
                index = int(slot)
                code = int(candidate_kind[index])
                if code == 1:
                    kind = BIRTH_KIND_INVALID_TIMER
                    status = OBSERVATION_INVALID_TIMER
                    candidate_support_start = None
                elif code == 2:
                    kind = BIRTH_KIND_BOOTSTRAP_RECENT
                    status = OBSERVATION_CAPTURE_SPANNED
                    candidate_support_start = None
                elif code == 3:
                    kind = BIRTH_KIND_ACTIVATION_EDGE
                    status = OBSERVATION_CAPTURE_SPANNED
                    candidate_support_start = support_start
                elif code == 4:
                    kind = BIRTH_KIND_TIMER_REGRESSION
                    status = OBSERVATION_SLOT_REUSE_AMBIGUOUS
                    candidate_support_start = support_start
                else:
                    raise AssertionError(
                        f"unknown birth candidate code {code}"
                    )
                values = geometry[evidence_index]
                evidence.append(
                    BulletBirthEvidence(
                        slot=index,
                        kind=kind,
                        observation_status=status,
                        state=int(states[index]),
                        age=int(ages[index]),
                        previous_state=(
                            int(previous_states[index])
                            if previous_states is not None
                            else None
                        ),
                        previous_age=(
                            int(previous_ages[index])
                            if previous_ages is not None
                            else None
                        ),
                        activation_support_start=candidate_support_start,
                        activation_support_end=frame_after,
                        x=float(values[0]),
                        y=float(values[1]),
                        velocity_x=float(values[2]),
                        velocity_y=float(values[3]),
                        width=float(values[4]),
                        height=float(values[5]),
                        transform_flags=int(
                            transform_flags[evidence_index]
                        ),
                        geometry_finite=bool(
                            geometry_finite[evidence_index]
                        ),
                    )
                )
        result = BulletBirthObservation(
            frame_before=frame_before,
            frame_after=frame_after,
            previous_frame_before=self._previous_frame_before,
            previous_frame_after=self._previous_frame_after,
            active_count=int(np.count_nonzero(active)),
            evidence=tuple(evidence),
        )

        self._previous_states, self._current_states = (
            self._current_states,
            self._previous_states,
        )
        self._previous_ages, self._current_ages = (
            self._current_ages,
            self._previous_ages,
        )
        self._has_previous = True
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
