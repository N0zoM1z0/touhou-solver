"""TH08 enemy contact and shot-damage gates conditioned on player mode."""

from __future__ import annotations

from dataclasses import dataclass

from th08_option_model import Route2FocusState

ENEMY_ACTIVE_FLAG = 0x00000001
ENEMY_CONTACT_ENABLED_FLAG = 0x00000004
ENEMY_MANAGER_BLOCKING_FLAGS = 0x00000830
ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG = 0x00000040
ENEMY_SECONDARY_CHARACTER_SYNC_FLAG = 0x00000100
ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG = 0x00000800


@dataclass(frozen=True)
class EnemyModeProjection:
    """One enemy's native flag gates after the priority-11 mode sync."""

    raw_flags: int
    projected_flags: int
    secondary_character_synchronized: bool
    manager_gate_open: bool
    contact_eligible: bool
    player_shot_damage_eligible: bool


def route2_enemy_mode_state_key(
    state: Route2FocusState,
) -> tuple[int, bool, int]:
    """Return the player fields that determine all future enemy-mode gates.

    Option positions and timers do not affect the enemy bit-0x800 sync.  The
    exact focus byte is retained because the native initializer's value 2 and
    the steady focused value 1 have different next-update behavior.
    """

    return (
        state.focus_logic_value,
        state.remilia_character_active,
        state.transition_counter,
    )


def project_enemy_mode(
    flags: int,
    *,
    secondary_character_active: bool,
) -> EnemyModeProjection:
    """Apply the shipped player-mode sync and separate the two native gates.

    The enemy manager calls the sync helper only for active enemies carrying
    bit 0x100.  That helper mirrors ``player[+5] & 1`` into enemy bit 0x800.
    The later manager gate excludes 0x10, 0x20, and 0x800 before evaluating
    contact bit 0x04 and player-shot-damage bit 0x40 independently.
    """

    if not 0 <= flags <= 0xFFFFFFFF:
        raise ValueError("enemy flags must fit in one unsigned 32-bit word")

    synchronized = bool(
        flags & ENEMY_ACTIVE_FLAG
        and flags & ENEMY_SECONDARY_CHARACTER_SYNC_FLAG
    )
    projected = flags
    if synchronized:
        if secondary_character_active:
            projected |= ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG
        else:
            projected &= ~ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG

    manager_gate_open = bool(
        projected & ENEMY_ACTIVE_FLAG
        and not projected & ENEMY_MANAGER_BLOCKING_FLAGS
    )
    return EnemyModeProjection(
        raw_flags=flags,
        projected_flags=projected,
        secondary_character_synchronized=synchronized,
        manager_gate_open=manager_gate_open,
        contact_eligible=bool(
            manager_gate_open
            and projected & ENEMY_CONTACT_ENABLED_FLAG
        ),
        player_shot_damage_eligible=bool(
            manager_gate_open
            and projected & ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG
        ),
    )


def project_route2_enemy_mode(
    flags: int,
    *,
    focus_state: Route2FocusState,
) -> EnemyModeProjection:
    """Project one enemy against the current route-2 delayed character byte."""

    return project_enemy_mode(
        flags,
        secondary_character_active=focus_state.remilia_character_active,
    )


__all__ = [
    "ENEMY_ACTIVE_FLAG",
    "ENEMY_CONTACT_ENABLED_FLAG",
    "ENEMY_MANAGER_BLOCKING_FLAGS",
    "ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG",
    "ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG",
    "ENEMY_SECONDARY_CHARACTER_SYNC_FLAG",
    "EnemyModeProjection",
    "project_enemy_mode",
    "project_route2_enemy_mode",
    "route2_enemy_mode_state_key",
]
