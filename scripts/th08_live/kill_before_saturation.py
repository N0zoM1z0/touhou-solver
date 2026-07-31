"""Default-off ordinary-enemy early-kill observation and action preference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from th08_local_planner import PlannerAction

from .enemy_combat_progress import EnemyCombatProgressInventory
from .models import EnemyBody
from .movement import PLAYFIELD_LEFT, PLAYFIELD_RIGHT


MAXIMUM_TARGET_HP = 22
MAXIMUM_SMALL_ENEMY_HEALTH = 30
MINIMUM_PLAYER_POWER = 100.0
MAXIMUM_HORIZONTAL_SEPARATION = 184.0
MINIMUM_ALIGNMENT_IMPROVEMENT = 0.25


@dataclass(frozen=True, slots=True)
class KillBeforeSaturationTarget:
    """One decision-time ordinary enemy that matches the native winner."""

    slot: int
    enemy_pointer: int
    current_health: int
    maximum_health: int
    x: float
    y: float
    vx: float
    vy: float
    half_width: float
    position_uncertainty: float
    horizontal_separation: float
    vertical_separation: float
    local_damage_flags_open: bool

    def record(self) -> dict[str, int | float | bool]:
        return {
            "slot": self.slot,
            "enemy_pointer": self.enemy_pointer,
            "current_health": self.current_health,
            "maximum_health": self.maximum_health,
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "half_width": self.half_width,
            "position_uncertainty": self.position_uncertainty,
            "horizontal_separation": self.horizontal_separation,
            "vertical_separation": self.vertical_separation,
            "local_damage_flags_open": self.local_damage_flags_open,
        }


@dataclass(frozen=True, slots=True)
class KillBeforeSaturationObservation:
    """Fail-closed target selection result from one coherent prefix blob."""

    target: KillBeforeSaturationTarget | None
    reason: str


@dataclass(frozen=True, slots=True)
class KillBeforeSaturationPreference:
    """One optional action selected inside a winning global safe set."""

    action: str | None
    reason: str
    target_x: float
    planned_endpoint_x: float | None
    preferred_endpoint_x: float | None
    alignment_improvement: float
    forecast_frames: int
    global_safe_action_count: int

    def record(self) -> dict[str, str | int | float | None]:
        return {
            "action": self.action,
            "reason": self.reason,
            "target_x": self.target_x,
            "planned_endpoint_x": self.planned_endpoint_x,
            "preferred_endpoint_x": self.preferred_endpoint_x,
            "alignment_improvement": self.alignment_improvement,
            "forecast_frames": self.forecast_frames,
            "global_safe_action_count": self.global_safe_action_count,
        }


def observe_kill_before_saturation_target(
    *,
    enabled: bool,
    inventory: EnemyCombatProgressInventory | None,
    enemy_bodies: Sequence[EnemyBody],
    player_x: float,
    player_y: float,
    power: float,
    spell_active: bool,
    excluded_enemy_pointer: int = 0,
) -> KillBeforeSaturationObservation:
    """Select an observed ordinary enemy using only current-prefix evidence."""

    if not enabled:
        return KillBeforeSaturationObservation(None, "disabled")
    if spell_active:
        return KillBeforeSaturationObservation(None, "spell_active")
    if power < MINIMUM_PLAYER_POWER:
        return KillBeforeSaturationObservation(None, "power_below_native_root")
    if inventory is None:
        return KillBeforeSaturationObservation(
            None,
            "combat_progress_unavailable",
        )

    bodies_by_pointer = {body.pointer: body for body in enemy_bodies}
    candidates: list[KillBeforeSaturationTarget] = []
    for progress in inventory.observations:
        body = bodies_by_pointer.get(progress.enemy_pointer)
        if body is None:
            continue
        if (
            progress.enemy_pointer == excluded_enemy_pointer
            or progress.defeat_mode != 0
            or progress.current_health <= 0
            or progress.maximum_health <= 0
        ):
            continue
        horizontal_separation = body.x - player_x
        vertical_separation = player_y - body.y
        if vertical_separation <= 0.0:
            continue
        if (
            abs(horizontal_separation)
            > MAXIMUM_HORIZONTAL_SEPARATION + body.half_width
        ):
            continue
        candidates.append(
            KillBeforeSaturationTarget(
                slot=progress.slot,
                enemy_pointer=progress.enemy_pointer,
                current_health=progress.current_health,
                maximum_health=progress.maximum_health,
                x=body.x,
                y=body.y,
                vx=body.vx,
                vy=body.vy,
                half_width=body.half_width,
                position_uncertainty=body.uncertainty,
                horizontal_separation=horizontal_separation,
                vertical_separation=vertical_separation,
                local_damage_flags_open=(
                    progress.local_damage_flags_open
                ),
            )
        )
    if not candidates:
        return KillBeforeSaturationObservation(None, "no_matching_target")
    selected = min(
        candidates,
        key=lambda target: (
            target.maximum_health > MAXIMUM_SMALL_ENEMY_HEALTH,
            abs(target.horizontal_separation),
            target.current_health,
            target.enemy_pointer,
        ),
    )
    return KillBeforeSaturationObservation(
        selected,
        (
            "small_ordinary_enemy_observed"
            if selected.maximum_health <= MAXIMUM_SMALL_ENEMY_HEALTH
            else (
                "low_hp_ordinary_enemy_observed"
                if selected.current_health <= MAXIMUM_TARGET_HP
                else "ordinary_enemy_observed"
            )
        ),
    )


def unfocused_peer_action(
    planned_action: str,
    *,
    actions: Sequence[PlannerAction],
) -> str | None:
    """Return the same-direction unfocused action, if it is representable."""

    action_by_name = {action.name: action for action in actions}
    planned = action_by_name.get(planned_action)
    if planned is None or not planned.focused or planned.direction == 0:
        return None
    return next(
        (
            action.name
            for action in actions
            if (
                action.direction == planned.direction
                and not action.focused
            )
        ),
        None,
    )


def choose_kill_before_saturation_preference(
    planned_action: str,
    *,
    target: KillBeforeSaturationTarget,
    player_x: float,
    action_hold_frames: int,
    target_forecast_frames: int,
    allowed_first_actions: tuple[str, ...] | None,
    actions: Sequence[PlannerAction],
) -> KillBeforeSaturationPreference:
    """Prefer target alignment only before the global kernel is exhausted.

    The returned action is an objective proposal, not safety authority.  The
    issue transaction must still intersect it with fresh local certificates.
    """

    forecast_frames = max(int(target_forecast_frames), 0)
    target_x = min(
        PLAYFIELD_RIGHT,
        max(
            PLAYFIELD_LEFT,
            target.x + target.vx * forecast_frames,
        ),
    )
    safe_action_count = len(allowed_first_actions or ())

    def result(
        action: str | None,
        reason: str,
        *,
        planned_endpoint_x: float | None = None,
        preferred_endpoint_x: float | None = None,
        alignment_improvement: float = 0.0,
    ) -> KillBeforeSaturationPreference:
        return KillBeforeSaturationPreference(
            action=action,
            reason=reason,
            target_x=target_x,
            planned_endpoint_x=planned_endpoint_x,
            preferred_endpoint_x=preferred_endpoint_x,
            alignment_improvement=alignment_improvement,
            forecast_frames=forecast_frames,
            global_safe_action_count=safe_action_count,
        )

    if allowed_first_actions is None or not allowed_first_actions:
        return result(None, "global_viability_unavailable_or_exhausted")
    if action_hold_frames <= 0:
        return result(None, "invalid_action_hold")

    action_by_name = {action.name: action for action in actions}
    planned = action_by_name.get(planned_action)
    if planned is None:
        return result(None, "planned_action_unrepresentable")

    def endpoint_x(action: PlannerAction) -> float:
        return min(
            PLAYFIELD_RIGHT,
            max(
                PLAYFIELD_LEFT,
                player_x + action.dx * action_hold_frames,
            ),
        )

    def vertical_sign(action: PlannerAction) -> int:
        return (action.dy > 0.0) - (action.dy < 0.0)

    planned_endpoint_x = endpoint_x(planned)
    planned_distance = abs(planned_endpoint_x - target_x)
    planned_vertical_sign = vertical_sign(planned)
    allowed = set(allowed_first_actions)
    candidates = tuple(
        action
        for action in actions
        if (
            action.name in allowed
            and vertical_sign(action) == planned_vertical_sign
        )
    )
    if not candidates:
        return result(
            None,
            "no_global_safe_action_preserves_vertical_tendency",
            planned_endpoint_x=planned_endpoint_x,
        )

    preferred = min(
        candidates,
        key=lambda action: (
            abs(endpoint_x(action) - target_x),
            action.focused,
            action.name != planned.name,
            action.name,
        ),
    )
    preferred_endpoint_x = endpoint_x(preferred)
    improvement = (
        planned_distance - abs(preferred_endpoint_x - target_x)
    )
    if (
        preferred.name != planned.name
        and improvement >= MINIMUM_ALIGNMENT_IMPROVEMENT
    ):
        return result(
            preferred.name,
            "global_viable_target_alignment",
            planned_endpoint_x=planned_endpoint_x,
            preferred_endpoint_x=preferred_endpoint_x,
            alignment_improvement=improvement,
        )

    unfocused_peer = unfocused_peer_action(
        planned.name,
        actions=actions,
    )
    if unfocused_peer is not None and unfocused_peer in allowed:
        peer = action_by_name[unfocused_peer]
        peer_endpoint_x = endpoint_x(peer)
        peer_distance = abs(peer_endpoint_x - target_x)
        if peer_distance <= planned_distance + target.half_width:
            return result(
                peer.name,
                "global_viable_same_direction_unfocused",
                planned_endpoint_x=planned_endpoint_x,
                preferred_endpoint_x=peer_endpoint_x,
                alignment_improvement=planned_distance - peer_distance,
            )

    return result(
        None,
        "no_improving_global_safe_early_kill_action",
        planned_endpoint_x=planned_endpoint_x,
        preferred_endpoint_x=preferred_endpoint_x,
        alignment_improvement=improvement,
    )


def choose_upcoming_spawn_preference(
    planned_action: str,
    *,
    spawn_x: float,
    player_x: float,
    action_hold_frames: int,
    allowed_first_actions: tuple[str, ...] | None,
    actions: Sequence[PlannerAction],
) -> KillBeforeSaturationPreference:
    """Pre-position for one causally forecast fixed spawn location."""

    synthetic_target = KillBeforeSaturationTarget(
        slot=-1,
        enemy_pointer=0,
        current_health=1,
        maximum_health=1,
        x=spawn_x,
        y=0.0,
        vx=0.0,
        vy=0.0,
        half_width=0.0,
        position_uncertainty=0.0,
        horizontal_separation=spawn_x - player_x,
        vertical_separation=0.0,
        local_damage_flags_open=False,
    )
    preference = choose_kill_before_saturation_preference(
        planned_action,
        target=synthetic_target,
        player_x=player_x,
        action_hold_frames=action_hold_frames,
        target_forecast_frames=0,
        allowed_first_actions=allowed_first_actions,
        actions=actions,
    )
    if preference.reason == "global_viable_target_alignment":
        return KillBeforeSaturationPreference(
            action=preference.action,
            reason="global_viable_upcoming_spawn_alignment",
            target_x=preference.target_x,
            planned_endpoint_x=preference.planned_endpoint_x,
            preferred_endpoint_x=preference.preferred_endpoint_x,
            alignment_improvement=preference.alignment_improvement,
            forecast_frames=preference.forecast_frames,
            global_safe_action_count=(
                preference.global_safe_action_count
            ),
        )
    if preference.reason == "global_viable_same_direction_unfocused":
        return KillBeforeSaturationPreference(
            action=None,
            reason="no_improving_global_safe_spawn_action",
            target_x=preference.target_x,
            planned_endpoint_x=preference.planned_endpoint_x,
            preferred_endpoint_x=preference.preferred_endpoint_x,
            alignment_improvement=preference.alignment_improvement,
            forecast_frames=preference.forecast_frames,
            global_safe_action_count=(
                preference.global_safe_action_count
            ),
        )
    return preference


__all__ = [
    "KillBeforeSaturationObservation",
    "KillBeforeSaturationPreference",
    "KillBeforeSaturationTarget",
    "MAXIMUM_HORIZONTAL_SEPARATION",
    "MAXIMUM_SMALL_ENEMY_HEALTH",
    "MAXIMUM_TARGET_HP",
    "MINIMUM_ALIGNMENT_IMPROVEMENT",
    "MINIMUM_PLAYER_POWER",
    "choose_kill_before_saturation_preference",
    "choose_upcoming_spawn_preference",
    "observe_kill_before_saturation_target",
    "unfocused_peer_action",
]
