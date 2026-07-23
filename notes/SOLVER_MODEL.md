# TH08 Route Solver Model

Status: design contract grounded in the currently recovered ECL, bullet, laser,
player, and SHT behavior. It is not yet a validated gameplay solver.

## Acceptance Target

The first fixed acceptance target is the Sakuya/Remilia team on Lunatic and
Extra. A route is accepted only when the same input trace can be replayed from
a pinned initial state and demonstrates all of the following:

1. Player collision never occurs outside a deliberately scheduled bomb window.
2. Every bomb has a resource-feasible trigger frame and preserves survival.
3. Reported graze and collected items agree with instrumented game state.
4. The trace includes stage transitions, boss nonspells, spell phases, and the
   Extra stage rather than optimizing isolated screenshots.
5. Repeated runs with the same replay inputs produce the same result, or every
   remaining random seed/state input is captured explicitly.

"Accurate planning" therefore means an executable frame-indexed control trace,
not only a path drawn over one recorded bullet image.

## Evidence Boundary

- **Observed**: fixed 60 Hz scheduling; ECL timeline/VM structure; direct bullet
  and laser creation; bullet transforms; player input bits; SHT movement and
  collision widths; hit-to-predeath/Bomb resource rules; all used item motion
  states and direct item reward conversions; stable registered callback
  priority order and the solver-critical player/enemy/item/projectile suborder;
  route-2 focus transitions and all four option shot-source positions;
  enemy opcode `0xB2` random/player-biased motion selection and its seven
  easing-code behaviors;
  opcode `0x53` boss identity consumers and opcode `0x81` health-zero defeat
  mode dispatch;
  the 16-bit RNG transition; replay decode and per-frame input streams; and all
  callback indices reachable on the three acceptance routes.
- **Inferred**: domain names for several residual SHT fields and some ECL
  opcodes.
- **Unknown**: exact RNG consumption order across all subsystems, nonspell
  presentation names, and runtime parity of a future simulator. Spell ID/name
  and phase-local subroutine-component mapping is
  complete statically; Bomb geometry is executable but still needs full-frame
  differential validation.

Static analysis establishes formulas and state mutations. It does not by itself
establish a successful route; replay validation is required.

Opcode `0x91` is explicitly outside the planning-state boundary: it reapplies
saved ANM script IDs only in `enemy_manager_render`, including trail nodes, and
has no motion/collision consumer. The per-game visual validator may retain it,
but the deterministic search kernel must not branch or hash on it. By contrast,
boss identity (`0x53`) and defeat mode (`0x81`) stay in the kernel because they
change damage, health-zero cleanup, projectile/enemy removal, score, and phase
consequences.

Two additional per-enemy Bomb policies are solver state. Opcode `0xAD` can
pause the enemy's entire VM/motion/phase/damage block while the player Bomb or
global transition state is active; opcode `0xB7` can instead leave the enemy
updating but suppress its player-shot/hurtbox damage only during Bomb. A planner
that treats every Bomb as uninterrupted damage will predict wrong phase lengths
and may allocate resources to an infeasible route.

## Discrete-Time State

Use one engine update as one step, `dt = 1/60 s`. The minimum solver state is:

```text
S_t = (
  stage_time, phase_id, route_id, difficulty, rank, rng_state,
  player_position, player_mode, player_state, invulnerability,
  power, lives, bombs, bomb_gate_counter, predeath_counter,
  enemies[], bullets[], lasers[], items[], pending_events
)
```

The control at each frame is:

```text
u_t = (direction in {neutral, U, D, L, R, UL, UR, DL, DR},
       focus, shot, bomb)
```

Observed input bits are `shot=0x01`, `bomb=0x02`, `focus=0x04`, with direction
bits in `0x10..0x80`.

For team route ID 2, the observed nominal movement increments are:

| Mode | Cardinal | Each diagonal axis |
| --- | ---: | ---: |
| Sakuya / unfocused | 4.0 | 2.8284271 |
| Remilia / focused | 2.3 | 1.6263456 |

The engine further multiplies each axis by player scale fields and global time
scale before applying playfield clamps. Those multipliers belong in the state,
not in an assumed constant-speed approximation.

TH08 decodes directions in the exact priority `UL,DL,UR,DR,D,U,L,R,neutral`,
which also defines behavior for contradictory replay bits. While a Bomb is
active, effective focus ignores input bit `0x04` and instead uses
`bomb_callback_index & 1`. Callback indices 0/2 therefore force the primary
unfocused movement/SHT profile, while 1/3 force the secondary focused profile.
`scripts/movement_model.py` contains reusable movement/clamp geometry and
`scripts/th08_movement_model.py` supplies these TH08-specific input rules.
The generic primitive accepts an injected numeric-store policy. TH08 applies
binary32 rounding separately when it stores scaled velocity, time-scaled
delta, and position; accumulating Python doubles is not replay-equivalent.

Enemy movement is separated the same way. `scripts/pattern_ir.py` defines the
game-neutral `PolarVelocity`, `TimedDisplacement`, and easing family. The TH08
adapter in `scripts/th08_enemy_movement_model.py` implements opcode `0xB2`:
it consumes four 16-bit RNG outputs, chooses a uniform angle with probability
1/4 or a player-x-biased left/right cone with probability 3/4, uses the
shortest direction on a 384-unit periodic horizontal span, reflects motion away
from the top/bottom 48-unit margins, then lowers to constant polar velocity or
a timed displacement. Native easing codes 0/7 are linear, 1..3 are ease-in
powers 2..4, and 4..6 are ease-out powers 2..4. This is an enemy-motion event,
not a TH08-specific solver special case.

Timeline spawning also has a neutral event boundary.
`SetTimelineSpawnEnabled` means future timeline spawn records may or may not
create entities; it does not pause the timeline or preserve a suppressed record
for later. TH08 opcode `0xAF` stores the inverse boolean, lowered by
`scripts/th08_pattern_adapter.py`. This distinction is solver-critical because
suppressed records still advance the stage schedule and can change every later
enemy/RNG dependency.

Trail effects use the same state-slicing rule. The neutral
`HistoricalHitboxTrail` contains only historical positions that repeat an
entity hitbox; renderer-specific fading, strip geometry, and ANM state do not
enter it. TH08 opcode `0x9D` can express both domains, but every shipped record
sets its historical-collision limit to zero. Those records therefore retain a
validator-side visual trail and add no search state. A future game adapter, or
a modified TH08 ECL with a limit above one, emits the neutral collision event
instead of silently discarding the trail.

Opcode `0x9B` lowers independently to `FixedSpellRewardPolicy`: working bonus
99,999,990, no per-frame decay, and capture-result field 700. This belongs in a
score-aware objective but does not change survival geometry. Opcodes `0x9F`
(four render layers), `0xB6` (secondary-ANM shared anchor), and `0xB3..0xB5`
(stage-background ANM sequence) have only presentation consumers and are
excluded from the deterministic search snapshot.

Route 2 uses two distinct focus fields. The focus-logic byte at player `+0x03`
changes on the input edge and immediately selects focused movement and the
secondary SHT. The character-display byte at `+0x05` changes only after the
transition counter reaches 7; it must not drive solver physics.

Initialization uses a third, transient value: focus-logic byte `2`. All four
option callbacks begin in state 1. On the first movement callback, effective
focus normalizes the byte to 0/1; an unfocused first callback releases the
initial option records to state 3. A simulator initialized directly to a
stable boolean state misses this boundary.

Normal stage initialization starts player state 1 at timer 120. Its first
priority-9 callback immediately crosses the `>=30` spawn threshold, installs
state 3 timer 240, decrements it to 239, and permits movement in that same
callback. With run-state flag `0x4000`, initialization instead starts at 10;
the first 20 callbacks do not move, and the next callback transitions using
the retained timer 30, decrements it to 29, then moves.

On a focus edge, four option records are created before movement, but their
shared callback runs after player movement and captures that post-movement
position. Their fixed target offsets are `(-30,-16)`, `(-10,-32)`,
`(10,-32)`, and `(30,-16)`. Each option is placed on a radius-8 orbit with
initial angles `0,pi,0,pi`. Once its integer timer is greater than 12, the
per-update angle deltas are `+1.5,-2,+2,-1.5` degrees. On release, positions
freeze in exit state and clear after the timer is greater than 16. The exact
state machine and SHT source-index mapping are in
`scripts/th08_option_model.py`.

## Dynamics

The transition function follows the native stable callback list. Lower
priority runs first; equal priorities retain registration order. The observed
solver-critical chain is:

```text
priority 2   gameplay controller
priority 6   replay input publication (playback only)
priority 7   replay RNG synchronization (record/playback only)
priority 8   stage background
priority 9   player
priority 11  enemy manager
priority 12  spell-card manager
priority 13  callback 0x00427BF0 (domain role still unknown)
priority 14  item manager -> bullet buckets -> hostile bullets -> lasers
priority 17  replay input capture (record only)
priority 18  replay post-update (playback only)
```

Within priority 9 the observed order is player projectile-pool update,
deathbomb/death transition, respawn/auxiliary state, input/movement, animation,
active-shot update, shot cadence, and final counters. Within priority 11 the
stage timeline advances before the per-enemy ECL/motion/damage loop. Within
priority 14 the entire item pass precedes hostile bullets and lasers.

These static orders imply, but runtime differential traces must still confirm,
that playback input affects player movement in the same update; item collection
uses the post-movement player position; active bullets emitted by the enemy VM
are eligible for the later bullet pass; and items created by bullet cancellation
wait until the following item pass. Priority 9 also handles deathbomb state
before a priority-14 hostile bullet/laser hit can create it, so that hit first
reaches deathbomb processing on the following update.

The reusable scheduler and TH08 adapter live in `scripts/frame_schedule.py`
and `scripts/th08_update_order.py`. Presentation callbacks not needed for
physics are intentionally not claimed as a complete native callback inventory.

Enemy/ECL execution expands procedural commands, so each bullet must retain its
spawn mode, transform program, timers, and active flags. Lasers require their
origin, angle, tail/head distances, maximum length, width, warmup/active/fade
timers, collision window, and runtime phase. A snapshot-only velocity model is
insufficient.

## Collision And Graze Constraints

For each frame, let `P_t` be the player collision shape and `H_i(t)` each active
hostile bullet/laser collision shape after that frame's engine updates.

```text
alive constraint: P_t intersection H_i(t) is empty for every hostile i
```

The observed shared collision routine performs a rotated-object versus player
axis-aligned-box test. Its graze branch expands the incoming shape's AABB by
48 units. The simulator must reproduce the exact comparisons and timing before
using a faster geometric approximation for search.

A normal Bomb is feasible when input bit `0x02` is set, stock is nonzero, the
shared gate counter and lockout permit it, no Bomb is active, and the global
state does not prohibit it. It costs one stock. A hit installs a separate
predeath countdown:

```text
stock == 0: 2
stock > 0: min(6 * stock + (meter_left >= meter_right ? 7 : 0), 15)
spell state active: double the result, capped at 30
stage-load index in {0,4,5}: floor(result * 9 / 5)
```

The Bomb-input branch is evaluated before decrementing this counter, so a
statically observed value of one still accepts input. The registered order
places player deathbomb processing at priority 9 and hostile bullet/laser
collision at priority 14. A hit established there therefore first reaches the
deathbomb transition on the following update; runtime traces must still verify
the boundary frame against the game.

For route ID 2, a normal Bomb selects Sakuya while unfocused and Remilia while
focused; both last 290 frames. A deathbomb invokes the partner's Last Spell:
focused Remilia selects Sakuya's 350-frame Last Spell, while unfocused Sakuya
selects Remilia's 320-frame Last Spell. It costs `min(stock, 2)`. The special
200-frame Dissolve Spell path is forced and does not consume stock. SHT header
`+0x08` is a shared Bomb-gate reset value (10 for both route-2 characters),
not the predeath countdown formula.

Bomb selection occurs before the current frame's focus input is processed, so
it uses the prior focus-logic byte. The accepted callback runs at local timer
0 before movement and its timer advances in the same update. Sakuya normal and
Last Spell set both movement axes to 0.5 for their lifetime. Remilia normal
sets them to 0 for local frames 0..59 and to 2.0 when the integer timer first
reaches 60; Remilia Last Spell uses 0 then 3.0 at the same boundary. Dissolve
sets both axes to 0. On `timer >= duration`, common teardown resets both axes
to 1 before that frame's movement.

These boundaries are executable in `scripts/th08_route2_player_runtime.py`.
Accepted Bomb starts are exogenous events at the replay-projection boundary:
the replay input word contains the button but does not say whether a hit made
it a Last Spell or whether item collection supplied stock.

Bomb collision is represented by the same observed 64-byte region primitive
used by normal player attacks. Separate 192-entry pools hold enemy-damage and
hostile-projectile-cancel shapes. Circles and axis/rotated rectangles, size
deltas, remaining frames, tick intervals, accumulated damage, and damage caps
are implemented in `scripts/th08_attack_model.py`. Sakuya's per-knife regions
and exact normal/Last-Spell damage values are modeled. Remilia's normal Bomb
selects `ply02as.sht` level 6 from Bomb-local frame 60; her Last Spell selects
level 7. `scripts/th08_player_shot_model.py` executes their cadence, option or
player spawn origin, velocity, AABB collision, piercing, and damage rules.

The Remilia records all have base damage 45, type 6, speed 20, and a 32 x 16
hitbox. Because they are emitted while a Bomb is active, the ordinary-shot
consumer contributes `max(floor(45 / 5), 1) = 9` per overlapping shot and caps
the ordinary-shot subtotal at 50 per enemy check. Type 6 remains active after a
hit. Level 6 has 16 cardinal records sourced from the four options. Level 7
adds two player-sourced diagonals for 18 records total. Emission still requires
shot input and the independent integer cadence timer, so Bomb-local time alone
does not determine the exact firing frame.

## Items And Scoring

Each item is a moving stateful object, not a static waypoint. The observed pool
contains 2,096 records of `0x2E4` bytes. Standard free motion clamps vertical
velocity to at least -2.2, advances with the character's fall scale, then adds
`0.03 * fall_scale * time_scale` up to 3.0. Standard homing points directly at
the player with SHT speed 10. A dying/spawning player releases a homing item to
free motion with vertical velocity -0.7.

Homing activates above the SHT `point_value_line_y=128` when the player is
focused, at full power, or the stage-load index is 1/6; an already homing item
continues while player state permits. Route 2 uses collection width 24, and the
observed inclusive AABB test therefore collects when both center-coordinate
differences are at most 24. Sakuya and Remilia use free-fall scales 0.65 and
0.9 respectively.

The remaining motion states are also executable. State 2 linearly interpolates
from its spawn point to an RNG-selected target for 60 timer frames. States 3
and 5 consume two RNG samples for an upward scatter velocity and add
`0.05*time_scale` to vertical speed each frame. State 3 uses the generic fall
pass but blocks collection until it changes to homing; state 5 performs an
initial movement pass, blocks collection while `vy<=0`, and performs a second
generic movement pass on its transition frame.

Numeric item types 0..8 now have direct resource mutations in
`scripts/th08_item_model.py`: small/large power, point value, Bomb capped at 8,
full power, life with Bomb fallback at the life cap, scaled score, time-unit
and point-value growth, and the one-tenth overflow-power value. Point-item
extend thresholds are `(100,250,500,800,1100,9999,...)` below difficulty index
4 and `(200,666,9999,99999)` at index 4 or above. Conventional display names
for some types remain inferred; the numeric effects are observed.

Use a lexicographic objective until all scoring fields are named:

```text
1. minimize deaths / reject infeasible survival
2. minimize bombs consumed
3. maximize collected high-value items
4. maximize graze
5. maximize damage uptime / minimize phase duration
6. minimize control complexity and narrow timing margins
```

This prevents score gains from silently trading away the primary survival
requirement. Weighted objectives can be added after their units and replay
measurements are stable.

## Search Architecture

1. Deterministic emulator: execute timeline, ECL, bullets, lasers, player, and
   items from pinned inputs and RNG state.
2. Game-state recorder: capture authoritative per-frame state from the running
   game for differential tests.
3. Corridor planner: propagate a coarse reachable set over 80 frames, retain
   connected safe-region choices, and emit a gate waypoint plus deadline.
4. Local planner: use short-horizon safe-set search or model-predictive control
   over direction/focus actions while preserving gate reachability as a
   lexicographic constraint.
5. Resource planner: dynamic programming or graph search across phase boundaries
   for bomb/life allocation and collection detours.
6. Route compressor: convert the frame trace to held-input intervals, retaining
   enough margin for deterministic replay.

The two-level search avoids branching on every bomb/resource decision at every
movement frame. Candidate paths still require exact full-stage replay before
acceptance.

## Counterexample-Guided Agent Refinement

Every live miss is a model/planner counterexample. Preserve a bounded pre/post
window of native player, Bullet, Laser, Item, resource, RNG, input, frame, and
read/action-lag state. Classify it as world-model discrepancy, sensing/latency,
planner/corridor choice, objective/resource error, or control/runtime error.
Reduce reproducible failures into fixtures and regression tests before changing
heuristics. The durable ledger is `notes/COUNTEREXAMPLES.md`.

The runtime test boundary is prewarmed and manually armed. The operator selects
difficulty and team, then presses F8 on the final Sakuya/Remilia confirmation
page. `scripts/th08_agent_hotkey.py` verifies executable identity, runtime
patch, `g_difficulty_index` in `{3,4}`, route ID 2, and foreground ownership;
it starts the waiting agent before sending the final confirm. F9 creates a
safe-stop request. The agent releases all injected keys, pauses gameplay, and
emits a bounded first-hit report rather than leaving an uncontrolled process
running.

## Cross-Game Boundary

The reusable solver must consume a game-neutral frame/event model rather than
calling TH08 opcode handlers directly. The current separation is:

1. Game adapter: archive/script decoder, callback ordering, RNG, character
   profile, and native field mapping.
2. Pattern IR: scheduled emitters, polar velocity, timed displacement and
   easing, timeline spawn gates, projectile/laser transforms, phase exits, and
   spawn dependencies expressed without native addresses.
3. Simulation kernel: ordered events, geometry, collision/graze, resources,
   and deterministic snapshots.
4. Search layer: survival constraints and configurable Bomb/item/graze/damage
   objectives over only the kernel interface.
5. Validator: per-game recorder and replay encoder comparing authoritative
   runtime state with the neutral snapshots.

For another Touhou title, layers 2 through 4 should remain reusable; the main
new work should be its adapter and validator. TH08 remains the first complete
acceptance target, so abstractions are extracted only when backed by a current
runtime requirement.

## Pinned Script Targets

The static phase graph is no longer an open prerequisite. Generated manifests
pin route ID 2, difficulty, SHT resources, stage ECL sequence, and every
reachable opcode `0x7A` occurrence:

| Profile | Reachable spell IDs |
| --- | ---: |
| `sakuya_remilia_lunatic_final_a` | 33 |
| `sakuya_remilia_lunatic_final_b` | 37 |
| `sakuya_remilia_extra` | 14 |

Each reachable spell occurrence also contains its phase-local component
subroutines, internal edges, phase-transition exits, and feature counts for
bullet emissions, transforms, lasers, and callbacks. The component traversal
includes calls, child enemies, interrupt handlers, and auxiliary VMs, but stops
at enemy-end/health/timeout transitions. The JSON manifests under
`artifacts/route_manifests/` are machine inputs for the incremental simulator.
`scripts/test_th08_routes.py` prevents accidental phase loss or cross-phase
component merging as ECL semantics are refined.

## Replay Baseline

The local `th8_06.rpy` provides an observed route-2 Extra input baseline. Its
stage-8 record pins seed `0xC0A4`, 66,386 input frames, and canonical input
SHA-256
`4a33179986ad9ef203deae92f0f94d25d2f94b59de19e4a1507fdf11c867ffba`.
Bomb rising edges occur at frames 13,041, 27,305, 45,553, 59,744, and 64,086.
The compact 5,302-run trace is generated under
`artifacts/replay_reports/traces/`.

The input-only route-2 projection under
`artifacts/replay_reports/th8_06_stage8_player_projection.json` executes all
66,386 frames through the observed replay-publication and player schedule
events, with binary32 position writes and 127 checkpoints. Its
position hash is
`9bf4956d1ccd1143596522a5a4d0819a724eeda71ce44fccb3ff55f85dbc2957`.
All five Bomb press frames remain explicitly unresolved and are treated as not
accepted in that projection; therefore this artifact is a player-kernel test
vector, not the authoritative Extra route.

`scripts/deterministic_sim.py` is the game-neutral frame executor. It selects
reconstructed events from a full engine schedule, rejects every selected event
that lacks a handler, and preserves native priority/registration order.
`scripts/state_trace.py` projects explicit state fields at each event boundary,
including raw binary32/binary64 bit encodings, and reports the first differing
record and field. `scripts/th08_simulator.py` is the TH08 adapter. Its current
integrated slice includes replay input, route-2 player movement/Bomb state,
stage timelines, the stable item pool, base straight hostile bullets, and
laser/player contact. It is still deliberately partial: the enemy ECL VM,
bullet transform VM, item drops/cancellation, death/respawn, and complete
cross-manager collision order remain required for a stage simulator.

The eventual controller is not screenshot-driven. `scripts/runtime_agent.py`
defines a game-neutral one-frame-ahead protocol; the TH08 bridge validates the
executable identity, observes the native frame counter and state through
read-only process memory, sends an input only while explicitly armed and while
the game owns the foreground, then checks the following frame. Missing frames,
identity/state divergence, or focus loss abort control instead of guessing.

The online implementation is `scripts/th08_live_dodge_agent.py`. It reads the
1536-slot hostile-bullet pool, 256-slot laser pool, and 2096-slot item manager.
A vectorized 10-frame MPC follows asynchronous waypoints from a game-neutral
80-frame time-expanded corridor planner. Physical input remains `SendInput`;
normal Bomb is disabled by default and native phase-2 deathbomb remains the
bounded failure fallback.

Runtime timing is part of the plant state. Player position is observed before
the large pool read; projectile memory belongs to a later sensor epoch; a
decision then spends another two to four game frames reading/planning before
injected input affects movement. The local planner evaluates the previous
input across an explicit three-frame uncontrollable prefix, offsets projectile
prediction by the measured sensor skew, and advances corridor deadlines to the
same actuation epoch. Trial reports retain both lags, pipeline clearance, and
the nearest native hit slot. This timing contract is game-neutral even though
TH08 supplies the counters and movement adapter.

This proves the physical control path but is not acceptance. The first two
prewarmed Lunatic trials reached frames 3259 and 4969 before their first hit,
with zero stale corridor records and substantially reduced edge occupancy.
Remaining work includes recurrence-testing the delay-aware controller,
incremental active-slot reads/native spatial buckets, exact transform motion,
stage-level Bomb/resource optimization, and an executor-produced trajectory
tube.

This is a candidate/baseline control sequence, not yet an accepted clear. The
replay file does not by itself prove its terminal result or establish
game-vs-simulator state parity. No local route-2 Lunatic replay baseline is
currently present.

## Verification Gates

1. File parsers reproduce all decoded ECL/SHT corpus boundaries exactly.
2. Unit tests cover every recovered emission mode and transform kind.
3. Differential traces match game bullet/laser/player positions frame by frame.
4. Collision, graze, item, damage, and bomb events match recorded frames.
5. Lunatic and Extra routes replay on route ID 2 from pinned initial/RNG state.
6. Robustness runs perturb input transitions by one frame and report minimum
   collision margin instead of presenting a brittle trace as generally safe.

## Immediate Unknowns Blocking Solver Fidelity

- Ten unused ECL opcode slots retain conservative names. No opcode present in
  the shipped 24-file corpus remains unknown.
- Runtime differential traces for the recovered update order and transforms;
  presentation-only and dynamically inserted callback nodes remain outside the
  solver-critical schedule.
- Exact input/option/collision runtime parity against authoritative traces; the
  static route-2 option and callback orders are now executable.
- Ancillary UI/statistic meanings for several item-run fields; their direct
  numeric mutations are modeled by stable structure offsets.
- RNG consumption order across callbacks and all stage-transition seed writes.
- Runtime order/naming for nonspells and game-vs-simulator differential traces.
