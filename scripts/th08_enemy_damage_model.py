"""Native-ordered TH08 enemy player-shot damage gates.

This module separates the manager/update gates that decide whether a player
shot can reach HP subtraction from geometric overlap and shot damage.  The
result is reusable for ordinary enemies and bosses and deliberately exposes
each native gate instead of collapsing them into one optimistic
``damageable`` flag.
"""

from __future__ import annotations

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
    "evaluate_enemy_player_shot_damage_gate",
]
