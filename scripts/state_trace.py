#!/usr/bin/env python3
"""Game-neutral exact state projection and first-difference reporting."""

from __future__ import annotations

import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from deterministic_sim import EventContext


PathPart = str | int


class FloatEncoding(Enum):
    VALUE = "value"
    BINARY32_BITS = "binary32_bits"
    BINARY64_BITS = "binary64_bits"


@dataclass(frozen=True)
class ProjectionField:
    name: str
    path: tuple[PathPart, ...]
    float_encoding: FloatEncoding = FloatEncoding.VALUE

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("projection field name cannot be empty")
        if not self.path:
            raise ValueError("projection field path cannot be empty")


def _resolve_path(value: Any, path: tuple[PathPart, ...]) -> Any:
    current = value
    for part in path:
        if isinstance(part, int):
            if not isinstance(current, Sequence):
                raise TypeError(f"cannot index non-sequence with {part}")
            current = current[part]
        elif isinstance(current, Mapping):
            current = current[part]
        else:
            current = getattr(current, part)
    return current


def _encode_value(value: Any, encoding: FloatEncoding) -> Any:
    if encoding is FloatEncoding.VALUE:
        return value
    if not isinstance(value, float):
        raise TypeError(f"{encoding.value} requires a float, got {type(value).__name__}")
    if encoding is FloatEncoding.BINARY32_BITS:
        return struct.unpack("<I", struct.pack("<f", value))[0]
    if encoding is FloatEncoding.BINARY64_BITS:
        return struct.unpack("<Q", struct.pack("<d", value))[0]
    raise ValueError(f"unsupported float encoding {encoding!r}")


@dataclass(frozen=True)
class StateProjection:
    fields: tuple[ProjectionField, ...]

    def __post_init__(self) -> None:
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("projection field names must be unique")

    def capture(self, state: Any) -> dict[str, Any]:
        return {
            field.name: _encode_value(
                _resolve_path(state, field.path), field.float_encoding
            )
            for field in self.fields
        }


@dataclass(frozen=True)
class TraceRecord:
    frame_index: int
    event_key: str
    values: Mapping[str, Any]


class TraceCollector:
    def __init__(self, projection: StateProjection) -> None:
        self._projection = projection
        self._records: list[TraceRecord] = []

    @property
    def records(self) -> tuple[TraceRecord, ...]:
        return tuple(self._records)

    def observe(self, context: EventContext, state: Any) -> None:
        self._records.append(
            TraceRecord(
                frame_index=context.frame_index,
                event_key=context.event_key,
                values=self._projection.capture(state),
            )
        )


@dataclass(frozen=True)
class TraceMismatch:
    record_index: int
    frame_index: int | None
    event_key: str | None
    field: str
    expected: Any
    actual: Any


def first_trace_difference(
    expected: Sequence[TraceRecord], actual: Sequence[TraceRecord]
) -> TraceMismatch | None:
    for index, (left, right) in enumerate(zip(expected, actual)):
        if (left.frame_index, left.event_key) != (right.frame_index, right.event_key):
            return TraceMismatch(
                index,
                right.frame_index,
                right.event_key,
                "<record_identity>",
                (left.frame_index, left.event_key),
                (right.frame_index, right.event_key),
            )
        field_names = tuple(dict.fromkeys((*left.values.keys(), *right.values.keys())))
        for field in field_names:
            expected_value = left.values.get(field, "<missing>")
            actual_value = right.values.get(field, "<missing>")
            if expected_value != actual_value:
                return TraceMismatch(
                    index,
                    right.frame_index,
                    right.event_key,
                    field,
                    expected_value,
                    actual_value,
                )
    if len(expected) == len(actual):
        return None
    index = min(len(expected), len(actual))
    left = expected[index] if index < len(expected) else None
    right = actual[index] if index < len(actual) else None
    record = right or left
    return TraceMismatch(
        index,
        record.frame_index if record else None,
        record.event_key if record else None,
        "<record_count>",
        len(expected),
        len(actual),
    )
