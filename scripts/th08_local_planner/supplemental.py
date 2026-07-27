"""Lookup-only consumption of completed exact-version supplemental work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import PlannerAction, SearchNode


@dataclass(frozen=True)
class CompletedSupplementalLookup:
    status: str
    completed: bool
    historical_fallback: bool
    background_compute_ms: float | None
    terminal_labels: tuple[tuple[int, float], ...] | None
    beam: tuple[SearchNode, ...]


def lookup_completed_supplemental(
    *,
    service: Any,
    identity: tuple[object, ...],
    actions: tuple[PlannerAction, ...],
) -> CompletedSupplementalLookup:
    """Perform one nonblocking exact-version lookup; never submit or wait."""

    publication = service.lookup(identity)
    if publication is None:
        return CompletedSupplementalLookup(
            status="async_miss",
            completed=False,
            historical_fallback=True,
            background_compute_ms=None,
            terminal_labels=None,
            beam=(),
        )
    return CompletedSupplementalLookup(
        status="async_hit",
        completed=True,
        historical_fallback=False,
        background_compute_ms=publication.compute_ms,
        terminal_labels=publication.terminal_threats,
        beam=tuple(
            SearchNode(
                x=node.x,
                y=node.y,
                first_action=actions[node.first_action],
                last_action=actions[node.last_action],
                risk=node.risk,
                collisions=node.collisions,
                min_clearance=node.min_clearance,
                immediate_clearance=node.immediate_clearance,
                collected_mask=0,
                item_utility=0.0,
            )
            for node in publication.nodes
        ),
    )
