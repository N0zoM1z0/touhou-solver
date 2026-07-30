"""Native-ordered TH08 enemy player-shot damage gates.

This module separates the manager/update gates that decide whether a player
shot can reach HP subtraction from geometric overlap and shot damage.  The
result is reusable for ordinary enemies and bosses and deliberately exposes
each native gate instead of collapsing them into one optimistic
``damageable`` flag.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


ENEMY_ACTIVE_FLAG = 0x00000001
ENEMY_HP_SUBTRACTION_FLAG = 0x00000008
ENEMY_PLAYER_SHOT_DAMAGE_FLAG = 0x00000040
ENEMY_DAMAGE_BLOCKING_FLAGS = 0x00000830
ENEMY_PAUSE_DURING_BOMB_OR_TRANSITION_FLAG = 0x40000000
ENEMY_BOMB_DAMAGE_IMMUNITY_FLAG = 0x80000000
ENEMY_FLAGS2_UPDATE_BLOCKED = 0x00000080


@dataclass(frozen=True)
class EnemyPlayerShotDamageContext:
    """Observed state consumed by the native manager/damage gates."""

    flags: int
    flags2: int
    bomb_active: bool
    player_transition_state: int
    damage_tick_due: bool = True
    spell_active: bool = False
    active_spell_owner: bool = False

    def __post_init__(self) -> None:
        if type(self.flags) is not int or not 0 <= self.flags <= 0xFFFFFFFF:
            raise ValueError("enemy flags must fit in one unsigned dword")
        if type(self.flags2) is not int or not 0 <= self.flags2 <= 0xFFFFFFFF:
            raise ValueError("enemy flags2 must fit in one unsigned dword")
        if type(self.bomb_active) is not bool:
            raise ValueError("bomb_active must be Boolean")
        if (
            type(self.player_transition_state) is not int
            or not 0 <= self.player_transition_state <= 0xFF
        ):
            raise ValueError("player transition state must fit in one byte")
        if type(self.damage_tick_due) is not bool:
            raise ValueError("damage_tick_due must be Boolean")
        if type(self.spell_active) is not bool:
            raise ValueError("spell_active must be Boolean")
        if type(self.active_spell_owner) is not bool:
            raise ValueError("active_spell_owner must be Boolean")
        if self.active_spell_owner and not self.spell_active:
            raise ValueError("an active spell owner requires an active spell")


@dataclass(frozen=True)
class EnemyPlayerShotDamageGate:
    """Native gate outcomes before geometric overlap and damage arithmetic."""

    manager_update_open: bool
    damage_block_open: bool
    shot_collision_open: bool
    hp_subtraction_open: bool
    blocked_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.hp_subtraction_open and not self.shot_collision_open:
            raise ValueError("HP subtraction cannot open without shot collision")
        if self.shot_collision_open and not self.damage_block_open:
            raise ValueError("shot collision cannot open outside damage block")
        if self.damage_block_open and not self.manager_update_open:
            raise ValueError("damage block cannot open outside manager update")
        if self.hp_subtraction_open == bool(self.blocked_reasons):
            raise ValueError("open gate and blocked reasons disagree")

    def record(self) -> dict[str, object]:
        return {
            "manager_update_open": self.manager_update_open,
            "damage_block_open": self.damage_block_open,
            "shot_collision_open": self.shot_collision_open,
            "hp_subtraction_open": self.hp_subtraction_open,
            "blocked_reasons": list(self.blocked_reasons),
        }


@dataclass(frozen=True)
class EnemyResolvedDamageContext:
    """Observed/explicit inputs to 0x42D135..0x42D355 damage arithmetic."""

    primary_return_damage: int
    alternate_return_damage: int = 0
    alternate_enabled: bool = False
    bomb_region_overlap: bool = False
    route_id: int = 0
    player_damage_bonus_active: bool = False
    hp_subtraction_open: bool = True
    special_enemy_damage_mode_active: bool = False
    bomb_region_damage_allowed: bool = False
    post_damage_timer_active: bool = False
    post_damage_timer_reduction_enabled: bool = False

    def __post_init__(self) -> None:
        for name in ("primary_return_damage", "alternate_return_damage"):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value <= 0x7FFFFFFF:
                raise ValueError(f"{name} must be a nonnegative signed dword")
        if type(self.route_id) is not int or not 0 <= self.route_id <= 0xFF:
            raise ValueError("route_id must fit in one byte")
        for name in (
            "alternate_enabled",
            "bomb_region_overlap",
            "player_damage_bonus_active",
            "hp_subtraction_open",
            "special_enemy_damage_mode_active",
            "bomb_region_damage_allowed",
            "post_damage_timer_active",
            "post_damage_timer_reduction_enabled",
        ):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be Boolean")


@dataclass(frozen=True)
class EnemyResolvedDamage:
    primary_after_player_bonus: int
    alternate_after_player_bonus: int
    after_alternate_combination: int
    after_frame_cap: int
    hp_damage: int
    blocked_reason: str | None

    def record(self) -> dict[str, object]:
        return {
            "primary_after_player_bonus": self.primary_after_player_bonus,
            "alternate_after_player_bonus": self.alternate_after_player_bonus,
            "after_alternate_combination": self.after_alternate_combination,
            "after_frame_cap": self.after_frame_cap,
            "hp_damage": self.hp_damage,
            "blocked_reason": self.blocked_reason,
        }


def _player_damage_bonus(damage: int, *, active: bool) -> int:
    return damage * 106 // 100 if active and damage else damage


def resolve_enemy_hp_damage(
    context: EnemyResolvedDamageContext,
) -> EnemyResolvedDamage:
    """Resolve shipped positive-damage arithmetic through the final HP write.

    Opaque native predicates are explicit Boolean inputs. This function grants
    arithmetic parity for a fully observed context; it does not infer Boss,
    spell, timer, route, or physical benefit state.
    """

    primary = _player_damage_bonus(
        context.primary_return_damage,
        active=context.player_damage_bonus_active,
    )
    alternate = _player_damage_bonus(
        context.alternate_return_damage,
        active=context.player_damage_bonus_active,
    )
    combined = primary
    if context.alternate_enabled and not context.bomb_region_overlap:
        divisor = 6.5 if context.route_id in (3, 11) else 1.7
        combined = math.trunc(primary + alternate / divisor)
    capped = min(combined, 70)
    blocked_reason = None
    damage = capped
    if damage <= 0:
        blocked_reason = "nonpositive_combined_damage"
        damage = 0
    elif not context.hp_subtraction_open:
        blocked_reason = "hp_subtraction_gate_closed"
        damage = 0
    elif context.special_enemy_damage_mode_active:
        if not context.bomb_region_overlap:
            damage = damage // 7 if damage > 7 else 1
        elif not context.bomb_region_damage_allowed:
            blocked_reason = "bomb_region_damage_blocked"
            damage = 0
        else:
            damage = math.trunc(damage / 2.5) if damage > 2 else 1
    if damage and context.post_damage_timer_active:
        if context.post_damage_timer_reduction_enabled:
            damage //= 9
        else:
            blocked_reason = "post_damage_timer_blocks_damage"
            damage = 0
    return EnemyResolvedDamage(
        primary_after_player_bonus=primary,
        alternate_after_player_bonus=alternate,
        after_alternate_combination=combined,
        after_frame_cap=capped,
        hp_damage=damage,
        blocked_reason=blocked_reason,
    )


def evaluate_enemy_player_shot_damage_gate(
    context: EnemyPlayerShotDamageContext,
) -> EnemyPlayerShotDamageGate:
    """Evaluate the shipped manager-to-HP-write gate in native order.

    This answers only whether an overlapping supported player shot is allowed
    to reach the HP subtraction path.  It does not assert overlap, positive
    damage, spell scaling, a lethal crossing, or an end reason.
    """

    reasons: list[str] = []
    active = bool(context.flags & ENEMY_ACTIVE_FLAG)
    if not active:
        reasons.append("enemy_inactive")

    flags2_open = not context.flags2 & ENEMY_FLAGS2_UPDATE_BLOCKED
    if not flags2_open:
        reasons.append("flags2_update_blocked")

    pause_flag = bool(
        context.flags & ENEMY_PAUSE_DURING_BOMB_OR_TRANSITION_FLAG
    )
    pause_during_bomb = pause_flag and context.bomb_active
    pause_during_transition = (
        pause_flag and context.player_transition_state != 0
    )
    if pause_during_bomb:
        reasons.append("pause_during_bomb")
    if pause_during_transition:
        reasons.append("pause_during_player_transition")

    manager_update_open = bool(
        active
        and flags2_open
        and not pause_during_bomb
        and not pause_during_transition
    )

    blocking = context.flags & ENEMY_DAMAGE_BLOCKING_FLAGS
    if blocking:
        reasons.append(f"damage_blocking_flags_{blocking:#x}")
    bomb_immune = bool(
        context.flags & ENEMY_BOMB_DAMAGE_IMMUNITY_FLAG
        and context.bomb_active
    )
    if bomb_immune:
        reasons.append("bomb_damage_immunity")

    damage_block_open = bool(
        manager_update_open and not blocking and not bomb_immune
    )

    shot_flag = bool(context.flags & ENEMY_PLAYER_SHOT_DAMAGE_FLAG)
    if not shot_flag:
        reasons.append("player_shot_damage_disabled")
    if not context.damage_tick_due:
        reasons.append("player_damage_tick_not_due")
    spell_bomb_blocked = bool(
        context.spell_active
        and context.active_spell_owner
        and context.bomb_active
    )
    if spell_bomb_blocked:
        reasons.append("active_spell_owner_bomb_block")

    shot_collision_open = bool(
        damage_block_open
        and shot_flag
        and context.damage_tick_due
        and not spell_bomb_blocked
    )

    hp_flag = bool(context.flags & ENEMY_HP_SUBTRACTION_FLAG)
    if not hp_flag:
        reasons.append("hp_subtraction_disabled")
    hp_subtraction_open = bool(shot_collision_open and hp_flag)

    # Reasons for later gates remain useful even when an earlier gate blocks.
    # If everything required is open there must be no residual reason.
    if hp_subtraction_open:
        reasons.clear()
    return EnemyPlayerShotDamageGate(
        manager_update_open=manager_update_open,
        damage_block_open=damage_block_open,
        shot_collision_open=shot_collision_open,
        hp_subtraction_open=hp_subtraction_open,
        blocked_reasons=tuple(reasons),
    )


__all__ = [
    "ENEMY_ACTIVE_FLAG",
    "ENEMY_BOMB_DAMAGE_IMMUNITY_FLAG",
    "ENEMY_DAMAGE_BLOCKING_FLAGS",
    "ENEMY_FLAGS2_UPDATE_BLOCKED",
    "ENEMY_HP_SUBTRACTION_FLAG",
    "ENEMY_PAUSE_DURING_BOMB_OR_TRANSITION_FLAG",
    "ENEMY_PLAYER_SHOT_DAMAGE_FLAG",
    "EnemyPlayerShotDamageContext",
    "EnemyPlayerShotDamageGate",
    "EnemyResolvedDamage",
    "EnemyResolvedDamageContext",
    "evaluate_enemy_player_shot_damage_gate",
    "resolve_enemy_hp_damage",
]
