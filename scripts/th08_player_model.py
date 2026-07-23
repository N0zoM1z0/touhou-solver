#!/usr/bin/env python3
"""Recovered TH08 hit-to-bomb transition rules for route ID 2.

This is the resource/state layer of the future solver, not a complete player
emulator.  The formulas come from player_dead_handler (0x0044AB40),
player_deathbomb_or_death_transition (0x0044C650), and the route-2 callback
table at 0x004C7B20.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class BombIndex(IntEnum):
    SAKUYA_NORMAL = 0
    REMILIA_NORMAL = 1
    SAKUYA_LAST_SPELL = 2
    REMILIA_LAST_SPELL = 3
    DISSOLVE_SPELL = 4


@dataclass(frozen=True)
class BombProfile:
    index: BombIndex
    callback_address: int
    display_name: str
    duration_frames: int
    owner: str
    is_last_spell: bool


@dataclass(frozen=True)
class BombDecision:
    profile: BombProfile
    bombs_before: int
    bombs_consumed: int
    bombs_after: int
    forced: bool


ROUTE2_BOMBS = {
    BombIndex.SAKUYA_NORMAL: BombProfile(
        BombIndex.SAKUYA_NORMAL,
        0x0040FCD0,
        '幻符「殺人ドール」',
        290,
        "Sakuya",
        False,
    ),
    BombIndex.REMILIA_NORMAL: BombProfile(
        BombIndex.REMILIA_NORMAL,
        0x0040EE10,
        '紅符「不夜城レッド」',
        290,
        "Remilia",
        False,
    ),
    BombIndex.SAKUYA_LAST_SPELL: BombProfile(
        BombIndex.SAKUYA_LAST_SPELL,
        0x004103F0,
        '幻葬「夜霧の幻影殺人鬼」',
        350,
        "Sakuya",
        True,
    ),
    BombIndex.REMILIA_LAST_SPELL: BombProfile(
        BombIndex.REMILIA_LAST_SPELL,
        0x0040F570,
        '紅魔「スカーレットデビル」',
        320,
        "Remilia",
        True,
    ),
    BombIndex.DISSOLVE_SPELL: BombProfile(
        BombIndex.DISSOLVE_SPELL,
        0x0040D100,
        '「ディゾルブスペル」',
        200,
        "system",
        False,
    ),
}


def predeath_countdown_frames(
    bombs: int,
    *,
    team_meter_left_at_least_right: bool,
    spell_state_active: bool,
    stage_load_index: int,
) -> int:
    """Return the exact counter installed by player_dead_handler.

    The no-bomb branch is always two frames.  With stock, the game derives the
    count from current bombs, meter ordering, spell state, and three stage-load
    indices.  This function intentionally does not rename those two meter
    fields beyond their observed comparison.
    """

    if bombs < 0:
        raise ValueError("bomb stock cannot be negative")
    if bombs == 0:
        return 2

    frames = 6 * bombs
    if team_meter_left_at_least_right:
        frames += 7
    frames = min(frames, 15)
    if spell_state_active:
        frames = min(2 * frames, 30)
    if stage_load_index in (0, 4, 5):
        frames = frames * 9 // 5
    return frames


def route2_bomb_index(*, focused: bool, deathbomb: bool) -> BombIndex:
    """Resolve the route-2 callback index selected by 0x0044C9C7."""

    if not deathbomb:
        return BombIndex.REMILIA_NORMAL if focused else BombIndex.SAKUYA_NORMAL
    # A deathbomb invokes the partner's Last Spell.
    return BombIndex.SAKUYA_LAST_SPELL if focused else BombIndex.REMILIA_LAST_SPELL


def decide_route2_bomb(
    bombs: int,
    *,
    focused: bool,
    deathbomb: bool,
    forced_dissolve: bool = False,
) -> BombDecision:
    """Apply route-2 bomb selection and stock consumption.

    A normal bomb costs one.  A player-triggered Last Spell costs one when only
    one is left and otherwise costs two.  The special automatic dissolve path
    chooses callback 4 without entering the stock-consumption branch.
    """

    if bombs < 0:
        raise ValueError("bomb stock cannot be negative")
    if forced_dissolve:
        profile = ROUTE2_BOMBS[BombIndex.DISSOLVE_SPELL]
        return BombDecision(profile, bombs, 0, bombs, True)
    if bombs == 0:
        raise ValueError("a normal or deathbomb action requires bomb stock")

    index = route2_bomb_index(focused=focused, deathbomb=deathbomb)
    cost = min(bombs, 2) if deathbomb else 1
    return BombDecision(ROUTE2_BOMBS[index], bombs, cost, bombs - cost, False)
