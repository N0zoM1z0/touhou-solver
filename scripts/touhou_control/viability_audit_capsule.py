"""Compact, lossless inputs for offline viability differential audits.

The live trace intentionally retains only nearby gameplay geometry.  These
ignored NPZ capsules instead preserve the already-lowered, game-neutral hazard
epoch used by one asynchronous corridor solve.  They are inputs for offline
experiments, never a gameplay sensor or a committed artifact format.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np

from corridor_planner import (
    MovingAabbHazard,
    PiecewiseAabbHazard,
    SegmentHazard,
    SegmentTrajectoryHazard,
)
from .trajectory import PiecewiseLinearTrajectory, VelocityChange


@dataclass(frozen=True)
class ViabilityAuditCapsule:
    metadata: dict[str, object]
    aabbs: tuple[MovingAabbHazard, ...]
    piecewise_aabbs: tuple[PiecewiseAabbHazard, ...]
    segment_trajectories: tuple[SegmentTrajectoryHazard, ...]


def _rows(
    values: list[tuple[float, ...]],
    width: int,
) -> np.ndarray:
    if not values:
        return np.empty((0, width), dtype=np.float64)
    return np.asarray(values, dtype=np.float64)


def write_viability_audit_capsule(
    path: Path,
    *,
    metadata: Mapping[str, object],
    aabbs: tuple[MovingAabbHazard, ...],
    piecewise_aabbs: tuple[PiecewiseAabbHazard, ...],
    segment_trajectories: tuple[SegmentTrajectoryHazard, ...],
) -> None:
    """Atomically retain one exact neutral policy input epoch."""

    moving = _rows(
        [
            (
                hazard.x,
                hazard.y,
                hazard.velocity_x,
                hazard.velocity_y,
                hazard.half_width,
                hazard.half_height,
                hazard.base_uncertainty,
                hazard.uncertainty_per_frame,
            )
            for hazard in aabbs
        ],
        8,
    )
    piecewise = _rows(
        [
            (
                hazard.motion.x,
                hazard.motion.y,
                hazard.motion.velocity_x,
                hazard.motion.velocity_y,
                hazard.half_width,
                hazard.half_height,
                hazard.base_uncertainty,
                hazard.uncertainty_per_frame,
            )
            for hazard in piecewise_aabbs
        ],
        8,
    )
    piecewise_event_offsets = [0]
    piecewise_events: list[tuple[float, ...]] = []
    for hazard in piecewise_aabbs:
        piecewise_events.extend(
            (
                float(change.frame),
                change.velocity_x,
                change.velocity_y,
            )
            for change in hazard.motion.changes
        )
        piecewise_event_offsets.append(len(piecewise_events))

    segment_offsets = [0]
    segment_samples: list[tuple[float, ...]] = []
    for trajectory in segment_trajectories:
        for sample in trajectory.samples:
            if sample is None:
                segment_samples.append(
                    (
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    )
                )
            else:
                segment_samples.append(
                    (
                        1.0,
                        sample.origin_x,
                        sample.origin_y,
                        sample.angle,
                        sample.tail,
                        sample.head,
                        sample.half_width,
                        sample.base_uncertainty,
                        sample.uncertainty_per_frame,
                    )
                )
        segment_offsets.append(len(segment_samples))

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as output:
        np.savez(
            output,
            schema=np.asarray("touhou-viability-audit-capsule-v1"),
            metadata=np.asarray(
                json.dumps(
                    dict(metadata),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            ),
            moving=moving,
            piecewise=piecewise,
            piecewise_event_offsets=np.asarray(
                piecewise_event_offsets,
                dtype=np.int64,
            ),
            piecewise_events=_rows(piecewise_events, 3),
            segment_offsets=np.asarray(segment_offsets, dtype=np.int64),
            segment_samples=_rows(segment_samples, 9),
        )
    os.replace(temporary, path)


def read_viability_audit_capsule(path: Path) -> ViabilityAuditCapsule:
    """Load a capsule without permitting pickled Python objects."""

    with np.load(path, allow_pickle=False) as data:
        schema = str(data["schema"])
        if schema != "touhou-viability-audit-capsule-v1":
            raise ValueError(f"unsupported viability audit schema {schema!r}")
        metadata = json.loads(str(data["metadata"]))
        moving = np.asarray(data["moving"], dtype=np.float64)
        piecewise = np.asarray(data["piecewise"], dtype=np.float64)
        event_offsets = np.asarray(
            data["piecewise_event_offsets"],
            dtype=np.int64,
        )
        events = np.asarray(data["piecewise_events"], dtype=np.float64)
        segment_offsets = np.asarray(
            data["segment_offsets"],
            dtype=np.int64,
        )
        segment_samples = np.asarray(
            data["segment_samples"],
            dtype=np.float64,
        )

    if moving.ndim != 2 or moving.shape[1] != 8:
        raise ValueError("invalid moving-AABB capsule array")
    if piecewise.ndim != 2 or piecewise.shape[1] != 8:
        raise ValueError("invalid piecewise-AABB capsule array")
    if events.ndim != 2 or events.shape[1] != 3:
        raise ValueError("invalid piecewise event capsule array")
    if segment_samples.ndim != 2 or segment_samples.shape[1] != 9:
        raise ValueError("invalid segment sample capsule array")
    if (
        len(event_offsets) != len(piecewise) + 1
        or event_offsets[0] != 0
        or event_offsets[-1] != len(events)
        or np.any(np.diff(event_offsets) < 0)
    ):
        raise ValueError("invalid piecewise event offsets")
    if (
        len(segment_offsets) < 1
        or segment_offsets[0] != 0
        or segment_offsets[-1] != len(segment_samples)
        or np.any(np.diff(segment_offsets) < 0)
    ):
        raise ValueError("invalid segment trajectory offsets")

    aabbs = tuple(
        MovingAabbHazard(
            x=float(row[0]),
            y=float(row[1]),
            velocity_x=float(row[2]),
            velocity_y=float(row[3]),
            half_width=float(row[4]),
            half_height=float(row[5]),
            base_uncertainty=float(row[6]),
            uncertainty_per_frame=float(row[7]),
        )
        for row in moving
    )
    piecewise_aabbs = []
    for index, row in enumerate(piecewise):
        changes = tuple(
            VelocityChange(
                frame=int(change[0]),
                velocity_x=float(change[1]),
                velocity_y=float(change[2]),
            )
            for change in events[event_offsets[index] : event_offsets[index + 1]]
        )
        piecewise_aabbs.append(
            PiecewiseAabbHazard(
                motion=PiecewiseLinearTrajectory(
                    x=float(row[0]),
                    y=float(row[1]),
                    velocity_x=float(row[2]),
                    velocity_y=float(row[3]),
                    changes=changes,
                ),
                half_width=float(row[4]),
                half_height=float(row[5]),
                base_uncertainty=float(row[6]),
                uncertainty_per_frame=float(row[7]),
            )
        )
    segment_trajectories = []
    for start, end in zip(segment_offsets[:-1], segment_offsets[1:]):
        samples = []
        for row in segment_samples[start:end]:
            samples.append(
                SegmentHazard(
                    origin_x=float(row[1]),
                    origin_y=float(row[2]),
                    angle=float(row[3]),
                    tail=float(row[4]),
                    head=float(row[5]),
                    half_width=float(row[6]),
                    base_uncertainty=float(row[7]),
                    uncertainty_per_frame=float(row[8]),
                )
                if row[0] != 0.0
                else None
            )
        segment_trajectories.append(
            SegmentTrajectoryHazard(tuple(samples))
        )
    return ViabilityAuditCapsule(
        metadata=metadata,
        aabbs=aabbs,
        piecewise_aabbs=tuple(piecewise_aabbs),
        segment_trajectories=tuple(segment_trajectories),
    )


def read_viability_audit_metadata(path: Path) -> dict[str, object]:
    """Read only the small policy index payload from a capsule."""

    with np.load(path, allow_pickle=False) as data:
        schema = str(data["schema"])
        if schema != "touhou-viability-audit-capsule-v1":
            raise ValueError(f"unsupported viability audit schema {schema!r}")
        metadata = json.loads(str(data["metadata"]))
    if not isinstance(metadata, dict):
        raise ValueError("viability audit metadata must be an object")
    return metadata


__all__ = [
    "ViabilityAuditCapsule",
    "read_viability_audit_capsule",
    "read_viability_audit_metadata",
    "write_viability_audit_capsule",
]
