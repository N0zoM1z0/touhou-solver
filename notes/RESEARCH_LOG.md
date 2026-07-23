# TH08 Research Log

## 2026-07-22: Workspace and Danmaku Investigation Start

### Target Identity

- Disk executable: `th08.exe`
- Image base: `0x00400000`
- Architecture: x86 PE32
- Clean SHA-256: `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
- Current IDA database contains the historical one-byte life patch at
  `0x0044D0FA` (`FF -> 00`). The disk executable remains clean.

### Established Engine Model

- Fixed-step 60 Hz update loop with separate ordered update and render callback
  chains.
- Stage content is data-driven through `.std`, `.ecl`, `.anm`, and `msg*.dat`
  resources stored in `th08.dat` (`PBGZ`).
- Known subsystem entry points:
  - stage background registration: `0x409B20`
  - enemy/ECL registration: `0x42C590`
  - bullet-system registration: `0x4311A0`
  - player registration: `0x44C230`
  - combined stage bootstrap: `0x43ABD7`

### Active Questions

- How does the stage index select ECL, STD, ANM, and message resources?
- What is the exact on-disk ECL layout used by TH08?
- How are ECL timelines and subroutines represented and scheduled?
- Which ECL opcodes create enemies, invoke enemy subroutines, and emit bullets?
- What argument structures cross from the enemy VM into the bullet manager?
- How are bullet position, velocity, acceleration, angle, color, sprite, and
  transformations updated per frame?
- Can each stage's scripts be extracted and rendered as a readable instruction
  listing without running the game?

### Method Decision

- The investigation will be self-contained.
- Format layouts and opcode meanings must be derived from the shipped TH08
  files, IDA/REA analysis, and controlled local experiments.
- No third-party archive implementation, ECL decompiler, opcode table, or
  online format documentation will be used as analysis authority.
- A partially started external toolkit clone was stopped and removed before
  its source was inspected or used.

## 2026-07-22: Archive, ECL, and Bullet Pipeline Recovered

### Resource Layer

- Implemented `scripts/th08_pbgz.py` from executable routines
  `0x0043E1D0`, `0x004740E0`, and `0x004748C0` through `0x00474FA0`.
- Parsed 317 `th08.dat` members and extracted all ECL/STD resources.
- Implemented all eight `edz?` codec parameter sets in
  `scripts/th08_resource.py`, based on `0x0043E390` and `0x004C78E0`.
- Decoded 24 ECL and 18 STD members into `artifacts/decoded/`.

### ECL Selection and Scheduling

- `enemy_manager_init_stage` (`0x0042EBF0`) chooses normal stage ECL names
  `1,2,3,4a,4b,5,6,7,8`, the corresponding spell-practice `*sp` resource,
  or a per-spell resource for IDs 205 and later.
- `ecl_load_file` (`0x00418330`) validates magic `0x800` and relocates 16
  timeline/end slots plus the subroutine offset table.
- Confirmed header `+0x04` is subroutine count and `+0x06` is timeline count.
  Timeline slot `[count]` is the file-end sentinel.
- `stage_timeline_step` (`0x0042A8A0`) processes variable-length stage records
  and spawns enemies through `enemy_spawn_from_timeline` (`0x0042A4E0`).
- Enemy pool: 480 slots, stride `0x53D0`.

### Enemy VM and Firing

- `enemy_ecl_vm_step` (`0x004184B0`) executes variable-length instructions
  with 12-byte headers and opcodes through `0xB8`.
- Opcodes `0x60..0x68` share `enemy_ecl_emit_bullets` (`0x00422720`) and an
  eight-dword payload.
- Recovered exact parameter-mask mapping for dynamic type, color, counts,
  speeds, and angles.
- `bullet_emitter_spawn_pattern` (`0x00430E10`) expands two nested counts.
- `bullet_pool_spawn_one` (`0x0042F5F0`) implements emission modes 0 through 8
  and allocates from 1536 slots of stride `0x10B8`.
- `bullet_manager_update` (`0x00431240`) applies queued transformations,
  movement, culling, and animation each frame.

### Parser Results

- Added `scripts/th08_ecl.py`.
- Successfully validated all 24 decoded ECL files.
- Corpus: 1,449 subs, 32 timelines, 36,661 VM instructions, 2,003 timeline
  records, and 2,008 direct firing instructions.
- Generated complete per-file listings and summary JSON in
  `artifacts/ecl_reports/`.
- Dynamic parameters are rendered as VM references, not false literals.

### IDA Database Persistence

- Renamed and commented the resource decode, ECL loader, stage scheduler,
  enemy VM, emission, pattern expansion, bullet allocation, transformation,
  and update functions.
- Renamed the stage ECL tables, ECL context/difficulty mask, and bullet pool.
- Added four recovered ECL structures to IDA Local Types.

### REA Evidence

- Clean executable overview:
  `ev_6ef75aaa7bb141094b89d4dd018cf0686f727d09dbf9b1dee58501d3d5b3eb8b`
- Five-function pipeline batch:
  `ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`

## 2026-07-22: SHT, Spell Metadata, Phase Graph, Lasers, And Transforms

### Player And Route Identity

- Parsed all eight `ply*.sht` resources with `scripts/th08_sht.py`; 227 shot
  records validate across the corpus.
- Route ID `2` is the Sakuya/Remilia team. Its resources are `ply02a.sht`
  (Sakuya/unfocused) and `ply02as.sht` (Remilia/focused).
- Observed movement increments: Sakuya 4.0 cardinal / 2.8284271 per diagonal
  axis; Remilia 2.3 / 1.6263456.
- Both headers carry Bomb-gate reset value 10. This field is shared with normal
  Bomb activation and is not the computed predeath/deathbomb countdown.
- Route-ID 2 selects Stage 4A/Reimu. Message route-table correlations and the
  player-route branch are commented in IDA.

### Spell Catalog

- Recovered opcode `0x7A` payload decoding, including spell ID, owner, and
  Japanese display name.
- Every shipped spell ID `0..221` now maps to an exact ECL file, subroutine,
  instruction offset, and difficulty mask in `spell_catalog.json/.md`.
- IDA names now include `ecl_start_spell_card`, `ecl_finish_spell_card`,
  `spell_card_start`, `spell_card_finish`, and `g_spell_card_state`.

### Exact Phase Transitions

- ECL `0x82` writes the end-transition subroutine to enemy `+0x2CEE`.
  `enemy_manager_update` starts it during cleanup.
- ECL `0x85` writes indexed HP thresholds at `+0x3358` and their sub IDs at
  `+0x3368`. `enemy_apply_health_phase_transition` starts the selected sub.
- ECL `0x86` writes timeout frame `+0x3378` and timeout sub ID `+0x337C`.
  `enemy_apply_timeout_phase_transition` starts it when the timer expires.
- ECL `0x7E` installs a subroutine into interrupt slot `+0x2CF0[index]`;
  `0x7D` saves the 0x228-byte VM frame and invokes the selected slot.
- ECL `0x99` copies the end-transition sub ID into the timeout-transition
  field.
- VM integer `10040` is `g_difficulty_index`; `10052` is
  `g_player_route_id`.

Added `scripts/th08_ecl_flow.py` and route manifests. Static reachability now
resolves:

- Lunatic Final A: 33 spell IDs.
- Lunatic Final B: 37 spell IDs.
- Extra: 14 spell IDs, including all three Keine and eleven Mokou cards.

`scripts/test_th08_routes.py` pins these sets and verifies that target-route
graphs contain no unresolved dynamic subroutine edges.

### Bullet Transform And Laser Runtime

- Verified `Th08BulletTransformRecord` is 24 bytes with two floats, two ints,
  kind, and wait flag; each bullet has 18 records.
- Recovered field use for acceleration, angular acceleration, stop/turn,
  re-aim, snap angle, reflection, culling grace, template clone, active-queue
  barrier, fade, spatial sound, horizontal/vertical wrap, and two-record
  derived emission kinds. The later 2026-07-22 transform section supersedes
  this checkpoint's remaining field uncertainty.
- Verified `Th08Laser` is 1436 bytes (`0x59C`) and the pool has 256 slots.
- Recovered origin/angle/tail/head/length/width/speed, phase timers, collision
  gates, flags, packed type/color, and warmup/active/fade state.
- ECL `0x72` creates absolute-angle lasers; `0x73` creates player-relative
  lasers.

### IDA Persistence

- Renamed `g_difficulty_index`, `enemy_apply_health_phase_transition`, and
  `enemy_apply_timeout_phase_transition`.
- Commented the handlers and manager consumers for opcodes `0x7D`, `0x7E`,
  `0x82`, `0x85`, `0x86`, and `0x99`, plus VM variables 10040/10052.
- The opcode catalog now has names for all 185 slots: 96 observed, 57
  inferred, and 32 explicitly retained as unknown-confidence names.

## 2026-07-22: Bomb Resources, Replay Frames, RNG, And Items

### Observed Player Resource Rules

- `player_dead_handler` (`0x0044AB40`) installs state 2 and a computed predeath
  counter. With zero stock it is 2; with stock it is derived from `6 * bombs`,
  a meter comparison, caps at 15/30, spell state, and a 9/5 stage multiplier.
- `player_deathbomb_or_death_transition` (`0x0044C650`) tests Bomb input before
  decrement. A normal Bomb costs one; Last Spell costs `min(stock, 2)`.
- Recovered all five route-2 callbacks and durations: Sakuya/Remilia normal
  290/290, Sakuya/Remilia Last Spell 350/320, and forced Dissolve 200.
- Added an executable resource model in `scripts/th08_player_model.py`.

### Observed Replay And RNG Rules

- Recovered the exact 16-bit RNG transition at `0x0043ECC0` and added
  `scripts/th08_rng.py` with pinned vectors.
- Replay stage records carry a 36-byte header followed by one input record per
  callback frame. Legacy records are 2 bytes; expanded records are 6 bytes and
  retain the input mask in their first word.
- Added checksum/decompression, seed extraction, canonical input hashing, Bomb
  edge detection, and held-input run compression to `scripts/th08_replay.py`.
- Local route-2 Extra replay `th8_06.rpy` contains 66,386 stage-8 frames at
  seed `0xC0A4`, with five Bomb rising edges and 5,302 compact input runs.
  It is retained as a baseline, not claimed as a validated clear.

### Observed Item Rules

- Item pool capacity is 2,096, stride `0x2E4`.
- Standard free and homing motion, route-2 collection AABB, point-line trigger,
  homing speed, and character-specific fall scales are implemented in
  `scripts/th08_item_model.py`.
- Player SHT widths are now separated into hitbox, auxiliary collision/graze,
  and item-collection roles. Route-2 collection width is 24.
- Special motion states 2/3/5, full value conversion, and same-frame collection
  order remain runtime verification tasks.

### Verification And Evidence

- Seventeen local regression tests pass across route reachability, RNG, replay
  extraction, Bomb resources, and item motion/collection.
- REA batch evidence:
  `ev_50cb146240388720e6825183ae13c99f83c95141b2f23908d97a88071351120d`.

## 2026-07-22: Player Damage And Bomb-Cancel Geometry

### Observed Shared Region System

- Recovered two player-owned arrays of 192 records, stride `0x40`: damage at
  `player+0xB8834` and hostile-projectile cancellation at `player+0xBB834`.
- Named their four circle/rectangle allocators, shared updater, point-cancel
  consumer, and enemy-damage consumer in IDA.
- Cancel circles use strict center-point containment; damage circles use
  inclusive enemy-center containment. Rectangle paths and damage-cap behavior
  are implemented in `scripts/th08_attack_model.py`.

### Observed Route-2 Bomb Geometry

- Killing Doll emits 96 knives in frame-pairs from Bomb-local time 20 through
  114. Each knife owns radius-32 cancel/damage circles; damage is 20.
- Phantom Killer emits 128 knives in frame-pairs from time 20 through 146,
  using the same radius and damage 30.
- Remilia's callbacks establish radius-96 and perpendicular full-playfield
  cancel regions. Her damage is routed through four option/player-shot slots;
  the next section supersedes the earlier open damage-scheduling conclusion.
- Twenty-three regression tests pass after adding six region tests.

REA evidence:
`ev_e97b8a031969fbddae5e602d0d1ac8d9dc567a23ec31ef07a6925a503582e3df`.

## 2026-07-22: Remilia Bomb Player-Shot Damage

### Observed Special SHT Path

- Route-2 callback index 1 selects `ply02as.sht` level 6 after Bomb-local frame
  60. Callback index 3 selects level 7 after the same gate.
- Level 6 has 16 cardinal option shots. Level 7 adds two player-sourced diagonal
  shots. Every record is type 6, base damage 45, speed 20, with a 32 x 16
  hitbox and no custom callback.
- Records emit when the independent 0..19 shot cadence satisfies
  `frame % period == phase`; holding shot remains required.
- Initial velocity is `(cos(angle) * speed, sin(angle) * speed)`. Collision uses
  inclusive AABBs. Bomb-active ordinary-shot damage is divided by five, making
  each overlap worth 9, and the ordinary-shot subtotal is capped at 50 per
  enemy check. Type 6 remains active after overlap.
- Added `scripts/th08_player_shot_model.py` and six resource-backed regression
  tests. All 29 local tests pass.

### IDA Persistence And Evidence

- Renamed `player_shot_record_emit_if_due` (`0x0044FD80`) and
  `aabb_from_center_size` (`0x00451CE0`).
- Commented the level override, trigonometric velocity, Bomb damage divisor,
  type-6 piercing branch, and ordinary-shot frame cap.
- REA evidence:
  `ev_d3ee55dd161e311c6750c0bb9341a85ebeb0e01a139bed11faba302b73060f41`.

## 2026-07-22: Laser Collision And Phase Model

### Observed Geometry

- The laser loop is inside `bullet_manager_update` from `0x00431B7A`; it scans
  256 records of `0x59C` bytes.
- Collision uses a laser-local horizontal rectangle. The player center is
  rotated around the laser origin by `-angle`, then compared by inclusive AABB
  with the player's SHT hitbox half extents.
- Collision length is the visible `head-tail` segment while tail is zero, and
  70 percent of that segment after tail becomes positive. Collision height is
  half the configured laser width.
- Graze expands all four local rectangle bounds by 48. It is requested only in
  active phase every 20 integer timer ticks.

### Observed Lifecycle

- Warmup collision begins at the enable threshold; fade collision ends at the
  disable threshold. Neither requests graze.
- Warmup-to-active and active-to-fade transitions fall through in the same
  update, so a boundary update can perform two collision calls.
- Head motion, maximum-length tail clamping, nonnegative tail clamping, and the
  tail-distance 640 cull are implemented in `scripts/th08_laser_model.py`.
- Added six laser tests; all 35 local regression tests pass.

### IDA Persistence

- Commented the laser-loop entry, collision-box construction, three phase
  collision sites, both fallthrough transitions, and the rotated player test.

## 2026-07-22: Complete Corpus Transform-Record Fields

### Observed Queue And Kind Semantics

- All 15 transform kinds present in decoded ECL now have field mappings in
  `scripts/th08_bullet_transform_model.py`.
- Corrected kind `0x20000`: it is a timed active queue barrier and does not stop
  normal bullet movement. Kind `0x2000` is the independent offscreen-culling
  suppression countdown.
- Reflection waits until the entire sprite AABB leaves the playfield. Kind
  `0x400` reflects all edges; kind `0x800` reflects sides/top but counts a
  bottom exit without changing angle.

### Observed Stage-8 Derived Pattern

- Kind `0x1000000` consumes an adjacent `0x2000000` parameter record. Its packed
  dword contains parent-fade, mode, type, color, and child transform-start index.
- The pair supplies both angle/speed ranges, both counts, and child transform
  flags. Stage-8 records use mode 8 and dynamic VM operands for child speeds.
- Added six corpus/geometry tests; all 41 local regression tests pass.

### IDA Persistence

- Named timer threshold/decrement helpers, angle normalization, and playfield
  sprite-AABB testing.
- Commented reflection, cull suppression, queue barrier, template replacement,
  sound, and both derived-pattern records at their setup sites.

## 2026-07-22: Spell Phase Component Manifests

### Static Component Boundary

- Extended every reachable spell occurrence in the route manifests with its
  phase-local call, child-spawn, interrupt, and auxiliary-VM subgraph.
- Enemy-end, health-threshold, and timeout edges are retained as exits but are
  not traversed into the current component.
- Added aggregate and per-subroutine counts for bullet emissions, transform
  definitions, laser spawns, and built-in callback operations.
- Extra spell 201 owns subs `[85, 126, 127, 128, 129, 130]`, including the
  decoded two-record derived pattern at sub 127. Both of its phase exits target
  sub 82. Extra spell 202 owns sub 141 and its transform program.
- Added a phase-boundary regression; all 42 local tests pass after this change.

This mapping is a conservative static ownership result. Runtime branch visits,
emission timestamps, rendered geometry, and screen parity remain differential
trace tasks.

## 2026-07-22: Target ECL Callback Table And Sound Opcode

### Observed Callback Dispatch And Route Use

- Recovered all 32 native function addresses dispatched by ECL `0x88`; `0x89`
  installs the same functions as per-frame enemy callbacks or clears them with
  a negative index.
- Full-route reachability uses 15 indices on Lunatic Final A, 13 on Final B,
  and 5 on Extra. All target callback indices are literal; the manifests now
  retain every invoke/install/clear occurrence, including nonspell subs.
- Implemented target-used boundary bounce, two Reimu rectangular bullet portal
  maps, two Reisen tagged-bullet phase transitions, linked-enemy proximity,
  reciprocal global time scale, and Extra item-type selection in
  `scripts/th08_ecl_callback_model.py`.
- Renamed all 19 target-used callback functions and `g_gameplay_time_scale` in
  IDA, with comments on dispatch order and projectile state mutations.

### Observed ECL 0x71

- Argument 0 enables/disables a spatialized sound queued after the full pattern
  expands. Argument 1 is copied to every bullet and played when a gated
  transform activates.
- Extra derived-pattern subs 127 and 141 select pattern sound 15 and leave the
  transform sound disabled.
- Upgraded opcodes `0x71`, `0x88`, and `0x89` to observed confidence. The
  regenerated catalog has 105 observed, 53 inferred, and 27 unknown slots.
- Added nine regressions across callback dynamics and full-route callback sets;
  all 51 local tests pass after this change.

REA's Hopper provider timed out on both batch and bounded single-function
callback decompilation during this pass. Callback bodies and addresses above
were observed through the connected IDA database; the VM dispatch remains
covered by Evidence `ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`.

## 2026-07-22: Complete Item Motion And Direct Rewards

### Observed Motion State Machine

- Completed motion states 2, 3, and 5 in `scripts/th08_item_model.py`, including
  exact spawn RNG consumption, state-transition timing, collection suppression,
  and state 5's two position updates on its transition frame.
- State 2 consumes targets `x=48+rng(288)`, `y=-64+rng(192)` and interpolates
  from the spawn position for 60 timer frames.
- States 3/5 consume `vy=-2-rng(0.2)` and `vx=signed_rng()*0.6`; both add
  `0.05*time_scale` before their state-specific movement branches.

### Observed Collection Effects

- Implemented numeric types 0..8, full-power conversion of active type 0/2
  items to type 8, Bomb/life caps and fallback, scaled-score and time-item
  paths, and the type-8 one-tenth point conversion.
- Point value uses a strict `y<point_line` full-value condition. On the other
  side of the screen-coordinate line it uses the exact integer order
  `base/2-int(y-line)*int(base/1000)` and truncates to a multiple of 10.
- Recovered point-item extend thresholds: difficulty `<4` uses
  `100,250,500,800,1100,9999` then increments by 500; difficulty `>=4` uses
  `200,666,9999` then the sentinel 99999.
- Added nine item regressions; the item suite now has 13 tests and the full
  suite passes all 60 tests. Python bytecode compilation is also clean.

### IDA Persistence And Evidence

- Renamed the signed-scaled RNG helper, all type-specific item collection
  helpers, power-item conversion, power/score/time mutation helpers, and the
  point-extend threshold helper. Commented all three special motion branches,
  the type dispatch, and both point-value formulas.
- Two new bounded REA requests for the item manager and point helper timed out;
  these detailed conclusions were observed in the connected IDA database.
  Earlier item-system coverage remains Evidence
  `ev_50cb146240388720e6825183ae13c99f83c95141b2f23908d97a88071351120d`.

## 2026-07-22: Registered Frame Order And Reusable Scheduler

### Observed Native Order

- Recovered ascending stable priority insertion in `0x0043C880` and forward
  execution in `0x0043CA50`. Equal priorities retain registration order.
- Confirmed the 60 Hz frame pump executes update before the separately ordered
  render chain.
- Pinned solver-critical priorities 2, 6, 7, 8, 9, 11, 12, 13, 14, 17, and
  18, including live/record/legacy-playback/extended-playback differences.
- Recovered player internal order, timeline-before-enemy order, and the
  priority-14 item -> bucket reset -> hostile bullet -> laser order.

### Executable Boundary And Tests

- Added the game-independent stable scheduler in `scripts/frame_schedule.py`.
  It has no TH08 addresses or subsystem names and preserves adapter-supplied
  priority, registration, internal-event, mode, and confidence metadata.
- Added `scripts/th08_update_order.py` as the TH08 adapter. Static same-frame
  implications are explicitly marked inferred rather than runtime-observed.
- Added ten regressions. The complete local suite now passes 70 tests, and
  Python bytecode compilation is clean.
- Renamed/commented the update/render chain helpers, 60 Hz frame pump,
  gameplay/background/spell callbacks, and bullet spatial-bucket reset in IDA.
  Priority 13 remains deliberately unnamed because its domain role is not yet
  established.

This work was observed through the connected IDA database. The fixed-step
pipeline remains supported by Evidence
`ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`;
the same-frame implications still require game-vs-simulator traces.

## 2026-07-22: Route-2 Focus And Option Shot Sources

### Observed Option State Machine

- Recovered route-2 callback table entries: all four slots use update
  `0x0044EB70` and render `0x0044E9E0`.
- Focus entry allocates four option records before movement. Their callbacks run
  after player movement, so state 1 captures the post-movement player position
  plus offsets `(-30,-16)`, `(-10,-32)`, `(10,-32)`, `(30,-16)`.
- State 2 uses a radius-8 orbit. Initial angles are `0,pi,0,pi`; after timer
  `>12`, angle deltas are `+1.5,-2,+2,-1.5` degrees per update.
- Focus release changes active slots to state 3 and resets their timers. Their
  positions freeze, and state/position clear after timer `>16`.
- Player focus-logic byte `+0x03` changes immediately and selects movement/SHT.
  The separate byte `+0x05` changes only after transition counter `+0x08`
  reaches 7.

### Executable Model And IDA Persistence

- Added `scripts/th08_option_model.py`, including fractional global-time-scale
  timer behavior and the source-index 1..4 mapping consumed by SHT shots.
- Added five regressions; the full suite now passes 75 tests and bytecode
  compilation is clean.
- Renamed/commented the route-2 update/render callbacks, option callback tables,
  focus entry/release sites, post-movement callback loop, and shared timer
  set/advance/equality/greater-than helpers in IDA.

These conclusions were observed through the connected IDA database. No new REA
Evidence was produced; the earlier player-shot batch remains Evidence
`ev_d3ee55dd161e311c6750c0bb9341a85ebeb0e01a139bed11faba302b73060f41`.

## 2026-07-22: Reusable Movement And TH08 Input Adapter

### Observed TH08 Movement Path

- Recovered the native direction test priority `UL,DL,UR,DR,D,U,L,R,neutral`,
  including deterministic behavior for contradictory replay bits.
- Active Bomb state ignores the input focus bit and uses callback-index parity:
  route-2 callbacks 0/2 force the primary-unfocused profile and 1/3 force the
  secondary-focused profile.
- Movement uses primary SHT unfocused cardinal/diagonal speeds or secondary SHT
  focused speeds, multiplies x/y by separate player scale fields, then global
  time scale, updates position, and clamps each axis to runtime playfield
  origin plus extent.

### Executable Separation

- Added game-neutral `scripts/movement_model.py` with direction, movement
  profile, per-axis scale, time scale, and axis-aligned clamp primitives.
- Added `scripts/th08_movement_model.py` for TH08 input bits, branch priority,
  Bomb override, and the exact route-2 SHT speed profile.
- Added six regressions, including an integration check that a focus-entry
  option captures the player's post-movement position. The full suite passes
  81 tests and bytecode compilation is clean.
- Commented the direction, Bomb focus override, SHT speed selection, axis/time
  scaling, position write, and clamp branches in IDA.

These conclusions were observed through the connected IDA database and local
decoded SHT bytes. Existing player/replay coverage remains Evidence
`ev_50cb146240388720e6825183ae13c99f83c95141b2f23908d97a88071351120d`
and `ev_d3ee55dd161e311c6750c0bb9341a85ebeb0e01a139bed11faba302b73060f41`.

## 2026-07-22: Route-2 Priority-9 Runtime And Replay Projection

### Observed Player Boundaries

- Resolved the shared state timer: phase 3 calls the scaled decrement helper,
  while other player phases advance it. Expiry changes phase to 0 before
  movement and the later priority-14 hostile-collision pass.
- Normal initialization uses state 1 timer 120 and therefore transitions to
  state 3 timer 240 on the first callback, immediately decrements to 239, and
  permits same-frame movement. Run-state flag `0x4000` uses timer 10 and the
  shorter 20-callback spawn gate.
- Corrected route-2 initialization to retain focus sentinel byte 2 and all four
  option records in state 1 until the first movement callback normalizes them.
- Recovered Bomb movement-scale timelines: Sakuya normal/Last Spell use 0.5;
  Remilia normal is 0 through local frame 59 then 2.0; Remilia Last Spell is 0
  then 3.0; Dissolve is 0. Common teardown resets both axes to 1 before
  movement on the duration boundary.

### Executable Projection And Persistence

- Added reusable numeric store policies and injected binary32 write rounding
  into the generic movement primitive at native velocity/delta/position store
  boundaries.
- Added `scripts/th08_route2_player_runtime.py` and
  `scripts/th08_replay_player_projection.py`. The latter keeps accepted normal
  Bomb versus Last Spell events explicit instead of inferring them from a
  replay button word.
- Projected all 66,386 frames of local Extra replay `th8_06.rpy`, producing 127
  checkpoints and position hash
  `9bf4956d1ccd1143596522a5a4d0819a724eeda71ce44fccb3ff55f85dbc2957`.
  The five press frames remain marked unresolved, so this is not yet an
  authoritative clear trajectory.
- Renamed the scaled timer decrement, integer-just-reached helper, and flag
  getter in IDA. Commented player initialization/expiry and all route-2 Bomb
  scale/boundary writes.
- The full suite passes 92 tests and Python bytecode compilation is clean.

These conclusions were observed through the connected IDA database and local
replay/SHT artifacts. Existing player/replay Evidence remains
`ev_50cb146240388720e6825183ae13c99f83c95141b2f23908d97a88071351120d`;
no new REA Evidence was produced during the provider timeout window.

## 2026-07-22: General Pattern Motion IR And ECL 0x5F/0xB2/0xB8

### Observed Enemy Motion

- Recovered opcode `0xB2` at `0x00419FF6` and its handler `0x004224A0`.
  Arguments are duration, easing mode, and speed. Its four corpus occurrences
  use `(80,0,1.2)` or `(120,0,1.0)` in stage-4A resources.
- The direction selector consumes four 16-bit RNG outputs total. One quarter
  of executions sample uniformly in `[-pi,pi)`; three quarters choose a cone
  toward player x using the shortest direction on a 384-unit periodic span.
  Top/bottom 48-unit margins reflect angles back into the movement region.
- Positive durations install a stored polar displacement. The common per-frame
  state supports linear, ease-in powers 2..4, and ease-out powers 2..4, then
  snaps to the exact destination on expiry. Non-positive duration installs
  constant polar velocity.

### Clear And Spell Transition Operations

- Opcode `0x5F` calls `0x0042EFB0` with `(8000,0)`, removes eligible active
  enemies, invokes their end subroutines, and gives reward-flag `0x80` enemies
  type-6 scaled-score items. The popup/reward value increases by 30 per item
  and is capped at 8000.
- Opcode `0xB8` directly assigns spell-state bit `0x800`. All 82 shipped uses
  write 1 at time zero in spell-ending subroutines, while spell start/finish
  clear it. The name `set_spell_end_transition_flag` remains inferred from
  context even though the bit mutation itself is observed.

### Reusable Model And Persistence

- Added game-neutral `scripts/pattern_ir.py` with `PolarVelocity`,
  `TimedDisplacement`, and seven easing curves. Added the TH08-specific RNG,
  periodic-x, boundary, and binary32 adapter in
  `scripts/th08_enemy_movement_model.py`.
- Regenerated all ECL reports. The catalog now contains 107 observed, 54
  inferred, and 24 unknown opcode slots.
- Added six regressions; the full suite passes 98 tests and all scripts compile.
- Renamed the `0xB2` selector/installer/update, `0x5F` clear, and `0xB8` bit
  setter in IDA, with comments at selection, easing, expiry, item, and state
  mutation sites.

These results came from the connected IDA database and local decoded ECL
corpus. They remain covered by pipeline Evidence
`ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`;
no new REA Evidence was produced because the native provider timed out.

## 2026-07-22: Boss, Defeat Mode, And Presentation-State Separation

### High-Reach Opcode Consumers

- Opcode `0x53` writes the boss flag, not an unknown secondary behavior bit.
  `enemy_manager_update` consumes it for boss damage/score scaling, boss
  position selection, HP/marker UI publication, and health-zero projectile and
  enemy cleanup. The corpus writes 1 in 190 uses and later clears it in five.
- Opcode `0x81` selects a three-bit health-zero defeat mode. All 368 uses are
  values 0..3. The switch at `0x0042D6AF` controls distinct deactivate, score,
  cleanup, effect, phase, and player-state consequences.
- Opcode `0x91` is presentation-only. In `enemy_manager_render` it reapplies
  saved ANM script IDs to the primary animation and trail nodes. All 107 uses
  enable it, and no movement/collision consumer exists.

### Solver Boundary And Persistence

- Boss identity and defeat mode remain in the game-neutral phase-exit state
  because they change physics/resource consequences. ANM refresh is excluded
  from search snapshots and retained only for visual/runtime validation.
- Corrected the three opcode names and regenerated the corpus catalog: 110
  observed, 54 inferred, and 21 unknown slots.
- Added three catalog regression tests. The full suite passes 101 tests and all
  scripts compile.
- Renamed `enemy_manager_render`, `anm_vm_set_script`, and the boss HP/marker
  publication helpers in IDA. Writers and all relevant consumers are
  commented.

These observations use the connected IDA database and clean executable. The
existing pipeline Evidence remains
`ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`;
no new REA Evidence was produced during provider timeout.

## 2026-07-22: Enemy Bomb-Pause And Damage-Immunity Policies

### Observed Consumers

- Opcode `0xAD` assigns enemy bit `0x40000000`. With that bit set, the enemy
  manager skips the complete VM/motion/phase/damage block while the player
  Bomb-active field or global player-transition state is nonzero. Opcode
  `0xB0` also sets it; defeat mode 3 and the player death/deathbomb transition
  clear it.
- Opcode `0xB7` assigns enemy bit `0x80000000`. It only suppresses the
  player-shot/hurtbox damage block while Bomb is active, leaving normal damage
  enabled outside Bomb. Defeat mode 3 clears this bit as well.
- These are distinct solver policies: one freezes enemy execution; the other
  only prevents Bomb-time damage. Both affect predicted phase duration and
  damage uptime.

### Persistence

- Corrected both opcode catalog names and added a joint regression. Regenerated
  totals are 114 observed, 54 inferred, and 17 unknown; all 105 tests pass and
  scripts compile.
- Commented both writers, manager consumers, the common `0xB0` setter, and
  transition/defeat clear sites in IDA.

These observations use the connected IDA database. Pipeline Evidence remains
`ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`;
no new REA Evidence was produced during provider timeout.

## 2026-07-22: Timeline Spawn Gate And Write-Only State Slicing

### Observed Timeline Control

- Opcode `0xAF` writes the global checked by timeline spawn record types 0..5
  and 0xB/0xC. Nonzero suppresses the call to `enemy_spawn_from_timeline`, but
  the record is still consumed and the stage timeline continues. Zero restores
  spawning. Its five stage-2 writes are `0,1,0,1,0`.
- Added neutral `SetTimelineSpawnEnabled` to `scripts/pattern_ir.py` and the
  inverted TH08 lowering in `scripts/th08_pattern_adapter.py`. The event
  controls spawn side effects and intentionally has no pause/rewind semantics.

### Static State Relevance

- Opcode `0x93` writes `0x004EA290`, whose only direct IDA xref is that writer.
  It is classified as validator-only telemetry rather than assigned a guessed
  phase/display name. A runtime watchpoint remains the check for indirect
  aliasing.
- Regenerated catalog totals are 112 observed, 54 inferred, and 19 unknown.
  Three new regressions bring the full passing suite to 104 tests; bytecode
  compilation remains clean.
- Renamed both globals in IDA and commented opcode writers plus each timeline
  spawn-gate consumer.

These observations use the connected IDA database and decoded stage-2 ECL.
Pipeline Evidence remains
`ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`;
no new REA Evidence was produced during provider timeout.

## 2026-07-22: All Shipped Opcodes Classified And Trail Collision Sliced

### Remaining Shipped Handlers

- Opcode `0x9B` is the fixed spell-reward policy: initial working bonus
  99,999,990, no normal per-frame decay, and fixed capture-result field 700.
  Its separate global sentinel has a writer but no direct executable reader.
- Opcode `0x9D` maintains enemy position/ANM history for trail rendering and,
  when its third argument is above one, repeats player contact/graze tests at
  historical samples. Every shipped third argument is zero, so the original
  corpus uses are presentation-only even though the general opcode can affect
  survival.
- Opcode `0x9F` selects one of four enemy render layers. Opcode `0xB6` selects
  a shared anchor for both secondary enemy ANM slots. Neither has a
  motion/collision consumer.
- Opcodes `0xB3..0xB5` control the stage-background auxiliary ANM sequence;
  the direct `0xB4` disable handler is absent from shipped records but is
  statically observed.

### Generalized Model And Persistence

- Added game-neutral `FixedSpellRewardPolicy` and `HistoricalHitboxTrail`.
  TH08 lowering retains visual configuration separately and emits collision
  state only when collision history is active. This prevents both accidental
  solver-state bloat and loss of gameplay semantics in another game/asset.
- Regenerated the catalog at 121 observed, 54 inferred, and 10 unknown slots.
  All ten unknown slots have zero corpus occurrences; no shipped opcode remains
  unknown.
- Renamed the spell update, vector add, trail-strip builder, stage-background
  sequence helpers, render-layer heads, stage-background manager, and fixed
  reward sentinel in IDA. Writers and render/collision/reward consumers are
  commented.

These are static observations from the connected IDA database and decoded ECL
corpus. They remain covered by pipeline Evidence
`ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`;
no new REA Evidence was produced while the native provider was unavailable.

## 2026-07-22: Deterministic Executor And Event-Boundary Differential Trace

### General Simulation Infrastructure

- Added `scripts/deterministic_sim.py`. It executes an adapter-selected subset
  of a full `FrameSchedule` in native priority/registration order and rejects
  any selected event without a handler. This permits incremental subsystem
  integration without treating unimplemented gameplay as a silent no-op.
- Added `scripts/state_trace.py`. Explicit projections support raw binary32 and
  binary64 comparison, record state after individual schedule events, and
  return the first mismatching frame, event, and field.
- Added `scripts/th08_simulator.py` as the TH08 integration adapter. The first
  slice contains extended replay input publication followed by priority-9
  route-2 player movement/Bomb state at their actual schedule positions.

### Extra Baseline Migration

- Migrated `th08_replay_player_projection.py` to the integrated executor and
  regenerated the stage-8 artifact for `th8_06.rpy`.
- All 66,386 frames retain position hash
  `9bf4956d1ccd1143596522a5a4d0819a724eeda71ce44fccb3ff55f85dbc2957`.
  Bomb edges at 13,041, 27,305, 45,553, 59,744, and 64,086 remain explicitly
  unresolved rather than fabricated as accepted Bombs.
- Four executor/differential regressions bring the full suite to 114 tests;
  all scripts compile.

This infrastructure is analyst-authored design grounded in the already
observed frame order and player behavior. The unchanged Extra projection is a
local regression, not native runtime parity. Static pipeline Evidence remains
`ev_2d76b099af6e1d71a0098c53bfb019c8a22264c3a8cc39a1f6e8d22c7dc44c9c`.

## 2026-07-23: Timeline, Projectile Integration, And Runtime Control

### Observed Native Behavior

- `stage_timeline_step` (`0x0042A8A0`) walks timelines in ascending index
  order and consumes every due variable-length record in one call. Marker
  writes by an earlier timeline are visible to a later timeline in that same
  manager update. Opcode `0x0D` consumes all matching marker slots; when no
  marker matches it holds both the program counter and local clock. Opcode
  `0x0E` fills all negative marker slots. Opcode `0x0A` waits for the indexed
  enemy to become inactive, while `0x08` writes its `+0x2D30` field. Enemy ECL
  opcode `0x7F`, not the timeline scheduler, owns that indexed registry.
- Extra's native frame 400 demonstrates the same-frame dependency: timeline 0
  spawns and publishes an indexed enemy, then timeline 1 observes it and emits
  its dependent spawn before the manager update returns.
- Bullet allocation uses a wrapping cursor, but manager contact/update order is
  slot 0 followed by slots 1535 down through 1. Player collision checks laser
  exact overlap before the broad bullet pass. Bullet exact contact is inclusive
  AABB; player phases 1 and 2 suppress graze, while phase 3 can still graze.
- The Sakuya Bomb call at `0x0040FD0C` passes duration `0x122` (290 frames) in
  the fifth stack argument to `player_begin_bomb_callback`. This corrects the
  earlier model that initialized phase-3 Bomb timing to zero/one.
- A 121-frame built-in-demo observation had no native manager-counter gaps;
  raw keyboard input remained zero while published replay input changed. A
  controlled `th8_06.rpy` run is confirmed as route ID 2 with the gameplay flag
  active; holding raw `Ctrl` did not increase its roughly 60 Hz manager rate.

### Executable Integration

- Added `scripts/th08_timeline_model.py` for stage opcodes `0x00..0x10` and
  exact marker/indexed-enemy boundaries. Added stable-capacity item (2096),
  hostile-bullet (1536), and laser (256) pools with native allocation/scan
  rules where recovered.
- Extended `scripts/th08_simulator.py` so replay/player, timeline, item, base
  straight hostile-bullet, and laser steps share one deterministic executor,
  RNG stream, and event trace. Transform-bearing bullets remain fail-closed
  until their runtime handlers are integrated.
- Added `scripts/runtime_agent.py` and `scripts/th08_runtime_agent.py`. The live
  path verifies the pinned executable SHA-256, observes frame/input/player/
  resource state using `ReadProcessMemory`, and permits `SendInput` only with
  explicit arming plus a foreground-window check. Screenshot capture is only a
  menu/bootstrap audit and never feeds gameplay decisions.
- Bytecode compilation passes and the suite now contains 141 passing tests.
  The unchanged 66,386-frame input-only Extra projection still has position
  hash `9bf4956d1ccd1143596522a5a4d0819a724eeda71ce44fccb3ff55f85dbc2957`.
  Its Bomb edges at 13,041, 27,305, 45,553, 59,744, and 64,086 are pending the
  ongoing native event capture, not claimed as accepted.

### Evidence And Remaining Unknowns

- REA evidence for the timeline scheduler:
  `ev_3d75c2af0f019e8df7781e207f3fad519f39ce8f8b18fa9bb03a21eda10f08a1`.
  REA evidence for timeline enemy spawning:
  `ev_078f61dfaa75fe5464b37dfe0b686b27e1514b5379c04de29301b39bfd400249`.
  Player/Bomb/item/RNG/replay evidence remains
  `ev_50cb146240388720e6825183ae13c99f83c95141b2f23908d97a88071351120d`.
- The exact same-frame ordering above is statically observed and supported by
  the Extra timeline data, but still needs a targeted native differential
  watch trace. Complete enemy ECL execution, every bullet transform, bullet
  cancellation-to-item conversion, death/respawn transitions, and spell-name
  mapping remain unfinished.
- Main-menu selection state has not been assigned a stable memory field. Menu
  automation remains a foreground-gated bootstrap action and is excluded from
  the combat controller's acceptance contract.

### Patched Lunatic Runtime And Physical Dodge Smoke Test

- Migrated the no-life-decrement attach helper into
  `scripts/th08_attach_no_life_decrement.py` and updated the supplied launcher
  batch file to use it. The helper now refuses ambiguous processes and verifies
  exact path, executable SHA-256, PE identity, and patch-site byte before the
  single runtime write at `0x0044D0FA`. Runtime probes report byte `00` and
  `no_life_decrement=true`; the file on disk remains unchanged.
- Entered `START -> Lunatic -> Sakuya/Remilia` and confirmed native
  `gameplay_active=true`, `route_id=2`. A 1,801-frame read-only trace captured
  three death/respawn cycles at manager frames 1,636, 2,057, and 2,865 while
  lives remained exactly `2.0`, proving the patch under real stage updates.
- Added `scripts/th08_live_dodge_agent.py`. It reads bullet slot state at
  `g_bullet_pool + slot*0x10B8 + 0xDB8`, position at `+0xD44`, velocity at
  `+0xD50`, and the 256 lasers beginning at `0x015B57C8`. It then evaluates
  focused nine-direction action trajectories and sends ordinary physical key
  transitions one frame ahead. Screenshots do not enter this loop.
- The first 6,447-frame physical trial saw up to 1,139 simultaneous bullets and
  produced verified movement/Bomb readback. It also exposed two shortcomings:
  the old pre-hit Bomb threshold was too eager, and reading the full 6.6 MB
  bullet pool caused 43 counter discontinuities. Normal Bomb is now opt-in;
  default behavior moves until native phase 2 and only then permits deathbomb.
  Direction-change inertia was reduced to prevent empty-field sweeps.
- The full suite contains 147 passing tests. The live controller remains a
  smoke agent, not a Lunatic/Extra acceptance result: native spatial-bucket
  extraction, dynamic multi-action path search, items, graze objective, and
  executor/runtime differential parity are still required.

## 2026-07-23: First Complete Sakuya/Remilia Lunatic Final-B Run

### Completion And Provenance

- The no-life-decrement run completed all six route resources and unloaded
  gameplay at enemy-manager frame 209,373 with engine flags `0x1AA10`.
  Observed stage entries were Stage 1 frame 1, Stage 2 frame 19,384, Stage 3
  frame 42,139, Stage 4A/Reimu frame 68,119, Stage 5 frame 110,428, and
  Final B/Kaguya frame 151,703.
- Two valid trace segments contain 53,335 decisions and zero JSON decode
  errors. Segment 1 covers frames 1..158,850 and ended fail-closed on foreground
  loss; segment 2 covers 160,535..209,373. The 1,685-frame operator/manual-rearm
  gap is excluded from controlled-play scoring. SHA-256 values and byte sizes
  are pinned in the generated dossier.
- The run produced 91 native phase-2 hit edges: Stage 1 `2`, Stage 2 `4`,
  Stage 3 `13`, Stage 4A `21`, Stage 5 `22`, and Final B `29`. At 62 edges the
  controller requested a deathbomb. The observed 98 Bomb-unit spend is not a
  feasible budget because patched death recovery permits repeated resource
  resets.

### Failure Structure

- Primary classifications are 35 observed bullet overlaps, 18 collisions
  already visible in the committed-input prefix, 18 active-laser unresolved
  cases, and 20 sensor-gap/unmodeled-hazard cases.
- Cross-cutting contributors are stronger: 74/91 missed a corridor deadline,
  68/91 were in fast mode, 32/91 were at a side/bottom boundary, 16/91 had
  more than 1,000 bullets, and 14/91 exceeded the modeled action lag. This
  rejects the current assumption that repeated local corridor waypoints are a
  run-level plan.
- The highest recurrent windows are Stage-3 frames 66,537..67,877 and Final-B
  frames 187,413..189,223, with five hit edges each. Exact per-spell assignment
  is unavailable for this completed run; all 37 statically reachable spell
  cards remain listed without fabricated runtime counts.

### Durable Outputs And Post-Run Fixes

- `scripts/th08_run_dossier.py` streams multiple large JSONL segments and emits
  the review Markdown, provenance/hit JSON dossier, 91-row CSV, and 91-case
  regression input under `notes/runs/` and `artifacts/runtime_reports/`.
- Live observations now decode `g_spell_card_state` flags, owner pointer,
  exact spell ID, and Shift-JIS name. IDA comments pin the layout at
  `spell_card_start` and the active-bit lifetime at `spell_card_finish`.
- Auto-confirm now has a foreground-gated wall-clock path when dialogue freezes
  the manager frame. The same frozen-counter branch detects gameplay scene
  unload instead of waiting forever. The full suite passes 183 tests plus six
  subtests; the fixes still require the next physical full-run recurrence
  check.
