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

`tests/test_th08_routes.py` pins these sets and verifies that target-route
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
  `scripts/tools/th08_attach_no_life_decrement.py` and updated the supplied launcher
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

- Primary classifications are 35 observed bullet overlaps, 20 collisions
  already visible in the committed-input prefix, 11 exact finite-segment laser
  overlaps, five active-laser/no-overlap cases, and 20
  sensor-gap/unmodeled-hazard cases.
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

- `scripts/analysis/th08_run_dossier.py` streams multiple large JSONL segments and emits
  the review Markdown, provenance/hit JSON dossier, 91-row CSV, and 91-case
  regression input under `notes/runs/` and `artifacts/runtime_reports/`.
- Live observations now decode `g_spell_card_state` flags, owner pointer,
  exact spell ID, and Shift-JIS name. IDA comments pin the layout at
  `spell_card_start` and the active-bit lifetime at `spell_card_finish`.
- Auto-confirm now has a foreground-gated wall-clock path when dialogue freezes
  the manager frame. The same frozen-counter branch detects gameplay scene
  unload instead of waiting forever.

### Executable Corpus And Gate Commitment

- `scripts/analysis/th08_fullrun_regression.py` validates all 91 retained case IDs and
  their geometry, classification priority, resource fields, corridor/latency/
  density factors, stage totals, and spell-attribution status. The corpus now
  contains full exact geometry for 35 bullet and 11 laser contact witnesses.
- Corrected the local lexicographic order from
  `collision -> safety -> gate` to `collision -> gate -> safety`. The minimal
  regression preserves a tight left gate by choosing `down_left_fast` instead
  of entering a wider local dead end with `down_fast`.
- The game-neutral corridor planner can constrain a bottleneck gate to a
  left/center/right component. The live async adapter retains that component
  until a fixed non-rolling expiry, falls back only when the constrained
  component is proven unreachable, and resets at stage/live-spell boundaries.
  A synthetic 200-bullet benchmark remained about 27 ms median on WSL.
- The full suite passes 191 tests plus six subtests. These solver changes still
  require the next physical full-run recurrence check.

## 2026-07-23: Stage-Aware Auto-Confirm And Clean Rerun

- The first post-commit physical run controlled Stage 1 frames `1..20587` and
  recorded four native hit edges, but exited at the normal Stage-1 resource
  unload. The frozen-frame fix from CE-0025 correctly noticed gameplay
  inactivity but incorrectly equated every unload with final completion.
- Added a stage-aware scene guard over route-2 progression `0,1,2,3,5,7`.
  It fixes the transition source at the last active stage, releases combat
  keys on unload, drives transition dialogue with complete wall-clock Z pulses,
  logs inactive/resumed provenance, bounds non-final waits to 90 seconds, and
  requires a stable five-second Final-B unload.
- A second old-module segment at Stage 2 frames `21280..41315` was deliberately
  stopped before replacing the daemon. Both segments and their seven hits are
  labelled partial and cannot be combined into complete-run results.
- The Stage-1 trace exposed an independent global-planning flaw: two corridor
  solutions can share the `center` lane label while choosing opposite path
  branches. Stable connected-component identity, rather than lane retention,
  is now an explicit solver requirement.
- The first corrected trace began at frame 1 as `151557` and survived into
  Stage 2, but the boundary proved that TH08 writes the successor index before
  gameplay becomes inactive. It was stopped at frame 23,664. The guard now
  commits stage identity only at initial arm or inactive-to-active resume; all
  195 tests pass. The next clean run remains responsible for full provenance,
  per-hit CSV, executable regressions, and stage/spell/resource review before
  further planner correction.
- The stable-identity `152539` trace then physically validated Stage 1 to
  Stage 2: the inactive interval was 0.295 seconds and the expected stage
  matched. It stopped at Stage-2 frame 28,459 because eight frozen collectible
  items kept the old auto-confirm predicate false forever despite zero bullets
  and lasers. Auto-confirm now models only actual hazards and Bomb state;
  collectible count is absent by construction. All 196 tests pass.
- The `153736` trace crossed Stage 2 to 3 but froze at Stage-3 frame 53,623
  with 189 bullets and 315 items. Manager counter and RNG calls were both
  static, proving that a frozen projectile snapshot cannot be treated as an
  evolving hazard for a shot-key edge. Wall-clock confirm now excludes only an
  active Bomb; the moving-timeline predicate remains hazard-gated. All 197
  tests pass.

## 2026-07-23: THPRAC Stage Isolation And Hard No-Bomb Policy

- Adopted local `thprac.v2.1.3.0.exe` as the fast stage/checkpoint harness.
  The operator owns its menu; the existing F8 daemon takes over only after
  gameplay begins. Original-game full runs remain the integration acceptance.
- The first Stage-3 practice trace began at frame 233 with 8 lives, 8 Bombs,
  and full Power. Its early Bomb consumption demonstrated that deathbomb
  confounded planner diagnosis by changing invulnerability, bullet state, and
  later resources.
- F8 now always passes `--no-bomb`. Both proactive and deathbomb eligibility
  are disabled, the final input mask has a fail-closed Bomb-bit invariant, and
  trace provenance records `bomb_policy=disabled`.
- For causal regression, the first hit of each fresh practice attempt is
  authoritative. Later post-respawn hits are discovery evidence because death
  still changes state even under the no-life-decrement patch.

## 2026-07-23: Stage-3 No-Bomb Practice Review

- Scoped the `160344` thprac trace to Stage-3 manager frames `54..26858`.
  The following frame regression `26858 -> 1` marks a new practice/menu
  timeline; 287 decisions after it are excluded. The agent's raw
  `last_frame=345` summary is therefore not valid as a Stage-3 boundary.
- Verified the hard no-Bomb invariant across all 7,487 scoped decisions:
  controller policy is disabled, input mask bit `0x02` is never set,
  `bomb` is always false, and no action contains Bomb. Bomb-stock changes
  after hits are thprac respawn-state mutations rather than input.
- Recorded 16 native hit edges. Primary classes are six committed-prefix
  collisions, five observed bullet overlaps, three active-laser cases without
  a persisted segment overlap, one exact laser overlap, and one enemy-body
  contact candidate. Fourteen hits use fast mode, 11 follow a missed corridor
  deadline, six exceed modeled action lag, and five occupy a side/bottom
  boundary.
- The canonical fresh-attempt hit is frame 4,885 in spell 35
  `産霊「ファーストピラミッド」`: player `(178.775,156)`, zero bullets,
  zero lasers, projectile pipeline clearance `9999`, and live owner pointer
  `0x5826C0`. IDA proves the contact path
  `0x42CF7A -> 0x42C290 -> 0x44A360`; exact runtime overlap remains a
  candidate because the trace lacks owner position, contact size, and flags.
- Corrected and persisted IDA prototypes for
  `enemy_test_player_contact_at_position` and
  `player_test_deadly_aabb_contact`. The latter is `__thiscall` on player
  state, receives full hazard size, and constructs `center +/- size/2`.
  Because the former scales enemy `+0x2D70` by 1.5, planner half-extents must
  be `0.75 * contact_size`.
- Spell 50 `虚史「幻想郷伝説」` contains the final six discovery hits with
  180-200 active lasers. Its 32 unique corridor results took 895 ms median,
  2.99 s p95, and 3.20 s maximum; solution age reached 193 frames p95.
  This is a planner freshness failure in addition to incomplete laser
  witnesses, not merely a waypoint-scoring problem.
- Added `scripts/analysis/th08_practice_dossier.py` and focused tests. Durable outputs
  are the scoped dossier, 16-row death CSV, 16-case regression JSON, and
  `notes/runs/2026-07-23_lunatic_route2_stage3_nobomb.md`.
- REA independently covered the shipped executable and both collision
  functions as Evidence
  `ev_d0f27bd5ad4f901c2cc242681ed1658f5f790af3994d42dcd56c6eea69eee9e5`
  and
  `ev_686af513e3df698b5342223078b06605432486fe9d179a60bb22ab85434635d9`.
- Implemented the first correction without paying the roughly 10 MB cost of
  scanning all 480 enemy slots per decision. The live sensor reads the active
  spell owner's 1,500-byte movement/contact/flag window, filters it with the
  native contact gates, and lowers the resulting moving AABB into committed
  input-prefix, local MPC, and global corridor checks. Trace rows now persist
  owner geometry plus its snapshot frame. A new hit edge additionally retries
  a native player lethal-rectangle and spell-owner capture until both belong
  to one stable manager frame; projected overlap alone is not promoted to an
  exact dynamic witness.
- Vectorized finite laser-segment clearance in both local and global planners.
  On the preserved frame-25,433 spell-50 snapshot, the global solve fell from
  64.8 ms median before the change (three runs, 52.6..79.7 ms) to 32.7 ms
  median afterward (ten runs, 65.7 ms maximum). A local field containing 44
  nearby bullets and all 200 lasers took 21.0 ms median. These are offline
  component measurements, not a claim that the live hard deadline is solved.
- All 211 unit tests pass. Both the historical full-run corpus and this
  16-case practice corpus pass the generalized regression validator. Physical
  acceptance still requires a fresh no-Bomb Stage-3 run in which frame 4,885's
  spell-35 contact does not recur and spell-50 plan age is measured again.

## 2026-07-23: Stage-3 Corrected No-Bomb Rerun

- The `170433` run is a clean Stage-3 practice scope at frames `93..26383`,
  7,576 decisions, initial resources 8/4/128, and ten hits. All mask, action,
  decision-flag, and controller-config checks pass hard no-Bomb.
- Total hits fell from 16 to 10. Active spell-35 hits fell from two to zero.
  All ten new hit edges have a stable same-manager-frame player lethal AABB
  capture; eight include the active spell-owner AABB, and none overlap. The
  prior spell-35 body-contact failure did not recur.
- Spell-50 finite-segment vectorization physically reduced solve median from
  895.4 to 164.3 ms, p95 from 2.99 s to 362.2 ms, solution-age p95 from 193 to
  27 frames, and stale solutions from eight to zero. Spell-50 hits only fell
  from six to five, proving that stale global computation was real but not the
  sole survival blocker.
- The controller cadence is three frames median and four p95. Spell-50
  pre-hit windows commonly hold one input for four or five frames, while the
  MPC assumed two. The next runtime records complete timing components and
  models action hold from the rolling p90 of observed frame deltas, clamped to
  2..6. Persisted pre-hit subsets show that hold 4 changes five of ten first
  actions and roughly halves beam-search cost.
- Spell-50 bottom-eight-pixel occupancy is 83.1% in the 60 frames before hits
  versus 8.9% outside them. This is stronger than negative corridor slack near
  hits and isolates terminal escape-space collapse as the next global-planner
  target.
- `cffi` alone is rejected as a performance fix. A future native core is
  justified only after full-loop profiling, and must accept contiguous arrays
  in one coarse call rather than crossing the FFI boundary per hazard.
- Durable outputs are the 10-row death CSV, dossier, executable regression
  corpus, generalized comparison JSON, corrected run report, and
  `notes/runs/2026-07-23_lunatic_route2_stage3_nobomb_comparison.md`.

## 2026-07-23: Dynamic-Hold Physical Run And Actuation Split

- Scoped `173245` to Stage-3 frames `56..26550`: 8,884 decisions, initial
  8/4/128, eight native hits, and a complete hard no-Bomb pass. The 359-frame
  `173212` external-stop trace is explicitly discarded.
- Against `170433`, total hits fell 10 to 8 and active spell-50 hits fell 5 to
  1. Spell-50 solve median/p95 became slightly slower at 185/396 ms, solution
  age stayed 28 frames p95, and stale count stayed zero. This supports the
  dynamic action-hold correction independently of solver-speed improvement.
- Complete-loop timing is 27.3 ms median and 45.4 ms p95. Local planning is
  the largest component at 13.7/30.7 ms; pool reads cost 8.5/12.5 ms.
  Transition-bearing SendInput calls cost 1.72/5.53 ms. CFFI remains
  unjustified as the next architectural change.
- Corrected death-ledger causality: the hit-row output is issued only after
  phase 2 is observed. Five hits have an unsafe last-alive committed prefix
  with two-to-three-frame warning; three retain positive causal margin and
  have zero usable warning.
- Of 5,237 unambiguous output transitions, 86.3% are visible in the next
  snapshot with a one-frame median/p95 delta. Actuation delay and action hold
  are now separate plant parameters.
- The live controller now estimates the previous-input prefix from rolling
  p90 operational action lag, default two and clamp `1..4`. Its independent
  action-hold estimate remains rolling p90 decision cadence, clamp `2..6`.
  Both reset at scene transitions and are retained in trace provenance.
- Dossier output now includes active input, post-detection action, last alive
  decision, warning lead, physical contact class, planner failure class,
  action-hold distribution, control-delay distribution, and input-visibility
  evidence. All 215 tests pass.

## 2026-07-23: Scalar Delay Rejection And Adaptive Robust Control

- Scoped `180832` to Stage-3 frames `68..26736`: 8,878 decisions, eleven
  native hits, and a hard no-Bomb pass. The following 1,388 decisions belong
  to a thprac reset tail and are excluded.
- Relative to accepted run `173245`, total hits regressed from eight to eleven
  and spell-50 hits from one to three. Corridor solve p95 improved from 396 to
  384 ms and age p95 from 28 to 27 frames, so global-planner performance does
  not explain the regression.
- The rolling scalar selected delay 2 for 6,505 decisions. Eight hits followed
  a positive last-alive causal margin and three had an unsafe committed
  prefix. Only one hit exceeded the chosen scalar lag. Delay variation changes
  trajectories and cannot be reduced to one conservative quantile.
- Added game-neutral `touhou_control.delay.AdaptiveControlDelay`. It learns
  end-to-end delay only when an issued mask becomes visible in the game's
  native input state, separately records computation and pickup samples, marks
  overwritten commands censored, and expands the tail after hits/overruns.
- The TH08 MPC now validates surviving first actions over the learned discrete
  support until the next command can take effect. Trace and dossier fields
  retain support, samples, guard state, overrun/censored counters, robust
  clearance, worst delay, CVaR risk, and nominal-action overrides.
- Moved all 38 test modules from the flat `scripts/` directory to `tests/`.
  New reusable control code lives under `scripts/touhou_control/`; runtime
  entry points remain stable for the Windows daemon. All 221 tests pass.
- A synthetic dense-field benchmark (400 bullets, 200 lasers) measured local
  planning at 16.7 ms median without robust certification and 21.2 ms with
  support `(2,3,4)`. The next physical run must measure whether this overhead
  widens the very delay distribution it is intended to tolerate.

## 2026-07-23: Adaptive Robust Stage-3 Physical Acceptance

- Discarded the `184708` 239-frame bootstrap after the TH08 window lost
  foreground. The formal `184741` scope is frames `57..26582`, 8,005
  decisions; 477 reset-tail decisions are excluded at counter regression.
- A later `185544` handoff began mid-stage with a hit already present on its
  first retained frame and was safely stopped at frame 22,631. Its two hits
  are kept only as local raw corroboration; it is not a fresh-attempt or
  complete-stage acceptance sample and is not merged into `184741`.
- Hard no-Bomb passed. Six hits occurred at frames
  `2340, 16705, 20469, 22792, 23960, 24489`, down 25% from accepted baseline
  `173245` and down 45% from rejected scalar run `180832`.
- Phase attribution is two nonspells, spell 42 once, and spell 46 three times.
  Spell 35, spell 38, and spell 50 all completed with zero hits. Spell 46 is
  now the dominant focused practice target.
- Local-plan median/p95 rose from 13.7/30.7 ms to 18.2/35.3 ms and decision
  cadence from 2/3 to 3/4 frames. Spell-50 corridor solve p95 rose to 458 ms
  and age p95 to 32 frames, but stale count stayed zero and spell 50 had no
  hit.
- The estimator learned 120 end-to-end transition samples. Support most often
  covered `2..5` or `2..6`; 135 decisions overrode the nominal action. Maximum
  cumulative counters were 50 support overruns and 486 censored/overwritten
  transitions. Native next-observation visibility remained 86.4%.
- Every hit's last-alive robust certificate was already unsafe. Continuous
  robust action-set exhaustion supplied warning leads of 6, 4, 5, 7, 6, and
  3 frames. The dossier now reports and classifies this separately from scalar
  committed-prefix warning.
- This run accepts discrete delay support but exposes two next targets:
  robust viable-successor/reachable-volume scoring before the safe action set
  reaches zero, and true interval-censored pickup estimation instead of
  treating the first matching sampled frame as exact.
- All 223 tests and the six-case executable regression corpus pass.

## 2026-07-23: Robust Backward Viability Architecture

- Replaced the global planner's survival contract from one optimistic forward
  corridor to finite-horizon backward reachability:
  `exists next action, forall learned delays`. Because the prior input remains
  active during delay, the implemented state is
  `V[layer, active_action, y, x]`, not only `V[t,x,y]`.
- Added the game-neutral `scripts/touhou_control/viability.py`. It checks every
  intermediate physical frame, conservatively subtracts nearest-lattice
  sampling error from clearance, retains safe-action masks, and scores the
  minimum successor state-action volume across delay branches.
- The TH08 adapter supplies all 17 focused/unfocused route-2 controls, live
  bullet/laser/enemy clearance volumes, the learned delay support, and the
  currently active input. No TH08 address or input bit enters the neutral
  kernel.
- The asynchronous corridor result now retains the complete policy. The live
  loop queries it by source age, current projected position, and current input;
  a nonempty query hard-constrains the local MPC. Repair volume outranks the
  old waypoint and item/position soft objectives inside that viable action
  set.
- Trace, death ledger, CSV, dossier JSON, and Markdown now retain policy age,
  layer, delay support, viability, safe actions/count, selected repair volume,
  and global-kernel exhaustion warning lead. Global exhaustion is distinct
  from the prior short-horizon robust-certificate exhaustion.
- Added `AGENTS.md` as the binding workspace contract for evidence labels, IDA
  persistence, game-neutral architecture, per-death regressions, complete-run
  artifacts, physical trial protocol, and checkpoint commits. Added
  `notes/ROBUST_VIABILITY.md` as the durable algorithm design.
- A true-size empty-field benchmark fell from about 2.0 seconds before batch
  vectorization to 0.9 seconds on the first solve and 0.65 seconds after
  transition-geometry caching. A 400-bullet/200-laser synthetic field took
  about 1.0 second after warmup. The 80-frame policy remains queryable through
  frame 72, but physical spell-46 data must determine whether solve age leaves
  enough useful horizon.
- Synthetic regressions cover the quantifier-order trap
  (`forall delay, exists action` is rejected), the active-action state
  dimension, intermediate collision checking, continuous sampling margin,
  hard first-action guidance, repair-volume ordering, and asynchronous layer
  queries. All 240 tests pass. Physical acceptance is still pending.

## 2026-07-23: Complete Lunatic Discovery Run And Async Epoch Repair

- Completed one uninterrupted Sakuya/Remilia Lunatic Final-B trace,
  `194644`, through frame 225,973: 69,092 decisions, zero Bomb input, zero
  auto-Z stalls, exact live spell attribution, and 90 hit edges. Stage hits
  were `1/5/10/28/13/33`; Stage 4A and Final B are the dominant focused
  targets.
- The robust layer was effectively absent. Solve median/p95/max was
  2,456/4,039/6,142 ms and first-observed policy age 152/259/3,899 frames.
  Only 759 policy queries existed, 563 decisions were constrained, and 63,653
  robust-mode decisions had no query. The local controller therefore produced
  almost the whole route.
- Dossier v2 proves hard no-Bomb from input/config evidence. The 44-unit
  post-hit Bomb-stock decrease is a respawn reset and is no longer called Bomb
  spend. All 90 deaths are retained in CSV and executable JSON regressions.
- Replaced dense grid-by-hazard clearance with exact-below-cap neighborhood
  scatter and conservative influence-radius grouping. Repair volume moved
  from a full tensor to exact per-query evaluation. The hotkey daemon now
  prewarms transition geometry before F8.
- Added game-neutral `touhou_control.async_policy.AsyncPolicyLead`. Each
  asynchronous solve targets a forecasted future epoch based on rolling solve
  p90 minus overlap; the TH08 adapter projects bullets/enemies and grows
  bullet/laser/enemy uncertainty through that lead. Live traces explicitly
  label pending, queryable, expired, and outside-horizon policies.
- A deterministic Windows stress benchmark with 1,500 AABBs, 250 lasers,
  80 forecast frames, and the full 17-action/80-frame kernel measured
  1,237 ms warm median after optimization. The equivalent WSL median was
  906 ms. Synthetic timing is not physical acceptance.
- Rejected one cross-platform optimization: one large active-action batch
  reduced WSL time but regressed Windows warm time to about 1,903 ms. The
  small-batch implementation remains.
- Current checkpoint is offline-corrected only. The next physical sequence is
  focused Stage 4A, focused Final B, complete Lunatic, then Extra. The first
  acceptance signal is nonzero sustained live viability coverage together
  with fewer hits; resource-aware Bomb/item search remains later.

## 2026-07-23: Final B Rolling-Epoch Review And Native Planner

- Scoped focused Final B trace `20260723_213126` to frames `1..70642` with
  19,289 decisions, 25 native hit edges, and zero Bomb input. The complete
  dossier, death CSV, executable regression corpus, raw summary, and
  diagnostic comparison are retained under `artifacts/runtime_reports/` and
  `notes/runs/`.
- Future epochs fixed policy delivery: Final B policy queries rose from 80 in
  the complete-run reference to 8,454, and constrained decisions rose from 32
  to 3,017. The raw 33-to-25 hit difference is not an acceptance comparison
  because thprac and complete-route phase-entry resources differ.
- Delivery alone was insufficient. The candidate still had 8,834 expired
  decisions, 4,260 empty queried action sets, and 2,409 delay-support
  mismatches. Solve p95 was 2,915 ms, or about 175 frames, against an 80-frame
  policy.
- Per-phase analysis identifies general long-horizon positioning failure:
  bottom-eight-pixel occupancy rose from 20.4% outside pre-hit windows to
  41.0% before hits; negative corridor slack rose from 24.7% overall to 71.3%
  before hits. Spell 166 had five hits, 357/452 empty queries, and 65.3%
  bottom occupancy. Spell 162 had three hits and 518/552 empty queries.
- Replaced the two expensive numerical kernels with an optional game-neutral
  C ABI backend: moving-AABB/finite-segment clearance volume and robust
  backward viability. Python/NumPy remains the reference implementation.
  Randomized full-mask and mixed-geometry parity pass on WSL and Windows.
- Windows retained-stress warm median fell from 1,501.9 ms to 540.2 ms.
  With the full delay support `1..6`, native median/max was 511.4/561.4 ms,
  about 31/34 physical frames. The 80-frame worker is synthetically
  serviceable for the first time.
- Added generic async serviceability telemetry and a bounded delay-support
  submission envelope. The next physical Final B trial must verify the native
  backend, positive serial margin, fewer expired decisions, and retained
  no-Bomb evidence before this correction is accepted.

## 2026-07-23: Final B Multi-Epoch Failure And Transition-Cache Repair

- Scoped the operator-selected later epoch of `222808` to frames `0..72341`,
  excluding 16,964 earlier decisions. The selected attempt contains 17,722
  decisions, 31 native hit edges, and zero Bomb input. Its raw summary
  aggregates two attempts and is explicitly not scope-valid.
- The selected epoch did not test sustained native policy control. Its first
  corridor record appeared at frame 70,798 and source 70,925; all earlier
  phases had zero policy queries. The controller retained the first attempt's
  `corridor_last_submit` timestamp across the zero-based thprac restart.
- Scene resume now resets rolling-policy state and increments a gameplay
  epoch. Async context includes gameplay epoch, stage, and spell so an old
  running future cannot be accepted by an identical restarted phase.
- The trace also invalidated the dense-only native benchmark. Live native
  viability took 4,027 ms median because sparse/open fields preserve many more
  DP branches, while the dense benchmark pruned them early.
- The C++ kernel now caches hazard-independent physical transition indices and
  sampling errors across all delays. Windows warm medians are 294 ms open,
  184 ms at 600 AABBs/52 segments, and 446 ms at 1,500/250. Cold geometry
  construction remains in the pre-F8 daemon warmup.
- Practice artifacts now select a monotone frame epoch explicitly and retain
  earlier/later exclusion counts. The comparison schema is phase-generic and
  no longer assumes Stage-3 spell 50.
- Retained outputs are the scoped dossier, death CSV, executable 31-case
  regression corpus, generalized comparison, raw aggregate summary, three
  Windows performance artifacts, and the run note. Physical acceptance of
  these corrections remains pending a fresh daemon and Final-B attempt.

## 2026-07-23: Final B Policy-Delivery Acceptance And Empty-Kernel Failure

- Clean focused trace `20260723_234414` completed Final B frames `1..70295`
  with 17,723 decisions, 37 native hit edges, zero Bomb input, one frame
  epoch, valid raw summary scope, and no runtime or JSON error.
- The cross-attempt reset and native transition cache passed their physical
  gate. The worker produced 911 native policies at 208/369/609 ms
  median/p95/max, 16,817 decisions had queryable status, and serial coverage
  margin was +32 frames. The prior selected epoch had only five policies, 65
  queries, and a -544-frame median margin.
- Delivery did not improve survival. Of 16,813 available queries, 8,292 were
  empty and only 8,164 constrained the local action. Planner attribution is
  26 global-kernel exhaustions, nine local robust-set exhaustions, and two
  missing preceding alive samples. The raw hit count is six above the prior
  selected attempt.
- The remaining issue is therefore not Python/C++ throughput or SendInput
  pickup. The controller repeatedly enters states outside the finite-horizon
  viability funnel. Pre-hit bottom occupancy is 47.3% versus 20.2% outside
  those windows; spells 162 and 170 each have seven hits, and spell 166 is
  empty for 1,043 of 1,131 policy queries.
- Retained artifacts include a scoped dossier, 37-row death ledger,
  executable regression corpus, prior-attempt comparison, raw summary, and
  the human run note. The next modeling gate is a longer-lived invariant
  funnel with future ECL emission and laser-transition prediction rather than
  further worker micro-optimization.
- A separate `235835` trace recorded an unapproved second arm after the
  completed run. It was safely stopped at frames `5311..8725` with no hit.
  The daemon is now one-shot and exits when its first trial worker finishes.

## 2026-07-24: No-Bomb Feasibility And Phase-Exact Hazard Design

- External existence evidence confirms Scarlet Team no-Bomb completion is not
  merely theoretical: the current LNN database lists 17 Final-B Scarlet-Team
  LNNFS players, and a separate Extra report records Scarlet-Team No Miss,
  No Bomb, Full Spell. External material is used only as an acceptance
  witness; the controller remains based on shipped-game and runtime evidence.
- The `234414` dossier's empty-set rate is 68.95/84.17/57.96/92.22 percent
  for laser-heavy spells 154/158/162/166. Zero-laser phases 170/174/178/182/
  186/190 still range from 41.10 to 79.45 percent, proving that laser geometry
  is a major but not exclusive failure.
- IDA reinspection of `bullet_manager_update` (`0x00431240`) and
  `player_test_collision_and_graze` (`0x0044A6A0`) found that active laser
  transverse half-extent is descriptor width divided by four, because the
  manager passes width/2 and the player helper halves the size vector again.
  The live capsule currently uses descriptor width/2.
- Non-alpha warmup/fade overwrite the longitudinal rectangle size with half
  the ramped/fading width. The live planner instead treats every allocated
  laser as the same full static `tail..head` segment throughout its forecast.
  IDA comments were added at `0x00431C56`, `0x00431E5F`, `0x00432048`, and
  `0x0044A793`.
- REA independently corroborates the native field and control-flow evidence:
  `ev_d0f27bd5ad4f901c2cc242681ed1658f5f790af3994d42dcd56c6eea69eee9e5`,
  `ev_3703fc10b6c9874992d83e523870471a871517461e81f21cd4c1bc9d8480f48a`,
  and
  `ev_1d2d488e8cb1f98bcddeaf0d124c1445884ef4bcb3d163bf19546cc069493a63`.
- `notes/HAZARD_ORACLE_AND_ADAPTIVE_VIABILITY.md` specifies the general fix:
  an offline/instantiated/online-corrected ECL hazard oracle, event-aligned
  exact geometry, adaptive 16/4/2-pixel viability, multiple macro route
  classes, and terminal-kernel overlap certificates. Increasing the present
  uniform 80-frame horizon is explicitly rejected until those model defects
  are corrected.

## 2026-07-24: Unattended Original-Game Practice Bootstrap

- Added a pure original-game Practice Start menu plan for the operator-supplied
  eight-row stage screen: stage keys `1/2/3/4a/4b/5/6a/6b` lower to native
  stage-route indices `0..7`.
- Added `th08_practice_supervisor.py` to enable Caps Lock, recycle only an
  identity-verified TH08 process, launch the existing no-life-decrement BAT,
  verify the patch, acquire foreground, navigate the fresh-process menu, and
  hand the final confirm to an already waiting no-Bomb agent.
- The live agent now accepts expected/terminal stage arguments. It aborts if
  the confirmed native stage differs and treats the focused stage's stable
  unload as completion. Terminal unloads no longer receive transition Z
  pulses; normal cross-stage unloads retain auto-confirm.
- The supervisor prints bounded 30-second progress, writes a session manifest,
  builds practice dossier/death/regression/run-note artifacts, compares against
  the previous unattended attempt for the same stage, releases input, and can
  repeat after terminating the verified game.
- Windows validation exposed CE-0050: IDA's patcher Python has no `numpy`.
  The clickable wrapper now preflights and uses the installed Windows Store
  Python. Linux and Windows focused unit tests pass; armed physical menu
  acceptance remains pending.
- Physical bootstrap `20260724_010112` exposed CE-0052: the fresh team cursor
  starts on the first route. The bounded plan now sends `Right`, `Right`, `Z`
  for the third Sakuya/Remilia entry and still requires native `route=2`
  before the waiting agent can confirm the stage.
- Reverse inspection established the title state machine and removed
  delay-only menu navigation: modes `0/8/9/11` are main/difficulty/team/
  Practice-stage, their live cursor is title-manager offset zero, and only the
  final Practice-stage `Z` commits difficulty and stage gameplay globals.
- Complete unattended Stage-1 run `20260724_011933` physically accepted launch,
  Sakuya/Remilia selection, final handoff, auto-dialogue, terminal unload,
  no-Bomb capture, and artifact generation. It covered frames `2..21008`,
  retained hits `[1893, 6874, 14118, 20028]`, and passed the hard no-Bomb
  audit across 6,306 decisions.
- Post-stage lifecycle now sends one `Right` to select "do not save" and
  immediately kills the identity-verified game. A separate trace-stall timeout
  handles unresponsive terminal/save states.
- CE-0055 corrected session provenance: the launcher now refreshes exact target
  identity after the patch wait, instead of retaining the pre-patch `0xFF`
  snapshot. The accepted Stage-1 trace itself proves the patch was active:
  four hit edges left life stock fixed at eight.

## 2026-07-24: Randomized Stage-3 Baseline And Empty-Kernel Recovery

- Randomized unattended run `20260724_013045` physically covered Stage 3
  frames `1..27610` with 7,887 decisions, 11 hit edges, and zero Bomb input.
  The post-stage `Right` no-save action, refreshed patch identity byte zero,
  and verified process kill all passed their first physical gate.
- The run exposed 4,304 empty queries among 7,608 available. Seven hit windows
  were global-kernel exhaustions and four were local robust-set exhaustions;
  all retained contacts were bullets, so laser geometry was not the immediate
  cause of this run's deaths.
- CE-0056 adds game-neutral soft kernel recovery. Empty queries keep
  `safe_actions=()` but now retain worst-delay successor neighborhood volumes
  for all actions. Exact local collision and clearance remain lexicographically
  above this recovery signal.
- Practice dossiers now report recovery-guided and recovery-selected query
  counts so the next randomized stage can physically accept or reject the
  correction.

## 2026-07-24: Final-B Recovery Trial And Phase-Exact Laser Integration

- Randomized unattended Final-B run `20260724_014545` physically covered
  frames `2..74588` with 16,696 decisions, 42 hit edges, and zero Bomb input.
  The post-stage no-save Right action, refreshed patch byte zero, and verified
  process kill all passed.
- Compared with baseline `20260723_234414`, policy support improved but total
  hits rose from 37 to 42. Recovery was selected on 810 empty-kernel queries;
  its selection rate was 2.17 percent in alive 60-frame pre-hit windows versus
  5.24 percent outside. This is not causal evidence that recovery added hits,
  so CE-0058 keeps it soft and defers acceptance until the hazard oracle is
  corrected.
- Session `20260724_014341` exposed title-menu input overrun: seven queued
  Down taps wrapped the eight-row stage cursor back to zero. CE-0057 replaces
  counted batches with one-edge native cursor feedback and was physically
  accepted by the next launch.
- The live decoder now retains laser maximum length, target/current width,
  speed, five lifecycle thresholds, `Th08Timer`, mode flags, phase, slot, and
  collision/graze byte. IDA inspection of `timer_current` (`0x0040D3B0`) and
  `timer_elapsed_float` (`0x0040B8C0`) corrected the integer timer offset to
  laser `+0x590`; fractional elapsed remains `+0x58C`. Both sites carry durable
  IDA comments.
- `th08_laser_model.py` now reproduces non-alpha warning/fade longitudinal
  ramps, alpha-mode full-length geometry, collision enable/disable gates, and
  both same-update phase fallthrough calls. Each collision call owns its exact
  box, fixing the prior pool-executor ambiguity at boundaries.
- The game-neutral corridor layer gained `SegmentTrajectoryHazard`: adapters
  may supply a finite per-frame segment or absence without embedding TH08
  phases in the solver. TH08 lowers projected lethal laser boxes into this
  primitive and keeps the native AABB/static-segment kernel for the rest of
  the volume.
- A synthetic 52-laser, 80-frame robust solve retained the native viability
  backend and completed in about 174 ms after warmup; time-indexed clearance
  construction was about 35 ms. The full 282-test suite passes. Physical
  acceptance remains required on laser-heavy Final-B phases.

## 2026-07-24: Randomized Stage-5 Baseline And Full Enemy-Pool Sensor

- Randomized unattended Stage-5 run `20260724_022420` physically covered
  frames `2..41917` with 10,157 decisions, 20 hit edges, and zero Bomb input.
  Auto-confirm advanced the long wall-clock transition, post-stage Right
  selected no-save, and the verified game process was terminated.
- The run retained 8 observed bullet overlaps, 10 modeled committed-prefix
  collisions, and two sensor gaps at frames 6,810 and 10,993. Both gaps occur
  in nonspell stage play with no lasers; nearest-bullet clearance is 43.60 and
  13.00 pixels. This directly reopens CE-0033's deferred multi-enemy scan.
- CE-0059 replaces spell-owner-only sensing with one contiguous read of all
  480 fixed enemy slots from `0x005826C0`, stride `0x53D0`. Every
  contact-enabled record is decoded through the already verified
  `0.75 * full_contact_size` lethal half-extents and enters all three planning
  layers. Per-decision telemetry separates enemy-pool read cost so physical
  delay impact can be accepted or rejected. The full 283-test Linux suite and
  53 focused Windows tests pass.

## 2026-07-24: Stage-5 Full-Pool Acceptance And Async Sensor

- Stage-5 rerun `20260724_023923` completed frames `3..41615` with 8,160
  decisions, 18 hits, and zero Bomb. Compared with `022420`, aggregate hits
  fell 20 to 18 and nonspell hits fell 12 to 7. Spell 103 went 1 to 0 and
  spell 115 went 3 to 2, while spells 107/111 worsened by 3/2 hits.
- Frame 11,674 is the first exact full-pool enemy-body witness: stable frame
  11,675 telemetry contains 23 contact-enabled enemies and the native player
  lethal AABB overlaps the slot at `0x005E5F30`. The action snapshot one frame
  earlier contains no enabled bodies, proving that present-state sensing alone
  cannot predict same-frame ECL contact activation.
- CE-0060 rejects synchronous full-pool sensing as the final architecture.
  Enemy reads cost 13.97 ms mean; total read median rose from 11.10 to
  24.91 ms, cadence p95 from four to five frames, and available policy queries
  fell 20 percent.
- The sensor is now a dedicated one-worker snapshot pipeline. Control consumes
  only completed snapshots, projects bodies through their native velocity,
  and adds a bounded age uncertainty. Full-pool read time, source frame, and
  age remain trace-visible; the action loop no longer blocks on the 9.8 MiB
  transfer.
- The full 284-test Linux suite and 52 focused Windows tests pass. A new
  physical run must accept the restored cadence before this architecture is a
  checkpoint.
- Partial latency trial `20260724_025622` disproved continuous background
  scanning: concurrent process-memory bandwidth still kept main read latency
  at 18.51..32.31 ms with 3..5-frame-old snapshots. It was intentionally
  killed at frame 3,303 and is retained as discarded evidence. Scans are now
  submitted at most once per 16 manager frames.
- The same partial exposed CE-0061: the supervisor equated a joined agent
  thread with stage completion. Acceptance now requires
  `termination_reason=route_complete`; killed/partial trials skip no-save and
  receive `status=discarded`.

## 2026-07-24: Stage-5 Throttled Async Acceptance

- Complete run `20260724_030420` covered frames `2..43536`, retained 10,428
  decisions and 24 hit edges, and passed hard no-Bomb, auto-confirm,
  post-stage no-save, and exact-process termination gates.
- One full enemy scan per 16 manager frames restored the action loop: read
  median/p95 was 12.03/24.37 ms and decision cadence median/p95 was 3/4 frames.
  The synchronous run measured 24.91/33.18 ms and 3/5 frames; the pre-sensor
  run measured 11.10/15.43 ms and 3/4 frames.
- Dossiers now retain sensor telemetry. This run produced 1,826 snapshots with
  operational age 11/19/25 frames and capture cost 16.64/26.88/49.22 ms at
  median/p95/max. Eight phase-counter discontinuities are counted separately.
- Aggregate hits regressed from 18 to 24, with per-phase counts
  nonspell/103/107/111/115 = 11/1/4/4/4. Nineteen contacts were already
  modeled bullet failures; four remained sensor gaps and one was a body
  candidate. Since native RNG and phase lengths differ, this rejects only an
  improvement claim, not the sensor architecture.
- CE-0062 fixes comparison provenance: only completed, accepted sessions may
  become automatic baselines. The generated comparison now correctly uses
  complete run `20260724_023923`, not the killed `025622` latency experiment.

## 2026-07-24: Stage-4A Baseline, Native Locks, And Sparse Enemy Sensor

- Original-game Stage-4A run `20260724_033341` completed frames `2..46032`
  with 10,431 decisions, 27 hits, and zero Bomb. Per-phase hits were
  nonspell/57/61/65/69/73 = 10/5/4/3/2/3.
- Twenty-four hits were modeled bullet failures, two were sensor gaps, and
  frame 32,976 retained an exact overlap with helper slot 34. The action
  snapshot was seven frames old and contained one body; stable hit telemetry
  contained 35. This is cross-stage evidence for ECL activation forecasting.
- Stage-4A kept contact bodies in 79 percent of decisions. The contiguous
  9.8 MiB sensor cost 17.71/28.04 ms median/p95 and snapshot age was 11/20
  frames. A fixed-frame eight-body differential showed sparse flag/window
  capture was equivalent in 30/30 pairs and reduced median from 14.06 to
  3.34 ms. The production sensor now uses sparse capture every four frames.
- Original-game Stage 6A bootstrap failures `20260724_032745` and
  `20260724_033256` exposed a native availability mask, not input loss.
  Route-2 Lunatic read `0x40AF`, locking cursor bits 4 and 6. IDA now names
  `g_practice_stage_availability_masks`, names its update locals, and comments
  the bit filter at `0x0046AFCA`.
- CE-0065 corrects live status spell attribution: the renderer now reads the
  nested native spell record used by decision traces.

## 2026-07-24: Stage-4A Sparse-Sensor Physical Differential

- Complete run `20260724_040019` covered frames `2..45775`, retained 10,525
  decisions, 27 native hit edges, and zero Bomb input. The aggregate equals
  baseline `033341`, but phase counts moved from
  `10/5/4/3/2/3` to `16/6/1/2/1/1` for
  nonspell/spells 57/61/65/69/73, so one RNG sample does not support a
  survival-improvement claim.
- The sparse four-frame sensor passed its systems gate. Operational snapshot
  age improved from 11/20 to 5/8 frames median/p95, main-loop read latency
  improved from 12.72/26.03 to 11.71/15.32 ms, and decision cadence remained
  3/4 frames. Capture wall time rose under concurrent scheduling, but it did
  not re-enter the synchronous control path.
- Failure evidence contains 12 bullet overlaps, 11 committed-prefix
  collisions, and four exact enemy-body overlaps; the previous two generic
  sensor gaps fell to zero. Three exact body pointers were absent from their
  action snapshots. Frame 9,505 was the counterexample: 26 helpers were
  already visible, pipeline clearance was negative, and the global viability
  kernel had been exhausted before impact.
- CE-0066 therefore accepts sparse sensing as general observation
  infrastructure but rejects polling as the prediction architecture. The
  next general correction is an ECL executor that injects future
  spawn/contact-enable events into the same hazard timeline.

## 2026-07-24: First Original-Game Stage-2 Coverage

- Unattended run `20260724_042005` completed original Practice Stage 2 at
  frames `2..22886` with 6,087 decisions, eight native hit edges, and hard
  no-Bomb verification. Auto-confirm crossed the dialogue wall, Right selected
  no-save, and the exact game PID was terminated. All four observed spells
  (IDs 16, 20, 24, and 28) were clean; all hits occurred in nonspell waves.
- Contact evidence was four modeled prefix collisions, two exact bullet
  overlaps, and two exact enemy-body overlaps. One body pointer was absent
  from its action snapshot. Planner causality was three local robust
  exhaustions, four global viability exhaustions, and one late positive-margin
  contact.
- Canonical frame 1,582 exposes CE-0067. Bullet slot 637 did not exist in the
  active global policy's frame-1,498 snapshot, appeared at frame 1,545, and
  hit before the next policy's frame-1,594 source epoch. The fixed 48-frame
  lead is no longer justified by the observed 25-frame rolling p90 solve
  time.
- Performance and automation gates passed: read latency was 12.41/15.35 ms,
  local planning 21.48/39.09 ms, control cadence 3/4 frames, enemy snapshot
  age 5/8 frames, and no manual transition input was required.
- Offline CE-0067 correction replaces TH08's obsolete 48-frame lead floor
  with 16 frames, derived from two viability layers and maximum
  control-delay-plus-hold. Cold start remains 80 and the rolling p90,
  eight-frame late-arrival budget, horizon serviceability test, and
  pending/expired states are unchanged. Replaying all 387 ordered Stage-2
  solve durations moves lead median/p95 from 48/48 to 16/18 frames. This is a
  scheduler-only result; a physical Stage-2 differential is required.

## 2026-07-24: Adaptive Policy-Lead Physical Acceptance

- Stage-2 differential `20260724_043310` completed frames `2..23279` with
  6,110 decisions, five hits, hard no-Bomb, working auto-confirm/no-save, and
  exact-process termination. Against baseline `042005`, total hits fell 8 to
  5 and nonspell hits fell 8 to 4; spell 20 regressed from zero to one, so this
  is not a clean-stage claim.
- The intended mechanism is directly visible. Lead median/p95 changed 48/48
  to 16/18 frames, policy age 25/46 to 13/26, unique completed policies 387 to
  766, missing queries 139 to 50, expired policy decisions 23 to 11, and
  support-uncovered queries 61 to 44. Empty queried kernels fell 2,434 to
  2,227. Serial coverage margin increased from 32 to 60 frames median.
- Main-loop safety was preserved: decision cadence remained 3/4 frames,
  read latency was 11.90/15.64 ms, and local plan latency was 22.52/41.57 ms
  versus 21.48/39.09. This accepts CE-0067's adaptive scheduling correction.
- CE-0068 is the next general local/global fusion failure. At the new spell-20
  hit, stale global guidance allowed only three bottom-clamped aliases while a
  visible straight bullet approached for more than 30 frames. A cheap extended
  terminal-threat rollout is required; increasing the full beam horizon would
  spend too much control-loop time.
- CE-0068's minimized six-bullet regression proves that a 32-frame
  constant-terminal-action warning can change the trapped `stay` to
  `left_fast`. Always-on Stage-4A run `20260724_045225` rejected the first
  implementation: total hits remained 27, spell 73 regressed 1 to 4, local
  planning rose 21.36/38.78 to 27.19/45.32 ms, and cadence p95 rose 4 to 5
  frames.
- CE-0069 now gates the heuristic on observed control collapse: player within
  four pixels of a boundary and the global safe labels mapping to at most
  three distinct clamped successors. Only 212/9,439 retained Stage-4A
  decisions meet that condition. A 100-row alternating-order Windows replay
  triggered 6 times and added about 1.7 ms at p95. Conditional physical
  acceptance on random Stage-1 run `20260724_050922` triggered 97/4,850
  decisions while preserving 3/4-frame median/p95 cadence and
  22.04/40.61-ms planning. The run still had four hits, so this accepts the
  performance gate only. Three hit windows exhausted the global kernel and
  one exhausted the robust local action set; those are the next planning
  target.
- That Stage-1 trace exposed CE-0070: frame 19,811 queried a 16-pixel policy
  cell with 9.636 pixels of position error and hard-constrained the player to
  three bottom-clamped aliases. Visible bullet slot 827 hit the stationary
  position 12 frames later. Clamped alias collapse now downgrades the coarse
  mask to soft repair evidence and runs the exact 32-frame cross-check over
  all physical first actions. The minimized regression changes `stay` to an
  escape action. A 68-row dense Windows replay activated 16 times, changed 11
  actions, and measured 8.11/17.32 versus 8.76/16.24 ms median/p95. Physical
  acceptance remains pending.
- Random Stage-2 physical differential `20260724_052616` accepted CE-0070's
  clamped-alias downgrade: total hits fell five to two, nonspell four to zero,
  and the original spell-20 hit one to zero with 3/4-frame cadence. The
  remaining spell-16 hit exposed CE-0071, an off-grid singleton mask that
  forced `stay` for visible bullet slot 866. Singleton downgrade is
  regression-tested but its 200-row dense benchmark adds about 9.5 ms at p95,
  so physical cadence acceptance remains pending.
- Random Stage-6B run `20260724_053742` was intentionally retained as a failed,
  truncated trial. It aborted at frame 34,506 after 24 hits because
  representative rollout and the backward kernel used different midpoint tie
  rules. CE-0072 centralizes round-to-even lattice projection and makes
  residual waypoint inconsistency nonfatal. Dossiers now label runtime errors
  and `accepted_completion=false`.
- The same partial 6B run establishes CE-0073's performance boundary:
  spell 154 held 205--240 lasers, accumulated ten hits, drove corridor solve
  p95 to 1.86 seconds, local-plan p95 to 97.31 ms, and cadence p95 to eight
  frames. Laser broad-phase/vectorization is now a higher-priority
  cross-stage correction than tuning individual spell paths.
- Laser projection now shares exact lifecycle templates across records that
  differ only in origin and angle. Retained frame 22,002 contained 215 lasers
  but only 19 templates; isolated cold projection improved from 372.13 to
  61.48 ms. A fully materialized trajectory-clearance volume regressed the
  same benchmark (about 190 versus 168 ms) and was removed rather than kept as
  speculative complexity.
- Random Stage-6B repeat `20260724_060039` completed through frame 77,112 with
  zero Bomb input and automatic no-save exit. It physically closes CE-0072:
  the midpoint projection mismatch no longer crashes live control. Relative
  to the previous complete 6B baseline, hits fell from 42 to 30; spell 162
  improved from six to one. Relative to the matched pre-cache dense-laser
  phase, spell-154 hits fell ten to five, solve median/p95 fell
  1340/1863 to 936/1345 ms, overall plan p95 fell 97.31 to 55.15 ms, and
  cadence p95 fell eight to five frames. This accepts template reuse only as a
  partial correction: five laser contacts and near-second global solves
  remain.
- Stage-1 baseline `20260724_062416` showed that all four hits followed global
  kernel exhaustion by 109--239 frames, while the existing one-cell repair
  neighborhood often supplied no direction. CE-0074 adds a game-neutral
  worst-delay distance from each action endpoint to the nearest viable
  next-layer state. It remains soft and ranks after exact local safety.
- Initial recovery run `20260724_063701` was rejected as an algorithm
  acceptance: frame 2,512 reported a 32-pixel recovery action but selected an
  81.58-pixel action because intermediate beam pruning ignored the new
  priority. CE-0075 makes deduplication, beam truncation, and final selection
  share the recovery contract.
- Corrected Stage-1 run `20260724_064421` completed at four hits and 3/5-frame
  cadence. Aggregate survival was neutral, but spell 5 changed from three hits
  to zero and 60-frame pre-hit bottom occupancy fell to 1.4 percent. This was
  retained as a behavioral gate, not a survival-improvement claim.
- Random cross-stage run `20260724_065029` physically accepted distant
  recovery: Stage 3 fell from 11 to seven hits versus its prior complete
  baseline, while pre-laser phases fell from 11 to four and spells 38/42/46
  were hitless. Distant recovery was selected 1,761 times at 3/5-frame
  cadence. A native auto-confirm wall pulse at frame 4,700 also advanced the
  dialogue without manual input.
- That Stage-3 run also opens CE-0076. Spell 50's 200 lasers drove corridor
  solve median/p95 to 1255/1565 ms and produced three hits, two with exact
  laser overlap. Lifecycle caching is accepted but insufficient; global
  segment-trajectory clearance needs exact spatial/time indexing.

## 2026-07-24: Exact Native Segment-Trajectory Rasterization

- Profiling a deterministic 200-trajectory, 81-frame workload assigned 780 of
  832 ms to Python's repeated segment matrix construction and reduction. The
  static native volume builder consumed only 3 ms, confirming that lifecycle
  projection and input injection were not the immediate bottleneck.
- Added C ABI `touhou_segment_trajectory_clearance_v1`. The adapter flattens
  authoritative finite samples frame-major, preserving lifecycle gaps. The
  kernel updates the existing volume using exact finite-segment distance and a
  conservative per-segment raster rectangle derived from frame maximum
  clearance plus occupied radius.
- A mixed AABB/static/moving/degenerate/lifecycle-gap regression matches the
  scalar framewise volume within `3e-5`. The full Linux suite passes 303 tests;
  focused Windows corridor and TH08 adapter suites pass 15 and 9 tests.
- Retained 200-trajectory benchmarks report warm clearance/whole-solve medians
  of 43.66/79.76 ms on Linux and 74.13/115.88 ms on Windows. The optimization
  retains all 200 trajectories and the 80-frame horizon.
- Random original-game Stage-1 run `20260724_070946` completed frames
  `2..20786`, hard no-Bomb, with four hits and automatic no-save termination.
  Against `064421`, hits remained four, cadence remained 3/4 frames, and
  global solve median changed 220.53 to 216.93 ms. This is a sparse-phase
  non-regression gate, not dense-laser acceptance.
- The four Stage-1 witnesses become CE-0077. Endpoint distance to a viable
  next-layer cell did not establish a collision-free bridge back to the
  kernel; the canonical frame-1,444 path chattered near a boundary after the
  gate became infeasible. The next general planning correction must make
  recovery path-aware rather than adding a spell-specific steering rule.

## 2026-07-24: Stage-3 Dense-Laser Separation

- Stage-3 run `20260724_072026` physically accepts CE-0076 throughput:
  spell-50 solve median/p95 fell 1255/1565 to 263/333 ms, maximum fell 1660
  to 381 ms, and query coverage rose 243 to 301. The phase still had three
  hits, so no survival claim is attached.
- A new raw-trace analyzer matched 33,230 same-allocation/same-phase laser
  pairs. Head/tail p99 error was zero, maxima were 2.5 pixels for 13/10
  boundary pairs, and origin/angle never drifted. The trace now retains all
  lifecycle thresholds, timer fraction, and uncertainty for cross-phase
  reprojection.
- CE-0078 removes unsupported `0.08/frame` growth only from exact state-backed
  trajectories. Unknown-state fallback behavior is unchanged. Stage-3 run
  `20260724_073640` reduced spell-50 empty queries 180 to 121 while hits stayed
  at three. Total hits rose 10 to 12 under a different route realization, so
  this is model calibration rather than aggregate survival acceptance.
- Retained frame 26,892 profiled three repeated lifecycle projections plus
  repeated array packing. CE-0079 creates one maximum-horizon timeline and
  shares packed frame geometry across prefix, beam, terminal, and robust
  checks. The exact decision and clearance tuple are unchanged; warm offline
  solve is 30.64 ms.
- Physical run `20260724_075004` reduced spell-50 local plan median/p95
  62.46/163.12 to 45.90/135.03 ms, cadence 6/13 to 5/11 frames, and
  over-model decisions 103 to 87. The persistent three hits reject latency as
  the only cause.
- CE-0080 is now the semantic priority. Twice, off-grid singleton downgrade
  discarded a sole global safe action that still had positive exact prefix
  clearance, selected an unrestricted local alternative, and was followed by
  a hit. Relaxation must be conditional on all globally allowed actions
  failing continuous-state prefix validation.

## 2026-07-24: Certificate Preservation And Stage-6B Boundary Contract

- CE-0080 now distinguishes a degenerate coarse mask from a failed
  certificate. Partial clamped aliases keep any real unclamped motion and use
  the 32-frame warning without dropping the mask. An off-grid singleton is
  preserved only with exact delay-prefix safety and repair volume greater
  than one. Retained frames 26,892 and 27,216 remain globally constrained;
  frame 26,928 still relaxes because its allowed action fails exact geometry.
- The first random Stage-6B run `081231` exposed CE-0081 at frame 22,801.
  Robust certificates and TH08 clamp motion, but the local beam discarded raw
  out-of-bounds successors. A prolonged constrained diagonal emptied the beam
  and the neutral fallback caused `KeyError('stay')` during certificate reuse.
- Local motion now clamps per axis, and certificate reuse checks complete
  action-domain coverage. The retained boundary regression plus all 307 Linux
  tests and three focused Windows tests pass.
- Repeat `081952` completed Final B frames `2..75091`, hard no-Bomb, with 18
  hits and automatic dialogue/no-save handling. Against complete baseline
  `060039`, hits fell 30 to 18 and spell-154 solve median/p95 fell
  936/1345 to 246/346 ms. Multiple intervening accepted changes prevent
  isolated survival attribution.
- The complete run opens CE-0082. Every hit followed global-kernel exhaustion,
  12 involved a boundary, and pre-hit bottom occupancy increased 30.4 to 51.7
  percent. Spell 170 alone produced six bullet-only hits at the bottom edge.
  Scalar distant recovery needs a robust path/control-reserve extension; the
  next change must preserve the earlier cross-stage recovery acceptance.

## 2026-07-24: Delay-Scaled Recovery Control Reserve

- Empty-kernel ranking now prices the loss of one maximum-supported-delay
  unfocused command near each playfield boundary. Exact collision, terminal
  threat, and local safety remain higher priorities; reserve only breaks
  heuristic recovery choices before scalar distance.
- A reusable retained-trace ablation covers Stage 1, Stage 3, Stage 4A, and
  Stage 6B. Broad 200-sample median reserve deficits fell to zero on all four
  stages. Stage-4A zero-deficit selections rose from 79 to 151, while p95
  planning changed from 21.00 to 22.74 ms.
- Random original-game Stage-4A run `20260724_084835` completed frames
  `2..43356`, with 19 hits, zero Bomb input, automatic dialogue, and automatic
  no-save termination. Complete baseline `045225` had 27 hits.
- Pre-hit bottom occupancy fell from 40.5 to 23.2 percent. Nonspell hits fell
  12 to eight and spell 61 fell one to zero. This is directional physical
  acceptance despite intervening solver changes; it is not an isolated
  survival attribution.
- The new dossier retains selected reserve percentiles and pre-hit/outside
  means. Stage 4A still had 16 global-kernel-exhausted hit windows and 11
  boundary hits; pre-hit mean deficit was 3.654 versus 0.581 outside. CE-0082
  therefore remains open for a collision-checked bridge back to viability.

## 2026-07-24: Full Async Delay Envelope And Stage-2/5 Random Gates

- Async corridor solves now cover the complete configured control-delay
  support `{1..6}`. A cached policy can outlive several estimator updates, so
  padding only the current support by one did not establish the universal
  delay contract at query time.
- The single policy worker is now work-conserving with an eight-frame minimum
  submit interval. It still permits only one solve in flight; this changes
  freshness without creating a stale backlog. Query records retain
  `phase_frames = age % frames_per_layer`.
- Random Stage-2 run `20260724_091120` completed frames `1..23129` with three
  hits and zero Bomb. Total hits rose by one versus complete baseline
  `052616`, but all four spell phases became hitless. The final nonspell hit
  exposed CE-0083: a layer-3 certificate at age 30 represented the age-24
  boundary and was six frames out of phase.
- Random Stage-5 run `20260724_093713` completed frames `2..40607` with 15
  hits and zero Bomb, down from 24 in complete baseline `030420`. Available
  policy queries rose from 7,806 to 8,010, unique policies from 626 to 1,283,
  unsupported-delay queries fell from 148 to zero, and decisions without a
  query fell from 201 to 71. Solve median/p95 changed from 291/422 to
  299/445 ms.
- Stage-5 phase hits changed from nonspell/spells 103/107/111/115 counts
  `11/4/2/4/3` to `3/2/1/6/3`. The aggregate gain therefore does not accept
  spell 111. Three of its six retained hits had no modeled contact despite
  exactly 96 stopped bullets, opening CE-0084.
- An exact local retry that drops a contradicted stale mask was benchmarked
  across retained Stage 2, 3, 4A, and 6B samples. It had inconsistent
  collision effects and approximately doubled local planning on the sampled
  contradictions. It remains an explicit, default-off research switch; the
  physical Stage-2/5 runs used the hard certificate path.
- Linux passed 312 tests plus 14 subtests. Focused Windows live-agent,
  async-policy, and fusion-benchmark suites passed 63 tests.

## 2026-07-24: Native Stop/Resume Runtime Layout

- REA evidence `ev_7f655f7f0cb4948ce0753ef441b6bef7a3008601e345b6b8f40d40db44054338`
  confirms bullet spawn copies `0x6C` dwords (432 bytes, 18 records) to
  `+0xDD0`, copies original flags to `+0xDB0`, clears active flags at
  `+0xDAC`, initializes queue index `+0xDCC`, then calls
  `bullet_apply_next_transform`.
- Queue/setup evidence
  `ev_f80073c867ce14ae63fe52283dcfeeea322b83b3368b790fb539960fcd65ae2d`
  confirms each record is 24 bytes and the 0x40/0x80/0x100 shared setup stores
  record floats in `+0x1014/+0x1010`, resets the timer at `+0x1004`, and
  stores duration/repeat limit/count at `+0x1024/+0x1028/+0x102C`.
- Handler evidence
  `ev_cb4ea55181ccda8975025583d74b724906f398c642cb3cbfb4ab7e3935304de0`,
  `ev_32f2db8cee21ec27800551c2a308ed12c19f57c8d0593bf894f68bed4c59b37f`,
  and
  `ev_7cf3f4a46e21867c5be0c74c5188fd83f6b6843f6784f33a01f715e024fd34d5`
  establish turn, absolute snap, and player-relative re-aim completion
  behavior respectively.
- Timer evidence
  `ev_8cd3b7f623c9bb779121d7d21491b3812bc30fcf9d5284100e63f9868c1050ae`,
  `ev_ba62f112b8bfb52df89711e970634c49babc138aaea9889f1e8dbe6fe05bd41e`,
  and
  `ev_5c50a5e1604263f7141eb0013c3567acf78174ebb964cf6c66a5214889725ae9`
  identify elapsed integer at timer `+8`, fractional elapsed at `+4`, and the
  per-update integer advance. For the bullet timer rooted at `+0x1004`, these
  are `+0x100C` and `+0x1008`.

## 2026-07-24: Behavior-Neutral Live Transform Decoder

- **Observed in IDA:** `bullet_apply_next_transform` computes
  `bullet + 0xDD0 + 24 * queue_cursor` at `0x00430001`. It advances
  `+0xDCC` when a record is skipped, executed immediately, or installed as an
  active handler. The cursor therefore selects the next unconsumed record;
  the active stop record has already moved into `+0x1010..+0x102C`.
- Added native 24-byte record parsing and a compact
  `BulletTransformRuntime`. Live bullets now retain finite native speed/angle,
  original flags, queue cursor and next record, timer fraction/elapsed,
  duration, resume speed, angle operand, and repeat limit/count.
- The first eight `nearby_bullets` fields remain byte-for-byte structurally
  compatible with dossiers and retained replay tools. A ninth optional list
  carries transform runtime only for transform-relevant bullets.
- **Inferred architecture:** TH08 owns runtime layout and transform semantics.
  This checkpoint deliberately leaves the local linear bullet frames and
  global `MovingAabbHazard` lowering unchanged; a later native same-slot
  differential must validate stop/resume/re-aim timing before either planner
  consumes the fields.
- Five CE-0084 parser/decoder/schema/neutrality regressions and 33 adjacent
  transform, corridor, dossier, and report tests pass. The physical
  differential remains pending.

## 2026-07-24: Stage-5 Decoder Capture And Full-Pool Diagnostic Gate

- Failed bootstrap session `20260724_103511` lost foreground before gameplay,
  invoked the existing fail-closed cleanup, and is excluded from all physical
  conclusions. No target or agent process remained.
- Complete behavior-neutral Stage-5 run `20260724_103617` covered frames
  `2..41593`, recorded 12 hits and zero Bomb input, reached
  `route_complete`, handled no-save automatically, and terminated the exact
  target. Spell 111 itself was hitless in this randomized attempt.
- The compact spell-111 transform report covers 798 decisions and 159,692
  decoded runtime samples. A radius-160 trace saw a median 229 relevant
  bullets but only 61.5 percent of the native active pool. Every retained
  active flag was zero, so it contained no active-stop adjacent pair.
- **Inference:** The decoder is physically readable but the player-centered
  trace cannot validate an offscreen transform lifecycle. Absence of active
  flags in this partial observation is not evidence that the handler never
  ran.
- Added an explicit `--trace-transform-runtime` diagnostic that serializes
  only transform-relevant bullets from the full native pool. Default
  acceptance traces remain unchanged. `scripts/analysis/th08_transform_trace.py`
  streams raw
  JSONL into a compact, hashed same-slot differential with coverage, flag,
  queue, timer, motion, angle, and repeat evidence.
- The next behavior-neutral Stage-5 run must enable this diagnostic and
  produce adjacent active stop/resume samples before projection code is
  allowed to consume the runtime state.

## 2026-07-24: Spell-111 Callback Mechanism And Rejected Transform Hypothesis

- Complete diagnostic run `20260724_105457` covered the whole 1,536-slot
  bullet pool during spell 111. Its compact source-hashed report retains
  189,877 samples at 100 percent active-pool coverage. Active flags were
  always zero, original flags were always `0x00100202`, the queue cursor was
  always zero, and no queued stop transition occurred.
- **Observed runtime differential:** Same-slot groups changed from normal
  velocity to zero together at frames 35,689 and 36,047, then resumed at
  35,788 and 36,148. The approximately 100-frame zero-velocity interval
  rejects the queued 0x40/0x80/0x100 hypothesis while preserving the
  previously recovered transform layout as a separate mechanism.
- **Observed static/native cause:** `ecldata5` sub 63 invokes callback 12 at
  local times 350 and 450 and jumps from 710 back to 350. Callback 12
  (`0x00424A20`) matches VM tag mask `+0x18` against bullet original/tag flags
  `+0xDB0`, toggles bullet phase `+0x1FC`, presentation state, animation,
  aux byte `+0x10B4`, and velocity. Its phase-one branch uses VM
  angle/speed `+0x38/+0x3C`; the other restores bullet base angle/speed.
- No new REA claim is used for the callback conclusion. The earlier queued
  transform evidence remains
  `ev_7f655f7f0cb4948ce0753ef441b6bef7a3008601e345b6b8f40d40db44054338`,
  `ev_f80073c867ce14ae63fe52283dcfeeea322b83b3368b790fb539960fcd65ae2d`,
  and the handler Evidence IDs recorded above; the new separation is based on
  decoded shipped ECL, IDA/native code, and physical same-slot traces.

## 2026-07-24: Piecewise Hazards, Adversarial Differential, And Failed Activation

- Added a game-neutral finite piecewise-linear trajectory contract. A
  `VelocityChange` applies before movement on its event update. The neutral
  corridor planner accepts time-indexed AABB trajectories, and both the
  scalar oracle and native C++ backend lower those trajectories without
  fitting a constant velocity.
- Added deterministic adversarial generation with straight, stop, resume,
  redirect, and reversal cases. The retained benchmark uses seeds
  `8008..8011`, 2,048 hazards per seed, and 32 frames—denser than TH08's
  1,536-slot native pool. Native volumes match the independent scalar oracle
  within `1.72e-5` against a `5e-5` tolerance. Failure paths retain the seed
  and delta-debug the hazard subset. This is a differential gate, not physical
  acceptance.
- Complete Stage-5 run `20260724_113250` recorded 21 hits and zero Bomb.
  Spell 111 had hits at frames 39,706 and 41,151. The compact callback report
  retains 42,377 stopped `(phase=0,aux=1)` samples, 83,930 moving
  `(phase=1,aux=0)` samples, and 3,037 adjacent coordinated state/motion
  changes.
- **Failed implementation gate:** Every one of 844 lookahead records had
  timer zero, zero future events, and zero attached bullets. VM `+0x94/+0x98`
  had been mistaken for the main timer. Runtime memory and native opcode-4
  code establish the actual timer at `+0x04/+0x08/+0x0C`; opcode 4 stores its
  target time to `VM+0x0C` and adds the signed displacement to the current
  instruction address.
- The real decoded sub-63 loop now forms an executable regression: from
  pending jump `0x6FE8` at timer 600 it predicts callbacks at `+110` and
  `+210`. The live trace exposes instruction count, stop reason, horizon
  coverage, tag/phase/attachment counts, and capture-frame windows, so a
  future run cannot silently claim this feature while attaching zero hazards.
- Corrected a second timing ambiguity before another physical run.
  `HazardEpochAlignment` distinguishes old source-state lag, fresh hazard age,
  ECL-to-hazard event offset, and capture-window uncertainty. The corridor no
  longer advances newly read bullets by the older player-state lag.

## 2026-07-24: Callback Activation Regression And Sparse Native Projection

- Complete Stage-5 run `20260724_120128` reached `route_complete`, emitted no
  Bomb input, and recorded 31 native hits. It is a regression from the prior
  21-hit run and cannot be an acceptance baseline.
- **Observed activation:** Spell 111's ECL timer covered 1 through 709 with
  eight loop resets. Future callbacks appeared on 672/721 rows and attached
  bullets on 544 rows, including both stopped and moving callback states.
  This closes CE-0085's silent-zero-attachment failure.
- **Observed performance cause:** Spell 107 attached a median 988 event-driven
  bullets and reached `463.87 ms` local-planning p95 with `7/37`-frame
  median/p95 cadence. Spell 115 had no callback events and retained
  `39.90 ms` local p95 with `4/6`-frame cadence. The adapter had expanded each
  attached bullet into 81 Python `AabbHazard` objects before entering C++.
- Replaced that dense boundary with game-neutral `PiecewiseAabbHazard` and
  `touhou_piecewise_aabb_clearance_v1`. The new native ABI accepts double-
  precision initial kinematics, float geometry/uncertainty, and compact
  per-hazard velocity-event offsets. The sampled trajectory path remains a
  fallback and an ablation.
- Initial float-native projection failed the unchanged adversarial tolerance
  at approximately `8.3e-5`; the gate was not weakened. Double kinematics
  reduce maximum error to `9.54e-7` over four seeds, 2,048 hazards, 32 frames,
  and up to six events.
- Retained benchmark `piecewise_native_speed_seed82408.json` measures a
  `4.89×` median end-to-end speedup for 1,024 hazards over 80 frames:
  `325.88 ms` dense versus `66.70 ms` sparse. Python lowering falls from
  `218.80 ms` to `1.01 ms`; maximum dense/sparse volume difference is
  `2.01e-5`.
- **Observed epoch bug:** Spell-boundary decisions 27,169 and 36,140 joined
  source state to bullet pools across native `+1800/+1801` counter jumps.
  `HazardEpochAlignment.total_frame_extent` and `fits_epoch` now expose this
  generally. Live TH08 control rejects extents above eight frames, releases
  movement, advances the gameplay epoch, clears cached planning state, and
  logs `sensor_epoch_discontinuity`.
- Linux passes 345 tests. Windows Python passes 54 live-agent, 18 corridor,
  and two adversarial focused tests with the rebuilt x86-64 DLL.
- Physical acceptance is deliberately deferred to a randomized non-Stage-5
  run so the performance/epoch correction is not judged only on Reisen.

## 2026-07-24: Stage-3 Cross-Control And Action-Time Deadline Guard

- Complete randomized Stage-3 run `20260724_123136` reached
  `route_complete`, emitted zero Bomb input, and recorded eight hits. All
  Stage-3 spell lookahead rows had zero callback events/attachments, so this
  is a valid non-Reisen architectural control. Eight lies within the retained
  Stage-3 range `7..12`; no improvement claim is made.
- All eight hits followed robust viability exhaustion. Spell 50 contributed
  four hits and 98/308 decisions beyond the six-frame action-delay support.
  Three contacts were at or immediately preceded by invalid action timing.
- Frame 11,056 proved the existing epoch guard was incomplete: capture
  9,254..9,255 passed, then the counter jumped by 1,800 during local planning.
  The stale action issued at lag 1,802 and old corridor state survived into
  later queries.
- Added game-neutral `ActionIssueAlignment`. TH08 now revalidates immediately
  before input: ordinary delay-support misses suppress the new direction and
  retain planned/issued telemetry; implausible post-capture advance releases
  movement and invalidates the gameplay epoch.
- Corrected dossier attribution to use the support high value and the last
  alive causal decision. The Stage-3 compact dossier now marks hit frames
  26,246, 26,759, and 27,421 instead of only the hit-row overrun.
- Profiling identifies batched laser lifecycle construction as the next
  measured local C++ candidate, but the algorithmic empty-kernel recovery
  problem remains separate. The next solver experiment is a max-min robust
  clearance value whose positive threshold must exactly reproduce Boolean
  viability before negative-margin ranking is considered.

## 2026-07-24: Max-Min Live Rejection And Fused Laser Projection

- Added a threshold-free robust max-min clearance recurrence and compact
  native policy. For every clearance threshold its positive set exactly
  matches the existing Boolean viability kernel. Full and compact native
  implementations match the scalar/NumPy oracle; the compact 32-frame policy
  benchmark is approximately `38 ms` and `0.40 MB` on the Linux host.
- Complete Stage-3 run `20260724_132007` explicitly enabled the 32-frame
  safety value. It reached `route_complete`, emitted zero Bomb input, and
  recorded 15 hits—the worst of seven retained complete Stage-3 attempts.
  Because the native RNG states differ, this aggregate is a failed experiment,
  not a controlled causal estimate.
- Global solve median/p95 rose `245.11/398.44 -> 300.86/461.06 ms`; the
  safety-value phase cost `49.97/58.70 ms`. Spell-50 local-plan p95 rose
  `134.69 -> 210.37 ms`, pre-trace p95 `182.58 -> 258.44 ms`, and action-lag
  p95 `10 -> 15` frames. The model remains an offline/opt-in oracle and live
  default remains zero.
- A retained paired replay made the safety guidance active on identical
  hazards. It changed 168/300 actions without increasing robust-collision or
  negative-clearance counts. The evidence therefore separates a plausible
  compute-contention failure from an unproved ranking failure.
- The issue-time guard suppressed all 96 expired new actions and caught one
  `+1803` post-capture logical jump at issue frame 21,141. It released input
  and invalidated the gameplay epoch. This physically closes stale new-input
  injection, but five spell-50 hits show that holding the older command is not
  a survival certificate.
- Profiling the 200-laser phase found an avoidable object pipeline:
  lifecycle geometry became thousands of `Laser` dataclasses and was then
  immediately unpacked into NumPy arrays. Fusing lifecycle projection into
  contiguous structure-of-arrays frames reduced retained whole-decision
  median/p95 `33.97/56.96 -> 23.44/46.52 ms` (`1.45x/1.22x`) with zero
  complete-decision differences on 100 spell-50 samples.
- A C++ finite-segment micro-kernel was prototyped and rejected. After fusion
  it only improved whole-decision median/p95
  `23.31/42.29 -> 22.19/39.09 ms`, while a changed reduction order altered
  1/100 actions. No native code from that exploration is retained.
- Linux and Windows Python each pass 360 tests. Both ignored native libraries
  were rebuilt from the retained source. Physical verification must now use a
  different randomized stage with safety value disabled.

## 2026-07-24: Stage-6B Cross-Control And Hard-Before-Soft Pruning

- Complete randomized Stage-6B run `20260724_135201` reached
  `route_complete`, emitted no Bomb input, and recorded 27 native hits.
  Retained complete Stage-6B hit counts are `42,30,18,27`; native RNG differs,
  so the result is a cross-stage workload rather than an improvement or
  regression claim.
- The fused laser path passed its physical performance check. Spell 154 local
  planning changed from 41.9/115.1 to 31.8/111.7 ms median/p95 against the
  comparison run. Total local planning was 24.48/46.69 ms, and global spell-
  154 solves remained 290.61/454.02 ms, so four spell hits keep survival open.
- Twenty-four of 27 hit windows followed global viability exhaustion.
  5,518/12,374 queries had empty action sets, 17 hits carried a boundary
  factor, and pre-hit control-reserve deficit averaged 10.043 versus 1.422
  elsewhere.
- Paired replay exposed CE-0089: soft boundary reserve participated in beam
  pruning before uncertain-delay first-action certificates were computed.
  Enabling reserve increased robust-collision selections `24 -> 26` and
  negative-certificate selections `39 -> 42` over 300 identical decisions.
- The planner now computes those existing certificates before beam expansion,
  ranks certificate collision/negative clearance before every soft term, and
  reuses the result during final robust selection. Corrected enabled/disabled
  counts are equal at 22/36 over 300 rows and 56/72 over 213 pre-hit rows.
  `test_ce_0089_delay_certificate_precedes_recovery_beam_pruning` pins the
  beam-width-one failure.
- Default live bullet decoding now omits diagnostic queue/stop runtime objects
  while retaining every gameplay field, including original callback tags.
  Explicit `--trace-transform-runtime` retains the full evidence path. The
  stable trace runtime field remains null in planning mode; a separate compact
  projection payload retains callback tags, phase, attached velocity events,
  and uncertainty so default physical failures remain reproducible. A dense
  800-record regression exercises the NumPy gather branch. The retained
  200--1,200-record benchmark reports exact gameplay-field parity and
  1.25x--2.24x median decode speedup.
- A new algorithm review formalizes the solver as a robust min-max game,
  requires hard dominance at every approximate search operator, sketches a
  time-expanded recovery-band value, and sets objective gates for future C++
  boundaries. A naive action-stratified beam that broke terminal-threat
  regressions was removed rather than weakening tests.
- Linux and Windows Python each pass all 362 tests. No native source changed
  in this checkpoint.

## 2026-07-24: Stage-5 Cross-Check, Latent Spell Body, And Soft Objective Scale

- Complete randomized Stage-5 run `20260724_144805` reached
  `route_complete`, emitted no Bomb input, and recorded 16 native hits.
  Different RNG and respawn histories make the prior 31-to-16 delta
  descriptive only.
- The sparse C++ piecewise trajectory path is now physically performance-
  accepted. Against `20260724_120128`, spell-107 local-plan p95 changed
  `463.61 -> 50.44 ms` and cadence p95 `37 -> 8` frames; spell 111 changed
  `142.72 -> 40.95 ms` and `13 -> 6`. Overall global solve p95 changed
  `623.50 -> 485.81 ms`.
- Default trace analysis initially reported zero transform coverage because
  it understood only the optional diagnostic field. It now decodes the
  lightweight planning projection. Spell 107 retained 186,521 projected
  samples, 99,176 with velocity events; spell 111 retained 104,595/102,870.
  The latter includes 28,761 stopped and 75,834 moving callback states.
- The recovery-reserve benchmark now reconstructs full diagnostic or
  lightweight piecewise trajectories. Stage-5 paired replay preserves
  disabled/enabled hard counts at 28/45 over 300 rows and 18/24 over 60
  pre-hit rows while materially reducing selected boundary deficit.
- Fifteen of 16 hits still followed global-kernel exhaustion. Thirty-two of
  6,901 decisions missed the issue-delay support; three coincided with hits,
  but all three were already modeled collisions. Two `+1803/+1806` action
  epoch jumps were rejected. Performance and stale-input gates pass; survival
  recovery remains open.
- CE-0090 records a repeated spell-115 zero-projectile collision cluster at
  upper-center coordinates across five independent runs. The latest chain
  carried a pre-spell corridor `up_fast` through a context change, retained it
  with a 24-point reversal penalty, and then reinforced the climb with
  residual-item potential.
- The adapter now reads the current spell-owner geometry synchronously and
  lowers the union of latent contact-disabled/enabled modes. Context changes
  retain the physical old-command prefix but remove previous-context soft
  inertia. Item approach potential is reduced, and total item influence is
  saturating. No spell ID or coordinate is special-cased.
- Linux and Windows Python each pass all 368 tests. Native source did not
  change.

## 2026-07-24: Stage-5 Owner-Slot Root Cause And Physical Follow-Up

- **Observed:** Reisen's active spell-owner pointer is `0x0057D2F0`, exactly
  one `0x53D0` enemy stride before the ordinary 480-slot scan base
  `0x005826C0`. The previous “full enemy pool” sensor omitted the boss by
  construction.
- The live adapter now exposes whether the authoritative owner is covered by
  the async range. The regression uses the observed special-slot address and
  pins both range boundaries. This stays in the TH08 adapter; no generic
  planner contains a Reisen, stage, spell, or coordinate exception.
- Complete hard-no-Bomb Stage-5 run `20260724_152719` reached
  `route_complete` with 21 native hits. The compact dossier retains 2,658
  synchronous owner observations: 2,640 contact-enabled, 18 anticipatory,
  zero errors, and all 2,658 outside the ordinary scan.
- **Inferred from observed geometry:** At spell-115 entry the boss body was
  centered at `(192,128)` with half-size `(36,24)`. Its rectangle contains
  every coordinate in the five-run zero-projectile upper-center death
  cluster. The targeted cluster did not recur: no zero-bullet spell-115 row
  placed the player above `y=160`.
- The sole spell-115 death was frame 41,768 at `(8,432)` amid 1,145 bullets
  with negative modeled pipeline/robust clearance. All 21 run hits followed
  global viability-kernel exhaustion; 17 were modeled committed-prefix
  collisions and four had exact bullet overlap.
- Total hits changed `16 -> 21`; spell-107 changed `3 -> 9`. This is not an
  overall-regression or improvement claim because RNG, respawn, Power, and
  phase duration differ. Overall local planning remained `27.85/47.50 ms`
  median/p95 and global solve `285.01/474.16 ms`; spell-115 read time
  `13.64/17.45 ms` shows no material synchronous-read tail regression.
- Compact dossier output now retains synchronous owner counts, contact modes,
  errors, pointer frequencies, per-spell counts, and async-range coverage so
  the ignored raw trace is not required to reproduce this conclusion.
- The next physical gate is a randomized non-Stage-5 control. The remaining
  algorithmic target is general recovery before kernel exhaustion, tested
  first against generated adversarial workloads and an independent oracle.
- The new regression corpus initially failed executable validation at frame
  30,748 because its factor came from a last-alive lag `7 > 6`, while the
  validator inspected only the in-support hit row. CE-0091 aligns validation
  with CE-0087's two-row attribution and checks stored deadline context.
- Linux and Windows Python each pass all 370 tests. The 21-case Stage-5
  corpus passes its independent executable validator. Native source did not
  change.

## 2026-07-24: Stage-4A Causal Audit, Survival-Only Items, And Bounded Native Clearance

- Complete randomized Stage-4A practice
  `lunatic_route2_stage4a_unattended_20260724_155932` reached
  `route_complete` with 19 hits and zero Bomb input. The previous complete
  Stage-4A run also had 19 hits; per-phase differences move in both directions
  and are not a causal aggregate result.
- Native input visibility is usually one frame once observed, while the
  closed-loop decision cadence is `4/6` frames median/p95 and local planning is
  `29.09/48.38 ms`. The current evidence does not justify rewriting the input
  interface in C++.
- CE-0092 proves a during-computation observation gap. The causal frame-35,415
  decision read hazards at frame 35,412 and an enemy snapshot at 35,410. An
  18-body ring appeared in a frame-35,413 async snapshot before the action was
  issued, and ordinary slot 18 made stable exact contact at frame 35,420.
  Dossier semantics now distinguish hit-row visibility from last-alive causal
  visibility.
- The TH08 adapter now merges a synchronous 64-slot allocation prefix with the
  complete async tail and repeats the prefix read before input. A geometry-set
  change triggers a compact all-action robust recertificate; the retained
  19-body synthetic costs `4.92/7.17 ms` median/p95 when triggered.
- Item objectives are disabled for the survival acceptance phase. They cannot
  affect beam pruning, action ranking, utility, or predicted collections.
  Passive pickup remains. A fixed local workload improves from
  `11.68/19.44` to `8.10/12.54 ms` median/p95.
- Alive global/local telemetry covers 6,613 decisions. The initial report
  cross-tabbed 32 global-winning/local-prefix-unsafe and 2,395
  global-losing/local-prefix-safe rows, but those horizons were not the same
  contract. The action-aligned reinterpretation and correction are recorded
  in the following checkpoint.
- The existing native moving-AABB clearance loop was still dense over every
  hazard and cell. A cap-bounded hazard-major traversal preserves the fixed-
  seed float32 volume checksum while reducing the 1,360-AABB, 81-frame
  microbenchmark from `342.67/372.69` to `59.68/97.40 ms` median/p95
  (`5.74x` median). The full warm synthetic solve is `76.15 ms` median with
  clearance/viability `63.44/12.66 ms`.
- The new randomized dense-oracle regression passes; Linux and Windows native
  libraries rebuild, and both Python environments pass all 378 tests. The
  Windows warm synthetic solve is `82.83 ms` median with `67.00/13.70 ms`
  clearance/viability. Physical Stage-4A validation remains required for the
  two synchronous reads, issue-time override rate, timing tail, and survival.

## 2026-07-24: Versioned Safety Contract And Survival-Horizon Oracle

- **Reporting correction:** Global viability covers another 48--80 frames;
  local robust certification covers only an 8--12-frame selected-action
  prefix. Therefore the 2,395 global-losing/local-prefix-safe rows are not
  false-empty proofs. The regenerated Stage-4A dossier now uses explicit
  horizon semantics.
- **Observed direct contradiction:** Thirty selected actions belonged to the
  cached global winning set but had a fresh local collision certificate.
  Their underlying hazard snapshots were 19--48 frames old, and some local
  margins were `-10..-22`. Missing births/later geometry are inferred
  contributors; exact source-snapshot attribution remains open.
- The local controller now intersects cached global actions with fresh
  prefix-safe actions. An empty intersection triggers an all-17-action
  recertificate and relaxes the cached mask. This is a generic version-order
  invariant. Future traces report filtered and relaxed counts.
- On all 30 retained direct contradictions, paired trace-radius replay changed
  16 actions, improved the hard vector on 10, regressed on zero, changed
  robust-collision decisions `29 -> 23`, and changed negative certificates
  `30 -> 23`. Eligible median/p95 cost changed
  `11.39/21.12 -> 20.00/36.08 ms`. This rare-path replay is not physical
  acceptance.
- Synchronous enemy-prefix capture now retries once when the manager frame
  crosses the contiguous read and records attempt/stability telemetry. An
  arbitrary hazard born after the final observation remains theoretically
  unpreventable unless its event/envelope is in the model.
- Added an independent scalar robust-game oracle. It maximizes guaranteed
  collision-free physical frames first and bottleneck signed clearance
  second. It matches the vectorized Boolean winning set and action masks on
  randomized small games.
- Across 9,720 states from 24 deterministic dense generated games, 4,905 were
  losing. Margin-only and survival-horizon best-action sets differed on 3,882;
  margin-only selection forfeited guaranteed survival frames on 190 states,
  losing 226 frames in aggregate. This invalidates max-min clearance as the
  first fallback outside the positive kernel while retaining it as a margin
  certificate inside the kernel.
- Added birth windows to the game-neutral adversarial generator. A regression
  proves that a future birth omitted from the event model can turn a stale
  winning result into an immediate losing result. Faster planning narrows the
  race; planning ahead helps only when births are modeled; issue-time
  validation remains necessary.
- The next justified C++ boundary is a packed issue-time
  decode/project/all-action certificate over bullets, lasers, and enemy
  bodies, followed by native survival-horizon induction. Both remain gated on
  scalar parity, Linux/Windows tests, whole-pipeline timing, and physical
  Stage-4A validation.
- A fixed native timing pair prevents prematurely enabling the old
  full-horizon margin fallback. Boolean-only warm median was `67.28 ms`;
  adding a separate 80-frame safety-value pass raised it to `151.30 ms`, with
  `87.59 ms` in value induction. The next C++ experiment should fuse outputs
  or refine on demand rather than stacking two complete recurrences.

## 2026-07-24: Enemy Lifecycle, World Motion, And Post-Issue Births

- Five complete Stage-4A hard-no-Bomb trials
  (`173718`, `175647`, `181700`, `183707`, `185059`) reached
  `route_complete`; all compact dossiers, death ledgers, executable
  regressions, comparisons, summaries, sessions, and run notes are retained.
- CE-0094 distinguishes object identity from native active/contact modes.
  The synchronous prefix now unions contact-enabled and active
  contact-disabled geometry, then retains recently absent observed slots for
  the 80-frame policy horizon. Physical anticipatory/dormant coverage reached
  1,294/3,785 decisions. Exact body overlaps absent from the governing action
  changed from three in `173718` to zero in `181700`; aggregate hit counts are
  not causal.
- IDA at `0x42DEB0` proves `enemy+0x2D4C` advances only internal motion
  `+0x2D34`, while lethal world position `+0x2D88` is composed later. Comments
  were added at `0x42DF57` and `0x42CA54`. Runtime pointer `0x00597600`
  retained world `y=164` while the second internal float reached `146.910`.
- CE-0096 replaces that false world-velocity projection with consecutive
  `+0x2D88` secants and compares issue snapshots after aligning them to the
  same player epoch. Raw state supplies only topology/contact/size changes.
- A first attempt widened unknown/jump bodies by 16 pixels. `183707` rose to
  34 hits, affected 79,809/85,788 body samples, and produced 26,004 trajectory
  invalidations. This was a failed reachable-set approximation and was
  removed, not tuned.
- Corrected run `185059` completed with 26 hits and zero Bomb. Relative to
  `181700`, global empty queries were `3,391` versus `3,376`, local planning
  `27.05/49.96` versus `27.89/50.41 ms`, and cadence remained `4/6` frames.
  Issue changes fell `2,841 -> 1,258` and trajectory invalidations
  `6,004 -> 1,574`. These accept model/performance gates, not aggregate
  survival improvement.
- CE-0095 retains a 23-frame cached-policy bullet-emission contradiction.
  CE-0097 adds exact enemy contacts from rings first observed 4/5 frames after
  the governing action's final issue observation. State-only speedups, larger
  margins, and dormant TTL cannot predict never-observed births; ECL/timeline
  spawn/emission lowering is the next semantic target.
- Planner-consistency reporting now excludes observed issue invalidations and
  deadline-held input, while describing remaining direct cases as
  forecast/version contradictions rather than same-snapshot theorem failures.

## 2026-07-24: Stage-5 Strict-Version Cross-Control

- Complete hard-no-Bomb Stage-5 run
  `lunatic_route2_stage5_unattended_20260724_191313` exercised the final
  0.25-pixel aligned trajectory guard through `route_complete`. The
  unattended session verified Lunatic, route 2, Sakuya/Remilia, the
  no-life-decrement patch, terminal unload, and process cleanup.
- The 28 retained hits classify as 11 exact bullet overlaps, 16 modeled
  committed-prefix collisions, and one positive-clearance sensor gap. Seven
  stable hit contact captures contained no exact enemy-body overlap; CE-0094
  and CE-0096 did not recur as the contact cause on this stage.
- Twenty-six hits followed global viability-kernel exhaustion. Overall
  losing queries were 4,514/7,054; spell 107 contributed 12 hits and
  635/769 empty queries. This makes native survival-horizon induction and
  adaptive boundary refinement the next general planning target.
- The strict issue guard recertified 2,307/7,223 decisions, overrode 870
  actions, and excluded 1,474 newer hazard versions. Zero remaining selected
  cached actions contradicted the fresh prefix checker. The relevant cost was
  local plan `28.53/57.24 ms` and cadence `4/7` frames, versus
  `27.85/47.50 ms` and `4/6` in the prior Stage-5 baseline.
- The bounded native clearance traversal improved global solve
  `285.01/474.16 -> 151.78/365.36 ms` median/p95 on this cross-stage
  comparison. Total hits `21 -> 28` are descriptive only because RNG,
  respawn, Power, and phase duration differ.
- All 28 failures are retained in the compact executable corpus and CE-0098.
  The six new physical corpora from this checkpoint pass the independent
  validator.
- Focused TH08 discovery passes 303 tests. Linux and Windows Python each pass
  the complete 394-test suite.

## 2026-07-24: Stage-5 Differential Viability Audit

- Complete hard-no-Bomb Stage-5 capture `20260724_201636` reached
  `route_complete` with 27 retained hits. It wrote 1,879 exact lowered-hazard
  capsules; raw JSONL/capsules remain ignored and compact run/audit artifacts
  are retained.
- The last two available pre-hit queries for every hit produced 54/54 exact
  16-pixel reconstruction matches. Primary empty classification is 51 modeled
  losing/unresolved and three spatial coarse false-empties. The 8/4-pixel
  winners all occur in phase 103; no sampled phase-107 empty became winning.
- Bullet slot 1446 was absent from the frame-32546 governing capsule, appeared
  in a later 1420..1457 ring, and made exact contact at hit 32581. Because the
  governing state was already losing, the birth is recorded as orthogonal
  hazard evidence, not the cause of its empty kernel.
- Added a fused native lexicographic survival-horizon/bottleneck pass with
  full scalar parity. All 54 queries now have labels. One query before hit
  3491 guaranteed 10 modeled safe frames against an eight-frame hit interval,
  while endpoint-distance recovery issued an action outside the best mask.
  The other 53 labels were shorter than time-to-hit, so the shadow is a
  specific fallback correction rather than a general Stage-5 solution.
- Added optional terminal masks to native and NumPy Boolean induction. The
  selected cohort was already empty, so next-policy overlap had zero winning
  samples. Its monotonic role is now explicit: it may reject instant-safe
  terminal wins but cannot rescue an empty predecessor.
- The first 4-pixel audit exposed a 203,190,120-sample, roughly 1.514-GiB
  native transition table. Factoring regular-lattice x/y transitions reduces
  it to 4,119,984 axis samples and about 47.15 MiB. Randomized Boolean,
  safety-value, and fused-survival parity pass. An isolated retained 4-pixel
  solve now peaks at 94,080 KiB RSS; the complete audit still peaks near
  1.27 GiB and needs separate offline allocation profiling.
- Synchronous capsule I/O added `91.58/117.58 ms` median/p95 and doubled
  policy worker service in the capture run. Audit writes now use an independent
  one-worker queue and are drained on exit; physical timing acceptance remains
  pending.
- CE-0099..0101 retain the harness wiring failure, physical coarse
  false-empty witnesses, and survival-vs-endpoint counterexample. The durable
  design analysis is
  `notes/STAGE5_VIABILITY_DIFFERENTIAL_AUDIT_20260724.md`.
- Linux and Windows builds succeed, and both complete Python suites pass 404
  tests.

## 2026-07-24: Live Refinement Rejection And Strategy Ledger

- Full-horizon 8-pixel refinement reproduced all three CE-0100 coarse
  false-empty capsules offline, and fused survival labels retained scalar
  parity. Short terminal-stitch experiments did not provide a general rescue:
  only one of three witnesses could reconnect to the exact coarse
  continuation under the tested endpoints.
- Complete Stage-4A run `20260724_220032` physically rejected the combined
  live promotion. Empty queries fell `3391 -> 2434`, but solve median/p95 rose
  `170.77/380.59 -> 532.04/1174.21 ms`, delivered policies fell
  `1728 -> 630`, expired decisions rose `34 -> 178`, and the run retained 40
  hits versus 26 in the RNG-distinct comparison.
- An isolation run with fine refinement disabled returned solve median/p95 to
  `196.09/354.90 ms` but ended `process_unreadable` at frame 13,077. It is
  explicitly discarded and cannot accept or reject survival-label ranking.
- Live control is restored to the coarse Boolean path: refinement steps are
  empty, fused survival labels are off, prewarm is Boolean-only, and
  experimental native concurrency is reverted. Both experimental policies
  remain shadow/offline and are pinned by
  `test_rejected_fine_and_survival_strategies_remain_shadow_only`.
- Survival-label requests now fail explicitly if the fused native backend is
  unavailable instead of silently returning an unlabeled Boolean policy.
- The oversized live module is partially decomposed:
  `th08_corridor_runtime.py` owns asynchronous corridor epochs/queries and
  `touhou_control/policy_guidance.py` owns the pure global-to-local guidance
  contract. Live entry points remain stable.
- Added root `STRATEGY.md` as the durable status ledger for live, shadow,
  rejected, infrastructure, and hypothesis strategies. `AGENTS.md` now
  requires updating it when a strategy changes status.
- A new damage-aware phase-completion hypothesis is recorded, not enabled.
  Existing traces already hold Shot on 97.38--97.78 percent of output
  decisions, but the controller has no boss-HP/damage objective. The shadow
  alignment audit records large and phase-dependent player/boss horizontal
  error while post-hit Power is commonly depleted. Native HP delta,
  damageability, shot cadence/options, phase timer, and exit cause must be
  traced before damage can break ties between survival-equivalent actions.
- Detailed evidence and the new architecture order are in
  `notes/DELIVERY_AWARE_STRATEGY_REASSESSMENT_20260724.md`; CE-0102/0103 retain
  the complete delivery regression and discarded isolation run.

## 2026-07-24: Native Boss Progress, Alignment Rejection, And Practiced Profiles

- **Observed static/native fields:** ECL `0x83` writes current/max/phase HP at
  enemy `+0x2DFC/+0x2E00/+0x2E04`; thresholds are four signed integers at
  `+0x3358`; phase timer elapsed is `+0x2E1C`; timeout is `+0x3378`; resolved
  player-shot damage commits to current HP at `0x0042D349`. The indexed Boss
  registry is four pointers at `0x00F54CC0`.
- **Observed runtime correction:** A read-only live probe showed Stage-4A slot
  0 pointing at `0x5826C0`, with primary flags `0x1128004F`, flags2 `0x4`,
  current HP 4268, phase HP 15000, next threshold 2000, timer 2590/2700, and
  an open damage gate in one stable manager frame. Earlier prose saying
  “flags2 bit 0x2” meant bit **index** 2; the concrete mask is `1 << 2 = 0x4`.
  Two preliminary sessions loaded the wrong mask and were safely stopped and
  marked discarded before strategy interpretation.
- Added `th08_boss_phase.py`, the read-only
  `scripts/tools/th08_boss_probe.py`, and the
  game-neutral `touhou_control.phase_progress` tracker/lexicographic
  safe-objective primitive. The live trace now observes registered nonspell
  Bosses as well as spell owners and records stable HP, phase boundary, timer,
  timeout, damage gate, HP delta, and a damage shadow action.
- **Observed shadow capture:** Discarded focused partial Stage-4A run
  `20260724_231247` retained 873 spell-57 Boss samples; all were stable and
  damageable. It observed HP `2000 -> 633` over 2872 comparable game frames
  (`0.47597 HP/frame`). Of 725 decisions with both fresh viability guidance
  and an issue-time certificate, the horizontal shadow disagreed 198 times.
  This capture was manually stopped at timer 2729/3000 and is not a completed
  phase or stage baseline.
- **Observed rejected live experiment:** Discarded focused partial run
  `20260724_231637` temporarily allowed horizontal alignment to rank only the
  same fresh viable, issue-safe action set. It changed 123 spell-57 actions
  and improved normal horizontal-error median `51.50 -> 25.19 px`, but
  observed HP response was `0.37837 HP/frame` (`2000 -> 835` over 3079
  comparable frames) despite higher measured Power (first/median `100/84`
  versus `75/43`). It reached timer 2996/3000. RNG, hit history, Power
  trajectory, entry state, and trace extent differ, so this is adverse
  evidence rather than a causal HP-rate or phase-duration A/B.
- CE-0104 records the proxy/native disagreement. Runtime live alignment
  authority and its CLI switch were removed after the experiment. Stable Boss
  telemetry and safe-set shadow output remain. The next damage hypothesis
  must use the already executable SHT cadence/source/shot collision/damage
  model plus route-2 option state and demonstrate predicted/native HP-delta
  parity before another physical promotion.
- **Architectural decision:** Keep movement, collision, laser/transform,
  event-time, sensing, delay, viability, and issue certification semantically
  reusable. Permit explicit game/team/stage/phase practiced profiles for
  reference tubes, lead times, resolution/horizon, Power floors, pickup
  windows, and exact phase-progress objectives. Power, Boss HP, and remaining
  time are route state/resource constraints, not merely three scalar weights.
  Profiles must validate across RNG/entry-state samples and must not become
  hidden branches in the safety kernel. The full rationale is
  `notes/ROUTE_CONDITIONED_STRATEGY_ARCHITECTURE_20260724.md`; `STRATEGY.md`
  records S12.
- Test policy is now research-tiered. Profiling found that one differential
  wiring test spent about 8.6 of 9.9 seconds recomputing complete 16/8/4-pixel
  policies. It now stubs the solver and tests classification in 0.004 seconds;
  real multi-resolution solves remain retained capsule experiments. The
  complete 420-test Linux suite passes in 1.351 seconds and the complete
  Windows suite passes in 2.561 seconds.
- Added IDA comments at `0x0041C97A`, `0x0041C989`, `0x0041C998`,
  `0x0042D349`, and `0x0042DCB3` for max/current/phase HP writes, native
  damage commit, and the current/max UI consumer. No REA session was used for
  this checkpoint.

## 2026-07-24: Model, Solver, Structure, And Storage Audit

- **Observed exact-laser inconsistency:** The global adapter already honored
  CE-0078 and added no generic horizon drift to state-backed lasers, but local
  MPC still added `min(6, 0.08 * step)` to every laser. Exact
  `LaserState` records now carry zero per-frame growth; only missing-state
  fallback records retain the conservative `0.08`. Legacy trace replay also
  restores exact records with zero growth.
- A 100-row paired Spell-50 replay changed 7 selected actions and 90 complete
  decisions when the non-native growth was removed, with effectively equal
  median time (`15.20` versus `14.99 ms`). Compact hashed evidence is
  `artifacts/benchmarks/local_laser_model_audit_20260724.json`.
- **Observed bullet-size inconsistency from IDA only:**
  `bullet_spawn_from_emission_descriptor` (`0x0042F5F0`) copies template
  collision dimensions to bullet `+0xD34`, and
  `player_test_bullet_collision_or_cancel` (`0x0044A230`) divides those values
  by two directly. Native code has no `[1,24]` half-extent clamp. Both compact
  and diagnostic live decoders now preserve positive sizes exactly; a
  regression covers 0.5- and 96-pixel widths. Added concise reproduction
  comments at `0x0042FA12` and `0x0044A284` in the connected IDA database.
- **Solver audit:** 24 seeds of 2,048 generated piecewise hazards, 48 frames,
  and up to six events all matched the independent scalar oracle with maximum
  absolute error `9.835e-7`. Heavy-corridor warm median was `152.97 ms`, split
  into `146.39 ms` clearance and `5.24 ms` viability. Clearance construction,
  not Boolean induction, remains the global performance target.
- **Structural split:** Laser trace/projection/packing moved to
  `th08_laser_runtime.py`; the separable C++ delay/lattice transition cache
  moved to `native/robust_transition_table.hpp`. Fourteen offline timing and
  ablation programs moved to `scripts/benchmarks/`, eleven differential and
  dossier programs to `scripts/analysis/`, and build/probe/patch/capture entry
  points to `scripts/tools/`. Root `scripts/` remains the importable/live
  boundary.
- **Research test decision:** No quick regression was disabled. The complete
  Linux/Windows suites pass 423 tests in `1.368/2.714 s`; expensive raw
  replay, multi-resolution solve, Windows duplication, and physical trials
  remain conditional tiers. The correct Windows UNC loader command and three
  invalid approaches are recorded in `START_HERE.md` and `AGENTS.md`.
- **Storage cleanup:** 203 ignored runtime JSONL/PNG/log files
  (11,040,649,198 bytes), 1,889 ignored viability capsules (104,309,566
  bytes), ten menu PNGs (5,065,295 bytes), caches, stop sentinels, and
  rebuildable native libraries were removed after compact artifacts were
  verified. Workspace size fell from about 11 GiB to 74 MiB. The user's
  untracked `image.png` was not touched.
- Detailed evidence, unresolved transform/birth/HP-delta boundaries, and the
  next decomposition order are in
  `notes/MODEL_SOLVER_MAINTENANCE_AUDIT_20260724.md`. New binary analysis is
  restricted to connected IDA Pro MCP; REA use is prohibited by `AGENTS.md`.

## 2026-07-25: Clearance Pipeline Optimization

- Reclassified the earlier 1,500-AABB/250-static-segment/200-trajectory
  benchmark as a game-neutral stress workload rather than a live TH08 cost
  attribution. TH08 lasers use the segment-trajectory path; the stress
  workload's static and trajectory geometry also substantially overlaps.
- Added a conservative squared-distance rejection before the authoritative
  `std::hypot` call in the native segment-trajectory kernel. Against the old
  native library, 500 randomized workloads and one generated live-like
  800-AABB/200-trajectory workload were bit-identical. Raw trajectory median
  improved from 21.92 to 6.25 ms.
- The ordered architecture, benchmark separation, packed frame-major
  contract, static broad phase, and shadow-only Boolean/query-local proposal
  are recorded in `notes/CLEARANCE_PIPELINE_OPTIMIZATION_20260725.md`.
- Added the packed frame-major segment contract and changed live TH08 laser
  lowering to produce it directly. Object and packed native clearance were
  bit-identical; direct lowering of a generated 215-laser/17,415-sample epoch
  measured 16.67 ms versus 40.47 ms for object lowering plus repacking.
  Capsule schema v2 preserves packed arrays while the reader remains
  compatible with v1. The complete Linux quick suite passes 432 tests.
- Split clearance timing into live-like packed lasers, static finite-segment
  stress, and piecewise-transform adversarial benchmark identities. Added a
  cap-aware finite-geometry broad phase for static segments. Five hundred
  old/new randomized native workloads were bit-identical; the
  1,500-AABB/250-static clearance median improved 122.28 to 81.86 ms.
- Re-ran 24 seeds of 2,048 piecewise hazards against the scalar oracle; all
  passed with maximum error `9.537e-7`. Compact reports are retained under
  `artifacts/benchmarks/`.
- **Rejected shadow:** one Boolean occupancy bit per cell does not preserve
  the current robust recurrence because it subtracts transition-specific
  nearest-lattice error. Sign-only occupancy added 338,218 false-positive
  action bits on the retained synthetic shadow; uniform maximum dilation
  removed 115,584 valid bits. Query-local exact endpoint ranking touched only
  72 cells but cannot repair intermediate/delay admissibility. Keep this
  direction shadow-only until a multi-margin, continuous-query, or
  signed-distance-narrow-band design achieves full-policy parity.
- Final offline gate: packed/object full policies and representative rollouts
  are identical; Linux and Windows complete suites pass 434/434 in
  1.074/2.367 seconds. Both native libraries were rebuilt. No physical trial
  or live strategy promotion was performed.

## 2026-07-25: Continuous Lunatic Physical Validation

- Added `run_th08_full_route_agent.bat` and
  `scripts/th08_full_route_supervisor.py`. The fail-closed normal-start path
  verifies the exact image and life patch, anchors Game Start with a real
  Down/Up transition, observes native title modes `0 -> 4 -> 5`, selects
  Lunatic and Sakuya/Remilia, arms before the final `Z`, expects Stage 1, and
  accepts only the native successor chain through Final B.
- Fixed two Windows relocation faults before gameplay: the external patch BAT
  still named the old pre-reorganization script path, and the relocated tool
  did not prepend its parent `scripts/` import root. The exact no-life patch
  gate then passed at `0x0044D0FA`.
- Linux and Windows quick suites passed 436/436 in 2.039/2.661 seconds before
  the physical run. The ignored Windows native DLL was rebuilt from the
  current source.
- **Observed physical completion:** Continuous run
  `lunatic_route2_fullrun_unattended_20260725_083917` reached Final-B
  `terminal_unload` at frame `226864`, then `route_complete`. It contains
  52,479 decisions, 77 native hit edges, zero deathbomb requests, zero Bomb
  input violations, zero foreground interruptions, zero runtime errors, and
  zero JSON decode errors.
- Stage hit counts are `3/5/6/19/20/24` for
  Stage 1/2/3/4A/5/Final B. Against the retained complete hard no-Bomb
  baseline, the deltas are `+2/0/-4/-9/+7/-9`, for `90 -> 77` total.
  This is one RNG/resource sample; Stage 1 and Stage 5 remain explicit adverse
  evidence and no route strategy was promoted.
- **Observed global delivery:** Solve median/p95/max changed
  `2455.95/4038.64/6141.66 -> 99.99/386.09/540.90 ms`; solution age
  median/p95 changed `152/259 -> 3/9` frames; unique solutions changed
  `1,064 -> 9,308`, queries `759 -> 51,747`, and stale reports `484 -> 15`.
  Current phase telemetry measures clearance
  `12.11/33.53/104.71 ms` and viability
  `74.63/372.11/519.15 ms`. The former clearance bottleneck is removed in
  this live workload; viability induction is now the global tail target.
- Failure attribution contains 21 exact bullet overlaps, three exact laser
  overlaps, three exact enemy-body overlaps, 49 modeled committed-prefix
  collisions, and one remaining sensor-gap/unmodeled case. The old
  unattributed sensor-gap count was 18, but improved telemetry and differing
  samples prevent treating that delta as pure causal model-accuracy parity.
- CE-0105 records a postprocessing contract bug: the final inactive edge is
  `terminal_unload`, and only the later summary becomes `route_complete`.
  The physical run itself was never interrupted; its session preserves the
  temporary status error and recovery reason. A focused regression protects
  the corrected two-stage completion contract.

## 2026-07-25: Stage-5 Losing-State Root Cause And Shadow Repair

- Completed focused hard-no-Bomb Stage-5 capture
  `lunatic_route2_stage5_unattended_20260725_103655`: 6,884 decisions, 34 hit
  edges, zero Bomb-input violations, and clean `route_complete`. Only the
  first hit is a fresh canonical attempt; later respawn deaths remain
  discovery counterexamples.
- Exact differential reconstructed all 272 stratified policy queries. Of 195
  base-empty states, independent ablations rescued 16 at 4-pixel resolution,
  6 with query-time delay support, 24 without uncertainty growth, 34 without
  retained uncertainty, and 45 with at least one shorter horizon. No single
  factor rescued the remaining 147.
- Confirmed the fallback ordering defect at canonical decision 1,680: the
  live policy selected `down_right_fast` outside the 74-frame survival-best
  mask and carried a 24-pixel diagnostic reserve deficit. Repair-volume
  guidance had disabled the prior boundary-reserve term.
- Added default-off losing-state reserve diagnostics and exact offline
  survival/reserve replay. Survival-first changed 42/195 actions and improved
  survival-best membership `134 -> 175`; combined ordering changed 50/195.
  Fresh local hard vectors regressed on zero rows.
- Whole-solve delivery audit on 48 exact capsules preserved Boolean/fused
  viable and action-mask parity, but fused median/p95 remained
  `125.31/229.58 ms` versus `76.96/197.99 ms`. Survival labels and fine
  refinement therefore remain shadow/offline.
- Linux and Windows quick suites both passed 441 tests in 1.450/2.881
  seconds. The default live strategy remains unchanged.
- Recorded CE-0106 for the losing fallback and CE-0107 for packed
  short-horizon slicing. The unresolved temporal hypothesis is an explicit
  pending-command/remaining-delay state, not a Stage-107 special case.
- Full analysis: `notes/LOSING_STATE_ROOT_CAUSE_20260725.md`.

## 2026-07-25: Boolean-First Publication And Pending-Command Oracle

- Split losing-state label induction from the Boolean publication path.
  `CorridorPlan` retains an immutable numeric query problem; the labels-only
  native recurrence reuses the published Boolean arrays, skips winning states,
  and returns a separate shadow policy that cannot enter live guidance.
- Added an independent scalar/native phase-exact recurrence with explicit
  game-observed active action, older pending desired action, remaining-delay
  support, and new-command delay support. Sixty-four randomized
  pending-pipeline seeds passed scalar/native parity. Twenty-four full
  Stage-5-size structured fields passed exact fused/post-publication parity on
  every losing label and best-action mask.
- Single-worker post-publication benchmark median/p95 was
  `71.33/89.36 ms`, versus Boolean `282.88/310.69 ms` and fused
  `353.88/379.78 ms`. This is an offline workload identity, not live service
  time.
- Complete hard-no-Bomb Stage-5 run `20260725_122624` showed that putting
  shadow labels on the same corridor executor was not side-effect-free:
  expired decisions rose from the Boolean-only comparison's 14 to 34.
- Moved physical shadow work to an independent executor and restricted the
  label kernel to one native worker. Complete RNG-distinct run
  `20260725_125037` reached `route_complete` with 7,921 decisions, 18 hits,
  zero Bomb violations, no runtime interruption, and no residual TH08/control
  process. Boolean solve was `114.91/425.22 ms`, first policy age `4/10`
  frames, query age `11/27`, expired decisions 15, and local read/plan/action
  lag `13.08/18.18 ms`, `22.71/42.74 ms`, and `3/5` frames. This accepts
  publication isolation, not the RNG-distinct hit count.
- Both physical traces directly falsified issued-action-as-active semantics.
  Desired/native input mismatched on 754/8,077 and 805/7,772 Boolean queries.
  Among completed labels, changing only to native observed input flipped
  winning classification nine times in each run. Two deterministic 16-query
  exact cohorts then changed 13 best-action sets each when pending command
  state was added; winning classification changed four and six times.
- Dense labels therefore remain shadow-only. Query-local exact p95/max on the
  selected physical cohorts reached `86.13/183.04` and `68.33/250.76 ms`;
  exact phase/pending semantics need a reachable-tube, incremental, or
  augmented precomputed form before action-authority A/B.
- Linux and Windows complete quick suites pass 453 tests in
  `1.558/4.080 s`. Full design, evidence labels, artifacts, and promotion gate
  are in `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md`. CE-0108 records
  serialized-shadow delivery, and CE-0109 records active/pending input
  conflation.

## 2026-07-25: Sparse Augmented Pipeline Reachable Tube

- Added a versioned native workspace over exact frame, lattice cell, observed
  active action, older pending action, and remaining-delay branch. It keeps a
  persistent flat state-value memo and exact-root action-label cache inside
  one immutable clearance policy.
- Added only sound discrete reductions: feasibility termination,
  last-write-wins pipeline canonicalization, admissible lexicographic action
  upper bounds, and non-root incumbent delay pruning. Public roots still
  compute exact labels for every action.
- Split the C++ workspace out of the already large viability kernel into
  `native/pipeline_survival_workspace.hpp`; Python owns its clearance-array
  lifetime behind a narrow ctypes handle. TH08 runtime attachment is explicit,
  version checked, shadow-only, and not called by the live controller.
- Retained benchmark
  `artifacts/benchmarks/augmented_pipeline_workspace_20260725.json` passes 512
  scalar differentials and ten full TH08-size native-v1 differentials with
  zero failures.
- TH08 v1 cold query median/p95 was `819.90/986.61 ms`; persistent workspace
  cold/incremental roots measured `38.76/104.46 ms`, and repeated exact roots
  measured `0.103/0.128 ms`. Median state expansion fell from `54,982` to
  `2,621.5`.
- **Decision:** accept the optimized recurrence as an offline exact prototype.
  Do not run cold expansion synchronously or grant action authority. The next
  experiment is isolated background prewarming and exact root/version
  publication with measured hit rate and delivery cost.
- Full proof boundaries, one-pending limitation, and the veto-only promotion
  gate are in `notes/AUGMENTED_PIPELINE_REACHABLE_TUBE_20260725.md`.

## 2026-07-25: Exact-Root Frontier And Phase-Skeleton Prewarm

- Replaced single-next-root prediction with a game-neutral kinematic frontier
  over issued action, command delay, next-decision interval, observed action,
  older pending action, and remaining-delay support. Duplicate physical
  branches are grouped into exact public roots.
- Tested and rejected naive recursively variable `(4,5,6)` cadence in the
  sparse TH08-sized workspace: a manual probe did not finish after more than
  60 seconds and was terminated as `discarded/external_stop`. The retained
  value branches cadence only on the public root's first transition and states
  its fixed-continuation boundary explicitly.
- Added native C ABI v2 support for one-transition root cadence, retained v1
  construction compatibility, and added lookup-only root consumption. A cache
  miss returns without expanding the C++ state graph.
- Added phase-shard prewarming: an expensive likely-cell seed can run before
  the exact root is known; after issuance, the reachable roots are specialized
  inside their exact-frame shard and then published.
- Retained benchmark
  `artifacts/benchmarks/exact_root_frontier_20260725.json` passes 512
  scalar/native differentials and 70 TH08-shaped cold/specialized root
  comparisons with zero failures.
- Cold exact roots measured `90.37/131.95/135.84 ms`
  median/p95/max. Three-shard post-issue frontier wall time measured
  `39.61/49.35/62.50 ms`; lookup-only consumption measured
  `0.061/0.100/0.143 ms`.
- Phase-seed wall remained `112.51/122.02/140.69 ms`, and a seed alone was an
  exact hit for zero of 70 roots. **Decision:** accept the decomposition and
  fail-closed lookup offline, but keep it shadow-only. The next gate is an
  isolated rolling scheduler with native cooperative cancellation,
  newest-version-wins behavior, calibrated cadence support, and physical hit
  rate/delivery telemetry.
- Linux and Windows native libraries were rebuilt; both complete quick suites
  pass 460 tests in `1.629/3.182 s`.
- Full design and evidence boundary:
  `notes/EXACT_ROOT_FRONTIER_PREWARM_20260725.md`.

## 2026-07-25: Cancellable Rolling Exact-Root Prewarm

- Added atomic native cancellation and per-query deadlines throughout the
  augmented pending-pipeline recurrence. Cancellation is permanent; deadline
  expiry may retain completed state values but never a partial public root.
- Added continuation-only prewarm and exact-compatible memo merge. Merge
  requires the same immutable Python problem/version and native equality of
  axes, action motion, delay/fixed-cadence contract, boundary semantics, and
  clearance values.
- Added a game-neutral bounded newest-version scheduler. Each new policy
  cancels the old native work and uses a fresh executor; rolling extensions
  are rejected while a prior round runs, exact specialization replaces its
  older batch, and controller consumption remains lookup-only.
- Removed duplicate native branch construction between continuation action
  upper bounds and exact action evaluation. Shared Python root-enumeration
  validation plus terminal-only lattice rounding also moved enumeration cost
  from an exploratory `15--32 ms` range to retained
  `8.894/12.729 ms` median/p95.
- Retained
  `artifacts/benchmarks/rolling_pipeline_prewarm_20260725.json`: 256
  scheduler/scalar differentials and 25 TH08-shaped rolling decisions have
  zero label failures; every exact specialization adds zero continuation
  states. Preparation plus seed plus specialization is
  `59.125/228.992/295.904 ms`, and lookup is
  `0.066/0.135/0.445 ms`.
- The first two decisions of all five immutable-policy cases miss a
  four-frame budget; decision three passes 4/5 and decisions four/five pass
  10/10. Five stale replacements take `5.265/5.348/6.312 ms` and never expose
  old results.
- Reran the independent 512-seed augmented differential plus ten full
  TH08-size v1 cases, and the 512-seed one-transition differential plus 70
  phase-specialized TH08 roots, with zero failures after the branch-reuse
  change.
- **Decision:** accept cancellation, exact memo merge, and bounded scheduling
  as offline infrastructure. Keep S09 shadow-only. The unresolved blocker is
  now cross-version cold start: a live policy may be replaced during its first
  two decisions, before same-version rolling becomes useful. The next shadow
  must overlap seed work with Boolean induction and measure policy lifetime,
  current-version hit rate, discarded work, and delivery contention.
- Both native libraries were rebuilt; Linux and Windows complete quick suites
  pass 465 tests in `1.710/3.131 s`.
- Full contract and evidence boundary:
  `notes/ROLLING_PIPELINE_PREWARM_20260725.md`.

## 2026-07-25: Augmented-Pipeline Problem Formalization

- Formalized the intended robust-control problem as a finite-horizon
  information-set game over frame, projected position, observed action,
  pending desired action, and a support of indistinguishable remaining
  delays.
- Identified two separate completeness boundaries in the current “exact”
  prototype: cadence uncertainty is branched only on the first transition,
  and deeper maximization may condition on a hidden exact remaining delay.
  Existing scalar/native parity proves implementation parity for that hybrid
  recurrence, not exactness for the physical controller.
- Defined the required observation partition, non-anticipativity condition,
  lexicographic value, proof obligations, performance accounting, and exact,
  anytime, reachable-tube, and incremental algorithm candidates.
- The authoritative active specification is
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`.

## 2026-07-25: Belief-Pipeline Correctness And Native Prototype

- Built an independent recursively variable-cadence scalar oracle with
  physical hold/no-write semantics that merges indistinguishable
  remaining-delay branches before every future action maximization.
- Formal review found a third state/transition error after the first
  prototype: live code emits an input transition only when the selected mask
  changes, while the legacy recurrence treated every decision as a new issue.
  CE-0114 shrinks the resulting winning error to three future frames.
- Replaced the invalid first CE-0111 with a no-write-correct 5-cell/10-frame
  cadence counterexample. One-transition/fixed-maximum cadence is optimistic
  there; recursive cadence flips winning to losing. CE-0112 still records
  hidden-delay clairvoyance.
- Four deterministic 128-case cohorts now separate the causes:
  always-issue/no-write has 30 winning mismatches; wider recursive cadence has
  3 action-label and 1 winning mismatch; fixed-cadence
  clairvoyant/non-clairvoyant has 15 action-label and 11 best-action
  mismatches. A smaller cadence cohort has zero mismatches and is retained as
  negative evidence, not proof.
- Added a cancellable C++ belief workspace with remaining-delay bitmask memo,
  conditional no-write, observation grouping, admissible upper bounds, and
  restricted continuation policy classes. Another 128 scalar/native cases
  pass with zero failures.
- Small-model scalar/native median is `5.94/0.105 ms`; warm native lookup is
  `0.028 ms`. C++ fixes language overhead but not full TH08 state growth.
- On a TH08-shaped 32-frame `(4,5,6)` workload, all 17 actions recursively
  required `1507.74 ms`. Allowing all 17 actions at the public root but only
  nine focused continuation actions required `29.52 ms`; this is an
  attainable conservative lower bound. A recursive `(2..9)` envelope still
  required `552.69 ms` at 16 frames and exceeded three seconds at 32.
- Three physical Stage-5 shadows recorded direct CPU/action-lag regressions
  despite top-2 exact-hit improvement (CE-0113). No new physical run is
  authorized by this checkpoint.
- `AGENTS.md` and `START_HERE.md` now require every later algorithm change to
  recheck physical/model state equivalence, non-anticipativity, whether the
  solver actually solves or bounds the recurrence, and issue-time delivery.
  Complete proof is not mandatory, but unknown-direction approximations
  remain shadow-only.
- Rebuilt both native libraries. Linux and Windows complete quick suites pass
  482 tests in `3.010/5.410 s`.
- Full analysis:
  `notes/BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md`.

## 2026-07-25: Research Test Gate And Budgeted Belief Refinement

- Audited the complete unit suite by file and test. The main avoidable costs
  were retired prepublication-prewarm integration, audit-capsule file I/O,
  benchmark/report CLI plumbing, repeated route-manifest construction, and
  broad randomized counts already covered by retained differential programs.
- Removed seven benchmark/report CLI tests, three rejected legacy-prewarm
  integration tests, and two optional audit-file-wiring tests. Retained the
  constant-time assertion that rejected refinement/survival strategies remain
  shadow-only. Route manifests are now constructed once per class, and quick
  randomized oracle smoke counts are separated from the 128-case retained
  benchmark.
- Linux quick-suite runtime changed from 482 tests in `3.010 s` to 471 tests
  in `1.324 s`; Windows passes the same 471 tests in `2.481 s`. This is a
  research-gate reduction, not removal of scalar/native parity, concrete
  counterexamples, collision semantics, or live-authority boundaries.
- The independent Python formal audit now defaults to 16 cases per cohort and
  takes about `1.26 s`; `--cases 128` remains the retained full gate. It was
  not replaced with C++ because it specifies/checks the recurrence
  independently. The belief benchmark defaults to a roughly `1.1 s` quick
  profile; unrestricted, long-horizon, wide-cadence, and deliberate timeout
  cases require `--profile full`.
- Formalized and implemented per-history continuation-action budgets. Every
  root still evaluates all actions; later non-base actions consume budget.
  The resulting policy sets give nested attainable bounds
  `L_0 <= L_1 <= ... <= V_unrestricted`, and a sufficiently large budget
  recovers the exact unrestricted finite policy class.
- Added budget to scalar and native memo state, C ABI v3 action
  base/extra/budget construction, C ABI v2 per-query budget selection, and
  progressive `B=0,1,2` reuse inside one workspace. The retained 128-case
  scalar/native differential exercises budgets 0, 1, and 2 with zero
  failures.
- Added C ABI v4/native revealed-remaining-delay information relaxation. This
  is a proved optimistic upper bound because it preserves transitions and
  uncertainty while giving the controller more information. Another 128
  scalar/native comparisons have zero failures.
- On the TH08-shaped 32-frame `(4,5,6)` workload, `B=0` costs `32.30 ms`;
  progressive `B=1/2` increments cost `687.54/1054.42 ms`. The unrestricted
  belief solve costs `1488.38 ms`, and the complete upper costs `1471.15 ms`.
  `L_0` and the upper both equal `(32, 8.9031067)`, formally certifying the
  unrestricted state value for this instance. This certificate does not
  generalize to other fields without recomputing valid bounds.
- C++ removes interpreter overhead but not policy-state growth. The next
  performance target is incumbent-seeded selective upper evaluation and
  per-action certification, followed by retained Stage-5 capsule coverage;
  blind budget widening is not the next step.
- Retained design and benchmark:
  `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md` and
  `artifacts/benchmarks/budgeted_belief_refinement_20260725.json`.
- No physical trial, binary reverse engineering, IDA mutation, or REA session
  was used for this offline checkpoint.

## 2026-07-25: Incumbent-Seeded Optimistic Upper Certification

- Replaced routine construction of every complete revealed-delay upper label
  with an exact threshold game: for each root action, ask only whether its
  optimistic value can strictly exceed the completed attainable lower state
  label.
- The C++ recurrence memoizes belief state plus one prefix-clearance bit and
  preserves controller existential choice, nature-universal delay/cadence/
  hidden branches, and revealed observation merging. An action/state is
  pruned only by an admissible lexicographic upper bound. Unfinished queries
  report unresolved actions and never publish optimistic labels.
- Added C ABI and Python APIs, native/scalar mask differential coverage, and
  schema-v6 retained benchmark evidence. All 128 deterministic games have
  zero belief failures, upper failures, lower-above-upper violations, and
  selective-certificate mask mismatches.
- On the retained 32-frame TH08-shaped workload, `L_0` costs `32.35 ms`; the
  selective upper certificate costs `0.223 ms`, reports no unresolved action,
  and replaces the complete upper's roughly `1.5 s`. The upper bottleneck is
  therefore resolved for this workload; the attainable lower solve and
  cross-stage certification coverage remain.
- Linux and Windows quick complete suites pass 471 tests in `1.391/2.415 s`.
  Design: `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`. Retained artifact:
  `artifacts/benchmarks/budgeted_belief_refinement_20260725.json`.
- This checkpoint grants no live authority and used no physical trial, binary
  reverse engineering, IDA mutation, or REA session. The next physical gate is
  a hard-no-Bomb Lunatic Stage 6B run with the established controller.

## 2026-07-25: Stage 6B Cross-Stage Gate And Deadline-Safe Certification

- Completed instrumented hard-no-Bomb Lunatic Stage 6B run
  `lunatic_route2_stage6b_unattended_20260725_204521`: frames `2..76235`,
  15,536 decisions, route complete, 31 native hits, zero Bomb, and no
  runtime/JSON/control interruption or manual re-arm. No TH08/control process
  remained after supervisor cleanup.
- The comparable RNG-distinct Stage 6B dossier had 27 hits. The new run is
  not survival acceptance. It recorded 19 committed-prefix, five bullet,
  five laser, one enemy-body, and one residual unmodeled/sensor-gap contact;
  all 31 hit windows followed global viability exhaustion. Empty action sets
  occurred on `7213/15149` available queries.
- Cross-stage performance improved: global solve median changed
  `266.80 -> 97.41 ms` and clearance median `118.55 -> 13.72 ms`. Local plan
  remained `18.97/37.70 ms` median/p95; full sensor read was
  `19.02/43.64 ms`. Thus clearance optimization generalized, while viability
  completeness and earlier losing-state formation remain.
- Added `scripts/analysis/belief_upper_certification_audit.py`. A deterministic
  32-root cohort uses the root nearest 30 frames before every hit plus one
  stratified non-hit root, exact observed/pending action, current delay
  support, `(4,5,6)` cadence, and a 32-frame physical capsule window.
- Uncapped replay certified 31/32 roots; one retained eight unresolved
  actions. Certificate median/p95/max was `0.039/88.33/1907.33 ms`.
  The two hard otherwise-certified roots took `1907.33/540.83 ms`, proving
  selective thresholding does not eliminate unrestricted growth on every
  full-horizon margin problem.
- Added proof-safe full-horizon prefix rejection, a teleporting
  global-clearance suffix upper bound, and deadline-safe partial return.
  Under a 100-ms certificate service limit, 29/32 roots certified, the
  eight-action gap remained, and two expired roots retained all 17 actions
  unresolved. Certificate median/p95/max became
  `0.040/91.59/100.18 ms`; deadline only enlarged uncertainty.
- Retained 128-case belief/upper/certificate differential has zero failures
  and zero lower-above-upper violations. Structured lower/certificate is now
  `32.99/0.062 ms`; complete upper remains `1493.23 ms` as an offline oracle.
  Linux/Windows quick suites pass 471 tests in `1.368/2.422 s`.
- New counterexamples: CE-0115 and CE-0116. No binary reverse engineering,
  IDA mutation, or REA session was used.

## 2026-07-25: Resumable Incumbent-Threshold Certification

- Formalized repeated short upper work as one exact keyed session, not
  independent simulation: immutable workspace/version, canonical root,
  absolute target frame, and bit-preserving float32 margin must all match.
- Changed the C++ threshold workspace to preserve normally completed
  subproblem memos and exact root-action tri-state results across deadline
  slices. Interrupted states are never memoized; known-exceeds plus all
  unknown actions remain unresolved at deadline. Any key change resets the
  session.
- Added a retained hard-root benchmark comparing one-shot exact, resumable
  5-ms slices, equal-budget one-shot, and fresh 5-ms restarts. Across five
  repetitions, resumable search completed in 21--23 slices with exact final
  eight-action mask parity and conservative monotone intermediate masks.
  Total median/p95 was `112.92/113.61 ms` versus
  `109.39/110.36 ms` exact.
- Resumable and one-shot exact both completed 11,436 threshold states.
  Resumption used about 1.7 percent more hidden simulations; fresh restarts
  remained at all 17 unresolved and rebuilt a median 24,517 states. The
  method provides bounded service granularity with about 3 percent wall-time
  overhead, not a total-CPU speedup.
- The exact result still retains eight unresolved actions. Root/version
  churn before roughly 115 ms still causes correct invalidation, so targeted
  lower refinement and cross-version delivery remain open. Monte Carlo/MCTS/
  beam search remains proposal/order-only unless followed by an exact
  adversarial verifier.
- Added CE-0117, one focused same-session regression assertion, executable
  benchmark, compact artifact, and
  `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`. No physical trial,
  binary reverse engineering, IDA mutation, or REA session was used.
- Rebuilt Linux and Windows native libraries. The complete quick suite passes
  471 tests in `1.400/2.415 s`; the retained 128-case full benchmark has zero
  belief, upper, lower-bound, or threshold-mask failures.

## 2026-07-25: Feasibility-First Dual-Bound Policy Synthesis

- Formalized per-root-action attainable lower and optimistic upper labels,
  with separate stopping conditions for finite-horizon feasibility and
  unrestricted optimality. A full-horizon positive candidate lower is enough
  for modeled feasibility; it does not require completing the upper.
- Implemented scalar/native greedy-prefix lower policy classes, exact
  singleton continuation portfolios, robust proposal-first exact action
  ordering, and action-column CEGIS. Every candidate preserves all modeled
  hidden delay/cadence branches. A timeout contributes no label; every
  proposed column is exactly re-solved before it can raise the incumbent.
- The retained 128-case differential has zero exact parity, candidate parity,
  candidate/portfolio-above-exact, upper, or certificate failures.
- On structured seed 0, unrestricted exact belief cost `4379.39 ms` and the
  old nine-action lower cost `733.42 ms`. Two singleton candidates prove
  full-horizon feasibility in median `4.01 ms`; all 17 candidates cost
  `36.68 ms` and leave only `up_left_fast` unresolved. Gap-directed columns
  `down_right_fast, up_left_fast, up` reach the exact
  `(32, 18.80272)` label and certify optimality in median `287.64 ms`.
- On seed 3, the first `always_stay` candidate proves feasibility in
  `1.90 ms`; dual optimality costs `38.36 ms` versus `209.30 ms`
  unrestricted exact. The old approximately 113-ms upper is therefore no
  longer a synchronous prerequisite on roots with a completed winning lower.
- Added scalar/native remaining-delay bucket upper bounds. Six randomized
  cohorts verify nested physical/bucketed/exact bounds. The hard first upper
  remains `114.25--120.99 ms` across widths and still correctly leaves
  `up_left_fast` unresolved, rejecting information coarsening as the main
  performance lever.
- Added safe cross-version proposal-order reuse. Prior labels rank candidates
  only; every current-version candidate is re-solved. On a root with every
  future clearance cell changed by `+0.125`, median feasibility time changed
  `3.980 -> 2.200 ms`, candidates `2 -> 1`, while complete current-version
  per-action labels remained order-invariant.
- Design:
  `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`. Retained artifacts:
  `artifacts/benchmarks/dual_bound_policy_synthesis_20260725.json` and
  `artifacts/benchmarks/upper_hierarchy_cross_version_20260725.json`.
- This is offline finite-model evidence, not live authority. No physical
  trial, binary reverse engineering, IDA mutation, or REA session was used.
- Rebuilt Linux and Windows native libraries. Both complete quick suites pass
  475 tests in `2.270/4.056 s`.

## 2026-07-26: Stage-6B Feasibility-First Replay And Physical Delivery Gate

- Formalized the physical candidate-service boundary around one immutable
  Boolean policy version and exact public root: phase, lattice cell, native
  observed action, pending action, and remaining-delay support. Each
  stationary continuation is solved exactly under recursive cadence
  `(4,5,6)` and the no-write belief recurrence. Completed candidates are
  attainable lower bounds; candidate/budget exhaustion and timeout remain
  unresolved.
- Added aggregate between-candidate budgeting to the portfolio. The 12-ms
  service budget retains every completed lower, lists timed-out and unvisited
  candidates, and never turns unfinished work into a losing label. Added
  one-worker exact-key candidate delivery, reusable below-normal background
  priority, TH08 root construction, explicit hotkey/supervisor opt-in, and
  trace telemetry. The result has no action authority.
- Replayed 32 retained Stage-6B roots in each of complete captures `000654`
  and `004142`. Both cohorts classified 20 exact losing, 11
  stationary-candidate feasible, and one refined feasible. Candidate
  median/p95/max was `2.13/6.75/12.37 ms` and
  `2.22/8.09/10.21 ms`. One `000654` exact threshold took `265.77 ms`;
  targeted action columns then changed a 27-frame losing lower into a
  positive 32-frame witness and certified optimality. Stationary-candidate
  exhaustion is therefore directly disproved as an unrestricted losing test.
- A live-like losing-only `10 ms/candidate, 12 ms aggregate` replay kept two
  feasible roots in `000654` and seven in `004142`. Incomplete portfolios
  remained explicitly budget exhausted. The portfolio itself took
  `3.14/11.74/12.49 ms` and `3.89/11.82/12.40 ms`
  median/p95/max.
- Physical every-root shadow `004142` completed Stage 6B hard no-Bomb with
  12,607 decisions and 33 RNG-distinct hits. It delivered
  `8004/12220 = 65.50%` exact roots but accumulated 205 queue replacements
  and 1,099 stale completions. Against Boolean-only `000654`, local-plan
  median increased `21.20 -> 26.46 ms`, iteration
  `45.89 -> 53.11 ms`, action lag `2 -> 3` frames, cadence `3 -> 4`, and
  first policy age `3 -> 4`. This every-root form is rejected as CE-0118.
- Changed admission to available Boolean-losing roots only, explicitly
  discarding obsolete targets on viable/unavailable decisions. Physical v2
  `011639` completed frames `2..74963` with 14,652 decisions, 26
  RNG-distinct native hits, zero Bomb, and no runtime, JSON, foreground, or
  manual-rearm failure. It delivered `6192/6618 = 93.56%` exact roots with
  zero replacement and zero stale completion. Outcomes were 949 feasible,
  899 fully candidate exhausted, 4,524 budget exhausted, and seven timeout.
- v2 recovered the Boolean-only controller envelope: read
  `12.10/17.09 ms`, local plan `21.85/38.95 ms`, iteration
  `44.88/67.42 ms`, action lag `2/4` frames, cadence `3/5`, viability
  `69.54/407.96 ms`, and first policy age `3/9`. Submit/lookup medians were
  only `0.0045/0.0140 ms`; candidate queue/computation medians were
  `1.41/13.46 ms`. This accepts losing-only candidate delivery as shadow
  infrastructure, not survival or action authority.
- Read every v2 hit row. All 26 contacts followed Boolean-kernel exhaustion:
  18 modeled committed-prefix, five bullet, one laser, one multiple-hazard,
  and one sensor-gap/unmodeled. Boundary pressure remained strong at 19/26
  hits. Candidate shadow could not cause or prevent these actions because it
  never entered live selection.
- Added a complete raw-bundle auditor and validated all three complete
  captures before retention cleanup. v2 has 14,791 JSONL records, 2,689
  readable capsules, zero missing references, and bundle hash
  `9e8af717c548dc6456d471c15ac2be9777f755d7b94bc3fc6067e4b289b38a77`.
  The locally retained replay floor is the newest two complete bundles,
  `004142` and `011639`; compact reports and hashes preserve the older
  baseline conclusion.
- Five launch attempts were discarded and excluded from every comparison:
  `235741` process unreadable at frame 375, `235800` supervisor mutex failure,
  `000500` and `011113` foreground loss, and `011218` process unreadable at
  frame 13,011.
- Focused candidate/policy/corridor/hotkey/supervisor tests pass. Linux and
  Windows complete quick suites both pass 481 tests in `2.187/3.461 s`.
- Full design, formal boundary, physical table, limitations, and next gate:
  `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`.

## 2026-07-26: Exact Candidate Witness Publication Boundary

- Audited every delivered winning candidate root within 120 frames of a
  Stage-6B v2 contact. The 82 selected roots covered 17 contacts and all
  matched the retained augmented root fields. Current exact replay reproduced
  both historical aggregate label and best-action set for only 47 roots,
  covering 14 contacts; 35 are now explicit
  `historical_replay_mismatch`. A two-root current Windows/Linux probe agreed
  exactly, so no current cross-platform split was observed.
- Among the 47 auditable roots, candidate choice changed the issued action 23
  times and provided a modeled 32-frame feasibility gain 21 times. All 23
  changed actions lacked the alternate-action fresh hard certificate, so none
  had retrospective input authority. The other 24 candidate-best issued
  actions retained safe selected-action certificates. No delivered winning
  candidate root was within its 32-frame horizon of contact.
- Recorded CE-0119: aggregate label, best-action names, and completed
  candidate names are not a content-complete attainable decision witness.
  Trace-radius bullets cannot reconstruct the omitted full alternate-action
  certificate.
- `CandidateVerifierOutcome` now retains every root-action
  `CandidateActionWitness`. Runtime JSON serializes best witnesses plus the
  issued-action exact label. `Decision` carries the certificate vector already
  computed by local planning; issue-time enemy recertification replaces it
  with its fresh all-action vector.
- Added a one-shot exact-key publication join. It is issue-eligible only for a
  completed positive full-horizon result with matching witness, current
  deadline, zero certificate collisions, and nonnegative clearance. It
  records full policy/root identity and expires after the current issue. It
  never changes the selected mask and remains shadow-only.
- A 200,000-call synthetic helper probe measured `1.376 us/call`; it adds no
  candidate recurrence or geometry work. Physical JSON/copy/CPU contention is
  still unmeasured and is the next non-Stage-6B shadow gate.
- Focused publication, candidate-service, historical-audit, and 80 live-agent
  tests pass. Linux and Windows complete quick suites pass 487 tests in
  `2.210/5.092 s`.
- Formal review and evidence:
  `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md` and
  `artifacts/viability_audit/stage6b_20260726_011639_candidate_witness_counterfactual.json`.

## 2026-07-26: Stage-4A Candidate Shadow And Frozen Input Clock

- Completed hard-no-Bomb Stage-4A physical candidate shadow
  `lunatic_route2_stage4a_unattended_20260726_100451`: 9,222 decisions,
  21 hits, route complete, no foreground/runtime/manual/JSON failure.
  Candidate delivery hit 3,913/4,187 losing-root attempts (`93.46%`), with
  438 winning hits, 223 modeled candidate feasibility gains, zero stale
  completions/replacements, and zero publication-integrity errors. The run
  predates explicit publication-helper timing, so that field is unavailable.
- Replay review exposed a separate physical clock defect. At manager frame
  21467, `up_left_fast` remained held across six wall-clock dialogue pulses
  and moved `(252.69,391.37) -> (8.00,32.16)`, 434.63 pixels over only three
  reported manager frames. At frame 30128, eight pulses held `left_fast` and
  moved 343.65 pixels to the left boundary over two reported frames.
  Equivalent `stay` wall-pulse episodes had zero displacement. Item utility
  and predicted collection were zero.
- Recorded CE-0120 and refined the formal clock contract: the enemy-manager
  counter is a valid planner clock only inside a contiguous gameplay epoch;
  it can freeze while player input physics continues.
- Implemented a fail-closed repeated-counter guard. After 50 ms it releases
  movement/focus, keeps only `SHOT`, increments the gameplay epoch, resets
  delay/cadence evidence, retires corridor policy/commitment and phase/ECL/
  enemy memory, and rejects async enemy snapshots from older epochs. Later
  wall-clock `Z` pulses cannot reintroduce movement.
- This bounds persistent movement after user-space detection but is not a
  scheduler-independent hard-real-time proof. Fresh Stage-4A physical
  validation must measure `frozen_input_neutralized` delivery and next-phase
  entry displacement before the correction is accepted.
- Formal analysis and compact evidence:
  `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md` and
  `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260726_100451.frozen_input.json`.

## 2026-07-26: Physical Rejection And Rollback Of 50-ms Input Guard

- Fresh Stage-4A physical run
  `lunatic_route2_stage4a_unattended_20260726_103856` completed the route with
  7,925 hard-no-Bomb decisions and 64 hits. This was the latest live
  Boolean/local controller plus the candidate verifier in shadow-only mode,
  not a planner ablation.
- The 50-ms repeated-manager-frame guard fired 2,780 times, beginning at frame
  91, despite the same 72 wall-clock auto-confirm pulses seen in the pre-guard
  run. It created gameplay epochs through 2,782 and reduced available
  viability queries from 9,073/9,222 decisions to 691/7,925. Queryable policy
  decisions fell from 9,073 to 829; pending-future-epoch decisions rose from
  42 to 623.
- This directly rejects the detector: it classified ordinary slow iterations
  as semantic transitions and starved live policy authority. The hit change
  `21 -> 64` is descriptive only because RNG and timing differ.
- Removed the guard, epoch/sensor invalidation path, constant, and focused
  test. The live controller now matches `1ce5b44` exactly except for retained
  shadow candidate-publication timing. CE-0120 remains open.
- The supervisor accepted the runtime trial and terminated the game, then its
  artifact postprocessor failed on explicit
  `enemy_body_snapshot_frame: null`. The dossier now preserves null rather
  than inventing a frame; projected fallback uses zero elapsed time, and
  enemy-sensor aggregation skips absent snapshots. The focused regression is
  `test_explicit_missing_enemy_snapshot_does_not_abort_dossier`.
- Recovered the complete dossier, death ledger, comparison, regressions, run
  note, and candidate-shadow audit without changing the original session
  failure provenance. The two newest complete Stage-4A raw JSONL/capsule
  bundles are `100451` and `103856`. The `103856` raw-bundle audit passed all
  checks over 10,784 records and 2,060 readable capsules, bundle SHA-256
  `d8d6ecdf7b0ae955c58317fd27fa3735fea9c14ee1471faebe1d7fca1f5e4c29`.
- Rejection evidence:
  `artifacts/viability_audit/stage4a_20260726_103856_frozen_guard_rejection.json`,
  CE-0121, and
  `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`.
- Linux and Windows complete quick suites pass 489 tests in
  `2.495/4.012 s`.

## 2026-07-26: Current-State Handoff And Contract Consolidation

- Audited `AGENTS.md`, `START_HERE.md`, `STRATEGY.md`, the active formal
  notes, the latest Stage-6B/Stage-4A evidence, and the current Git checkpoint
  before preparing a new Codex session.
- Reassigned documentation ownership:
  - `AGENTS.md` now contains durable workspace, evidence, formal-authority,
    architecture, testing, artifact, and live-control rules;
  - `START_HERE.md` now contains only the volatile checkpoint, current
    live/shadow/rejected boundary, P0-P2 problems, retained workloads,
    reference routing, verified commands, and next gate;
  - `STRATEGY.md` remains the status ledger;
  - design notes, counterexamples, run notes, and this log retain derivations
    and history.
- Removed stale startup tables and blockers that predated the belief-state,
  candidate-verifier, publication, and frozen-manager-frame work. Preserved
  exact WSL/Windows launch, test-discovery, foreground, completion, and cleanup
  differences needed to avoid repeating known failed command paths.
- Updated the candidate witness and Stage-6B contention notes: Stage-4A
  `100451` is the clean publication delivery/integrity shadow; `103856`
  measures helper cost but cannot serve as a survival/contention gate because
  the rejected 50-ms guard contaminated live policy availability.
- Current priority is explicit: CE-0120 semantic input-clock boundary first,
  a clean post-rollback candidate-publication shadow second, and attainable
  lower/issue-time coverage on retained Boolean-losing roots third. No shadow
  component gained live action authority through this documentation change.
- Documentation checkpoint validation: every newly routed formal/run
  reference exists, `git diff --check` passes, and the Linux quick suite passes
  489 tests in `2.235 s`. Windows duplication and a physical trial were
  intentionally omitted for a documentation-only change.

## 2026-07-26: Native Semantic Input-Clock Shadow

- **Observed static evidence:** IDA analysis identified
  `frscreen_blocks_enemy_clock` at `0x4358BB`. It reads the FRScreen
  implementation pointer at `0x0160F430` and blocks the ordinary
  enemy-manager counter increment when signed MSG state `+0x2181C` is
  nonnegative or `-2`. `msg_state >= 0` is active MSG execution; `-1` is
  inactive. The producer and physical meaning of `-2` remain unknown.
- **Observed static ordering:** priority-9 player movement consumes native
  active input and applies position changes at `0x44BAB6` before the
  priority-11 enemy-manager callback consults the FRScreen predicate.
  FRScreen runs at priority 15 and normal input publication at priority 17.
  `g_frscreen_update_serial` (`0x0160F428`) is therefore positive post-player
  chain evidence, but its failure to advance is not proof of no movement.
- **IDA database changes:** renamed `0x4358BB` to
  `frscreen_blocks_enemy_clock`, `0x4338CA` to `frscreen_update`,
  `0x43396D` to `frscreen_start_message_script`, `0x433DB3` to
  `frscreen_step_message_script`, `0x439710` to
  `frscreen_load_message_resource`, `0x437AD0` to `frscreen_register`, and
  `0x43587E` to `frscreen_timeline_message_wait_active`. Renamed globals
  `0x0160F428`, `0x0160F430`, and `0x0160F534` to
  `g_frscreen_update_serial`, `g_frscreen_impl`, and
  `g_ecl_scripted_global_update_freeze`; applied partial FRScreen
  wrapper/implementation types. Added comments at `0x42C69C`, `0x44BAB6`,
  `0x4358FE`, `0x433920`, and `0x452339` to preserve the counter, movement,
  unresolved `-2`, serial, and publication boundaries.
- **Inferred mechanism:** joining that ordering with CE-0120 runtime
  displacement explains how the manager frame can freeze while held native
  input continues moving the player. This is not a native instruction trace
  and does not make the FRScreen serial a universal player clock.
- Added game-neutral `SemanticInputClockTracker`, a tri-state TH08 paired
  native probe, opt-in live/hotkey/supervisor shadow plumbing, and the
  streaming `th08_input_clock_audit.py`. The role is explicitly
  `shadow_no_input_or_epoch_authority`: it never writes an input, resets an
  epoch, changes delay/cadence or estimator evidence, retires a policy, or
  starts proof work. Desired held input and native `input_current` remain
  distinct.
- Fresh complete hard-no-Bomb Stage-4A run
  `lunatic_route2_stage4a_unattended_20260726_120839` retained 7,349
  decisions, 26 descriptive hits, `terminal_unload`, and `route_complete`.
  It logged 3,216 semantic observations (`false/true/unknown =
  3134/81/1`) and five delayed pulse groups. The v1 tracker merged the
  `4963 x 4` and `6763 x 34` groups while the gate remained active, giving
  four episodes and one proxy false negative. This was a telemetry
  segmentation counterexample, not a missed native gate.
- Corrected the tracker so a physical-frame change while active censors the
  old episode and opens a new one. Confirmatory complete hard-no-Bomb run
  `lunatic_route2_stage4a_unattended_20260726_122014` retained 8,914
  decisions, 17 descriptive hits, both completion markers, and 3,116
  observations (`3031/84/1`). It produced five episodes for five delayed
  pulse groups (`TP/FP/FN = 5/0/0` relative only to that proxy); the terminal
  episode was right-censored. All reads were valid, one interval was
  unstable/unknown, and `-2` was not observed.
- Post-run review found that the censored old episode used the first
  new-frame observation as its endpoint. Thus `122014`'s first `+76` serial
  delta is an upper boundary sample. Future tracker output now closes the old
  episode at its last semantically known old-frame observation before
  beginning the new one. This is unit-tested and leaves the retained
  five-episode classification unchanged, but was not physically rerun.
- **Observed runtime evidence:** at frozen manager frame `20845`, native
  active input `0x81` moved `(66.494, 399.499)` to `(376.000, 399.499)`,
  `309.506 px` over `2.056 s`, while FRScreen serial advanced 124. At
  `29506`, `stay` moved `0 px` over `2.629 s` while serial advanced 158.
  The earlier `120839` directional episodes moved `282.900` and `355.904 px`
  with serial deltas 123 and 159.
- The `122014` gate-positive first-repeat observations occurred after
  `32.864..68.187 ms`; gate-negative repeats overlapped them. Hypothetical
  50-ms cuts disagreed with the native gate on 2,744 inactive repeats in
  `120839` and 1,728 in `122014`, confirming CE-0121 without granting the
  delayed pulse proxy ground-truth status.
- Logged probe captures had median/p95/max
  `0.341/0.444/12.640 ms` and `0.191/0.490/17.181 ms`. These exclude
  unlogged calls and do not bound total CPU/delivery contention. The
  98.19%/98.26% viability-query availability lacks the rejected guard's
  epoch-starvation signature but is not a controlled performance A/B.
- Review also confirmed no direct mask/epoch/estimator/policy mutation, but
  found synchronous captures and trace flushes on the issue thread. The
  telemetry is therefore physically perturbative; lookup timing alone cannot
  establish a side-effect-free shadow.
- **Authority conclusion:** accept the native gate and corrected tracker as
  Stage-4A shadow infrastructure only. CE-0120 remains open at movement
  neutralization, pending-command/delay support, one-reset semantics,
  next-phase entry, `-2`, other workloads, and total delivery contention.
- Both semantic trials intentionally disabled viability-audit capsules to
  keep the sensor experiment isolated. Their raw and compact telemetry are
  retained, but they are not finite-model replay bundles and do not replace
  the `100451`/`103856` Stage-4A replay-capable floor.
- Compact input-clock audits SHA-256:
  `120839 =
  76d052d36f9b5183fa01508f11504835400ad8fce39c92a42b28d69134b9f0cf`,
  `122014 =
  f145a5f2631d833ce90ae2d5059948e38251ce191b9cfc16b1f6ef5ad7e98f6c`.
  Linux and Windows quick suites pass 509 tests in `2.321/3.898 s`.

## 2026-07-26: Local Pipeline Certificate And Beam Audit

- **Observed deterministic defect:** `_hazards_for_positions` used one global
  bullet/laser coarse slice for a batch and then reduced every selected hazard
  against every position. Positive clearance and soft risk could change when
  an unrelated companion position was added. Added per-position relevance
  masks before collision, robust-clearance, and risk reductions. The focused
  bullet/laser batch-versus-scalar regression is CE-0122.
- **Observed model defect:** the local certificate used the last desired mask
  as active input and sampled a new full pickup delay for every candidate,
  including the already-held no-write action. Added game-neutral
  `LocalPipelineRoot`, exact causal branch enumeration, and an independent
  scalar fixed-lease oracle for native active, held desired, one older pending
  command, conditioned remaining support, and conditional new writes.
  CE-0123 records the failure and authority boundary.
- Added a packed all-action TH08 implementation. With an omitted explicit
  root, it retains the current active-equals-held live fallback. Live
  selection and fresh-hazard recertification do not receive the new root.
  New trace rows retain a `shadow_no_action_authority`
  `local_pipeline_root` record with active/held/pending masks, motion-action
  projections, and estimator-consistency evidence. Replay prefers direct
  roots and rejects mask/action/snapshot/prior-write disagreement.
- Focused scalar/packed coverage includes pending/no-write ordering, the
  older/new delay product, a pending-prefix collision, invalid one-pending
  roots, distinct focused/unfocused zero-motion write identity, 24
  deterministic randomized TH08 roots, vectorized boundary parity, batch
  invariance, and legacy-equivalent hard labels.
- Refactored reusable TH08 trace-to-bullet/laser/enemy decoding into
  `scripts/th08_trace_replay.py` and added
  `scripts/analysis/local_pipeline_certificate_audit.py`. Old trace roots are
  explicitly labeled **inferred** because the schema predates direct local
  root telemetry.
- **Observed replay differential:** the deliberately mismatch/pre-hit-heavy
  Stage-4A `122014` sample changed `86/155` safe action sets, 76 ranked
  actions, and 21 recorded actions from legacy safe to pending-aware unsafe.
  Stage-6B `011639` changed `85/156`, 73, and nine; two recorded actions changed
  in the reverse direction. Packed equivalent-root hard parity failures were
  zero on both samples. These are sample counts, not population rates or
  causal prevented-hit estimates.
- **Observed certificate timing:** from already decoded TH08 objects, with
  projection/packing/induction/certification inside the boundary, the legacy
  corrected-batch path measured `4.786/6.763 ms` Stage 4A and
  `5.819/11.719 ms` Stage 6B median/p95. Packed equivalent roots measured
  `2.265/3.487` and `2.804/6.094 ms`; packed pending-aware roots measured
  `3.134/6.372` and `3.936/7.911 ms`.
- Added default-off first-action and exact-first-action beam deduplication
  modes plus `local_beam_stability_audit.py`. Across 96 roots per trace they
  changed five Stage-4A and four Stage-6B actions but improved or worsened no
  sampled hard vector. Independent width-24 continuation beams per first
  action changed/improved zero of five and six hard-nonzero roots while
  costing `191.795/275.649 ms` median. Width 256 changed 38/30 actions but
  cost `21.988/57.336` and `37.621/55.826 ms` median/p95 and is not an oracle.
  The beam modes are rejected for live promotion by this evidence.
- **C++ decision:** defer a wholesale local-planner rewrite. Packed Python
  removed about half of equivalent-root certificate median time, and the
  correct certificate currently meets the offline gate. If direct-root
  Windows observe/decode/project/certify/issue timing later misses its
  deadline, the next candidate native boundary is compact raw decode,
  projection, packing, and all-action certification checked against the
  independent Python scalar oracle—not a wholesale port of the unproved beam.
- Retained artifacts:
  `artifacts/benchmarks/local_pipeline_certificate_20260726.json`
  (`SHA-256
  15e9d2d8b1968dedc6d2cf957506cb4ac6870a43c7e32d04ab70766d3f48ac46`)
  and `artifacts/benchmarks/local_beam_stability_20260726.json`
  (`SHA-256
  747e6a39a88233f308f292a0670804992cc4c5e5d703c5da1cfd4576e7ec098f`).
  Full interpretation and the five formal review answers are in
  `notes/LOCAL_PIPELINE_CERTIFICATE_AND_BEAM_AUDIT_20260726.md`.
- Validation: focused local-oracle, local-certificate, and live-agent suites
  pass `5/5`, `7/7`, and `81/81`; `py_compile` and `git diff --check` pass.
  The bounded formal audit completed all four quick profiles and retained the
  expected legacy/no-write mismatches at seeds `20002/20003`; the quick belief
  workspace differential completed 16 cases with zero scalar/native, upper,
  candidate, certification, or bound failures.
  Linux and Windows complete quick suites pass `521/521` in
  `3.291/7.508 s`. No game, daemon, input injection, or physical trial was
  started.

## 2026-07-26: Native Local Pipeline, Geometry, And Hard Stage-1 Gate

- **Observed full-chain telemetry:** persistent `ReadProcessMemory`
  destination buffers reduced Windows bullet-pool read from
  `7.007` to `1.039 ms` median and all-pool read from `11.871` to
  `3.914 ms`; observe-to-input changed from `36.649` to `30.107 ms` on the
  paired Stage-6B boundary.
- **Observed native beam parity/performance:** the quantized no-item reducer
  passed adversarial/random/end-to-end differential gates. On 128 direct
  retained roots per trace with two repeats, action and hard-label mismatches
  were zero. Stage-4A beam changed from `6.423/8.221` to
  `4.549/5.759 ms` median/p95; Stage-6B changed from
  `9.547/13.528` to `6.204/8.270 ms`.
- **Observed packed bullet parity/performance:** native slot-order fields and
  17-frame projections matched the independent Python decoder across
  malformed and dense pools. The live sparse crossover is 16 active slots.
  Final Windows decode-plus-projection p95 was `0.130 ms` at 16,
  `0.155 ms` at 400, `0.175 ms` at 800, and `0.197 ms` at 1,536 bullets,
  versus Python `0.167`, `2.623`, `5.150`, and `9.263 ms`.
- **Observed focused physical gate:** complete Hard Route-2 Stage-1 run
  `hard_route2_stage1_unattended_20260726_175049` retained 7,099 decisions,
  zero native hits, zero Bomb, zero deadline misses, and a complete terminal
  summary. It measured bullet read `1.027/2.382`, bullet decode
  `1.092/3.836`, local certificate geometry `1.735/4.738`, native beam
  `7.549/13.430`, local plan `11.956/19.711`, and observe-to-input
  `22.265/33.234 ms` median/p95. Hard Stage-1 is an implementation gate, not
  Lunatic/Extra acceptance.
- **Observed menu-boundary defect CE-0125:** the first Hard attempt `174946`
  reached the correct stage screen with difficulty cursor 2 while the
  gameplay difficulty index was still 0. Preconfirm validation now uses the
  menu cursor; the armed agent separately validates gameplay index 2 after
  load. The successful `175049` attempt passed both.
- **Observed direct-root counterexample CE-0124:** an action-epoch
  discontinuity occurred at frame 16748. At frame 16750,
  `input_current=0xA5/down_right`, held desired was
  `0x01/stay_unfocused`, pending support was absent, and
  `estimator_consistent=false`. This disproves treating the first
  post-discontinuity root as active-equals-held. The explicit root remains
  shadow-only.
- **Observed geometry tail:** Stage-6B frame 22030 had 111 bullets,
  210 lasers, five bodies, 81 local branches, `67.119 ms` certificate
  geometry, `95.883 ms` local plan, and `110.549 ms` observe-to-input.
  Serialized laser records did not hide a segment-count explosion.
- **Observed hazard-major differential:** hoisting per-hazard segment
  geometry, candidate-AABB broad phase, and cached float32 laser inputs
  produced zero action and hard-label mismatches on 64 direct roots from each
  of Stage 4A `160712` and Stage 6B `165841`. Stage-6B certificate geometry
  changed from `2.210/4.903` NumPy to `1.337/2.304 ms` native; complete local
  planning changed from `14.441/23.110` to `12.540/17.223 ms`.
- **Inferred bottleneck:** a same-size offline native certificate workload
  costs about 1--2 ms, so the 40--67 ms physical geometry tail is mostly
  scheduler/background-solver contention rather than irreducible
  point-to-segment computation. A post-change physical trace is still
  required to attribute each tail.
- **Observed planner/contention tradeoff:** four interleaved Windows rounds
  measured representative native viability at `40.716/57.090 ms`
  median/p95 with one worker, `36.070/43.880` with two, and
  `26.953/29.821` with four. Four-worker beam-geometry p95 was `17.282 ms`
  versus `15.920 ms` with one. Per user priority, authoritative plan
  freshness wins: the live default remains four normal-priority native
  workers; smaller limits are ablations.
- **Hypothesized/deferred:** a dynamic uniform grid/BVH is not justified while
  exact certificate geometry is already near 1--2 ms outside contention and
  laser geometry changes every projected frame. Wider SoA/SIMD remains a
  possible beam optimization only if a physical trace isolates geometry as
  the remaining bottleneck. Signed clearance cannot be replaced by one
  occupancy bit.
- Retained design/evidence:
  `notes/LOCAL_NATIVE_GEOMETRY_AND_CONTENTION_20260726.md`,
  `notes/LOCAL_NATIVE_HAZARD_QUERY_PROPOSAL_20260726.md`,
  `notes/LOCAL_NATIVE_BEAM_REDUCTION_PROPOSAL_20260726.md`,
  `notes/PACKED_NATIVE_BULLET_DECODE_PROPOSAL_20260726.md`, and the new
  benchmark/runtime artifacts named there.
- Validation: Linux and Windows quick suites pass `556/556` in
  `4.764/6.993 s`; `git diff --check` and focused native/corridor/live suites
  pass. The bounded formal audit completed all four quick profiles and
  retained only expected legacy/no-write mismatches at seeds `20002/20003`.
  The quick belief workspace completed 16 cases with zero scalar/native,
  upper, candidate, certification, or bound failures.

## 2026-07-26: Selectable Full Route And Manual Replay-Save Handoff

- Added Easy, Normal, and Hard Sakuya/Remilia Route-2 Final-B manifests with
  explicit ECL difficulty masks `0x01`, `0x02`, and `0x04`. The retained
  reachable spell counts are `30`, `36`, and `37`; the existing Lunatic
  manifest remains `37`.
- Generalized the full-route supervisor from a fixed Lunatic cursor/index to
  `--difficulty easy|normal|hard|lunatic`. Native title cursor validation and
  the live agent independently validate the selected menu difficulty and the
  later gameplay difficulty index.
- Replaced the falsely Lunatic-specific new dossier output with
  `th08-route-run-dossier-v3`. Difficulty label/index, mask, spell inventory,
  Markdown title, and comparison baseline now come from the selected route
  manifest. Historical Lunatic v2 dossiers remain accepted as baselines.
- Added `--leave-game-running`. **Observed in tests, not yet physically
  exercised:** only accepted `route_complete` plus explicit opt-in retains the
  game. That branch releases injected keys, closes the hotkey agent, records
  the handoff, and sends no result/save choice. Failure, timeout, and
  incomplete-route paths retain identity-scoped cleanup.
- Focused full-route, route-manifest, and dossier suites pass `4/4`, `5/5`,
  and `19/19`. Linux and Windows complete quick suites pass `560/560` in
  `4.840/7.848 s`. No physical full-route run had started at this checkpoint.

## 2026-07-26: Complete Hard Route And Feasibility Bottleneck

- **Observed physical completion:** Original-game Hard Route-2
  `hard_route2_fullrun_unattended_20260726_184942` completed one continuous
  Sakuya/Remilia path through Final B. The trace has 70,699 decisions over
  frames `1..228661`, 39 native hits, zero Bomb/deathbomb input, zero
  foreground interruption, zero runtime/JSON error, and stage counts
  `1/1/8/11/9/9`.
- **Observed manual-save handoff:** After `terminal_unload` and
  `route_complete`, `--leave-game-running` released injected keys, closed the
  agent, sent no result/save choice, and left the verified PID running. The
  user saved the replay manually. Cleanup later reverified the full path,
  SHA-256, and live patch byte before terminating only PID 52660; no matching
  target remained.
- **Observed performance:** Stage pool-read median/p95 ranges were
  `4.09..4.71/7.02..8.15 ms`; local-plan ranges were
  `11.81..14.55/20.86..26.90 ms`. The run reached 1,231 bullets and 256
  lasers without a stall. The robust background planner published 9,265
  native solutions; solve median/p95 was `121.64/422.51 ms` and
  first-observed age median/p95 was `2/8` frames.
- **Observed failure split:** 38/39 hit ledgers report global viability-kernel
  exhaustion before contact. Causes were 23 modeled committed-prefix
  collisions, 14 exact bullet overlaps, one exact enemy-body overlap, and one
  sensor-gap/unmodeled contact. Boundary and fast-mode factors occurred on 30
  and 29 hits; only four hits exceeded 1,000 bullets. Fresh-local/global
  contradictions remain six selected actions over 56,196 comparable rows.
- **Inferred priority:** Decoder/native geometry performance is no longer the
  dominant physical bottleneck. Preserve the residual sensor/body/local-vs-
  global correctness gaps, but direct new CPU and algorithm work toward
  earlier feasibility, coarse false-empty separation, survival/control
  reserve after loss, and explicit route-conditioned tubes.
- Fixed full-route/practice regression IDs so the case prefix derives from
  physical difficulty. Rebuilt all 39 cases as
  `HARD-S0-F20606-T1` through `HARD-S7-F228457-T1`.
- Validation: Linux and Windows quick suites pass `561/561` in
  `4.637/11.793 s`; the focused dossier and practice-dossier suites pass.
  See CE-0126 and
  `notes/runs/hard_route2_fullrun_unattended_20260726_184942.md`.

## 2026-07-26: Hard Losing-State Reserve And Feasibility Audit Gate

- **Observed bounded replay:** streamed the retained 1.84-GB Hard full-route
  trace twice and kept a deterministic 400-row reservoir from 2,353 eligible
  empty-kernel repair/recovery decisions within 240 frames of a contact.
  This avoids treating RAM capacity as an experimental selection rule.
- **Observed paired result:** enabling the default-off
  `losing_control_reserve` changed 28/400 actions. All 400 fresh hard vectors
  were equal between variants. Of the changed actions, 27 reduced
  delay-scaled reserve deficit, one tied, and none regressed; zero-deficit
  selections rose from 192 to 222. Robust-collision selections remained
  38, negative robust-clearance selections remained 64, and terminal
  collision selections remained zero.
- **Observed timing:** interleaved replay cost changed from
  `10.057/13.429 ms` median/p95 to `10.139/13.257 ms`. This is an offline
  local boundary and not proof of issue-time cost or physical survival.
- **Inference:** the reserve is a credible proposal for the 30/39
  boundary-heavy post-loss histories because it ranks only actions that are
  already equal under the fresh hard vector. It does not recover a viable
  kernel, certify a bridge, or change a finite-model losing label.
- **CPU decision:** WSL exposes 20 logical CPUs on the i9-13900H, but the
  Hard run already observed published-policy age `2/8` frames median/p95.
  Use spare CPU first for isolated capsule replay at 16/8/4-pixel grids,
  horizons, delay support, and uncertainty ablations. Do not blindly expand
  the live four-worker pool, whose per-layer thread creation and contention
  can worsen local issue latency.
- Added
  `notes/HARD_FULL_ROUTE_FEASIBILITY_DIAGNOSIS_20260726.md`,
  `artifacts/benchmarks/hard_full_route_losing_control_reserve_20260726.json`,
  a bounded streaming reserve benchmark mode, and two focused eligibility
  regressions. No live selection or strategy status was promoted.
- Validation: focused reserve and live-agent suites pass `2/2` and `82/82`;
  Linux and Windows quick suites pass `563/563` in `4.846/7.435 s`;
  `py_compile` and `git diff --check` pass.

## 2026-07-26: Hard Stage-4A Same-Root Viability Differential

- **Observed audit-only physical capture:** Hard Stage-4A `202439` completed
  `route_complete` with 13,535 decisions, 15 hits, zero Bomb input, and no
  foreground/runtime/JSON failure. Capsule I/O was enabled, so hit count is
  provenance rather than a strategy A/B. Local plan remained
  `12.903/22.274 ms`; global solve and first age were
  `151.377/429.975 ms` and `2/8` frames median/p95.
- **Observed bundle integrity:** all 1,741 capsules opened, all 1,729 trace
  references resolved, and no capsule was unreadable. Trace SHA-256 is
  `88f54b6a7984878b0e6cf88580fc9f217226b0d6204d29701fb15a7e0af56b41`;
  bundle SHA-256 is
  `89b1bd71e299a429091092a59da0cfc628a259fdf181a68c546bccb5d78592e6`.
  The 15-case executable regression corpus passes.
- **Observed same-root split:** 120 stratified pre-hit queries produced 61
  empty roots: 47 modeled-losing/unresolved, 8 primary finite-horizon
  collapses, and 6 spatial false empties. Fresh 16-pixel recomputation rescued
  0/61; h32/h48/h64 rescued 11/3/0; exact current query delay support rescued
  one. Seven birth-gap observations were concentrated before two hits.
- **Observed optimistic boundary:** 9/59 comparable winning roots were
  rejected by a later-policy terminal overlap. This can remove false wins but
  cannot explain empty predecessors.
- **Observed uniform-grid cost:** on 12 same-capsule empty roots,
  16/8/4-pixel median/p95 was
  `59.10/201.94`, `225.90/907.68`, and
  `1062.85/3506.43 ms`. Full 4-pixel induction is about 18x the sampled
  16-pixel median for a 6/61 rescue rate.
- **Observed CE-0127:** the issue-time enemy recertifier ignores the global
  allowed-action set. It silently changed an in-mask plan to an out-of-mask
  action on 168 globally winning rows while retaining constrained telemetry.
  At canonical frame 3353 it changed `up_fast` to `down_fast`; the next query
  became empty before the first hit at 3419. The fresh intersection was not
  serialized, so this is an authority/transaction counterexample, not a
  prevented-hit claim.
- **Decision:** repair the issue transaction before strategy promotion. Then
  prioritize explicit pre-loss terminal/interior reserve strategy, followed
  by exact augmented-root partial-survival witnesses after loss. Keep
  full-field fine refinement rejected; use only proof-backed query-local
  refinement.
- **Report correction and validation:** the generated terminal-overlap caveat
  now calls its rejection a conservative diagnostic rather than incorrectly
  describing the 120-query cohort as empty-only; a focused regression guards
  that wording. Linux and Windows quick suites pass `563/563` in
  `5.103/8.215 s`; `git diff --check` passes.
- Detailed analysis and the five review questions are in
  `notes/HARD_STAGE4A_VIABILITY_DIFFERENTIAL_20260726.md`.

## 2026-07-26: CE-0127 Fresh/Global Issue Transaction Repair

- **Observed defect boundary:** ordinary local planning already intersected
  cached global actions with its fresh preflight certificates, but later
  enemy-change recertification ranked all 17 actions without the global mask.
- **Implemented correction:** issue recertification computes all-action fresh
  certificates once, preserves a planned action in the fresh/global
  intersection, restricts an unsafe replacement to that intersection, and
  explicitly relaxes only when the intersection is empty. With no global
  constraint it acts only as a local hard shield.
- **Telemetry correction:** each transaction retains the planned and selected
  certificates, complete fresh safe set, exact global intersection, selection
  reason, and relaxation state. Repair/recovery/safety/survival fields are
  rebound to the selected action; an old beam-endpoint control-reserve value
  is marked invalid after an action change.
- **Validation:** deterministic preserve/intersect/relax regressions pass;
  the complete Linux and Windows quick suites pass `567/567` in
  `4.996/9.072 s`; the retained Hard Stage-4A 15-case physical regression
  corpus passes with zero deathbomb. The old `202439` trace did not retain the
  fresh all-action tuple, so it cannot supply exact historical transaction
  replay. A new no-audit Hard Stage-4A physical gate is required.

## 2026-07-26: CE-0127 Hard Stage-4A Physical Gate And CE-0128

- **Observed complete physical gate:** no-audit Hard Stage-4A `211210`
  completed `route_complete` over 12,726 decisions and frames `3..42059`.
  It recorded seven hits, zero Bomb, no foreground/runtime failure, safe
  no-save cleanup, and no surviving game/supervisor process. Hit count is one
  RNG-distinct sample, not a causal A/B against the 15-hit audit capture.
- **Observed transaction authority:** all 2,417 enemy-change recertifications
  retained a transaction. The shield preserved 2,387 planned actions and
  changed 30. Independent recomputation found 924 nonempty applicable
  fresh/global intersections, ten explicit empty-intersection relaxations,
  18 inherited planner relaxations, 19 selected actions outside the advisory
  global set, and zero outside-global actions without an explicit relaxation.
  Certificate, selected-strategy, flag, no-Bomb, and intersection checks had
  zero authority violations.
- **Observed stability and latency:** action overrides fell from
  `1435/2672` in audit `202439` to `30/2417`. Local plan median/p95 changed
  `12.903/22.274 -> 12.155/21.486 ms`; issue recertification
  `2.316/4.842 -> 2.172/4.704 ms`; global solve
  `151.377/429.975 -> 145.076/421.706 ms`. Capture modes and RNG differ, so
  the timings establish no regression rather than a causal speedup.
- **Observed remaining planner failure:** global viability was empty before
  all seven contacts. The first hit at frame 3,296 occurred at the
  right/bottom boundary with a modeled committed-prefix collision. Boundary
  and fast-mode factors occurred on four and five hits. The transaction fix
  prevents authority loss but does not solve early feasible-set exhaustion.
- **CE-0128:** frames 32,515 and 40,699 explicitly relaxed an empty
  fresh/global intersection and safely preserved the planned action, but
  mislabeled the reason as preservation inside the intersection. No action or
  constraint flag was wrong. The reason selector and independent auditor were
  corrected and covered by a deterministic regression; one clean telemetry
  confirmation remains.
- **Post-correction validation:** Linux and Windows quick suites pass
  `571/571` in `4.792/7.298 s`; the seven-case physical regression corpus
  passes; JSON parsing, `py_compile`, and `git diff --check` pass.
- Raw trace SHA-256:
  `329407bbc0aac733cfd2b7722b653e0aa2c0b38abefe1df624ff53fc1e7b2fd3`.
  The compact first-gate audit is
  `artifacts/viability_audit/hard_stage4a_20260726_211210_issue_transaction.json`.

## 2026-07-26: CE-0128 Confirmation And Transaction Closure

- **Observed complete second gate:** no-audit Hard Stage-4A `212756`
  completed `route_complete` over 13,438 decisions and frames `1..43052`,
  with six hits, zero Bomb, accepted terminal unload/no-save cleanup, and no
  surviving process.
- **Observed exact transaction audit:** all 2,210 recertifications retained a
  transaction. The shield preserved 2,189 planned actions and changed 21;
  1,034 applicable intersections were nonempty, three empty intersections
  explicitly relaxed, and 30 earlier planner relaxations were inherited.
  The independent auditor found zero intersection, reason, constraint,
  certificate, selected-strategy, control-reserve-validity, no-Bomb, or
  silent outside-global violations.
- **Observed delivery:** recertification median/p95 was
  `2.027/4.433 ms`, local planning `11.686/20.830 ms`, global solving
  `148.298/420.866 ms`, and first policy age `2/8` frames. These remain inside
  the pre-repair envelope.
- **Physical outcome limit:** six hits is another RNG-distinct sample, not a
  causal survival estimate. Five contacts followed global-kernel exhaustion;
  one remained an unresolved sensor/model failure. The first fresh-attempt
  hit was delayed to frame 10,590 but still occurred after global loss.
- **Decision:** close CE-0127 and CE-0128 for the current enemy-change issue
  boundary. Begin the explicit pre-loss continuation/interior-reserve
  strategy gate; keep future bullet/laser birth completion a separate S07
  obligation.
- Raw trace SHA-256:
  `cea41e2914c32d7157082cefca81e60a8d83e6d891886d294fdffcdf5f6c79a2`.
  Compact transaction audit:
  `artifacts/viability_audit/hard_stage4a_20260726_212756_issue_transaction.json`.

## 2026-07-26: Pre-Loss Continuation Gate And CE-0129

- **Problem contract:** Added
  `notes/PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md`. The proposal may
  rank only a complete nonrelaxed global/fresh viable action set, never
  changes membership or Bomb authority, and treats repair volume as an exact
  finite-model continuation score rather than a physical survival proof.
  The note also rejects unproved screen cropping: hazard pruning must
  conservatively exclude the complete reachable space-time action tube,
  including delay/cadence error and stop/resume/redirect/transform/birth
  envelopes.
- **Observed opportunity:** Across full Hard `184942` and Stage-4A
  `202439/211210/212756`, 60,526 decisions had complete viable repair data.
  The historical selected action was below the maximum repair volume on
  21,634 viable rows. This is a candidate-ranking opportunity, not proof that
  maximum local volume is physically optimal.
- **Rejected aggressive implementation:** Adding repair and reserve to
  native/Python beam truncation changed `303/800` broad actions and improved
  repair on 288 with zero broad hard regressions. In the 300-frame pre-hit
  reservoir it changed `392/800`, improved repair on 356, but regressed two
  terminal hard vectors. CE-0129 records `202439:F28412` and
  `212756:F12843`. The experimental native-v2 ABI and beam changes were
  removed; the existing native reducer is unchanged.
- **Retained final-only implementation:** `choose_action` has an explicit
  default-off `preloss_continuation_preference`. It activates only when every
  effective nonrelaxed global action has same-query repair data. Historical
  beam pruning remains unchanged; final selection places repair and
  delay-scaled interior reserve after collision/negative-clearance and
  terminal hard columns. A reduced six-bullet regression from
  `212756:F17317` changes `left` repair 38 to `down` repair 39 with equal hard
  deficits.
- **Observed paired replay:** On the broad fixed reservoir the final-only
  form changed `7/800` actions; all seven had equal hard vectors and global
  membership, repair improved on three, and reserve improved on five. On the
  pre-hit reservoir it changed `13/800`; all 13 had equal hard vectors and
  global membership, reserve improved on 11, repair on two, with no repair or
  reserve regression. Route gate improved/tied/regressed `1/11/1`.
- **Observed timing:** The two final paired replays intentionally ran
  concurrently. Pre-hit baseline/proposal median/p95 was
  `10.601/17.187` versus `10.611/17.264 ms`; broad was
  `10.212/15.331` versus `10.170/15.296 ms`. This establishes negligible
  ranking cost under that offline contention workload, not Windows issue
  WCET.
- **Validation:** Linux and Windows quick suites pass `575/575` in
  `4.757/7.822 s`; Python/native end-to-end action parity includes enabled
  final-only roots. Native beam source, ABI, and default behavior are
  unchanged.
- **Decision:** Keep final-only ranking proposal-only and default-off. Its
  coverage is too small to be the main feasibility fix. The next stronger
  experiment must preserve the complete historical beam as an immutable
  incumbent and add a separately budgeted continuation-biased supplemental
  lane; final hard comparison over the union may improve coverage without
  making the baseline endpoint unavailable.

## 2026-07-26: Immutable Supplemental Lane And Intensive Geometry Gate

- **Problem contract:** Added
  `notes/IMMUTABLE_SUPPLEMENTAL_CONTINUATION_LANE_20260726.md`. CE-0129's
  historical beam and native reducer remain immutable. The new lane is a
  separately budgeted proposal search and cannot remove the historical
  endpoint. Final admission requires effective-global membership,
  componentwise issue-prefix/local/terminal hard nonregression, route
  nonregression, and a strict exact repair-volume then boundary-reserve
  improvement.
- **Implementation:** Added game-neutral
  `touhou_control.supplemental_local_beam`, a separate
  `touhou_local_supplemental_beam_reduce_v1` native export and independent
  Python oracle, default-off orchestration, historical fallback on failure,
  source/candidate/failure telemetry, separate supplemental timing, and a
  `local_collisions` hard component. The historical v1 reducer ABI and
  historical beam loop remain unchanged. There is no live CLI switch.
- **Reducer validation:** 128 randomized direct Python/native supplemental
  reductions and randomized end-to-end local decisions retained identical
  indices, actions, and hard labels. Focused regressions cover a high-repair
  action discarded by width-1 historical pruning, route-gate rejection,
  negative width rejection, and exception fallback.
- **Observed broad replay:** Across 800 fixed Hard roots, final-only changed
  8 actions. Width 4 changed 286, improved exact repair on 273, and improved
  equal-repair reserve on 13. Widths 8/12 changed 288/296, with diminishing
  returns. Width-4 supplemental median/p95 was `2.449/3.114 ms`; total
  historical versus width-4 was `6.461/9.546` versus `9.115/12.156 ms`.
- **Observed pre-hit replay:** Across 800 fixed roots within 300 frames of a
  recorded hit, final-only changed 13 actions. Width 4 changed 341, improved
  exact repair on 323, and improved equal-repair reserve on 18. Widths 8/12
  changed 350/364. Width-4 supplemental median/p95 was
  `2.425/3.026 ms`; total historical versus width-4 was `6.749/10.038`
  versus `9.429/12.663 ms`.
- **Contract result:** Both reservoirs had zero historical-action mismatch,
  effective-global membership violation, issue/local/terminal hard-component
  regression, route regression, continuation-admission violation, or
  supplemental failure. Width 4 is the retained Pareto candidate. This is
  same-root proposal evidence, not prevented-hit, deadline, or unrestricted
  optimality evidence.
- **Generated intensive cases:** Added six deterministic TH08-semantic
  workloads with up to 4,096 piecewise transformed bullets and 2,048 lasers,
  including stop/resume/reverse/redirect events, executable and degenerate
  lasers, bodies, tangent boundaries, uncertainty, companion-batch
  invariance, and end-to-end local decisions. Native/NumPy collision and
  clearance-sign parity were exact, batch mismatches were zero, end-to-end
  action/hard labels were equal, and maximum clearance difference was below
  `3.32e-5`. Risk-order difference reached `0.213` and remains soft with
  unknown error direction.
- **Geometry decision:** Ten already-lowered off-tube queries with 4,096
  bullets and 1,024 lasers cost only `2.211/2.408 ms` median/p95, while
  dense genuinely crossing beyond-pool geometry cost
  `108.711/112.989 ms`. The existing conservative AABB pruning is effective;
  no viewport crop, velocity cone, or per-decision grid/BVH is promoted.
- **Artifacts:** Broad replay SHA-256
  `28072dd8589bb3abcb8aa382443f93d6bd693f59194b62b5d8d7e495210b8a84`,
  pre-hit replay
  `8f336702b0d4f4ed5f798bb845be3c537d9352068204d2bb7a8ae84432500c38`,
  and intensive corpus
  `2e654aa456bfb9bbb1abee41d565950ab7a86c63f7ab45de05f0818672409d54`.
- **Validation:** Linux and Windows quick suites pass `583/583` in
  `5.158/7.979 s`. Both native libraries rebuilt successfully; native build
  output remains ignored.
- **Next gate:** Measure width 4 on direct Windows
  observe/decode/project/certify/supplemental/issue roots under the live
  four-worker planner contention. Optional work must not age authoritative
  publication; failure or budget miss returns the historical action. A
  focused Hard shadow and physical A/B remain downstream, not yet authorized.

## 2026-07-26: Direct-Root Windows Supplemental Contention Gate

- **Contract fixed before measurement:** Added
  `notes/SUPPLEMENTAL_DIRECT_ROOT_WINDOWS_CONTENTION_GATE_20260726.md`.
  It separates retained physical game-process telemetry from already-parsed
  JSON replay and fixes zero finite violations, p95/max compute increment,
  global-planner p95/throughput, and stable-60-Hz hybrid deadline criteria.
- **Implementation:** Moved the fail-closed direct active/held/pending root
  parser into the reusable TH08 trace adapter, taught the common replay helper
  to accept explicit roots and predecoded hazards, and added a Windows gate
  that rotates historical/width-4 idle/four-worker variants. It measures
  trace reconstruction, root parsing, local segments, forced same-snapshot
  issue recertification, viability solve throughput, CPU/wall ratio, physical
  chain telemetry, policy age, and paired deadline estimates.
- **Population:** Hard Stage-4A `212756` contained 8,180 valid non-overdue
  direct roots, zero invalid roots, and eight explicitly overdue exclusions.
  Broad/pre-hit-300/stress reservoirs deduplicated to 253 roots; three rounds
  produced 759 samples per variant and 1,518 finite comparisons.
- **Correctness observed:** Width 4 was active on 729/759 measurements in
  each contention class. All historical-incumbent, effective-global,
  issue/local/terminal hard, route, continuation, Bomb, exception,
  issue-transaction, and nonrelaxed issue-global violation counts were zero.
  Forced recertification changed no selected action.
- **Comparator correction:** An exploratory report incorrectly treated 30
  fresh-global contradiction samples, on which the supplemental lane was
  intentionally inactive, as historical/membership failures. The checker now
  conditions those two claims on lane admissibility; a deterministic test
  protects this information/authority distinction. Hard and issue checks
  remain unconditional.
- **Physical baseline observed:** Across all 8,180 valid direct-root rows,
  `observe/read/decode/local-plan/issue/observe_to_input` p95 was
  `0.526/7.662/1.986/20.144/7.247/33.229 ms`. Action lag p95 was two frames,
  corridor/viability age p95 was 28/27, all rows applied worker limit four,
  and deadline misses were zero.
- **Planner contention observed:** Historical/supplemental four-worker solve
  p95 was `40.135/40.060 ms`; throughput was
  `29.439/29.873 solves/s`. Ratios `0.998x/1.015x` pass the fixed
  `<=1.10x/>=0.90x` gate.
- **Delivery failure observed:** Paired supplemental-minus-historical
  direct-root compute under four-worker load was
  `2.354/14.273/25.184 ms` median/p95/max, failing fixed
  `<=5.0/<16.667 ms` limits. The supplemental search itself cost
  `3.273/6.858/10.553 ms`. One of 759 hybrid deadline estimates became a new
  miss. CE-0130's frame-37,834 witness rose from `18.551` to `43.735 ms`,
  taking recorded `41.999 ms` observe-to-input to a `67.183 ms` estimate
  against a `66.667 ms` support budget.
- **Decision:** Do not enter focused Hard shadow/physical A/B and do not add a
  live CLI. The finite selector remains proposal-only. Synchronous
  current-issue delivery is rejected; next test a complete deadline-aware
  native rollout/hazard-query boundary or exact-version asynchronous
  publication, with historical fallback on every miss/cancellation/mismatch.
- **Artifact:**
  `artifacts/benchmarks/hard_supplemental_direct_root_contention_windows_20260726.json`,
  SHA-256
  `43751f0a74c6285156acf1454df0c5be85deb27c3856d6570d3667ebba466ad0`.
- **Validation:** Linux and Windows quick suites pass `587/587` in
  `5.283/8.008 s`; focused gate tests, Python compilation, JSON parsing, and
  `git diff --check` pass.
