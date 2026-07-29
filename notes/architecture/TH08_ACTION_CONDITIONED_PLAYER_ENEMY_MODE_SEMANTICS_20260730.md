# TH08 Action-Conditioned Player/Enemy Mode Semantics

Date: 2026-07-30  
Roadmap item: `SEM-MODE` / Phase 1C  
Current authority: native semantics revalidated; decoder retention, pure
projection, frame-bracketed diagnostic capture, and compact reporting
implemented; an exact offline pickup/cadence transition primitive is
implemented; live hazard authority not promoted

## Decision

Route-2 focus is not only a movement-speed selector. The active input changes
an immediate focus byte, then changes the Sakuya/Remilia secondary-character
byte after a native seven-update delay. For active enemies marked by flag
`0x100`, the enemy manager mirrors that delayed byte into enemy flag `0x800`.
The later enemy-manager gate uses `0x800` to block both lethal body contact and
player-shot damage.

Therefore the solver must carry the focus transition state through each
causal action/history. It must not decode the current enemy body set once and
treat that set as action-independent over the planning horizon.

The first implementation checkpoint is deliberately one-way safe:

- first-64 contiguous sensing retains active geometry even while flags
  `0x10`, `0x20`, or `0x800` block current contact;
- a pure TH08 projection computes current/future contact and player-shot
  damage eligibility separately;
- the native player fields are exposed in diagnostic state and trace output;
- no live consumer may use the new projection to remove a latent body yet.

Until the complete causal recurrence, observation transaction, versioning,
and differential gates pass, retained latent geometry remains a conservative
union and unfocused combat promotion remains disabled.

## Revalidated Shipped-Program Evidence

The following conclusions are **observed** from the connected shipped TH08
IDA database and were revalidated against instructions, callers, and update
order on 2026-07-30:

- `player_update_input_movement` at `0x0044AEC0` runs at priority 9.
- With no Bomb callback active, effective focus is input bit `0x04`. If a Bomb
  callback is active, the callback index parity supplies effective focus.
  Physical policy remains hard no-Bomb, but the recovered primitive retains
  the full distinction.
- Player byte `+0x03` changes focus logic immediately. Player dword `+0x08`
  is the transition counter.
- On focus entry, `0x0044B1D9` writes player byte `+0x05 = 1` only after the
  counter reaches 7.
- On focus release, `0x0044B42C` writes player byte `+0x05 = 0` only after the
  counter reaches 7.
- The helper at `0x0040BC40` returns player byte `+0x05`.
- The enemy helper at `0x0042C420` is called only for active enemies carrying
  flag `0x100`; `0x0042C568` mirrors `(player[+5] & 1) << 11` into enemy flag
  `0x800`.
- `enemy_manager_update` runs at priority 11, after the player callback. Its
  outer contact/damage gate rejects flags `0x10`, `0x20`, or `0x800`.
- Contact eligibility is then controlled by enemy flag `0x04` and reaches the
  body collision call at `0x0042CF7A`.
- Player-shot damage eligibility is separately controlled by enemy flag
  `0x40`; its damage block begins at `0x0042D08B`.

The following IDA database changes record those strong conclusions:

- `0x0040BC40` renamed to `player_secondary_character_active`;
- `0x0042C420` renamed to `enemy_update_secondary_character_gate`;
- comments added at `0x0044B1D9`, `0x0044B42C`, `0x0042C568`, and
  `0x0042CF47`.

The nouns are intentionally mechanical. `secondary_character` applies across
routes; “Remilia” is route-2-specific context.

The connected IDB is not a byte-identical shipped executable image. This was
revalidated rather than hidden behind the inherited database metadata:

- **Observed:** the IDB input SHA-256 is
  `ec101fcff80b77e717d43b54e326375487af19661bb7c8d11a19ee5e0fbf928b`;
  the shipped disk image used by the launcher hashes to
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`.
- **Observed:** replacing only shipped file offset `0x4C4FA`, corresponding
  to VA `0x0044D0FA`, from `0xFF` to `0x00` reproduces the IDB input hash
  exactly. This changes `push -1` to research `push 0` before
  `add_player_lives`, preserving the miss/respawn path without decrementing
  lives.
- **Observed:** the critical SEM-MODE byte ranges beginning at
  `0x0044B1C0`, `0x0044B410`, `0x0042C960`, and `0x0042CF30` match the
  shipped disk image exactly.
- **IDA change:** the comment at instruction `0x0044D0F9` now records both
  hashes, the single-byte proof, the patch purpose, and an explicit warning
  never to infer shipped life behavior from this byte.

Thus the connected database remains valid static evidence for the rechecked
SEM-MODE ranges, while the no-life-decrement byte is research instrumentation
and not shipped-program semantics.

## Retained Runtime Witness

The following is **observed** in the retained Stage-5 runtime trace summarized
by F-011 in
`../review/TH08_NATIVE_TO_SOLVER_READ_ONLY_AUDIT_20260729.md`:

- the run remains focused through frame 10063;
- frame 10065 first selects an unfocused action;
- synchronized issue-prefix captures at frames 10065, 10068, 10071, and 10073
  contain no currently enabled ordinary bodies;
- at frame 10075, slots 0 through 15 appear together with flags
  `0x0100114D`: active, mode-sensitive `0x100`, contact `0x04`, and damage
  `0x40` are set while blocking bit `0x800` is clear;
- the transition caused no hit at that point. It proves a model omission, not
  a causal death.

The approximately ten-manager-frame observed interval is consistent with the
seven player callbacks plus controller sampling cadence. Static reasoning
alone does not turn that consistency into exact per-manager-frame runtime
proof.

## Formal Problem Contract

### Physical objective

Maintain hard no-hit/no-Bomb survival while controlling Sakuya/Remilia.
Enemy contact is a hard safety constraint. Player-shot damage, collection,
Power, score, and positioning are objectives only inside the viable set.

### State and observations

The mode-relevant native player state is:

```text
m = (focus_logic_byte, secondary_character_active, transition_counter)
```

The enemy observation retains position, body half-extents, motion evidence,
identity, and the complete raw flags word. Mode projection never destroys the
raw observation.

The new runtime diagnostic fields are:

- `player.focus_logic` from `ADDR_PLAYER + 0x03`;
- `player.secondary_character_active` from `ADDR_PLAYER + 0x05`;
- `player.focus_transition_counter` from `ADDR_PLAYER + 0x08`.

The broad `observe_state` read remains diagnostic only. `SEM-MODE-B` adds a
separate bounded transaction around the existing first-64 enemy-prefix read:
active input, player `+0..+11`, Bomb active/index, stable manager frame, and
the same player/input/Bomb fields are read in that order. An accepted
transaction additionally requires every retained active bit-`0x100` body to
mirror the delayed secondary-character byte in bit `0x800`. Two exhausted
attempts are retained as an explicit unstable observation; they never
fail-close the stage.

This bracket establishes coherence only for active, finite,
nonnegative-geometry bodies retained in the first 64 native slots. It does
not prove absent or invalid-geometry slots, the remaining native pool, or
future action-conditioned mode histories.

### Actions and issue semantics

The action is the complete physical input mask actually active at the player
callback. Desired/last-issued input is not active input. Pickup delay,
pending-command support, and no-write semantics remain those of
`AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`.

A no-write action retains the current complete mask and does not sample a new
pickup delay. A desired focus edge influences the mode recurrence only on the
history branches where that input has become native active input. Bomb bit
`0x02` is forbidden.

### Native transition

For one actual player update and effective-focus action `a`, the recovered
route-2 mode recurrence is:

```text
if a == focused:
    counter' = counter + 1  if focus_logic_byte == 1  else 0
    secondary' = true       if counter' >= 7          else secondary
    focus_logic_byte' = 1
else:
    counter' = 0            if focus_logic_byte != 0  else counter + 1
    secondary' = false      if counter' >= 7          else secondary
    focus_logic_byte' = 0
```

After that priority-9 transition, the same update's priority-11 enemy sync is:

```text
if enemy.active and enemy.flags & 0x100:
    enemy.flags[0x800] = secondary'
```

The later flag eligibility is:

```text
manager_gate = active and not (flags & 0x830)
contact_eligible = manager_gate and (flags & 0x04)
player_shot_damage_eligible = manager_gate and (flags & 0x40)
```

Contact and damage are deliberately separate booleans. Enemy geometry and
raw flags remain separate from both.

The enemy helper executes before that enemy's ECL and later contact/damage
gate. Therefore a contact-gate projection may accept a caller-supplied
per-frame body/flag schedule only if the schedule represents the exact
mode-independent flags and body identity at that later gate epoch. The mode
projection overwrites only bit `0x800` for active bit-`0x100` bodies; it does
not predict births, ECL writes, motion, transforms, or the other flag bits.

### Uncertainty and branch merging

Nature branches over the already-declared actuator pickup support, recursive
controller cadence, and any observation transaction ambiguity. The
controller may not maximize a hidden pickup/mode branch independently.

For enemy-mode evolution, the exact control-equivalence key currently used is
the full tuple `(focus_logic_byte, secondary_character_active,
transition_counter)`. The native initializer value 2 cannot be merged with
steady focused value 1. Histories with different hidden counters cannot merge
merely because current focus and secondary-character bytes match.

Options, their positions, and option timers may be omitted from this
mode-only key because they do not feed enemy bit `0x800`. They remain required
for shot geometry/damage objectives elsewhere.

Player mode advances on actual priority-9 player updates. Manager frame is
not substituted as a universal clock: post-spell/dialogue histories can
freeze `enemy_manager_frame` while held input continues moving the player.
Every recurrence consumer must carry a verified physical update schedule or
remain `UNKNOWN` across that boundary.

### Horizon, resources, and deadline

The horizon must cover the complete seven-update transition on every cadence
and pickup branch. The mode state is part of the immutable problem version
and continuation key. Power and damage are not allowed to relax survival.

The issue thread consumes only an exact-version published result. A missing,
stale, late, or unbracketed mode root falls back to the conservative latent
body union plus the existing fresh local hard certificate. It must not start
cold expansion or remove a body on a guessed mode history.

## Required Model Questions

1. **Which physical histories map to one model state?** Histories merge only
   when all observations available at the decision and the complete
   mode-control key agree. Different pickup support or hidden transition
   counters remain distinct until their observations and future transitions
   are control-equivalent.
2. **Are all uncertainty branches causal?** The target recurrence applies
   focus only after native pickup and applies enemy sync after the same
   branch's player update. It never selects mode separately for each hidden
   enemy outcome.
3. **Would an exact finite solve answer the physical question?** It would
   answer the declared flag-gate question if callback order, observation
   bracket, and retained geometry/motion are exact. It would not by itself
   prove full physical survival because geometry, bullet lifecycle, source,
   and scheduler counterexamples remain in later roadmap phases.
4. **What bounds the approximation, and what falsifies it?** The present
   decoder change is conservative because it retains extra latent geometry.
   The pure projection is shadow-only. A coherent native capture where player
   `+3/+5/+8`, active input, or an observed bit-`0x100` enemy's `0x800` state
   disagrees with the recurrence falsifies it. Persistent incoherence is an
   unresolved observation failure, not evidence for either mode.
5. **Can the result be consumed before issue time?** Not yet. The bracketed
   capture has diagnostic authority only, its extra reads/retries may perturb
   cadence, and the live hazard recurrence lacks the mode key. Live
   consumption remains forbidden until causal recurrence, exact-version
   publication, differential, timing, and physical gates pass.

## Implemented Checkpoint: SEM-MODE-A

The following changes are implemented and tested offline:

- `scripts/th08_live/enemy_sensor.py` now makes
  `include_contact_disabled=True` mean what its name says: all active,
  finite, nonnegative-size geometry survives decoding even when flags
  `0x10`, `0x20`, or `0x800` block current contact. The strict current-contact
  decoder is unchanged.
- `scripts/th08_enemy_mode.py` implements the pure bit-`0x100` sync,
  independent contact/damage eligibility, and the exact mode state key.
- `scripts/th08_runtime/sensing.py` exposes native player `+3/+5/+8`.
- decision traces retain those three diagnostic fields.
- `tests/test_th08_enemy_mode.py` exhaustively compares every 9-step binary
  focus history from three adversarial initial states against an independent
  scalar recurrence, including the native initializer sentinel.
- CE-0176 tests retain a bit-`0x800` body and reproduce the
  `10065 -> 10075` seven-update gate opening.

This closes the “decoder permanently loses latent `0x800` geometry” part of
CE-0176. It does not close the action-conditioned live recurrence or the
physical exit gate.

## Implemented Checkpoint: SEM-MODE-B Preflight

The whole-stage diagnostic path is now implemented and dual-platform gated:

- `scripts/th08_live/enemy_mode_capture.py` brackets the existing first-64
  prefix capture with active input, player mode, and Bomb state. It retries
  crossed player/enemy updates at most twice and explicitly reports
  `enemy_frame_unstable`, `player_or_input_changed`, or
  `enemy_mode_sync_mismatch` instead of terminating gameplay.
- accepted records retain raw pointer/flags pairs for every observed
  bit-`0x100` body, both player observations, frame bracket, attempts, read
  time, and an explicit `action_authority=false` marker;
- `--trace-enemy-mode-transitions` is default-off and threads through the
  original-game practice and full-route supervisors. When enabled it is
  active from stage/route entry, never at an operator-selected spell;
- `scripts/analysis/th08_enemy_mode_capture_report.py` streams raw JSONL,
  preserves source SHA-256, coherence/status/timing counts, adjacent
  secondary-character transitions and before/after body sets, and fails its
  integrity gate if mode records claim action authority;
- deterministic tests cover a coherent raw `0x0100114D` body, crossed
  player/enemy updates, retry exhaustion, Bomb callback focus override, and a
  synthetic `10065 -> 10075` report transition;
- Linux discovery passes 1,162 tests in 12.964 seconds. The exact Windows UNC
  suite passes 1,162 tests in 30.139 seconds with three existing skips.

This is implementation evidence, not shipped-runtime occurrence or survival
evidence. The trace is consumed by no mode-conditioned planner branch, but
its read/retry cost can perturb controller cadence. The physical Stage-5
observer gate therefore remains mandatory.

## Retained Checkpoint: SEM-MODE-B Physical Observation

Original-game run
`lunatic_route2_stage5_unattended_20260730_041408` physically exercises code
checkpoint `60ae5b9` across complete Lunatic Sakuya/Remilia Stage 5:

- **Observed:** the supervisor selected Stage 5, retained frames `1..42463`
  and 11,879 decisions, reached `route_complete`, verified hard no-Bomb, and
  continued through all ten native hit edges instead of fail-closing.
- **Observed:** 11,763 captures are coherent (`99.023%`). The 116 excluded
  captures are 70 `enemy_mode_sync_mismatch`, 43
  `player_or_input_changed`, and 3 `enemy_frame_unstable`; 571 decisions
  required the bounded second attempt.
- **Observed:** the compact report retains 1,455 focus-input edges, 299
  adjacent coherent secondary-character transitions, and 308 unique
  bit-`0x100` pointer/raw-flags pairs. Frames `394 -> 397` change 13 stable
  bodies from `0x11003B49` to `0x11003349`, and frames `444 -> 447` change 12
  stable bodies in the reverse direction. The changed flag bit is exactly
  `0x800`, matching the revalidated native synchronization rule.
- **Observed:** capture read time is 2.238 ms mean, 4.599 ms p95, and
  10.965 ms maximum. Extra reads and retries are therefore a real cadence
  perturbation, not a side-effect-free observer.
- **Observed:** ten root-only scale observations use the explicit
  `diagnostic_constant_current_root_unknown_direction` proxy. The report
  passes its integrity checks and marks `action_authority=false`,
  `hard_authority=false`, and `physical_survival_authority=false`.
- **Observed:** the supervisor selected no-save and no compatible new native
  replay was found. The ignored 482,944,752-byte JSONL remains local with
  SHA-256
  `773cbdb322dc5e15f80da4800ce82bcd0f41c1e6f82826812087edc9a328dca9`;
  the compact mode report hashes to
  `545677cead65e312942408cbaa977694be6416b7afbaea663802462c0775dfd9`.
  Cleanup released keys and left no gameplay/control process.
- **Inferred:** the stable player `+5` state and observed enemy `0x800` state
  are synchronized at the captured physical instant. The transaction does
  not identify that instant as an unconditional post-player callback root,
  nor does it prove how a pending desired input changes mode before the next
  observation.

This closes the SEM-MODE-B shipped-runtime occurrence gate. It does not close
SEM-MODE-C, validate the ten-hit survival policy, prove observer-off timing,
or promote unfocused combat. The canonical first hit is nonspell frame 3,519
after the modeled committed prefix already has clearance `-2.766`; all ten
hits remain routed through CE-0192.

## Implemented Checkpoint: SEM-MODE-C Offline Transition Primitive

`scripts/th08_enemy_mode.py` now composes the existing independent local
pipeline enumeration with the exact TH08 player/enemy mode transition:

1. each physical step chooses only the native active complete mask from that
   branch's old-pending/new-pickup history;
2. priority 9 advances player `+3/+5/+8`;
3. priority 11 overwrites bit `0x800` on each supplied active bit-`0x100`
   body; and
4. contact and player-shot-damage body identity sets are emitted separately.

The decision-transition form samples every declared next-decision cadence,
returns an exact successor active/held/pending root, and can be called again
at the next observation. Selecting the already-held desired action is
no-write: it preserves the older pending command and decrements its remaining
support without sampling a new delay. Cadence is resampled on every recursive
call, not replaced by one root-only or maximum interval.

Successor branches merge only when all of the following agree:

- caller-supplied complete base observation, which must include physical
  time/position and immutable body/flag/geometry version;
- elapsed physical update count;
- native active complete action;
- held desired complete action; and
- exact mode tuple `(focus_logic_byte, secondary_character_active,
  transition_counter)`.

Exact hidden remaining delays are then unioned into one support. They are
never exposed to the controller key. A different hidden mode counter remains
a different observation class even when active and desired inputs agree.

The focused offline gate covers:

- all 9-step focus histories from three adversarial initial states against an
  independent scalar `+3/+5/+8` recurrence;
- pickup delays that change the `0x800` contact/damage opening frame;
- pending no-write preservation and hidden remaining-support merging;
- recursive cadence successors with a second no-write decision; and
- the retained CE-0176 `10065 -> 10075` seven-update release capsule.

Complete discovery passes 1,175 tests in 14.858 seconds on Linux and 30.329
seconds on Windows through the exact UNC loader; Windows retains the three
existing platform skips.

This is the exact stage-neutral SEM-MODE transition/observation primitive,
not an integrated physical-survival solve. It deliberately omits player
geometry, enemy births/ECL/motion, recursive hazard-version production,
bullet/laser collision, scheduler freeze resolution, and exact-version
publication. The existing live viability/local-certificate consumers are
unchanged. Damage-body identities are diagnostic output only and do not
affect hard viability or unfocused combat selection.

## Retained Physical Post-Hoc Recurrence Audit

`scripts/analysis/th08_enemy_mode_recurrence_report.py` streams the retained
482,944,752-byte Stage-5 JSONL, hashes the complete source, and replays the
pure mode recurrence between adjacent coherent captures. It accepts an
interval only when:

- no non-decision trace record intervenes;
- stage, gameplay epoch, and player phase remain equal;
- the phase is not native-suppressed `1` or `2`, and no Bomb is active;
- effective focus is unchanged; and
- captured active, held desired, optional pending, newly dispatched target,
  and `input_current` focus bits agree with that effective value.

The result is **observed physical post-hoc recurrence evidence**:

- 9,839/9,839 eligible intervals reproduce native player
  `(focus_logic, secondary_character_active, transition_counter)` exactly;
- eligible manager deltas are 1 through 10;
- 1,869 adjacent coherent intervals are explicitly excluded, including 1,411
  focus changes, 171 same-phase native suppressions, 50 phase changes, and 20
  intervening non-decision boundaries; and
- no capture claims action authority or a role other than
  `diagnostic_shadow`.

Connected-IDA revalidation supplies the native phase boundary:
`player_update` at `0x0044C390` reaches the relevant update call at
`0x0044C4CB` only when phase byte `+0`, tested at `0x0044C4C6`, is neither
`1` nor `2`. A material comment at `0x0044C4C6` records the static gate and
the 9,839/9,839 retained result.

The same report preserves why this result cannot promote manager-frame clock
authority. Three auto-confirm intervals have manager deltas
`1800/1800/1801` but observed transition-counter increments `79/328/553`.
Those apparent mismatches disappear only by honoring the explicit
non-decision boundary; they strengthen CE-0120 rather than falsifying the
local recurrence.

The compact artifact is
`artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260730_041408.enemy_mode_recurrence_report.json`,
SHA-256
`da13e633dd11b65e837062b9286b736ee5dce618f57ba9bb1930d8c8c0315a66`.
Its source JSONL hashes to
`773cbdb322dc5e15f80da4800ce82bcd0f41c1e6f82826812087edc9a328dca9`.
The report declares manager-frame universal-clock, action, hard-survival, and
physical-survival authority false.

Six focused report tests, deterministic full-source regeneration, Ruff,
format, `py_compile`, and `git diff --check` pass. Complete discovery passes
1,181 tests in 14.647 seconds on Linux and 30.388 seconds through the exact
Windows UNC loader; Windows retains the three existing platform skips.

This closes a physical falsifier for the pure recurrence inside a strict
ordinary-update boundary. It does not provide the future body/flag/geometry
schedule required by the next decision, and therefore cannot yet be wired
into hard survival or unfocused-combat authority.

## Remaining Implementation And Promotion Plan

1. **SEM-MODE-C integration — exact hazard/version recurrence:** connect the
   offline primitive to a complete immutable body/flag/geometry schedule and
   exact physical-update clock without changing live action authority.
2. **SEM-MODE-D — damage separation:** apply the projected damage body set to
   shadow damage objective without letting damage affect hard viability.
   Keep unfocused combat selection disabled.
3. **SEM-MODE-E — differential gates:** compare independent scalar, optimized
   Python, and any native kernel for every action/history, no-write/pending
   edge, and retained `10065 -> 10075` capsule. Publish viable-state and
   safe-action-mask diffs.
4. **SEM-MODE-F — physical gate:** use an original-game whole-stage script,
   with the observer active from stage entry and no exact-spell/operator-time
   switch. Stage 5 is the first focused workload because it contains the
   retained witness. Do not fail-close or auto-stop mid-stage; preserve the
   complete trace, zero-Bomb evidence, and cleanup.

If a compatible native replay exists, replay the complete stage with the same
observer to reconstruct the transition at native update granularity and test
specific hypotheses. Replay analysis is a deterministic physical-runtime
oracle for the recorded history, not a replacement for a fresh physical
survival trial. If no replay exists, continue with the next original-game
stage run rather than introducing THPRAC.

Promotion requires the roadmap Phase-1C exit gate and then repeated clean
whole-stage physical evidence. The ultimate acceptance workloads remain
Lunatic Stages 3, 4A, 5, and Final B, followed by the full Power-0 no-miss,
no-Bomb route.
