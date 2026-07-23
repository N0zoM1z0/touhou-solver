#!/usr/bin/env python3
"""Observed solver-critical TH08 per-frame update order.

The native callback list inserts by ascending priority and preserves
registration order for equal priorities.  This adapter intentionally records
only phases relevant to deterministic gameplay modeling; omitted presentation
callbacks must not be treated as proof that the full engine list is complete.
"""

from __future__ import annotations

from dataclasses import dataclass

from frame_schedule import FrameEvent, FramePhase, FrameSchedule


LIVE = "live"
RECORD = "record"
PLAYBACK_LEGACY = "playback_legacy"
PLAYBACK_EXTENDED = "playback_extended"
PLAYBACK_MODES = frozenset({PLAYBACK_LEGACY, PLAYBACK_EXTENDED})


def _event(
    key: str,
    address: int | None = None,
    *,
    solver_relevant: bool = True,
    detail: str = "",
) -> FrameEvent:
    return FrameEvent(
        key,
        source_address=address,
        solver_relevant=solver_relevant,
        detail=detail,
    )


TH08_FRAME_SCHEDULE = FrameSchedule(
    (
        FramePhase(
            "gameplay_controller",
            2,
            0,
            (_event("gameplay_controller_update", 0x439BC7),),
            source_address=0x439BC7,
        ),
        FramePhase(
            "replay_input_legacy",
            6,
            0,
            (_event("replay_publish_input", 0x452550),),
            source_address=0x452550,
            modes=frozenset({PLAYBACK_LEGACY}),
        ),
        FramePhase(
            "replay_input_extended",
            6,
            0,
            (_event("replay_publish_input", 0x4526C0),),
            source_address=0x4526C0,
            modes=frozenset({PLAYBACK_EXTENDED}),
        ),
        FramePhase(
            "replay_rng_sync",
            7,
            0,
            (_event("replay_rng_sync", 0x4522A0),),
            source_address=0x4522A0,
            modes=frozenset({RECORD, *PLAYBACK_MODES}),
        ),
        FramePhase(
            "stage_background",
            8,
            0,
            (
                _event(
                    "stage_background_update",
                    0x407400,
                    solver_relevant=False,
                ),
            ),
            source_address=0x407400,
        ),
        FramePhase(
            "player",
            9,
            0,
            (
                _event("player_projectile_pool_update", 0x44C5B0),
                _event("player_deathbomb_or_death_transition", 0x44C650),
                _event("player_respawn_and_auxiliary_state", 0x44C48A),
                _event("player_input_movement", 0x44AEC0),
                _event(
                    "player_animation_update",
                    0x45EA00,
                    solver_relevant=False,
                ),
                _event("player_active_shot_update", 0x451150),
                _event("player_shot_cadence_update", 0x451500),
                _event("player_final_state_counters", 0x44C4F5),
            ),
            source_address=0x44C390,
        ),
        FramePhase(
            "enemy_manager",
            11,
            0,
            (
                _event("stage_timeline_step", 0x42A8A0),
                _event(
                    "enemy_vm_motion_and_player_shot_damage",
                    0x42C660,
                    detail=(
                        "Per-enemy region containing ECL VM, motion/state, "
                        "and player-shot damage handling."
                    ),
                ),
            ),
            source_address=0x42C660,
        ),
        FramePhase(
            "spell_card_manager",
            12,
            0,
            (_event("spell_card_manager_update", 0x418010),),
            source_address=0x418010,
        ),
        FramePhase(
            "effect_system_427bf0",
            13,
            0,
            (
                _event(
                    "effect_system_427bf0_update",
                    0x427BF0,
                    solver_relevant=False,
                    detail="Registered role is observed; domain name remains unknown.",
                ),
            ),
            source_address=0x427BF0,
            confidence="unknown",
        ),
        FramePhase(
            "bullet_manager",
            14,
            0,
            (
                _event("item_manager_update", 0x440500),
                _event("bullet_spatial_buckets_clear", 0x4321B0),
                _event(
                    "hostile_bullet_transform_motion_collision_graze",
                    0x4312A2,
                ),
                _event("laser_motion_collision_graze", 0x431B7A),
                _event("bullet_manager_final_timers", 0x431FE0),
            ),
            source_address=0x431240,
        ),
        FramePhase(
            "replay_record_input",
            17,
            0,
            (_event("replay_capture_input", 0x452310),),
            source_address=0x452310,
            modes=frozenset({RECORD}),
        ),
        FramePhase(
            "replay_playback_post",
            18,
            0,
            (
                _event(
                    "replay_playback_post_update",
                    0x452490,
                    solver_relevant=False,
                ),
            ),
            source_address=0x452490,
            modes=PLAYBACK_MODES,
        ),
    )
)


@dataclass(frozen=True)
class SameFrameImplication:
    earlier_event: str
    later_event: str
    implication: str
    confidence: str = "inferred_from_static_order"


SAME_FRAME_IMPLICATIONS = (
    SameFrameImplication(
        "replay_publish_input",
        "player_input_movement",
        "Playback input is visible to player movement in the same update.",
    ),
    SameFrameImplication(
        "player_input_movement",
        "item_manager_update",
        "Item attraction/collection tests the player's post-movement position.",
    ),
    SameFrameImplication(
        "player_deathbomb_or_death_transition",
        "hostile_bullet_transform_motion_collision_graze",
        (
            "A hostile-bullet hit created by the later projectile pass can first "
            "reach deathbomb processing on the following update."
        ),
    ),
    SameFrameImplication(
        "enemy_vm_motion_and_player_shot_damage",
        "hostile_bullet_transform_motion_collision_graze",
        "An enemy-created active bullet is eligible for bullet processing that frame.",
    ),
    SameFrameImplication(
        "item_manager_update",
        "hostile_bullet_transform_motion_collision_graze",
        "An item created later by bullet cancellation waits for the next item pass.",
    ),
)


def ordered_update_phases(mode: str = LIVE) -> tuple[FramePhase, ...]:
    return TH08_FRAME_SCHEDULE.phases_for(mode)


def solver_event_order(mode: str = LIVE) -> tuple[str, ...]:
    return tuple(
        event.key for event in TH08_FRAME_SCHEDULE.events_for(mode, solver_only=True)
    )
