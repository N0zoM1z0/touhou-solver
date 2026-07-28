"""Trace-only hostile-bullet birth evidence from one captured TH08 pool blob."""

from __future__ import annotations

import math
import struct
from collections.abc import Sequence
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

_CODE_TO_KIND_STATUS = {
    1: (BIRTH_KIND_INVALID_TIMER, OBSERVATION_INVALID_TIMER),
    2: (BIRTH_KIND_BOOTSTRAP_RECENT, OBSERVATION_CAPTURE_SPANNED),
    3: (BIRTH_KIND_ACTIVATION_EDGE, OBSERVATION_CAPTURE_SPANNED),
    4: (
        BIRTH_KIND_TIMER_REGRESSION,
        OBSERVATION_SLOT_REUSE_AMBIGUOUS,
    ),
}
_KIND_TO_CODE = {
    kind: code
    for code, (kind, _status) in _CODE_TO_KIND_STATUS.items()
}
_STATUS_TO_CODE = {
    OBSERVATION_INVALID_TIMER: 1,
    OBSERVATION_CAPTURE_SPANNED: 2,
    OBSERVATION_SLOT_REUSE_AMBIGUOUS: 3,
    OBSERVATION_COMPLETE: 4,
}
_EVIDENCE_CODE_TO_STATUS_CODE = np.asarray((0, 1, 2, 2, 3), dtype=np.uint8)


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


class BulletBirthEvidenceBatch(Sequence[BulletBirthEvidence]):
    """Read-only columnar evidence with lazy scalar witness materialization."""

    __slots__ = (
        "_ages",
        "_codes",
        "_geometry",
        "_geometry_finite",
        "_previous_ages",
        "_previous_states",
        "_slots",
        "_states",
        "_support_end",
        "_support_start",
        "_transform_flags",
    )

    def __init__(
        self,
        *,
        slots: np.ndarray,
        codes: np.ndarray,
        states: np.ndarray,
        ages: np.ndarray,
        previous_states: np.ndarray | None,
        previous_ages: np.ndarray | None,
        support_start: int | None,
        support_end: int,
        geometry: np.ndarray,
        transform_flags: np.ndarray,
        geometry_finite: np.ndarray,
    ) -> None:
        count = len(slots)
        if (
            len(codes) != count
            or len(states) != count
            or len(ages) != count
            or len(geometry) != count
            or len(transform_flags) != count
            or len(geometry_finite) != count
        ):
            raise ValueError("bullet birth evidence columns differ in length")
        if (
            previous_states is None
            or previous_ages is None
        ) and previous_states is not previous_ages:
            raise ValueError("previous birth columns must both be present")
        if (
            previous_states is not None
            and (
                len(previous_states) != count
                or len(previous_ages) != count
            )
        ):
            raise ValueError("previous birth columns differ in length")
        if geometry.shape != (count, 6):
            raise ValueError("bullet birth geometry must have six columns")
        if count and (
            int(codes.min()) < min(_CODE_TO_KIND_STATUS)
            or int(codes.max()) > max(_CODE_TO_KIND_STATUS)
        ):
            raise ValueError("unknown bullet birth evidence code")
        for array in (
            slots,
            codes,
            states,
            ages,
            previous_states,
            previous_ages,
            geometry,
            transform_flags,
            geometry_finite,
        ):
            if array is not None:
                array.setflags(write=False)
        self._slots = slots
        self._codes = codes
        self._states = states
        self._ages = ages
        self._previous_states = previous_states
        self._previous_ages = previous_ages
        self._support_start = support_start
        self._support_end = support_end
        self._geometry = geometry
        self._transform_flags = transform_flags
        self._geometry_finite = geometry_finite

    def __len__(self) -> int:
        return len(self._slots)

    def __getitem__(
        self,
        index: int | slice,
    ) -> BulletBirthEvidence | tuple[BulletBirthEvidence, ...]:
        if isinstance(index, slice):
            return tuple(self[position] for position in range(*index.indices(len(self))))
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError("bullet birth evidence index out of range")
        code = int(self._codes[index])
        kind, status = _CODE_TO_KIND_STATUS[code]
        values = self._geometry[index]
        return BulletBirthEvidence(
            slot=int(self._slots[index]),
            kind=kind,
            observation_status=status,
            state=int(self._states[index]),
            age=int(self._ages[index]),
            previous_state=(
                int(self._previous_states[index])
                if self._previous_states is not None
                else None
            ),
            previous_age=(
                int(self._previous_ages[index])
                if self._previous_ages is not None
                else None
            ),
            activation_support_start=(
                self._support_start if code in (3, 4) else None
            ),
            activation_support_end=self._support_end,
            x=float(values[0]),
            y=float(values[1]),
            velocity_x=float(values[2]),
            velocity_y=float(values[3]),
            width=float(values[4]),
            height=float(values[5]),
            transform_flags=int(self._transform_flags[index]),
            geometry_finite=bool(self._geometry_finite[index]),
        )

    def record(self) -> dict[str, object]:
        geometry: list[list[float | None]] = self._geometry.tolist()
        for index in np.flatnonzero(
            np.logical_not(self._geometry_finite)
        ):
            row = geometry[int(index)]
            geometry[int(index)] = [
                value if math.isfinite(value) else None
                for value in row
            ]
        return {
            "format": "columnar_v1",
            "slot": self._slots.tolist(),
            "code": self._codes.tolist(),
            "status": np.take(
                _EVIDENCE_CODE_TO_STATUS_CODE,
                self._codes,
            ).tolist(),
            "state": self._states.tolist(),
            "age": self._ages.tolist(),
            "previous_state": (
                self._previous_states.tolist()
                if self._previous_states is not None
                else None
            ),
            "previous_age": (
                self._previous_ages.tolist()
                if self._previous_ages is not None
                else None
            ),
            "geometry": geometry,
            "transform_flags": self._transform_flags.tolist(),
            "geometry_finite": self._geometry_finite.tolist(),
        }


def _evidence_columns(
    evidence: Sequence[BulletBirthEvidence],
) -> dict[str, object]:
    """Encode manually constructed scalar evidence in the columnar schema."""

    geometry: list[list[float | None]] = []
    for item in evidence:
        row = (
            item.x,
            item.y,
            item.velocity_x,
            item.velocity_y,
            item.width,
            item.height,
        )
        geometry.append(
            [
                value if math.isfinite(value) else None
                for value in row
            ]
        )
    return {
        "format": "columnar_v1",
        "slot": [item.slot for item in evidence],
        "code": [_KIND_TO_CODE[item.kind] for item in evidence],
        "status": [
            _STATUS_TO_CODE[item.observation_status]
            for item in evidence
        ],
        "state": [item.state for item in evidence],
        "age": [item.age for item in evidence],
        "previous_state": [item.previous_state for item in evidence],
        "previous_age": [item.previous_age for item in evidence],
        "geometry": geometry,
        "transform_flags": [item.transform_flags for item in evidence],
        "geometry_finite": [item.geometry_finite for item in evidence],
    }


@dataclass(frozen=True)
class BulletBirthObservation:
    """Birth evidence and provenance for one persistent-buffer capture."""

    frame_before: int
    frame_after: int
    previous_frame_before: int | None
    previous_frame_after: int | None
    active_count: int
    evidence: tuple[BulletBirthEvidence, ...] | BulletBirthEvidenceBatch

    @property
    def capture_span(self) -> int:
        return self.frame_after - self.frame_before

    def record(self) -> dict[str, object]:
        evidence = (
            self.evidence.record()
            if isinstance(self.evidence, BulletBirthEvidenceBatch)
            else _evidence_columns(self.evidence)
        )
        return {
            "role": "trace_only_no_action_authority",
            "frame_before": self.frame_before,
            "frame_after": self.frame_after,
            "capture_span": self.capture_span,
            "previous_frame_before": self.previous_frame_before,
            "previous_frame_after": self.previous_frame_after,
            "active_count": self.active_count,
            "evidence_count": len(self.evidence),
            "evidence": evidence,
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

    if len(slots) <= 32:
        rows: list[tuple[float, ...]] = []
        flags: list[int] = []
        for slot in slots:
            base = int(slot) * BULLET_STRIDE
            position = struct.unpack_from(
                "<2f",
                blob,
                base + BULLET_POSITION_OFFSET,
            )
            velocity = struct.unpack_from(
                "<2f",
                blob,
                base + BULLET_VELOCITY_OFFSET,
            )
            size = struct.unpack_from(
                "<2f",
                blob,
                base + BULLET_GEOMETRY_OFFSET,
            )
            rows.append(position + velocity + size)
            flags.append(
                struct.unpack_from(
                    "<I",
                    blob,
                    base + BULLET_TRANSFORM_FLAGS_OFFSET,
                )[0]
            )
        values = np.asarray(rows, dtype=np.float32)
        transform_flags = np.asarray(flags, dtype=np.uint32)
        geometry_finite = np.isfinite(values).all(axis=1)
        return values, transform_flags, geometry_finite

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
        evidence: (
            tuple[BulletBirthEvidence, ...]
            | BulletBirthEvidenceBatch
        ) = ()
        if candidate_slots.size:
            geometry, transform_flags, geometry_finite = _candidate_geometry(
                blob,
                slots=candidate_slots,
            )
            evidence = BulletBirthEvidenceBatch(
                slots=candidate_slots,
                codes=np.take(candidate_kind, candidate_slots),
                states=np.take(states, candidate_slots),
                ages=np.take(ages, candidate_slots),
                previous_states=(
                    np.take(previous_states, candidate_slots)
                    if previous_states is not None
                    else None
                ),
                previous_ages=(
                    np.take(previous_ages, candidate_slots)
                    if previous_ages is not None
                    else None
                ),
                support_start=self._previous_frame_before,
                support_end=frame_after,
                geometry=geometry,
                transform_flags=transform_flags,
                geometry_finite=geometry_finite,
            )
        result = BulletBirthObservation(
            frame_before=frame_before,
            frame_after=frame_after,
            previous_frame_before=self._previous_frame_before,
            previous_frame_after=self._previous_frame_after,
            active_count=int(np.count_nonzero(active)),
            evidence=evidence,
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
    "BulletBirthEvidenceBatch",
    "BulletBirthObservation",
    "BulletBirthTracker",
    "OBSERVATION_CAPTURE_SPANNED",
    "OBSERVATION_COMPLETE",
    "OBSERVATION_INVALID_TIMER",
    "OBSERVATION_SLOT_REUSE_AMBIGUOUS",
]
