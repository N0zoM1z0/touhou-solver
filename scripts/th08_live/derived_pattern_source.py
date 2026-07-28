"""Trace-only oracle for ready TH08 derived-bullet emission sources."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from th08_bullet_transform_model import (
    DerivedPattern,
    TransformKind,
    TransformRecord,
    decode_derived_pattern,
    parse_transform_record,
)

from .bullet_decode import (
    BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
    BULLET_POSITION_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_TRANSFORM_PROGRAM_OFFSET,
    BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
)
from .bullet_birth import BULLET_TIMER_CURRENT_OFFSET
from .sensor import BULLET_POOL_SIZE


DERIVED_SOURCE_SCHEMA_VERSION = 1
TRANSFORM_PROGRAM_LENGTH = 18
TRANSFORM_RECORD_SIZE = 24


def _finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _record_payload(record: TransformRecord) -> dict[str, object]:
    return {
        "index": record.index,
        "kind": record.kind,
        "allow_while_active": record.allow_while_active,
        "int_0": record.int_0,
        "int_1": record.int_1,
        "float_0": _finite_or_none(float(record.float_0)),
        "float_1": _finite_or_none(float(record.float_1)),
    }


def _pattern_payload(pattern: DerivedPattern) -> dict[str, object]:
    return {
        "kill_parent": pattern.kill_parent,
        "mode": pattern.mode,
        "bullet_type": pattern.bullet_type,
        "color": pattern.color,
        "start_transform_index": pattern.start_transform_index,
        "count_1": pattern.count_1,
        "count_2": pattern.count_2,
        "predicted_child_count": max(0, pattern.count_1)
        * max(0, pattern.count_2),
        "angle_1": _finite_or_none(float(pattern.angle_1)),
        "angle_2": _finite_or_none(float(pattern.angle_2)),
        "speed_1": _finite_or_none(float(pattern.speed_1)),
        "speed_2": _finite_or_none(float(pattern.speed_2)),
        "child_transform_flags": pattern.child_transform_flags,
    }


@dataclass(frozen=True)
class DerivedPatternSourceEvidence:
    slot: int
    state: int
    age: int
    x: float
    y: float
    transform_flags: int
    original_transform_flags: int
    queue_cursor: int
    first_words: tuple[int, int, int, int, int, int]
    second_words: tuple[int, int, int, int, int, int]
    geometry_finite: bool

    @property
    def first_record(self) -> TransformRecord:
        return _record_from_words(self.first_words, index=self.queue_cursor)

    @property
    def second_record(self) -> TransformRecord:
        return _record_from_words(
            self.second_words,
            index=self.queue_cursor + 1,
        )

    @property
    def pattern(self) -> DerivedPattern:
        return decode_derived_pattern(self.first_record, self.second_record)

    def record(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "state": self.state,
            "age": self.age,
            "position": (
                [self.x, self.y] if self.geometry_finite else None
            ),
            "geometry_finite": self.geometry_finite,
            "transform_flags": self.transform_flags,
            "original_transform_flags": self.original_transform_flags,
            "queue_cursor": self.queue_cursor,
            "first_words": list(self.first_words),
            "second_words": list(self.second_words),
            "first_record": _record_payload(self.first_record),
            "second_record": _record_payload(self.second_record),
            "pattern": _pattern_payload(self.pattern),
            "classification": "derived_pattern_ready_candidate",
            "authority": "trace_only",
        }


@dataclass(frozen=True)
class DerivedPatternSourceObservation:
    frame_before: int
    frame_after: int
    active_count: int
    candidates: tuple[DerivedPatternSourceEvidence, ...]

    @property
    def capture_span(self) -> int:
        return self.frame_after - self.frame_before

    def record(self) -> dict[str, object]:
        return {
            "schema_version": DERIVED_SOURCE_SCHEMA_VERSION,
            "role": "trace_only_no_action_authority",
            "frame_before": self.frame_before,
            "frame_after": self.frame_after,
            "capture_span": self.capture_span,
            "active_count": self.active_count,
            "candidate_count": len(self.candidates),
            "candidates": [
                candidate.record() for candidate in self.candidates
            ],
            "coverage": {
                "source_class": "ready_visible_parent_bullet_transform_only",
                "future_hazard_coverage": "unknown",
                "physical_action_authority": "none",
            },
        }


def _record_from_words(
    words: tuple[int, int, int, int, int, int],
    *,
    index: int,
) -> TransformRecord:
    return parse_transform_record(
        struct.pack("<6I", *words),
        index=index,
    )


def _validate_observation(
    blob: bytes | bytearray | memoryview,
    *,
    frame_before: int,
    frame_after: int,
) -> memoryview:
    required_size = BULLET_POOL_SIZE * BULLET_STRIDE
    if len(blob) < required_size:
        raise ValueError(f"bullet pool requires {required_size} bytes")
    if (
        type(frame_before) is not int
        or type(frame_after) is not int
        or frame_before < 0
        or frame_after < frame_before
    ):
        raise ValueError("invalid bullet capture frame interval")
    return memoryview(blob)


def observe_derived_pattern_sources(
    blob: bytes | bytearray | memoryview,
    *,
    frame_before: int,
    frame_after: int,
) -> DerivedPatternSourceObservation:
    """Independent scalar scan of the fixed TH08 readiness predicate."""

    view = _validate_observation(
        blob,
        frame_before=frame_before,
        frame_after=frame_after,
    )
    active_count = 0
    candidates: list[DerivedPatternSourceEvidence] = []
    for slot in range(BULLET_POOL_SIZE):
        base = slot * BULLET_STRIDE
        state = struct.unpack_from(
            "<H",
            view,
            base + BULLET_STATE_OFFSET,
        )[0]
        if state == 0:
            continue
        active_count += 1
        cursor = struct.unpack_from(
            "<i",
            view,
            base + BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
        )[0]
        if not 0 <= cursor + 1 < TRANSFORM_PROGRAM_LENGTH:
            continue
        first_offset = (
            base
            + BULLET_TRANSFORM_PROGRAM_OFFSET
            + cursor * TRANSFORM_RECORD_SIZE
        )
        second_offset = first_offset + TRANSFORM_RECORD_SIZE
        first_words = struct.unpack_from("<6I", view, first_offset)
        second_words = struct.unpack_from("<6I", view, second_offset)
        if (
            first_words[4] != TransformKind.EMIT_DERIVED_PATTERN
            or second_words[4]
            != TransformKind.DERIVED_PATTERN_PARAMETERS
        ):
            continue
        original_flags = struct.unpack_from(
            "<I",
            view,
            base + BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
        )[0]
        if not first_words[4] & original_flags:
            continue
        transform_flags = struct.unpack_from(
            "<I",
            view,
            base + BULLET_TRANSFORM_FLAGS_OFFSET,
        )[0]
        if first_words[5] == 0 and transform_flags != 0:
            continue
        x, y = struct.unpack_from(
            "<ff",
            view,
            base + BULLET_POSITION_OFFSET,
        )
        candidates.append(
            DerivedPatternSourceEvidence(
                slot=slot,
                state=state,
                age=struct.unpack_from(
                    "<i",
                    view,
                    base + BULLET_TIMER_CURRENT_OFFSET,
                )[0],
                x=x,
                y=y,
                transform_flags=transform_flags,
                original_transform_flags=original_flags,
                queue_cursor=cursor,
                first_words=first_words,
                second_words=second_words,
                geometry_finite=math.isfinite(x) and math.isfinite(y),
            )
        )
    return DerivedPatternSourceObservation(
        frame_before=frame_before,
        frame_after=frame_after,
        active_count=active_count,
        candidates=tuple(candidates),
    )


__all__ = [
    "DERIVED_SOURCE_SCHEMA_VERSION",
    "DerivedPatternSourceEvidence",
    "DerivedPatternSourceObservation",
    "TRANSFORM_PROGRAM_LENGTH",
    "TRANSFORM_RECORD_SIZE",
    "observe_derived_pattern_sources",
]
