# Route-2 Native Combat Root Projection Contract

Date: 2026-07-31

Taskbook cards: `COMBAT-FAST-01`, `COMBAT-KILL-01`

Status: offline exact-root/synthetic checkpoint; no physical predictive,
candidate-ranking, or live action authority

## Question

Can the existing full native snapshot retain enough player-shot and enemy
damage state to compare focused, unfocused, and dynamic-refocus branches from
one immutable root, while preserving hard survival and exposing every
unsupported damage case instead of silently scoring it?

The physical objective remains Sakuya/Remilia NMNB survival. Damage, early
enemy removal, resource gain, and phase shortening are secondary objectives
only among branches that remain survival-feasible. This checkpoint does not
change the live policy, actuator, cadence, issue path, or physical objective.

## Revalidated Native Evidence

The following are **observed** in the shipped TH08 instructions and connected
IDA database:

- `player_shot_initialize` at `0x0044FB70`,
  `player_update_shots` at `0x00451150`, and
  `player_compute_damage_to_enemy` at `0x00451670` agree on a 128-slot player
  shot pool at player `+0xBE838`, with stride `0x484`.
- The pool ends at player `+0xE2A38`, inside the existing
  `player_state_through_resource_transitions` full native-root component.
  Therefore no additional broad player-region capture is required.
- A shot slot carries position `+0x2A4`, collision size `+0x430`, velocity
  `+0x43C/+0x440`, speed `+0x44C`, angle `+0x450`, timer `+0x454`, signed
  damage/state/type `+0x460/+0x462/+0x464`, Focus-at-birth `+0x46C`, ANM
  index `+0x46E`, update callback `+0x474`, hit callback `+0x47C`, and SHT
  record pointer `+0x480`.
- The emission timer at player `+0xE2AC4` and damage-loop timer at
  `+0xE2AF4` are distinct. The latter controls whether the ordinary shot
  damage loop is due.
- `enemy_manager_update` at `0x0042C660` reads target position `+0x2D88`,
  primary hitbox `+0x2D70`, alternate hitbox `+0x2D7C`, HP/max HP
  `+0x2DFC/+0x2E00`, flags/flags2 `+0x3324/+0x3328`, published frame damage
  `+0x3354`, and main-VM identity/timer at `+0x7F8/+0x804`.
- `0x0042D0EE` enters the alternate collision pass only when the ordered
  alternate width is greater than positive zero. Positive or negative zero,
  negative values, and unordered NaN do not enter that pass.
- Ordinary eligibility remains `state != 0 && (state == 1 || type == 3)`.
  Types 4 and 5 depend on a still-unmodeled mode predicate, and any nonzero
  hit callback may veto or alter a geometric hit.
- The loop accumulates ordinary-shot damage in `[ebp-0x34]`. At
  `0x0045199F..0x004519BF`, `min([ebp-0x34], 50)` is added only to the
  caller-owned enemy `+0x2E10` hit-feedback accumulator. The uncapped
  `[ebp-0x34]` continues into the 192-slot damage-region pass and is returned.

IDA comments retain the exact alternate-width condition at `0x0042D0EE`, the
complete pool/slot boundary at `0x004516CF`, the update-callback/trajectory
boundary at `0x004511C8`, and the distinct feedback/damage accumulators at
`0x0042A1FA` and `0x004519A3`.

The locally pinned `th08-decomp` commit
`84738749bdcf6cffabe8d0d76e17f19253a20d50` provides address and extent
agreement only. Its player update functions are stubs or unnamed mappings, so
it supplies no shot lifecycle, callback, collision, or damage authority.

## Implemented Projection

`scripts/th08_runtime/native_combat_projection.py` implements
`th08-native-combat-root-projection-v4`. V1 established the complete
shot/target projection; V2 added normalized loaded-SHT identity and exact
source-record provenance; V3 separates uncapped returned damage from the
capped hit-feedback accumulator increment; V4 adds the complete player
damage-region pool and native-ordered supported pass.

For every exact root or future tick it retains:

- a SHA-256 identity of all `128 * 0x484` shot-pool bytes, including inactive
  stale bytes that may still distinguish a future initializer/callback state;
- decoded fields and per-slot raw identity for every active shot;
- both player shot timers;
- a SHA-256 identity of all `192 * 0x40` player damage-region bytes plus every
  active slot's circle/rectangle geometry, lifetime, damage, accumulated
  damage, cap, tick interval, and effect-suppression byte;
- every active enemy target decoded from the already-retained
  `ordinary_enemy_template_and_pool` component, without a second enemy-pool
  read;
- the revalidated player-shot/HP gate result using player transition, Bomb,
  spell-active, and spell-owner context;
- native primary overlap and, after supported primary state mutation, the
  optional alternate overlap;
- native damage-region active/due/overlap/cap arithmetic, with primary region
  mutation carried into the optional alternate pass and Bomb-region overlap
  retained separately for each target-local projection;
- a numeric subtotal only for eligible, overlapping shots whose type and
  zero hit callback are supported; and
- explicit unresolved slot lists for type-4/5 and nonzero-hit-callback
  overlaps.

The supported ordinary subtotal applies the native Bomb reduction, piercing
set `{4, 5, 6}`, and nonpiercing state-2 transition. It reports the uncapped
return subtotal separately from the `min(subtotal, 50)` feedback-accumulator
increment. The damage-region subtotal follows active, signed remainder-zero
tick due, inclusive circle/rectangle overlap, accumulated-damage update, and
positive-cap clipping order. Because type 4/5 overlap remains unresolved,
those types never
contribute to the numeric subtotal in this projection. Later alternate-route
combination, character/spell/Boss/timeout scaling, and the final HP write are
outside this subtotal.

The full pool digest is deliberately stricter than the decoded active list.
An inactive byte difference can reject deterministic equality even when no
active shot differs. This may produce a fail-closed false negative, but it
does not merge roots whose later initialization or callback behavior is not
proved control-equivalent.

The target records are instantaneous target-local projections from one
captured pool state. They do not replay manager-wide enemy iteration, so a
region consumed or capped by an earlier enemy is not propagated into a later
target record. That omitted cross-target order has unknown directional error
and remains outside delivered-damage, kill, and ranking authority.

The subsequent pinned-content audit closes the normal Route-2 SHT subset:
all 53 Power-selector-reachable records are type 0 with zero update and hit
callbacks. The projection now reports active slots compatible/incompatible
with that subset. This removes type-4/5 and hit-callback uncertainty only when
the exact Route-2/no-Bomb/root-history conditions in
`ROUTE2_NORMAL_SHOT_CONTENT_CLOSURE_CONTRACT_20260731.md` hold; arbitrary or
contaminated roots still fail closed.

## Rolling And Causal Integration

`scripts/tools/th08_native_snapshot_trial.py` schema
`th08-native-snapshot-rolling-trial-v7` now:

- captures the combat projection at the root and every tick;
- requires its SHA to agree in same-action replay and all-36 repeated-root
  checks;
- requires exact root/tick combat agreement in the natural same-seam
  reference; and
- retains compact combat summaries in the portfolio output.

`scripts/tools/th08_native_snapshot_causal_search.py` schema
`th08-native-snapshot-causal-secondary-search-v5` carries the same projection
through the origin, promoted subroots, future ticks, and parent-repeat
transaction.

The older collision projection remains schema v7 and unchanged. Combat state
is an independent projection so this checkpoint does not rewrite or weaken
the retained H1/H8/H32 collision evidence boundary.

`scripts/analysis/th08_native_combat_branch_report.py` lowers only accepted v7
rolling transactions or accepted v5 causal-search transactions into
`th08-native-combat-branch-comparison-v1`. It:

- rejects every branch whose native compact history enters player phase 2;
- reports native published frame damage and instantaneous supported ordinary
  plus damage-region overlap subtotals;
- reports unresolved-overlap counts rather than hiding them;
- exposes cross-slot positive-HP change only as a non-generation-safe proxy;
  and
- grants no candidate score, combat-benefit, kill, prevented-birth, physical
  prediction, or live-ranking authority.

No new TH08, replay, controller, supervisor, native runner, or physical trial
was launched for this checkpoint. Consequently all projection records remain
implementation/synthetic evidence until an explicitly authorized native
snapshot corpus exercises them.

## Formal Problem Contract

### Physical objective

Survive NMNB through the declared horizon. Among branches satisfying the same
hard survival predicate, later work may compare damage, verified kill time,
prevented hostile births, carried resources, and terminal position/reserve.
This checkpoint itself performs no such optimization.

### State and observations

One modeled root contains the immutable full native snapshot, complete
player-shot pool identity and decoded active slots, active enemy target
fields, spell/Bomb/player state, active input, Focus state, and manager frame.
A future comparison is admitted only from the rolling/casual transaction that
generated its own native future.

Two physical histories merge only if the existing full native root and the
new combat projection agree under the parent tool's exact transaction. The
projection does not claim that equal decoded summaries alone are
control-equivalent. Enemy slot reuse is not generation-safe across frames;
the exact lifecycle ring remains the required generation oracle.

### Actions and issue semantics

Actions are the parent tools' complete no-Bomb masks and action schedules.
The projection neither issues nor rewrites input. Pickup delay, held desired
input, active input, no-write, and scheduler semantics remain governed by the
unchanged native snapshot transaction. No result from this report reaches the
issue thread.

### Uncertainty and transitions

Every branch uses its own original-engine native future. Hidden RNG, shot
callbacks, enemy lifecycle, and target motion are not copied from another
action. Unsupported type-4/5 or hit-callback overlap remains explicit
unknown. There is no maximization over hidden branches in this checkpoint.

### Horizon, resources, and safety

The horizon is the exact finite branch retained by the parent tool. Native
player phase 2 is a hard rejection. Bomb emission remains forbidden; observed
Bomb state is context, not authority to issue Bomb. Lives, Bombs, Power,
items, Boss resources, and later phase entry are not optimized by this
lowerer.

### Deadline and fallback

Capture and lowering are offline and have no issue deadline. The unchanged
live Boolean policy plus fresh local hard certificate remains the physical
fallback. Any missing projection, schema mismatch, nonfinite active geometry,
short read, deterministic mismatch, unsupported accepted status, or malformed
frame sequence fails closed.

## Five Authority Questions

1. **Which histories map to one state?** Only histories sharing the parent
   tool's immutable full root and exact combat projection. Summary equality is
   insufficient, inactive stale bytes remain in identity, and enemy
   generations are not merged across slot reuse.
2. **Are uncertainty branches complete and causal?** Each retained action
   owns its native future. The projection makes no hidden-branch decision.
   Callback/type-4/5 cases are unresolved, not optimistically completed.
3. **Does exact solution answer the physical question?** No recurrence is
   solved here. Exact capture answers instantaneous shot/target/gate state and
   a bounded supported-overlap subtotal. It does not answer delivered future
   damage, lethal generation crossing, prevented emission, resource benefit,
   or route survival.
4. **What does the algorithm bound, and what falsifies it?** It exactly
   decodes declared fields and computes only the supported ordinary-shot
   subset. A native same-root trace that disagrees on pool identity, fields,
   ordered overlap, state mutation, cap, gate, or published frame damage
   falsifies it. A missing contribution from an explicitly unresolved
   callback/type case does not.
5. **Can it be consumed before issue?** No. It is offline-only and has no
   publication path or live consumer. Promotion would require exact-version
   lookup, deadline/contention evidence, independent lifecycle agreement,
   shadow isolation, and separate physical acceptance.

## Authority And Next Gate

This checkpoint grants:

- revalidated native shot-pool, target-field, and alternate-pass semantics;
- exact-root player-shot/enemy-target capture identity;
- synthetic parity for supported instantaneous ordinary-shot overlap;
- deterministic integration into rolling and causal snapshot transactions;
  and
- a hard-survival-filtered, non-ranking offline comparison format.

It grants no:

- observed v7/v5 runtime sample;
- generation-safe HP delta or kill/end classification;
- target-selection, Focus-switch, damage-ranking, or resource-ranking
  authority;
- prevented hostile birth or shortened exposure claim;
- physical predictive, shadow, or live action authority.

Six focused projection tests, six focused report tests, three loaded-SHT
provenance tests, twelve rolling snapshot tests, and four causal-search tests
pass. Complete discovery passes 1,522 tests in 14.857 seconds on Linux and
30.869 seconds through the Windows UNC loader, with the three existing skips.

The next authorized causal gate is a small immutable-root corpus spanning
focused, unfocused, and dynamic-refocus complete-mask schedules. Each branch
must pass the unchanged survival transaction and this combat projection, then
join exact v4 lifecycle damage/generation events before any HP change is
called a kill. Candidate benefit additionally requires action-specific
prevented hostile births or shorter exposure. Until runtime authorization
exists, continue other general high-ROI WS-H semantics rather than isolated
hit-producer investigation.
