"""Pure assembly of global-policy outputs for a local controller."""

from __future__ import annotations

from dataclasses import dataclass

from .viability import SafetyValueQuery, ViabilityQuery


@dataclass(frozen=True)
class LocalPolicyGuidance:
    """Validated hard and lexicographic hints for one local decision."""

    support_covers_current: bool
    allowed_first_actions: tuple[str, ...] | None = None
    repair_volumes: tuple[tuple[str, int], ...] = ()
    recovery_distances: tuple[tuple[str, float], ...] = ()
    safety_actions: tuple[str, ...] = ()
    safety_state_value: float | None = None
    survival_actions: tuple[str, ...] = ()
    survival_frames: int | None = None
    survival_bottleneck_margin: float | None = None
    position_error: float = 0.0


def assemble_local_policy_guidance(
    *,
    viability_query: ViabilityQuery | None,
    safety_value_query: SafetyValueQuery | None,
    policy_delay_frames: tuple[int, ...] | None,
    current_delay_frames: tuple[int, ...],
) -> LocalPolicyGuidance:
    """Separate hard viable actions from losing-state fallback labels."""

    support_covers_current = (
        policy_delay_frames is not None
        and set(current_delay_frames).issubset(policy_delay_frames)
    )
    available = (
        viability_query is not None
        and viability_query.available
        and support_covers_current
    )
    winning = bool(
        available
        and viability_query is not None
        and viability_query.state_viable
        and viability_query.safe_actions
    )
    losing = bool(
        available
        and viability_query is not None
        and not viability_query.state_viable
    )
    safety_available = bool(
        losing
        and safety_value_query is not None
        and safety_value_query.available
        and safety_value_query.best_actions
    )
    return LocalPolicyGuidance(
        support_covers_current=support_covers_current,
        allowed_first_actions=(
            viability_query.safe_actions
            if winning and viability_query is not None
            else None
        ),
        repair_volumes=(
            viability_query.repair_volumes
            if available and viability_query is not None
            else ()
        ),
        recovery_distances=(
            viability_query.recovery_distances
            if available and viability_query is not None
            else ()
        ),
        safety_actions=(
            safety_value_query.best_actions
            if safety_available and safety_value_query is not None
            else ()
        ),
        safety_state_value=(
            safety_value_query.state_value
            if safety_available and safety_value_query is not None
            else None
        ),
        survival_actions=(
            viability_query.survival_best_actions
            if (
                losing
                and viability_query is not None
                and viability_query.survival_best_actions
            )
            else ()
        ),
        survival_frames=(
            viability_query.survival_frames
            if losing and viability_query is not None
            else None
        ),
        survival_bottleneck_margin=(
            viability_query.survival_bottleneck_margin
            if losing and viability_query is not None
            else None
        ),
        position_error=(
            viability_query.position_error
            if winning and viability_query is not None
            else 0.0
        ),
    )


__all__ = [
    "LocalPolicyGuidance",
    "assemble_local_policy_guidance",
]
