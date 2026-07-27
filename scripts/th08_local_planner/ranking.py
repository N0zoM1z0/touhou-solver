"""Endpoint ranking policy separated from beam generation and issue commit."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .models import SearchNode


@dataclass(frozen=True)
class EndpointRanker:
    terminal_threats: Mapping[SearchNode, tuple[int, float]]
    survival_actions: frozenset[str]
    safety_value_actions: frozenset[str]
    recovery_by_action: Mapping[str, float]
    repair_by_action: Mapping[str, int]
    recovery_reserve_distance: float
    preloss_reserve_distance: float
    preloss_continuation_preference_active: bool
    item_safety_clearance: float
    horizon: int
    selected_items: tuple[Any, ...]
    target_x: float | None
    target_y: float | None
    target_deadline: int | None
    boundary_control_reserve_deficit: Callable[..., float]
    node_key: Callable[..., tuple[int, float, float, float, float]]
    minimum_travel_frames: Callable[..., float]

    def historical_key(self, node: SearchNode) -> tuple[object, ...]:
        threat_collisions, threat_clearance = self.terminal_threats[node]
        return (
            node.collisions,
            max(-node.min_clearance, 0.0),
            threat_collisions,
            max(-threat_clearance, 0.0),
            (
                0
                if (
                    not self.survival_actions
                    or node.first_action.name in self.survival_actions
                )
                else 1
            ),
            0,
            0.0,
            max(self.item_safety_clearance - threat_clearance, 0.0),
            (
                0
                if (
                    not self.safety_value_actions
                    or node.first_action.name in self.safety_value_actions
                )
                else 1
            ),
            self.boundary_control_reserve_deficit(
                node.x,
                node.y,
                reserve_distance=self.recovery_reserve_distance,
            ),
            self.recovery_by_action.get(
                node.first_action.name,
                math.inf,
            ),
            -self.repair_by_action.get(node.first_action.name, 0),
            self.node_key(
                node,
                step=self.horizon,
                selected_items=self.selected_items,
                target_x=self.target_x,
                target_y=self.target_y,
                target_deadline=self.target_deadline,
            ),
        )

    def selection_key(self, node: SearchNode) -> tuple[object, ...]:
        historical = self.historical_key(node)
        return (
            *historical[:5],
            (
                -self.repair_by_action.get(node.first_action.name, 0)
                if self.preloss_continuation_preference_active
                else 0
            ),
            self.boundary_control_reserve_deficit(
                node.x,
                node.y,
                reserve_distance=self.preloss_reserve_distance,
            ),
            *historical[7:],
        )

    def route_gate_deficit(self, node: SearchNode) -> float:
        if self.target_x is None or self.target_y is None:
            return 0.0
        return max(
            self.minimum_travel_frames(
                node.x,
                node.y,
                self.target_x,
                self.target_y,
            )
            - max(
                (self.target_deadline or 0) - self.horizon,
                0,
            ),
            0.0,
        )
