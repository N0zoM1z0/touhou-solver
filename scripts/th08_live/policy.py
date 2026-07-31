"""Immutable policy-query stage for one TH08 live iteration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from th08_corridor_runtime import (
    corridor_safety_value_query,
    corridor_target,
    corridor_viability_query,
)
from touhou_control.policy_guidance import (
    LocalPolicyGuidance,
    assemble_local_policy_guidance,
)


@dataclass(frozen=True)
class PolicyQueryRequest:
    solution: Any | None
    target_frame: int
    query_frame: int
    player_x: float
    player_y: float
    active_action: str
    observed_action: str
    lookahead_frames: int
    max_age_frames: int
    current_delay_frames: tuple[int, ...]


@dataclass(frozen=True)
class PrimaryPolicyQuery:
    target: tuple[float, float, int] | None
    viability_query: Any | None


@dataclass(frozen=True)
class PolicyQuerySnapshot:
    primary: PrimaryPolicyQuery
    safety_value_query: Any | None
    guidance: LocalPolicyGuidance


class PolicyCoordinator:
    """Query one immutable publication and assemble local guidance."""

    def __init__(
        self,
        *,
        target_query: Callable[..., Any] = corridor_target,
        viability_query: Callable[..., Any] = corridor_viability_query,
        safety_value_query: Callable[..., Any] = (
            corridor_safety_value_query
        ),
        guidance_assembler: Callable[..., LocalPolicyGuidance] = (
            assemble_local_policy_guidance
        ),
    ) -> None:
        self._target_query = target_query
        self._viability_query = viability_query
        self._safety_value_query = safety_value_query
        self._guidance_assembler = guidance_assembler

    def query_primary(
        self,
        request: PolicyQueryRequest,
    ) -> PrimaryPolicyQuery:
        target = self._target_query(
            request.solution,
            current_frame=request.target_frame,
            lookahead_frames=request.lookahead_frames,
            max_age_frames=request.max_age_frames,
        )
        viability = self._viability_query(
            request.solution,
            current_frame=request.query_frame,
            player_x=request.player_x,
            player_y=request.player_y,
            active_action=request.active_action,
            max_age_frames=request.max_age_frames,
        )
        return PrimaryPolicyQuery(
            target=target,
            viability_query=viability,
        )

    def complete_query(
        self,
        request: PolicyQueryRequest,
        primary: PrimaryPolicyQuery,
    ) -> PolicyQuerySnapshot:
        safety_value = self._safety_value_query(
            request.solution,
            current_frame=request.query_frame,
            player_x=request.player_x,
            player_y=request.player_y,
            active_action=request.active_action,
            max_age_frames=request.max_age_frames,
        )
        viability_policy = (
            request.solution.plan.viability_policy
            if request.solution is not None
            else None
        )
        guidance = self._guidance_assembler(
            viability_query=primary.viability_query,
            safety_value_query=safety_value,
            policy_delay_frames=(
                viability_policy.delay_frames
                if viability_policy is not None
                else None
            ),
            current_delay_frames=request.current_delay_frames,
        )
        return PolicyQuerySnapshot(
            primary=primary,
            safety_value_query=safety_value,
            guidance=guidance,
        )

    def query(self, request: PolicyQueryRequest) -> PolicyQuerySnapshot:
        """Convenience composition for callers without mid-query work."""

        return self.complete_query(
            request,
            self.query_primary(request),
        )


__all__ = [
    "PolicyCoordinator",
    "PrimaryPolicyQuery",
    "PolicyQueryRequest",
    "PolicyQuerySnapshot",
]
