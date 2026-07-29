# TH08 Action-Conditioned Player/Enemy Mode Semantics

Date: 2026-07-30  
Roadmap item: `SEM-MODE` / Phase 1C  
Current authority: native semantics revalidated; decoder retention, pure
projection, and diagnostic sensing implemented; live hazard authority not
promoted

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

The current broad `observe_state` read is not a frame-bracketed mode/enemy
transaction. These fields are therefore diagnostic observations, not yet an
exact live policy root. The promoted capture must either bracket player mode
and enemy-prefix reads by a stable native update identity or include every
one-callback ordering branch.

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
   The pure projection is shadow-only. A native capture where player
   `+3/+5/+8`, active input, or enemy bit `0x800` disagrees with the recurrence
   falsifies it.
5. **Can the result be consumed before issue time?** Not yet. The diagnostic
   sensor is unbracketed and the live hazard recurrence lacks the mode key.
   Live consumption remains forbidden until exact-version publication and
   timing gates pass.

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

## Remaining Implementation And Promotion Plan

1. **SEM-MODE-B — atomic observation:** add a bounded player-mode/enemy-prefix
   capture bracket. Retain a deterministic fixture containing raw player
   mode, active input, raw enemy flags, and body identities across an entire
   transition.
2. **SEM-MODE-C — causal hazard recurrence:** carry the mode key through
   pickup/cadence histories, project per-frame enemy contact body sets after
   the player update, and merge only observation-compatible branches.
3. **SEM-MODE-D — damage separation:** apply the same projected gate to the
   shadow damage objective without letting damage affect hard viability.
   Keep unfocused combat selection disabled.
4. **SEM-MODE-E — differential gates:** compare independent scalar, optimized
   Python, and any native kernel for every action/history, no-write/pending
   edge, and retained `10065 -> 10075` capsule. Publish viable-state and
   safe-action-mask diffs.
5. **SEM-MODE-F — physical gate:** use an original-game whole-stage script,
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
