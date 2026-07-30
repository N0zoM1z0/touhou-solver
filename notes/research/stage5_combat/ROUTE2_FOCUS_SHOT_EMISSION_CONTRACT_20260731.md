# Route-2 Focus/Shot Emission Contract

Date: 2026-07-31

Taskbook card: `COMBAT-FAST-01`

Status: offline semantic checkpoint; no live action authority

## Task Card

Question: at the player-shot priority of one physical update, how do the
observed route-2 Focus state, Power, shot cadence, player-shot pool capacity,
and shipped SHT records determine emitted shots and gameplay-RNG consumption?

Hypothesis: releasing or pressing Focus can change the selected SHT profile on
the Focus-logic edge, so a survival-feasible Focus schedule can change shot
coverage and can also change the RNG state seen by later same-frame enemy/ECL
updates. The effect is causal only when the shot timer is due and an empty
player-shot slot is available.

Earliest decision effect: player shot emission at priority 9, before ordinary
enemy/ECL work at priority 11. This checkpoint does not assume that a newly
issued complete mask is already active at that priority; it consumes the
observed active input and Focus state.

Win condition:

- shipped `ply02a.sht` and `ply02as.sht` normal-level selection, due-record
  order, callback-7 RNG consumption, and pool-full behavior are represented by
  an independently tested scalar model;
- future native roots retain the shot timer and free-slot count needed to use
  that model causally;
- the root-2129 four-u16 prefix is classified only to the strength supported
  by the old capture; and
- no combat score, Focus release, or Shot toggle is granted live authority.

Reject or defer:

- any unsupported callback, unavailable SHT/profile identity, missing cadence,
  or missing pool state remains `UNKNOWN`;
- geometry that depends on unverified native trigonometric rounding remains
  outside hard clearance authority; and
- a compatible RNG count alone is not proof of shot birth, damage, kill, or
  prevented hostile emission.

Out of scope for this checkpoint: a live Focus policy, unconditional Shift
release, full player-shot pool trajectories, enemy HP/kill-end causality,
Power-0 routing, Bomb use, a new physical trial, and the remaining individual
producer of hostile birth slot 1220.

## Problem Contract

Physical objective: preserve the unchanged no-hit/no-Bomb survival constraint
while making later combat experiments capable of comparing focused,
unfocused, and causal refocus schedules without silently changing same-frame
RNG.

State and observations at this decision:

- shipped executable identity and the SHA-256 identities of the primary and
  secondary SHT files;
- active `input_current`, route/team identity, `focus_logic`, Power, player and
  option positions;
- the full three-component shot timer
  `(previous_integer, fraction_bits, current_integer)`;
- the count of player-shot slots whose state word is zero/nonzero; and
- gameplay RNG state and call count.

The old root-2129 capsule lacks the timer and pool observations. Its result is
therefore an information set over cadence and capacity, not a single exact
shot-emission state.

Actions and issue semantics: the physical action is a complete input mask, but
this checkpoint models only a player-shot update from an already observed
active input/Focus state. It neither guesses pickup delay nor rewrites desired
input as active input. Selecting a mask and emitting a shot are distinct
events.

Uncertainty and transitions:

1. nonzero `focus_logic` selects the secondary SHT and zero selects the
   primary SHT;
2. normal Power selection starts at level 0 and advances while
   `Power >= level.power_upper_bound`;
3. emission is eligible only on a shot-timer integer transition;
4. records are evaluated in file order only while a free slot remains;
5. default callback 0 emits when `cadence % period == phase` without RNG;
6. callback 7 performs the same due test, initializes the record, consumes one
   `rng_next_signed_unit` (two u16 calls), stores a narrow random angle around
   `-pi/2`, and replaces velocity from that angle; and
7. a full pool evaluates no record and consumes no callback RNG.

The finite horizon is one player-shot emission priority. The resource
constraint is the 128-slot player-shot pool. The hard invariants are no Bomb
bit, no live publication, no hidden cadence maximization, no endpoint-derived
root state, and fail-closed handling of unsupported callbacks. The
computation deadline is offline; there is no issue-thread consumer or
fallback change.

## Native Evidence And Revalidation

Observed in the connected shipped-program IDB:

- `player_emit_shot_level` (`0x00450F60`) selects the secondary SHT from
  player byte `+0x03`, walks Power thresholds, scans 128 slots of stride
  `0x484`, treats slot word `+0x462 == 0` as free, and stops advancing records
  when no free slot remains;
- `player_update_shot_cadence` (`0x00451500`) tests timer integer change,
  emits with the current integer, advances the timer, and cycles the active
  firing timer through 0..19;
- `timer_current` (`0x0040D3B0`) reads timer base `+0x08`, and
  `timer_integer_changed` (`0x0040D3D0`) compares it with timer base `+0x00`;
- callback-table index 7 reaches `0x004501B0`, whose due path calls
  `rng_next_signed_unit` once and then overwrites angle and polar velocity;
  the stored angle and both velocity components are float32 fields;
- `player_shot_initialize` stores source-plus-offset position and
  `cos/sin(angle) * speed` velocity to float32 fields, and
  `player_update_shots` stores each default
  `time_scale * velocity + position` result back to float32; and
- `rng_next_signed_unit` (`0x0043ED80`) consumes one u32, hence two u16 RNG
  calls.

Observed in shipped data:

- primary `ply02a.sht` SHA-256
  `4765744ab5bbf797746469d5a6afc6ec7d4b0371422b5aa5a2e54ae668c48885`
  uses callback 0 for all normal records; and
- secondary `ply02as.sht` SHA-256
  `f7554b3a32e16da01de9432e22609482a1c98a33212eb904ad47789079abebd3`
  uses callback 0 for player-center records and callback 7 for normal option
  records.

Observed in retained root 2129: the root has active input `0x05`,
`focus_logic == 1`, Power 128, RNG state/calls `45644/22684`, and the
one-frame endpoint has consumed 32 u16 calls. The already attributed seven
hostile births consume 28 of those calls; four earlier u16 calls remain.

Inferred, not observed: a due focused level-5 option pair would consume exactly
those four earlier calls before priority-11 enemy work. Because the retained
root omitted shot cadence and pool capacity, this is a compatible and
well-ordered explanation, not yet a unique causal proof. The hostile producer
of birth slot 1220 remains unresolved and is deliberately not pursued here.

## Authority Answers

1. Histories are merged only when SHT identity, Focus profile, Power-selected
   level, cadence integer/change status, relevant pool capacity, positions,
   and RNG identity agree. Equal Focus alone is not control-equivalent.
2. This one-priority transition enumerates every supported record in native
   order and never maximizes a hidden cadence branch. Missing root fields
   produce a set of compatible outcomes.
3. Exact solution answers only the player-shot emission/RNG subproblem. It
   does not answer future shot collision, enemy death, hostile-emission
   prevention, or physical survival.
4. The algorithm is exact for record order, due tests, capacity, RNG-call
   count, and observed binary32 storage boundaries over callbacks 0 and 7.
   Static-CRT trigonometric low bits remain an unknown-direction numerical
   approximation until native-bit differential evidence exists. A native root
   with retained timer/pool fields whose RNG delta, emitted-record order, or
   post-store value disagrees falsifies the corresponding claim.
5. There is no live consumer. A later proposal may consume this state only
   after exact-version root capture and before its declared issue deadline;
   otherwise combat ranking stays disabled.

## Implementation Result

The semantic foundation is implemented without live promotion:

- normal SHT profile/Power selection, native record order, pool capacity,
  callbacks 0/7, and callback RNG consumption are executable in
  `scripts/th08_player_shot_model.py`;
- an independent test RNG agrees on state, call count, and stored callback-7
  angle; pool-full, capacity-prefix, non-due, unsupported-callback, shipped
  callback-partition, and threshold edges are covered;
- spawn position, stored angle/velocity, and default motion explicitly round
  at each native float32 memory write; an adversarial `2^24 +/- 1` regression
  rejects the old unbounded Python-double accumulation;
- `scripts/th08_player_shot_runtime.py` captures the timer identity and all
  slot words without changing the live sensing hot path;
- rolling native snapshot schema v4 retains that state at roots and endpoints
  and includes it in same-action and natural-frame acceptance; no native
  snapshot or physical trial was launched in this checkpoint; and
- deterministic report
  `artifacts/runtime_reports/th08_route2_focus_shot_emission_root2129_20260731.json`
  has SHA-256
  `f78e820fe7aeabd12d5c6b4a2fd901462a54ada26758f3ba11fae615318738e8`.

Focused checks, Ruff, and report byte-regeneration pass. Complete discovery
passes 1,530 tests in 14.568 seconds on Linux and 1,530 tests in 31.092
seconds through the Windows UNC loader, with the three existing Windows
skips.

`COMBAT-FAST-01` remains `semantic_foundation_only`. The next gate is an
explicit v4 identical-root ordinary-enemy corpus. Full shot trajectories,
HP/kill-end causality, prevented hostile emissions, survival-equivalent
dynamic refocus, and live ranking remain open.
