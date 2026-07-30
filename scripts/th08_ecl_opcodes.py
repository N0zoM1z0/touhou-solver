#!/usr/bin/env python3
"""Recovered TH08 enemy-ECL opcode catalog.

Names in this module are local analysis names, not names imported from another
project.  Confidence is deliberately explicit:

* observed: the VM's concrete state mutation/call establishes the behavior;
* inferred: the behavior is observed but the domain-facing noun is provisional;
* unknown: the shipped corpus or static analysis does not yet establish meaning.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class OpcodeSpec:
    opcode: int
    name: str
    category: str
    confidence: str
    description: str

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


def _spec(
    opcode: int,
    name: str,
    category: str,
    confidence: str,
    description: str,
) -> OpcodeSpec:
    return OpcodeSpec(opcode, name, category, confidence, description)


# The switch implementation is enemy_ecl_vm_step (0x004184B0).  The catalog
# covers the whole accepted opcode range; entries absent below are exposed as
# unknown/reserved by opcode_spec() instead of being silently assigned meaning.
_KNOWN = {
    0x00: ("nop", "control", "observed", "No state mutation in the VM switch."),
    0x01: ("terminate", "control", "observed", "Terminate this enemy ECL VM."),
    0x02: ("reset_timer", "control", "observed", "Reset the current VM timer, optionally from an integer VM value."),
    0x03: ("nop_with_argument", "control", "observed", "Accepted by the VM default path without a state mutation; shipped records carry one argument."),
    0x04: ("jump", "control", "observed", "Set VM time and apply a relative instruction-pointer displacement."),
    0x05: ("loop_decrement_jump", "control", "observed", "Decrement an integer lvalue and jump while the supplied test remains positive."),
    0x06: ("set_int", "arithmetic", "observed", "Assign an integer VM lvalue."),
    0x07: ("set_float", "arithmetic", "observed", "Assign a float VM lvalue."),
    0x08: ("set_int_random_sign", "arithmetic", "observed", "Assign value multiplied by a random sign."),
    0x09: ("set_float_random_sign", "arithmetic", "observed", "Assign value multiplied by a random sign."),
    0x0A: ("add_int", "arithmetic", "observed", "Add to an integer lvalue."),
    0x0B: ("sub_int", "arithmetic", "observed", "Subtract from an integer lvalue."),
    0x0C: ("mul_int", "arithmetic", "observed", "Multiply an integer lvalue."),
    0x0D: ("div_int", "arithmetic", "observed", "Divide an integer lvalue."),
    0x0E: ("mod_int", "arithmetic", "observed", "Apply integer remainder to an lvalue."),
    0x0F: ("add_float", "arithmetic", "observed", "Add to a float lvalue."),
    0x10: ("sub_float", "arithmetic", "observed", "Subtract from a float lvalue."),
    0x11: ("mul_float", "arithmetic", "observed", "Multiply a float lvalue."),
    0x12: ("div_float", "arithmetic", "observed", "Divide a float lvalue."),
    0x13: ("random_float", "arithmetic", "observed", "Assign the result of the VM random-range helper."),
    0x14: ("set_int_add", "arithmetic", "observed", "Assign integer a + b."),
    0x15: ("set_int_sub", "arithmetic", "observed", "Assign integer a - b."),
    0x16: ("set_int_mul", "arithmetic", "observed", "Assign integer a * b."),
    0x17: ("set_int_div", "arithmetic", "observed", "Assign integer a / b."),
    0x18: ("set_int_mod", "arithmetic", "observed", "Assign integer a % b."),
    0x19: ("set_float_add", "arithmetic", "observed", "Assign float a + b."),
    0x1A: ("set_float_sub", "arithmetic", "observed", "Assign float a - b."),
    0x1B: ("set_float_mul", "arithmetic", "observed", "Assign float a * b."),
    0x1C: ("set_float_div", "arithmetic", "observed", "Assign float a / b."),
    0x1D: ("set_float_random", "arithmetic", "observed", "Assign a random-range result from two float operands."),
    0x1E: ("increment_int", "arithmetic", "observed", "Increment an integer lvalue."),
    0x1F: ("decrement_int", "arithmetic", "observed", "Decrement an integer lvalue."),
    0x20: ("set_sin", "math", "observed", "Assign sine of a float operand."),
    0x21: ("set_cos", "math", "observed", "Assign cosine of a float operand."),
    0x22: ("set_angle_between_points", "math", "observed", "Assign atan2-derived angle between two points."),
    0x23: ("set_int_compare", "math", "inferred", "Evaluate an integer comparison helper and store its result."),
    0x24: ("set_float_compare", "math", "inferred", "Evaluate a float comparison helper and store its result."),
    0x25: ("normalize_angle", "math", "observed", "Normalize an angle with the engine angle helper."),
    0x26: ("set_vector_from_polar", "math", "observed", "Write two float lvalues from angle and magnitude."),
    0x27: ("set_distance", "math", "observed", "Assign Euclidean distance between two points."),
    0x28: ("jump_int_eq", "control", "observed", "Conditional relative jump: integer equal."),
    0x29: ("jump_float_eq", "control", "observed", "Conditional relative jump: float equal."),
    0x2A: ("jump_int_ne", "control", "observed", "Conditional relative jump: integer not equal."),
    0x2B: ("jump_float_ne", "control", "observed", "Conditional relative jump: float not equal."),
    0x2C: ("jump_int_lt", "control", "observed", "Conditional relative jump: integer less than."),
    0x2D: ("jump_float_lt", "control", "observed", "Conditional relative jump: float less than."),
    0x2E: ("jump_int_le", "control", "observed", "Conditional relative jump: integer less than or equal."),
    0x2F: ("jump_float_le", "control", "observed", "Conditional relative jump: float less than or equal."),
    0x30: ("jump_int_gt", "control", "observed", "Conditional relative jump: integer greater than."),
    0x31: ("jump_float_gt", "control", "observed", "Conditional relative jump: float greater than."),
    0x32: ("jump_int_ge", "control", "observed", "Conditional relative jump: integer greater than or equal."),
    0x33: ("jump_float_ge", "control", "observed", "Conditional relative jump: float greater than or equal."),
    0x34: ("call_subroutine", "control", "observed", "Call an ECL subroutine using the 16-entry VM context stack."),
    0x35: ("return_subroutine", "control", "observed", "Restore the caller VM context or terminate at stack bottom."),
    0x36: ("set_primary_animation", "animation", "inferred", "Set a primary enemy animation and clear animation mode bit 0x4."),
    0x37: ("set_primary_animation_sequence", "animation", "inferred", "Install six consecutive primary animation IDs."),
    0x38: ("set_primary_animation_set", "animation", "inferred", "Install six explicit primary animation IDs."),
    0x39: ("set_secondary_animation", "animation", "inferred", "Apply the secondary animation helper."),
    0x3A: ("set_primary_animation_mode", "animation", "inferred", "Set a primary animation and set animation mode bit 0x4."),
    0x3B: ("set_primary_animation_sequence_mode", "animation", "inferred", "Install six consecutive animation IDs and set mode bit 0x4."),
    0x3C: ("set_primary_animation_set_mode", "animation", "inferred", "Install six explicit animation IDs and set mode bit 0x4."),
    0x3D: ("set_secondary_animation_mode", "animation", "inferred", "Apply secondary animation and set mode bit 0x4."),
    0x3E: ("restore_primary_animation", "animation", "inferred", "Restore the saved primary animation ID."),
    0x3F: ("set_position", "movement", "observed", "Set enemy x/y position, clear z, then refresh derived position state."),
    0x40: ("move_to", "movement", "inferred", "Configure timed interpolation from the current position to a target."),
    0x41: ("set_velocity_polar", "movement", "inferred", "Set absolute movement angle and speed."),
    0x42: ("set_velocity_polar_timed", "movement", "inferred", "Set or interpolate absolute movement from duration, mode, angle and speed."),
    0x43: ("set_bounded_random_velocity", "movement", "inferred", "Choose a random direction and reflect it away from configured movement bounds."),
    0x44: ("set_velocity_aimed", "movement", "observed", "Set speed and angle aimed at the player."),
    0x45: ("set_velocity_aimed_timed", "movement", "inferred", "Set or interpolate player-aimed movement."),
    0x46: ("set_angular_velocity", "movement", "inferred", "Set movement angular-velocity field."),
    0x47: ("set_speed_acceleration", "movement", "inferred", "Set movement speed-acceleration field."),
    0x48: ("move_to_explicit", "movement", "inferred", "Configure timed interpolation with explicit start/target motion fields."),
    0x49: ("move_from_current", "movement", "inferred", "Configure timed interpolation beginning at current position."),
    0x4A: ("set_motion_interpolation", "movement", "inferred", "Configure timed motion interpolation parameters."),
    0x4B: ("set_movement_bounds", "movement", "observed", "Set left/top/right/bottom bounds and enable bounded movement."),
    0x4C: ("clear_movement_bounds", "movement", "observed", "Disable bounded movement."),
    0x4D: ("set_hitbox", "enemy", "inferred", "Set the first enemy collision extent pair."),
    0x4E: ("set_hurtbox", "enemy", "inferred", "Set the second enemy collision extent pair."),
    0x4F: ("set_enemy_flags", "enemy", "observed", "Assign a six-bit group of enemy behavior flags."),
    0x50: ("clear_enemy_flags", "enemy", "observed", "Clear selected enemy behavior flags."),
    0x51: ("set_enemy_flags_mask", "enemy", "observed", "Set selected enemy behavior flags."),
    0x52: ("set_minimum_fire_distance", "bullet", "observed", "Store squared radius inside which direct fire is suppressed."),
    0x53: ("set_boss_flag", "boss", "observed", "Assign the enemy boss flag. Its consumers drive boss-health UI and marker publication, boss damage scaling/position tracking, and boss-defeat projectile/enemy cleanup."),
    0x56: ("copy_enemy_int", "enemy", "inferred", "Copy an integer VM value from an indexed enemy slot."),
    0x57: ("copy_enemy_float", "enemy", "inferred", "Copy a float VM value associated with an indexed enemy slot."),
    0x58: ("call_subroutine_with_enemy", "control", "inferred", "Call a subroutine after resolving an indexed enemy."),
    0x59: ("set_enemy_animation_index", "animation", "inferred", "Set the saved animation ID on an indexed enemy."),
    0x5A: ("spawn_child_enemy", "enemy", "inferred", "Spawn/link a child enemy using the first spawn helper."),
    0x5B: ("spawn_child_enemy_variant", "enemy", "inferred", "Spawn/link a child enemy using the alternate spawn helper."),
    0x5C: ("spawn_child_enemy_relative", "enemy", "inferred", "Spawn/link a child enemy relative to the parent position."),
    0x5D: ("spawn_enemy_from_vm_position", "enemy", "inferred", "Spawn an enemy through the timeline spawn primitive at an explicit position."),
    0x5E: ("spawn_enemy_from_vm_offset", "enemy", "inferred", "Spawn an enemy through the timeline primitive at current position plus offset."),
    0x5F: ("zero_eligible_enemy_hp_with_score_items", "enemy", "observed", "Set current HP to zero for every eligible active non-boss enemy, unlink its parent relation, start its configured end subroutine, and spawn type-6 scaled-score items for enemies carrying reward flag 0x80; active-bit retirement is deferred to later manager processing."),
    0x69: ("set_fire_delay", "bullet", "observed", "Set rank-adjusted fire delay and reset its timer."),
    0x6A: ("set_fire_delay_random_phase", "bullet", "observed", "Set rank-adjusted fire delay and randomize the initial timer phase."),
    0x6B: ("enable_deferred_fire", "bullet", "observed", "Queue the next direct-fire instruction instead of emitting immediately."),
    0x6C: ("disable_deferred_fire", "bullet", "observed", "Disable deferred direct-fire mode."),
    0x6D: ("emit_current_pattern", "bullet", "observed", "Emit the current bullet descriptor at the current emission origin."),
    0x6E: ("set_emission_offset", "bullet", "observed", "Set x/y emission-origin offset and clear z."),
    0x6F: ("define_bullet_transform", "bullet_transform", "observed", "Write one 24-byte record in the 18-entry bullet-transform program."),
    0x70: ("clear_bullets_global", "bullet", "inferred", "Invoke the global bullet clear/cancel helper."),
    0x71: ("configure_bullet_sounds", "bullet", "observed", "Set/disable the spatialized pattern-emission sound ID and set the per-bullet transform-activation sound ID."),
    0x72: ("spawn_laser_absolute", "laser", "observed", "Create a laser whose supplied angle is absolute."),
    0x73: ("spawn_laser_aimed", "laser", "observed", "Create a laser whose supplied angle is relative to player aim."),
    0x74: ("select_laser_handle", "laser", "observed", "Select one of the enemy's 32 laser handles."),
    0x75: ("add_laser_angle", "laser", "observed", "Add and normalize an angle on a selected laser handle."),
    0x76: ("aim_laser_at_player", "laser", "observed", "Set selected laser angle to player aim plus offset."),
    0x77: ("set_laser_origin", "laser", "observed", "Set selected laser origin to enemy position plus x/y/z offset."),
    0x78: ("query_laser_active", "laser", "observed", "Write selected laser allocation/active state to VM result field."),
    0x79: ("fade_laser", "laser", "observed", "Force selected laser into fade phase."),
    0x7A: ("start_spell_card", "spell", "observed", "Start a spell card from a 232-byte payload containing its ID, score, XOR-encoded name, owner, and two description lines."),
    0x7B: ("finish_spell_card", "spell", "observed", "Finish the active spell card and run capture/failure bookkeeping."),
    0x7C: ("play_sound_at_enemy", "audio", "inferred", "Play a sound/effect ID spatialized at enemy x."),
    0x7D: ("invoke_interrupt_slot", "control", "observed", "Save the current ECL VM frame and start the subroutine installed in the selected interrupt slot."),
    0x7E: ("set_interrupt_slot", "control", "observed", "Install an ECL subroutine ID into an indexed interrupt slot."),
    0x7F: ("set_boss_slot", "boss", "inferred", "Register/unregister this enemy in one of four boss slots."),
    0x80: ("spawn_enemy_effect", "effect", "inferred", "Allocate and attach an effect instance to the enemy."),
    0x81: ("set_enemy_defeat_mode", "enemy", "observed", "Set the three-bit mode dispatched when enemy health reaches zero. Shipped values 0..3 select distinct deactivation, cleanup, phase, score, effect, and player-state consequences."),
    0x82: ("set_enemy_end_subroutine", "control", "observed", "Set the ECL subroutine started by enemy-manager cleanup when the current enemy or phase ends."),
    0x83: ("set_health", "boss", "observed", "Set current, maximum, and phase health to one integer value."),
    0x84: ("set_timer_current", "boss", "observed", "Set the phase timer's elapsed value from one evaluated integer operand."),
    0x85: ("set_health_phase_transition", "boss", "observed", "Set indexed health threshold and, unless the special engine-mode gate suppresses the write, its successor ECL subroutine."),
    0x86: ("set_timeout_phase_transition", "boss", "observed", "Set timeout frame, conditionally set its successor ECL subroutine under the engine-mode gate, and reset the phase timer."),
    0x87: ("start_interrupt_subroutine", "control", "observed", "Replace an indexed auxiliary VM context and start a subroutine in it."),
    0x88: ("invoke_enemy_callback", "enemy", "observed", "Invoke an indexed built-in callback from the 32-entry table referenced at 0x41D4F4."),
    0x89: ("set_enemy_callback", "enemy", "observed", "Install or clear an indexed built-in per-frame enemy callback from the same 32-entry table."),
    0x8A: ("set_enemy_bytes", "enemy", "unknown", "Set three adjacent enemy state bytes at +0x3310..+0x3312."),
    0x8B: ("spawn_effect", "effect", "inferred", "Spawn one or more typed effect-manager objects at enemy position."),
    0x8C: ("spawn_effect_with_vector", "effect", "inferred", "Spawn typed effect objects with an additional vector."),
    0x8D: ("spawn_item", "item", "observed", "Spawn one item of the supplied type at enemy position."),
    0x8E: ("spawn_item_bundle", "item", "inferred", "Spawn a randomized item bundle, with type depending on collection state."),
    0x8F: ("set_drop_type", "item", "inferred", "Set a single enemy drop-type field."),
    0x90: ("set_drop_counts", "item", "inferred", "Set two enemy drop-count/type fields consumed on death."),
    0x91: ("enable_enemy_animation_script_refresh", "animation", "observed", "Assign the flag that reapplies saved ANM script IDs to the main enemy animation and trail nodes in the render callback; every shipped use enables it."),
    0x92: ("set_global_vm_value", "global", "unknown", "Pass an integer value to helper 0x41FDF0."),
    0x93: ("write_unreferenced_global_4ea290", "validation", "observed", "Assign global dword 0x004EA290. Static xrefs contain this writer and no direct reader, so it is excluded from solver state pending a runtime watchpoint."),
    0x94: ("start_spell_phase", "boss", "inferred", "Call spell/phase helper 0x423130 and add 1800 frames to stage counter."),
    0x95: ("set_enemy_short_020a", "enemy", "unknown", "Set enemy field +0x020A."),
    0x96: ("set_enemy_object_short", "enemy", "unknown", "Set an indexed short in an enemy-owned 676-byte object array."),
    0x97: ("set_enemy_flag_04000000", "enemy", "unknown", "Assign enemy flag bit 0x04000000."),
    0x98: ("set_rank_interpolation", "difficulty", "observed", "Set float and integer endpoints used to scale bullet count/speed by rank."),
    0x99: ("copy_enemy_end_to_timeout_subroutine", "control", "observed", "Copy the signed enemy-end subroutine ID to the timeout-transition subroutine field and reset the phase timer."),
    0x9A: ("clear_laser_handles", "laser", "observed", "Clear all 32 laser handle pointers owned by this enemy."),
    0x9B: ("set_fixed_spell_reward_mode", "spell", "observed", "Assign the mode that initializes spell reward to 99,999,990, disables its per-frame decay, and uses capture-result field 700; every shipped use enables it."),
    0x9C: ("set_enemy_flag_00000080", "enemy", "unknown", "Assign enemy flag bit 0x80 and state byte 2."),
    0x9D: ("configure_enemy_trail", "enemy", "observed", "Set trail mode, position-history length, historical-collision limit, and render stride. Shipped collision limits are all zero, so shipped uses affect presentation only."),
    0x9E: ("set_boss_health_segment", "boss", "observed", "Publish normalized boss-health segment bounds and segment metadata."),
    0x9F: ("set_enemy_render_layer", "animation", "observed", "Select one of four enemy render-list layers consumed by the early (0/1) and late (2/3) render passes."),
    0xA0: ("set_timer_current_alt", "boss", "inferred", "Reset/set the same timer helper used by phase control."),
    0xA1: ("cancel_bullets_in_radius", "bullet", "inferred", "Invoke radial bullet cancel/conversion helper at enemy position."),
    0xA2: ("cancel_all_bullets", "bullet", "inferred", "Invoke global bullet cancel helper with mode 4."),
    0xA3: ("set_global_f54cec", "global", "unknown", "Assign global dword 0x00F54CEC."),
    0xA4: ("configure_global_effect", "effect", "unknown", "Select/clear a global effect and optionally set a 3-float vector."),
    0xA5: ("set_enemy_z_rotation", "animation", "inferred", "Set enemy animation/object float at +0x14."),
    0xA6: ("set_vector_from_polar_alt", "math", "observed", "Write two float lvalues from angle and magnitude in alternate order."),
    0xA7: ("set_laser_angle", "laser", "observed", "Set selected laser angle without normalization."),
    0xA8: ("spawn_point_items", "item", "inferred", "Spawn randomized point-item instances around enemy position."),
    0xA9: ("set_side_aware_angle", "math", "inferred", "Choose an angle based on enemy x and playfield side."),
    0xAA: ("set_laser_collision_flag", "laser", "inferred", "Set selected laser byte +0x599 used by collision/graze runtime."),
    0xAB: ("set_laser_max_length", "laser", "observed", "Set selected laser maximum length."),
    0xAC: ("set_laser_distances", "laser", "observed", "Set selected laser tail and head distances."),
    0xAD: ("set_enemy_pause_during_bomb_or_transition", "enemy", "observed", "Assign the flag that skips this enemy's VM, motion, phase, and damage block while the player Bomb-active field or global player-transition state is active."),
    0xAE: ("replace_enemy_effect", "effect", "inferred", "Replace the attached enemy effect/animation object by type."),
    0xAF: ("set_timeline_enemy_spawn_suppressed", "enemy", "observed", "Set the global gate checked by stage-timeline enemy-spawn records: nonzero consumes the record without spawning; zero permits the spawn."),
    0xB0: ("configure_last_spell_state", "boss", "inferred", "Set spell-state globals and enemy flag 0x40000000 from route/card state."),
    0xB1: ("set_phase_health", "boss", "inferred", "Set enemy phase-health field while preserving current/max health."),
    0xB2: ("set_random_player_biased_motion", "movement", "observed", "Choose a random angle (75% biased toward player x on a 384-unit periodic span), reflect it away from vertical movement bounds, then install constant polar motion or a timed displacement from duration, easing mode, and speed."),
    0xB3: ("start_stage_background_sequence", "effect", "observed", "Initialize the stage-background auxiliary ANM VM and select the script indexed by the current background-sequence state."),
    0xB4: ("disable_stage_background_sequence", "effect", "observed", "Clear the stage-background auxiliary sequence enable byte; the shipped ECL corpus does not invoke this handler."),
    0xB5: ("advance_stage_background_sequence", "effect", "observed", "If below 12, play sound 45, increment the background-sequence state, reload that ANM script, and select intermediate mode 1 or final mode 2."),
    0xB6: ("set_secondary_animation_shared_anchor", "animation", "observed", "Choose whether both secondary enemy ANM slots use the shared enemy anchor vector instead of their per-slot local anchors; every shipped use enables it."),
    0xB7: ("set_enemy_bomb_damage_immunity", "enemy", "observed", "Assign the flag that suppresses the enemy player-shot/hurtbox damage block while the player Bomb-active field is set; normal damage remains enabled outside Bomb."),
    0xB8: ("set_spell_end_transition_flag", "spell", "inferred", "Assign spell-manager flag bit 0x800. Every shipped use writes 1 at the start of a spell-ending enemy subroutine; spell start/finish clears the bit."),
}


for _opcode in range(0x60, 0x69):
    _KNOWN[_opcode] = (
        f"fire_pattern_mode_{_opcode - 0x60}",
        "bullet",
        "observed",
        f"Emit the shared 44-byte bullet pattern using expansion mode {_opcode - 0x60}.",
    )


def opcode_spec(opcode: int) -> OpcodeSpec:
    if not 0 <= opcode <= 0xB8:
        return _spec(opcode, f"invalid_{opcode:04x}", "invalid", "unknown", "Opcode is outside the accepted TH08 VM range.")
    values = _KNOWN.get(opcode)
    if values is None:
        return _spec(
            opcode,
            f"unknown_{opcode:02x}",
            "unknown",
            "unknown",
            "No handler/meaning has been established for this opcode.",
        )
    return _spec(opcode, *values)


OPCODE_SPECS = tuple(opcode_spec(opcode) for opcode in range(0xB9))
