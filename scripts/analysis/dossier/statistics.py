"""Stable statistics used by TH08 run and practice dossiers."""

from __future__ import annotations

import statistics
from typing import Iterable


def percentiles(values: Iterable[float]) -> dict[str, float] | None:
    """Return the dossier's historical median/p95/max convention."""
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    return {
        "median": statistics.median(ordered),
        "p95": ordered[int(0.95 * (len(ordered) - 1))],
        "max": ordered[-1],
    }


def resource_range(
    decisions: list[dict[str, object]],
    key: str,
) -> dict[str, float]:
    """Summarize one required resource field across scoped decisions."""
    values = [float(row["resources"][key]) for row in decisions]
    return {
        "start": values[0],
        "end": values[-1],
        "min": min(values),
        "max": max(values),
    }
