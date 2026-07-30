# TH08 Enemy ECL Opcode Catalog

This table is generated from the locally recovered VM switch and decoded shipped corpus.
Confidence values keep observed behavior separate from provisional naming and unknowns.

| Opcode | Name | Category | Confidence | Count | Sizes | Description |
| --- | --- | --- | --- | ---: | --- | --- |
| `0x00` | `nop` | control | observed | 278 | 12 | No state mutation in the VM switch. |
| `0x01` | `terminate` | control | observed | 519 | 12 | Terminate this enemy ECL VM. |
| `0x02` | `reset_timer` | control | observed | 530 | 16 | Reset the current VM timer, optionally from an integer VM value. |
| `0x03` | `nop_with_argument` | control | observed | 8 | 16 | Accepted by the VM default path without a state mutation; shipped records carry one argument. |
| `0x04` | `jump` | control | observed | 1005 | 20 | Set VM time and apply a relative instruction-pointer displacement. |
| `0x05` | `loop_decrement_jump` | control | observed | 575 | 24 | Decrement an integer lvalue and jump while the supplied test remains positive. |
| `0x06` | `set_int` | arithmetic | observed | 3954 | 20 | Assign an integer VM lvalue. |
| `0x07` | `set_float` | arithmetic | observed | 3816 | 20 | Assign a float VM lvalue. |
| `0x08` | `set_int_random_sign` | arithmetic | observed | 0 | - | Assign value multiplied by a random sign. |
| `0x09` | `set_float_random_sign` | arithmetic | observed | 38 | 20 | Assign value multiplied by a random sign. |
| `0x0a` | `add_int` | arithmetic | observed | 105 | 20 | Add to an integer lvalue. |
| `0x0b` | `sub_int` | arithmetic | observed | 48 | 20 | Subtract from an integer lvalue. |
| `0x0c` | `mul_int` | arithmetic | observed | 12 | 20 | Multiply an integer lvalue. |
| `0x0d` | `div_int` | arithmetic | observed | 8 | 20 | Divide an integer lvalue. |
| `0x0e` | `mod_int` | arithmetic | observed | 0 | - | Apply integer remainder to an lvalue. |
| `0x0f` | `add_float` | arithmetic | observed | 2239 | 20 | Add to a float lvalue. |
| `0x10` | `sub_float` | arithmetic | observed | 442 | 20 | Subtract from a float lvalue. |
| `0x11` | `mul_float` | arithmetic | observed | 325 | 20 | Multiply a float lvalue. |
| `0x12` | `div_float` | arithmetic | observed | 30 | 20 | Divide a float lvalue. |
| `0x13` | `random_float` | arithmetic | observed | 0 | - | Assign the result of the VM random-range helper. |
| `0x14` | `set_int_add` | arithmetic | observed | 2 | 24 | Assign integer a + b. |
| `0x15` | `set_int_sub` | arithmetic | observed | 14 | 24 | Assign integer a - b. |
| `0x16` | `set_int_mul` | arithmetic | observed | 2 | 24 | Assign integer a * b. |
| `0x17` | `set_int_div` | arithmetic | observed | 28 | 24 | Assign integer a / b. |
| `0x18` | `set_int_mod` | arithmetic | observed | 64 | 24 | Assign integer a % b. |
| `0x19` | `set_float_add` | arithmetic | observed | 355 | 24 | Assign float a + b. |
| `0x1a` | `set_float_sub` | arithmetic | observed | 263 | 24 | Assign float a - b. |
| `0x1b` | `set_float_mul` | arithmetic | observed | 499 | 24 | Assign float a * b. |
| `0x1c` | `set_float_div` | arithmetic | observed | 128 | 24 | Assign float a / b. |
| `0x1d` | `set_float_random` | arithmetic | observed | 0 | - | Assign a random-range result from two float operands. |
| `0x1e` | `increment_int` | arithmetic | observed | 81 | 16 | Increment an integer lvalue. |
| `0x1f` | `decrement_int` | arithmetic | observed | 25 | 16 | Decrement an integer lvalue. |
| `0x20` | `set_sin` | math | observed | 136 | 20 | Assign sine of a float operand. |
| `0x21` | `set_cos` | math | observed | 131 | 20 | Assign cosine of a float operand. |
| `0x22` | `set_angle_between_points` | math | observed | 38 | 32 | Assign atan2-derived angle between two points. |
| `0x23` | `set_int_compare` | math | inferred | 0 | - | Evaluate an integer comparison helper and store its result. |
| `0x24` | `set_float_compare` | math | inferred | 97 | 44 | Evaluate a float comparison helper and store its result. |
| `0x25` | `normalize_angle` | math | observed | 1708 | 16 | Normalize an angle with the engine angle helper. |
| `0x26` | `set_vector_from_polar` | math | observed | 110 | 28 | Write two float lvalues from angle and magnitude. |
| `0x27` | `set_distance` | math | observed | 2 | 32 | Assign Euclidean distance between two points. |
| `0x28` | `jump_int_eq` | control | observed | 93 | 28 | Conditional relative jump: integer equal. |
| `0x29` | `jump_float_eq` | control | observed | 0 | - | Conditional relative jump: float equal. |
| `0x2a` | `jump_int_ne` | control | observed | 94 | 28 | Conditional relative jump: integer not equal. |
| `0x2b` | `jump_float_ne` | control | observed | 0 | - | Conditional relative jump: float not equal. |
| `0x2c` | `jump_int_lt` | control | observed | 28 | 28 | Conditional relative jump: integer less than. |
| `0x2d` | `jump_float_lt` | control | observed | 11 | 28 | Conditional relative jump: float less than. |
| `0x2e` | `jump_int_le` | control | observed | 35 | 28 | Conditional relative jump: integer less than or equal. |
| `0x2f` | `jump_float_le` | control | observed | 31 | 28 | Conditional relative jump: float less than or equal. |
| `0x30` | `jump_int_gt` | control | observed | 95 | 28 | Conditional relative jump: integer greater than. |
| `0x31` | `jump_float_gt` | control | observed | 6 | 28 | Conditional relative jump: float greater than. |
| `0x32` | `jump_int_ge` | control | observed | 70 | 28 | Conditional relative jump: integer greater than or equal. |
| `0x33` | `jump_float_ge` | control | observed | 139 | 28 | Conditional relative jump: float greater than or equal. |
| `0x34` | `call_subroutine` | control | observed | 614 | 16 | Call an ECL subroutine using the 16-entry VM context stack. |
| `0x35` | `return_subroutine` | control | observed | 250 | 12 | Restore the caller VM context or terminate at stack bottom. |
| `0x36` | `set_primary_animation` | animation | inferred | 291 | 16 | Set a primary enemy animation and clear animation mode bit 0x4. |
| `0x37` | `set_primary_animation_sequence` | animation | inferred | 12 | 16 | Install six consecutive primary animation IDs. |
| `0x38` | `set_primary_animation_set` | animation | inferred | 0 | - | Install six explicit primary animation IDs. |
| `0x39` | `set_secondary_animation` | animation | inferred | 46 | 20 | Apply the secondary animation helper. |
| `0x3a` | `set_primary_animation_mode` | animation | inferred | 73 | 16 | Set a primary animation and set animation mode bit 0x4. |
| `0x3b` | `set_primary_animation_sequence_mode` | animation | inferred | 138 | 16 | Install six consecutive animation IDs and set mode bit 0x4. |
| `0x3c` | `set_primary_animation_set_mode` | animation | inferred | 0 | - | Install six explicit animation IDs and set mode bit 0x4. |
| `0x3d` | `set_secondary_animation_mode` | animation | inferred | 76 | 20 | Apply secondary animation and set mode bit 0x4. |
| `0x3e` | `restore_primary_animation` | animation | inferred | 201 | 12 | Restore the saved primary animation ID. |
| `0x3f` | `set_position` | movement | observed | 96 | 20 | Set enemy x/y position, clear z, then refresh derived position state. |
| `0x40` | `move_to` | movement | inferred | 342 | 28 | Configure timed interpolation from the current position to a target. |
| `0x41` | `set_velocity_polar` | movement | inferred | 171 | 20 | Set absolute movement angle and speed. |
| `0x42` | `set_velocity_polar_timed` | movement | inferred | 188 | 28 | Set or interpolate absolute movement from duration, mode, angle and speed. |
| `0x43` | `set_bounded_random_velocity` | movement | inferred | 270 | 24 | Choose a random direction and reflect it away from configured movement bounds. |
| `0x44` | `set_velocity_aimed` | movement | observed | 0 | - | Set speed and angle aimed at the player. |
| `0x45` | `set_velocity_aimed_timed` | movement | inferred | 0 | - | Set or interpolate player-aimed movement. |
| `0x46` | `set_angular_velocity` | movement | inferred | 54 | 16 | Set movement angular-velocity field. |
| `0x47` | `set_speed_acceleration` | movement | inferred | 78 | 16 | Set movement speed-acceleration field. |
| `0x48` | `move_to_explicit` | movement | inferred | 61 | 40 | Configure timed interpolation with explicit start/target motion fields. |
| `0x49` | `move_from_current` | movement | inferred | 70 | 28 | Configure timed interpolation beginning at current position. |
| `0x4a` | `set_motion_interpolation` | movement | inferred | 114 | 24 | Configure timed motion interpolation parameters. |
| `0x4b` | `set_movement_bounds` | movement | observed | 157 | 28 | Set left/top/right/bottom bounds and enable bounded movement. |
| `0x4c` | `clear_movement_bounds` | movement | observed | 34 | 12 | Disable bounded movement. |
| `0x4d` | `set_hitbox` | enemy | inferred | 363 | 20 | Set the first enemy collision extent pair. |
| `0x4e` | `set_hurtbox` | enemy | inferred | 33 | 20 | Set the second enemy collision extent pair. |
| `0x4f` | `set_enemy_flags` | enemy | observed | 16 | 16 | Assign a six-bit group of enemy behavior flags. |
| `0x50` | `clear_enemy_flags` | enemy | observed | 702 | 16 | Clear selected enemy behavior flags. |
| `0x51` | `set_enemy_flags_mask` | enemy | observed | 535 | 16 | Set selected enemy behavior flags. |
| `0x52` | `set_minimum_fire_distance` | bullet | observed | 76 | 16 | Store squared radius inside which direct fire is suppressed. |
| `0x53` | `set_boss_flag` | boss | observed | 195 | 16 | Assign the enemy boss flag. Its consumers drive boss-health UI and marker publication, boss damage scaling/position tracking, and boss-defeat projectile/enemy cleanup. |
| `0x54` | `unknown_54` | unknown | unknown | 0 | - | No handler/meaning has been established for this opcode. |
| `0x55` | `unknown_55` | unknown | unknown | 0 | - | No handler/meaning has been established for this opcode. |
| `0x56` | `copy_enemy_int` | enemy | inferred | 0 | - | Copy an integer VM value from an indexed enemy slot. |
| `0x57` | `copy_enemy_float` | enemy | inferred | 2 | 24 | Copy a float VM value associated with an indexed enemy slot. |
| `0x58` | `call_subroutine_with_enemy` | control | inferred | 2 | 20 | Call a subroutine after resolving an indexed enemy. |
| `0x59` | `set_enemy_animation_index` | animation | inferred | 0 | - | Set the saved animation ID on an indexed enemy. |
| `0x5a` | `spawn_child_enemy` | enemy | inferred | 214 | 36 | Spawn/link a child enemy using the first spawn helper. |
| `0x5b` | `spawn_child_enemy_variant` | enemy | inferred | 377 | 36 | Spawn/link a child enemy using the alternate spawn helper. |
| `0x5c` | `spawn_child_enemy_relative` | enemy | inferred | 425 | 36 | Spawn/link a child enemy relative to the parent position. |
| `0x5d` | `spawn_enemy_from_vm_position` | enemy | inferred | 9 | 40 | Spawn an enemy through the timeline spawn primitive at an explicit position. |
| `0x5e` | `spawn_enemy_from_vm_offset` | enemy | inferred | 152 | 40 | Spawn an enemy through the timeline primitive at current position plus offset. |
| `0x5f` | `zero_eligible_enemy_hp_with_score_items` | enemy | observed | 157 | 12 | Set current HP to zero for every eligible active non-boss enemy, unlink its parent relation, start its configured end subroutine, and spawn type-6 scaled-score items for enemies carrying reward flag 0x80; active-bit retirement is deferred to later manager processing. |
| `0x60` | `fire_pattern_mode_0` | bullet | observed | 352 | 44 | Emit the shared 44-byte bullet pattern using expansion mode 0. |
| `0x61` | `fire_pattern_mode_1` | bullet | observed | 546 | 44 | Emit the shared 44-byte bullet pattern using expansion mode 1. |
| `0x62` | `fire_pattern_mode_2` | bullet | observed | 241 | 44 | Emit the shared 44-byte bullet pattern using expansion mode 2. |
| `0x63` | `fire_pattern_mode_3` | bullet | observed | 802 | 44 | Emit the shared 44-byte bullet pattern using expansion mode 3. |
| `0x64` | `fire_pattern_mode_4` | bullet | observed | 10 | 44 | Emit the shared 44-byte bullet pattern using expansion mode 4. |
| `0x65` | `fire_pattern_mode_5` | bullet | observed | 1 | 44 | Emit the shared 44-byte bullet pattern using expansion mode 5. |
| `0x66` | `fire_pattern_mode_6` | bullet | observed | 0 | - | Emit the shared 44-byte bullet pattern using expansion mode 6. |
| `0x67` | `fire_pattern_mode_7` | bullet | observed | 0 | - | Emit the shared 44-byte bullet pattern using expansion mode 7. |
| `0x68` | `fire_pattern_mode_8` | bullet | observed | 56 | 44 | Emit the shared 44-byte bullet pattern using expansion mode 8. |
| `0x69` | `set_fire_delay` | bullet | observed | 165 | 16 | Set rank-adjusted fire delay and reset its timer. |
| `0x6a` | `set_fire_delay_random_phase` | bullet | observed | 44 | 16 | Set rank-adjusted fire delay and randomize the initial timer phase. |
| `0x6b` | `enable_deferred_fire` | bullet | observed | 25 | 12 | Queue the next direct-fire instruction instead of emitting immediately. |
| `0x6c` | `disable_deferred_fire` | bullet | observed | 25 | 12 | Disable deferred direct-fire mode. |
| `0x6d` | `emit_current_pattern` | bullet | observed | 0 | - | Emit the current bullet descriptor at the current emission origin. |
| `0x6e` | `set_emission_offset` | bullet | observed | 423 | 20 | Set x/y emission-origin offset and clear z. |
| `0x6f` | `define_bullet_transform` | bullet_transform | observed | 1269 | 40 | Write one 24-byte record in the 18-entry bullet-transform program. |
| `0x70` | `clear_bullets_global` | bullet | inferred | 10 | 12 | Invoke the global bullet clear/cancel helper. |
| `0x71` | `configure_bullet_sounds` | bullet | observed | 161 | 20 | Set/disable the spatialized pattern-emission sound ID and set the per-bullet transform-activation sound ID. |
| `0x72` | `spawn_laser_absolute` | laser | observed | 59 | 64 | Create a laser whose supplied angle is absolute. |
| `0x73` | `spawn_laser_aimed` | laser | observed | 0 | - | Create a laser whose supplied angle is relative to player aim. |
| `0x74` | `select_laser_handle` | laser | observed | 18 | 16 | Select one of the enemy's 32 laser handles. |
| `0x75` | `add_laser_angle` | laser | observed | 10 | 20 | Add and normalize an angle on a selected laser handle. |
| `0x76` | `aim_laser_at_player` | laser | observed | 0 | - | Set selected laser angle to player aim plus offset. |
| `0x77` | `set_laser_origin` | laser | observed | 10 | 28 | Set selected laser origin to enemy position plus x/y/z offset. |
| `0x78` | `query_laser_active` | laser | observed | 2 | 16 | Write selected laser allocation/active state to VM result field. |
| `0x79` | `fade_laser` | laser | observed | 4 | 16 | Force selected laser into fade phase. |
| `0x7a` | `start_spell_card` | spell | observed | 431 | 244 | Start a spell card from a 232-byte payload containing its ID, score, XOR-encoded name, owner, and two description lines. |
| `0x7b` | `finish_spell_card` | spell | observed | 191 | 12 | Finish the active spell card and run capture/failure bookkeeping. |
| `0x7c` | `play_sound_at_enemy` | audio | inferred | 422 | 16 | Play a sound/effect ID spatialized at enemy x. |
| `0x7d` | `invoke_interrupt_slot` | control | observed | 0 | - | Save the current ECL VM frame and start the subroutine installed in the selected interrupt slot. |
| `0x7e` | `set_interrupt_slot` | control | observed | 52 | 20 | Install an ECL subroutine ID into an indexed interrupt slot. |
| `0x7f` | `set_boss_slot` | boss | inferred | 307 | 16 | Register/unregister this enemy in one of four boss slots. |
| `0x80` | `spawn_enemy_effect` | effect | inferred | 210 | 32 | Allocate and attach an effect instance to the enemy. |
| `0x81` | `set_enemy_defeat_mode` | enemy | observed | 368 | 16 | Set the three-bit mode dispatched when enemy health reaches zero. Shipped values 0..3 select distinct deactivation, cleanup, phase, score, effect, and player-state consequences. |
| `0x82` | `set_enemy_end_subroutine` | control | observed | 357 | 16 | Set the ECL subroutine started by enemy-manager cleanup when the current enemy or phase ends. |
| `0x83` | `set_health` | boss | observed | 252 | 16 | Set current, maximum, and phase health to one integer value. |
| `0x84` | `set_timer_current` | boss | inferred | 153 | 16 | Set/reset a phase timer from an integer operand. |
| `0x85` | `set_health_phase_transition` | boss | observed | 113 | 24 | Set indexed health threshold and the ECL subroutine started when health crosses it. |
| `0x86` | `set_timeout_phase_transition` | boss | observed | 353 | 20 | Set timeout frame and the ECL subroutine started when the phase timer reaches it. |
| `0x87` | `start_interrupt_subroutine` | control | observed | 625 | 20 | Replace an indexed auxiliary VM context and start a subroutine in it. |
| `0x88` | `invoke_enemy_callback` | enemy | observed | 182 | 20 | Invoke an indexed built-in callback from the 32-entry table referenced at 0x41D4F4. |
| `0x89` | `set_enemy_callback` | enemy | observed | 95 | 20 | Install or clear an indexed built-in per-frame enemy callback from the same 32-entry table. |
| `0x8a` | `set_enemy_bytes` | enemy | unknown | 0 | - | Set three adjacent enemy state bytes at +0x3310..+0x3312. |
| `0x8b` | `spawn_effect` | effect | inferred | 404 | 24 | Spawn one or more typed effect-manager objects at enemy position. |
| `0x8c` | `spawn_effect_with_vector` | effect | inferred | 1093 | 36 | Spawn typed effect objects with an additional vector. |
| `0x8d` | `spawn_item` | item | observed | 17 | 16 | Spawn one item of the supplied type at enemy position. |
| `0x8e` | `spawn_item_bundle` | item | inferred | 22 | 16 | Spawn a randomized item bundle, with type depending on collection state. |
| `0x8f` | `set_drop_type` | item | inferred | 0 | - | Set a single enemy drop-type field. |
| `0x90` | `set_drop_counts` | item | inferred | 121 | 20 | Set two enemy drop-count/type fields consumed on death. |
| `0x91` | `enable_enemy_animation_script_refresh` | animation | observed | 107 | 16 | Assign the flag that reapplies saved ANM script IDs to the main enemy animation and trail nodes in the render callback; every shipped use enables it. |
| `0x92` | `set_global_vm_value` | global | unknown | 0 | - | Pass an integer value to helper 0x41FDF0. |
| `0x93` | `write_unreferenced_global_4ea290` | validation | observed | 41 | 16 | Assign global dword 0x004EA290. Static xrefs contain this writer and no direct reader, so it is excluded from solver state pending a runtime watchpoint. |
| `0x94` | `start_spell_phase` | boss | inferred | 188 | 16 | Call spell/phase helper 0x423130 and add 1800 frames to stage counter. |
| `0x95` | `set_enemy_short_020a` | enemy | unknown | 0 | - | Set enemy field +0x020A. |
| `0x96` | `set_enemy_object_short` | enemy | unknown | 0 | - | Set an indexed short in an enemy-owned 676-byte object array. |
| `0x97` | `set_enemy_flag_04000000` | enemy | unknown | 0 | - | Assign enemy flag bit 0x04000000. |
| `0x98` | `set_rank_interpolation` | difficulty | observed | 34 | 36 | Set float and integer endpoints used to scale bullet count/speed by rank. |
| `0x99` | `copy_enemy_end_to_timeout_subroutine` | control | observed | 153 | 12 | Copy the signed enemy-end subroutine ID to the timeout-transition subroutine field and reset the phase timer. |
| `0x9a` | `clear_laser_handles` | laser | observed | 0 | - | Clear all 32 laser handle pointers owned by this enemy. |
| `0x9b` | `set_fixed_spell_reward_mode` | spell | observed | 19 | 16 | Assign the mode that initializes spell reward to 99,999,990, disables its per-frame decay, and uses capture-result field 700; every shipped use enables it. |
| `0x9c` | `set_enemy_flag_00000080` | enemy | unknown | 0 | - | Assign enemy flag bit 0x80 and state byte 2. |
| `0x9d` | `configure_enemy_trail` | enemy | observed | 22 | 28 | Set trail mode, position-history length, historical-collision limit, and render stride. Shipped collision limits are all zero, so shipped uses affect presentation only. |
| `0x9e` | `set_boss_health_segment` | boss | observed | 244 | 28 | Publish normalized boss-health segment bounds and segment metadata. |
| `0x9f` | `set_enemy_render_layer` | animation | observed | 38 | 16 | Select one of four enemy render-list layers consumed by the early (0/1) and late (2/3) render passes. |
| `0xa0` | `set_timer_current_alt` | boss | inferred | 538 | 16 | Reset/set the same timer helper used by phase control. |
| `0xa1` | `cancel_bullets_in_radius` | bullet | inferred | 0 | - | Invoke radial bullet cancel/conversion helper at enemy position. |
| `0xa2` | `cancel_all_bullets` | bullet | inferred | 10 | 12 | Invoke global bullet cancel helper with mode 4. |
| `0xa3` | `set_global_f54cec` | global | unknown | 0 | - | Assign global dword 0x00F54CEC. |
| `0xa4` | `configure_global_effect` | effect | unknown | 0 | - | Select/clear a global effect and optionally set a 3-float vector. |
| `0xa5` | `set_enemy_z_rotation` | animation | inferred | 28 | 16 | Set enemy animation/object float at +0x14. |
| `0xa6` | `set_vector_from_polar_alt` | math | observed | 0 | - | Write two float lvalues from angle and magnitude in alternate order. |
| `0xa7` | `set_laser_angle` | laser | observed | 10 | 20 | Set selected laser angle without normalization. |
| `0xa8` | `spawn_point_items` | item | inferred | 22 | 16 | Spawn randomized point-item instances around enemy position. |
| `0xa9` | `set_side_aware_angle` | math | inferred | 0 | - | Choose an angle based on enemy x and playfield side. |
| `0xaa` | `set_laser_collision_flag` | laser | inferred | 0 | - | Set selected laser byte +0x599 used by collision/graze runtime. |
| `0xab` | `set_laser_max_length` | laser | observed | 0 | - | Set selected laser maximum length. |
| `0xac` | `set_laser_distances` | laser | observed | 0 | - | Set selected laser tail and head distances. |
| `0xad` | `set_enemy_pause_during_bomb_or_transition` | enemy | observed | 118 | 16 | Assign the flag that skips this enemy's VM, motion, phase, and damage block while the player Bomb-active field or global player-transition state is active. |
| `0xae` | `replace_enemy_effect` | effect | inferred | 38 | 16 | Replace the attached enemy effect/animation object by type. |
| `0xaf` | `set_timeline_enemy_spawn_suppressed` | enemy | observed | 5 | 16 | Set the global gate checked by stage-timeline enemy-spawn records: nonzero consumes the record without spawning; zero permits the spawn. |
| `0xb0` | `configure_last_spell_state` | boss | inferred | 41 | 16 | Set spell-state globals and enemy flag 0x40000000 from route/card state. |
| `0xb1` | `set_phase_health` | boss | inferred | 6 | 16 | Set enemy phase-health field while preserving current/max health. |
| `0xb2` | `set_random_player_biased_motion` | movement | observed | 4 | 24 | Choose a random angle (75% biased toward player x on a 384-unit periodic span), reflect it away from vertical movement bounds, then install constant polar motion or a timed displacement from duration, easing mode, and speed. |
| `0xb3` | `start_stage_background_sequence` | effect | observed | 2 | 12 | Initialize the stage-background auxiliary ANM VM and select the script indexed by the current background-sequence state. |
| `0xb4` | `disable_stage_background_sequence` | effect | observed | 0 | - | Clear the stage-background auxiliary sequence enable byte; the shipped ECL corpus does not invoke this handler. |
| `0xb5` | `advance_stage_background_sequence` | effect | observed | 8 | 12 | If below 12, play sound 45, increment the background-sequence state, reload that ANM script, and select intermediate mode 1 or final mode 2. |
| `0xb6` | `set_secondary_animation_shared_anchor` | animation | observed | 30 | 16 | Choose whether both secondary enemy ANM slots use the shared enemy anchor vector instead of their per-slot local anchors; every shipped use enables it. |
| `0xb7` | `set_enemy_bomb_damage_immunity` | enemy | observed | 61 | 16 | Assign the flag that suppresses the enemy player-shot/hurtbox damage block while the player Bomb-active field is set; normal damage remains enabled outside Bomb. |
| `0xb8` | `set_spell_end_transition_flag` | spell | inferred | 82 | 16 | Assign spell-manager flag bit 0x800. Every shipped use writes 1 at the start of a spell-ending enemy subroutine; spell start/finish clears the bit. |
