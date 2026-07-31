"""Default-off ordinary-enemy early-kill observation and action preference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from th08_local_planner import PlannerAction

from .enemy_combat_progress import EnemyCombatProgressInventory
from .models import EnemyBody


MAXIMUM_TARGET_HP = 22
MINIMUM_PLAYER_POWER = 100.0
MAXIMUM_HORIZONTAL_SEPARATION = 96.0


@dataclass(frozen=True, slots=True)
class KillBeforeSaturationTarget:
    """One decision-time ordinary enemy that matches the native winner."""

    slot: int
    enemy_pointer: int
    current_health: int
    maximum_health: int
    x: float
    y: float
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
            "horizontal_separation": self.horizontal_separation,
            "vertical_separation": self.vertical_separation,
            "local_damage_flags_open": self.local_damage_flags_open,
        }


@dataclass(frozen=True, slots=True)
class KillBeforeSaturationObservation:
    """Fail-closed target selection result from one coherent prefix blob."""

    target: KillBeforeSaturationTarget | None
    reason: str


def observe_kill_before_saturation_target(
    *,
    enabled: bool,
    inventory: EnemyCombatProgressInventory | None,
    enemy_bodies: Sequence[EnemyBody],
    player_x: float,
    player_y: float,
    power: float,
    spell_active: bool,
) -> KillBeforeSaturationObservation:
    """Select a low-HP ordinary enemy using only current-prefix evidence."""

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
            progress.defeat_mode != 0
            or progress.current_health <= 0
            or progress.current_health > MAXIMUM_TARGET_HP
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
                horizontal_separation=horizontal_separation,
                vertical_separation=vertical_separation,
                local_damage_flags_open=(
                    progress.local_damage_flags_open
                ),
            )
        )
    if not candidates:
        return KillBeforeSaturationObservation(None, "no_matching_target")
    return KillBeforeSaturationObservation(
        min(
            candidates,
            key=lambda target: (
                target.current_health,
                abs(target.horizontal_separation),
                target.enemy_pointer,
            ),
        ),
        "low_hp_ordinary_enemy_observed",
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


__all__ = [
    "KillBeforeSaturationObservation",
    "KillBeforeSaturationTarget",
    "MAXIMUM_HORIZONTAL_SEPARATION",
    "MAXIMUM_TARGET_HP",
    "MINIMUM_PLAYER_POWER",
    "observe_kill_before_saturation_target",
    "unfocused_peer_action",
]
