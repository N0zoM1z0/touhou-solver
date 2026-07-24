"""Packed, game-neutral hazard batches for native planning kernels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


SEGMENT_FIELD_NAMES = (
    "origin_x",
    "origin_y",
    "angle",
    "tail",
    "head",
    "half_width",
    "base_uncertainty",
    "uncertainty_per_frame",
)


@dataclass(frozen=True, eq=False)
class PackedSegmentFrames:
    """Frame-major segment samples in native structure-of-arrays form."""

    frame_offsets: np.ndarray
    origin_x: np.ndarray
    origin_y: np.ndarray
    angle: np.ndarray
    tail: np.ndarray
    head: np.ndarray
    half_width: np.ndarray
    base_uncertainty: np.ndarray
    uncertainty_per_frame: np.ndarray

    def __post_init__(self) -> None:
        offsets = self.frame_offsets
        if (
            offsets.dtype != np.int32
            or offsets.ndim != 1
            or not offsets.flags.c_contiguous
            or len(offsets) < 2
            or offsets[0] != 0
            or np.any(np.diff(offsets) < 0)
        ):
            raise ValueError(
                "packed segment offsets must be contiguous monotone int32"
            )
        sample_count = int(offsets[-1])
        for name in SEGMENT_FIELD_NAMES:
            values = getattr(self, name)
            if (
                values.dtype != np.float32
                or values.ndim != 1
                or not values.flags.c_contiguous
                or len(values) != sample_count
                or not np.all(np.isfinite(values))
            ):
                raise ValueError(
                    f"packed segment field {name} is not finite contiguous "
                    "float32 data"
                )
        if (
            np.any(self.half_width < 0.0)
            or np.any(self.base_uncertainty < 0.0)
            or np.any(self.uncertainty_per_frame < 0.0)
        ):
            raise ValueError(
                "packed segment width and uncertainty cannot be negative"
            )

    @property
    def frame_count(self) -> int:
        return len(self.frame_offsets) - 1

    @property
    def sample_count(self) -> int:
        return int(self.frame_offsets[-1])

    def frame_slice(self, frame: int) -> slice:
        if frame < 0 or frame >= self.frame_count:
            return slice(0, 0)
        return slice(
            int(self.frame_offsets[frame]),
            int(self.frame_offsets[frame + 1]),
        )

    @classmethod
    def empty(cls, frame_count: int) -> "PackedSegmentFrames":
        if frame_count < 1:
            raise ValueError("packed segment frame count must be positive")
        offsets = np.zeros(frame_count + 1, dtype=np.int32)
        fields = tuple(
            np.empty(0, dtype=np.float32) for _ in SEGMENT_FIELD_NAMES
        )
        return cls(offsets, *fields)

    @classmethod
    def from_frame_rows(
        cls,
        frames: Sequence[Iterable[Sequence[float]]],
    ) -> "PackedSegmentFrames":
        if not frames:
            raise ValueError("packed segment batch must contain a frame")
        offsets = np.empty(len(frames) + 1, dtype=np.int32)
        columns: tuple[list[float], ...] = tuple(
            [] for _ in SEGMENT_FIELD_NAMES
        )
        sample_count = 0
        for frame, rows in enumerate(frames):
            offsets[frame] = sample_count
            for row in rows:
                if len(row) != len(SEGMENT_FIELD_NAMES):
                    raise ValueError(
                        "packed segment row must contain eight fields"
                    )
                for column, value in zip(columns, row):
                    column.append(float(value))
                sample_count += 1
        offsets[-1] = sample_count
        fields = tuple(
            np.asarray(column, dtype=np.float32) for column in columns
        )
        return cls(offsets, *fields)

    @classmethod
    def from_trajectories(
        cls,
        trajectories: tuple[object, ...],
        *,
        frame_count: int,
    ) -> "PackedSegmentFrames":
        frames = []
        for frame in range(frame_count):
            frames.append(
                tuple(
                    (
                        sample.origin_x,
                        sample.origin_y,
                        sample.angle,
                        sample.tail,
                        sample.head,
                        sample.half_width,
                        sample.base_uncertainty,
                        sample.uncertainty_per_frame,
                    )
                    for trajectory in trajectories
                    if (sample := trajectory.sample(frame)) is not None
                )
            )
        return cls.from_frame_rows(frames)


__all__ = ["PackedSegmentFrames", "SEGMENT_FIELD_NAMES"]
