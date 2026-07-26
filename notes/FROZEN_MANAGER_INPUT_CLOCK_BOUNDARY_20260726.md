# Frozen Manager Counter And Input-Clock Boundary

Date: 2026-07-26

Status: physical clock counterexample confirmed; the 50-ms
repeated-manager-frame guard was physically rejected and removed. A native
FRScreen/MSG semantic boundary is now identified and validated in two
shadow-only Stage-4A runs. Input neutralization and epoch-reset authority
remain unresolved and unpromoted.

## Problem Contract

### Physical objective

Do not allow a finite-horizon movement decision to continue for unmodeled
wall time across dialogue or a phase transition. Preserve a reviewable,
freshly sensed entry state for the next attack.

### State and clocks

The robust planner advances a physical step `t` for every player-motion and
hazard transition. Live orchestration had identified this step with native
`enemy_manager_frame = m`.

Stage-4A physical evidence disproves that identification globally:

```text
m stays constant
held directional input remains active
player position continues to change
```

The relevant physical state is therefore at least:

```text
x = (m, wall time tau, player position q, active input a,
     held desired mask g, gameplay epoch e,
     FRScreen implementation identity r, signed MSG state z)
```

Histories with equal `(m, q, a, g)` before and after an unknown number of
hidden player-motion updates are not control-equivalent. A policy proved only
on the manager-frame recurrence has no authority across this boundary.

### Observations

The controller observes:

- `m` from native memory;
- its monotonic wall clock `tau`;
- the desired mask held by the actuator, kept distinct from native
  `input_current`;
- paired native reads of the FRScreen implementation pointer, MSG resource,
  MSG program counter, signed MSG state, manager frame, FRScreen update
  serial, player position/velocity, and native input state;
- gameplay/foreground state and the previous native player/spell snapshot;
- wall-clock auto-confirm pulse eligibility.

The native semantic predicate implemented by the shipped binary is:

```text
frscreen_blocks_enemy_clock =
    impl != null and (msg_state >= 0 or msg_state == -2)
```

The shadow probe reports a tri-state result. A stable non-null implementation
and stable MSG state produce `true` or `false`; a null pointer, read failure,
or interval instability produces `unknown`. `msg_state >= 0` is observed
active MSG dialogue. `-1` is observed inactive. `-2` also blocks the manager
clock, but its producer and physical meaning remain unknown and are retained
as a separate special state.

While `m` is repeated, the current fast path does not refresh a complete
hazard/player snapshot. More importantly, a repeated value by itself does not
distinguish:

1. ordinary controller work that lasts longer than 50 ms;
2. Windows scheduling delay;
3. a semantic dialogue/phase transition in which player input physics still
   advances.

This information ambiguity invalidates a short raw wall-time threshold as a
semantic transition detector.

### Actions and omitted transition

The dialogue auto-confirm path toggles only `Z`:

```text
release Z -> wait 40 ms -> press Z
```

It does not release `UP/DOWN/LEFT/RIGHT`. A desired action such as
`up_left_fast` can remain physically active for hidden player updates even
though its modeled manager-frame hold does not advance.

Let `n(tau)` be the unknown number of player-motion updates during a genuine
manager freeze. The omitted transition is:

```text
q' = clamp(q + n(tau) * velocity(g))
```

With unrestricted freeze duration, the reachable position support can reach
a playfield boundary.

The current checkpoint does not change this action path. The next shadow
counterfactual may compute:

```text
neutral_desired = held_desired with UP/DOWN/LEFT/RIGHT cleared
                  and SHOT/non-Bomb bits preserved
```

It must not pretend that `neutral_desired` is immediately active. If the
complete desired mask changes, the request is a real write that samples the
declared pickup delay; native `input_current` remains the active-action
evidence until pickup, and the pending remaining-delay support must be
carried. Selecting the complete mask already held is no-write: it samples no
new delay and preserves any pending command. A semantic episode may nominate
at most one immutable epoch transition, but the causal point at which that
transition follows the delayed write is deliberately unresolved and receives
no authority in this checkpoint.

### Invariants and current authority boundary

- `enemy_manager_frame` is not an unconditional physical input clock.
- No exact, lower-bound, upper-bound, delay, or viability claim crosses a
  genuine frozen-input boundary without modeling or conservatively handling
  its hidden player updates.
- A raw repeated-counter duration, including 50 ms, must not reset the
  gameplay epoch or retire live policy authority.
- The removed guard must not be reintroduced under another threshold without
  a semantic detector and a shadow false-positive audit.
- The current live controller is restored to the pre-guard behavior. This is
  the better observed controller, not a claim that CE-0120 is fixed.
- The semantic detector and episode tracker are shadow-only. They do not
  change input, delay support, cadence evidence, gameplay epoch, estimator
  state, policy version, or worker publication.
- The opt-in implementation performs synchronous native reads and trace
  writes on the issue thread. It is control-state authority-free, not
  physically side-effect-free; its total CPU/delivery effect remains an open
  measurement.
- `msg_state == -2` has no input authority until its producer and physical
  consequences are independently identified.
- Candidate-verifier results remain shadow-only and do not affect the mask.

### Delivery deadline and approximation direction

There is no proved finite upper bound on `n(tau)` under arbitrary Windows
scheduling and dialogue duration. A practical replacement may restrict the
actuator instead of expanding unbounded hidden time, but it must bind the
restriction to evidence of an actual transition.

The FRScreen/MSG predicate now supplies a native semantic evidence source.
Any actuator proposal must still report:

- predicted transition episodes versus actual wall-pulse episode groups;
- false positives during ordinary slow decisions;
- detection latency and displacement before detection;
- whether the proposed reset would retire a still-useful Boolean policy;
- next-phase entry position and policy freshness.

The expected semantic episode count is on the order of observed wall-pulse
groups, not thousands of ordinary repeated reads.

## Physical Evidence: Original Defect

Run:

```text
lunatic_route2_stage4a_unattended_20260726_100451
```

The complete hard-no-Bomb trace contains five same-frame wall-pulse groups,
not four: `4963 x 4`, `6763 x 34`, `21467 x 6`, `30128 x 8`, and terminal
`45836 x 20`. The first four are closed episodes; the fifth is right-censored
by `terminal_unload`/`route_complete`. The older compact report omitted that
terminal group. Of the two closed directional groups:

| frozen `m` | held action | wall pulses | before | after | displacement |
|---:|---|---:|---|---|---:|
| 21467 | `up_left_fast` | 6 | `(252.69, 391.37)` | `(8.00, 32.16)` | 434.63 px |
| 30128 | `left_fast` | 8 | `(351.65, 381.73)` | `(8.00, 381.73)` | 343.65 px |

At `m=21467`, item utility was zero and predicted collections were empty. The
center-lane target was reasonable inside the ordinary manager-frame model;
the defect was the unbounded hidden wall-clock hold. The next attack began
from the top-left edge and contact occurred at frame 21611, but temporal
proximity alone is not a causal prevention claim.

Evidence:

- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260726_100451.frozen_input.json`
- raw JSONL SHA-256
  `b8e9428f648b6c87ee379291d896804410019469b8b7f86ef6233456e050c5a1`
- CE-0120

## Rejected Experiment: 50-ms Repeated-Counter Guard

Run:

```text
lunatic_route2_stage4a_unattended_20260726_103856
```

This was the latest live Boolean/local controller plus a shadow-only
candidate verifier. It was not an ablation with a weaker planner. The only
new input authority was the 50-ms guard:

1. release movement and retain `SHOT`;
2. increment `gameplay_epoch`;
3. reset delay/cadence evidence;
4. retire current/pending corridor policies and model memory.

The accepted, route-complete trace recorded:

| metric | pre-guard `100451` | guard `103856` |
|---|---:|---:|
| decisions | 9,222 | 7,925 |
| native hits | 21 | 64 |
| guard firings | 0 | 2,780 |
| actual wall pulses | 72 | 72 |
| available viability queries | 9,073 | 691 |
| pending-future-epoch decisions | 42 | 623 |
| read median/p95 | 13.46/19.01 ms | 18.40/25.29 ms |
| local plan median/p95 | 23.40/41.34 ms | 30.25/49.24 ms |
| action lag median/p95 | 3/4 frames | 3/5 frames |

The first guard fired at manager frame 91; the first hit was frame 895. Thus
the guard had already caused repeated policy invalidation before the first
contact. It fired on 35.08% of decisions, while both runs had only 72 actual
wall pulses. Available global queries fell from 98.38% to 8.72% of decisions.

The direct causal rejection is policy starvation: each false positive created
a new immutable epoch and correctly invalidated the useful policy. The hit
increase supports the physical rejection but is not treated as a controlled
effect size because RNG, timing, and phase histories differ.

Evidence:

- `artifacts/viability_audit/stage4a_20260726_103856_frozen_guard_rejection.json`
- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260726_103856.dossier.json`
- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260726_103856.comparison.json`
- raw JSONL SHA-256
  `b32c941a7def998d62fc3e2820c5c779534e1a3c10055faed69d717127fb925f`
- CE-0121

## Native Mechanism From The Shipped Binary

The following claims are **observed static evidence** in the connected IDA
database:

- `0x0160F430` points to the `FRScreenImplInf` object. Its MSG resource,
  program counter, and signed state are at `+0x21814`, `+0x21818`, and
  `+0x2181C`.
- `frscreen_blocks_enemy_clock` at `0x4358BB` returns true exactly when the
  implementation exists and the signed MSG state is nonnegative or `-2`.
- `enemy_manager_update` at `0x42C660` increments
  `enemy_manager_frame` (`0x0164D30C`) only when that predicate is false.
- The priority-9 player callback consumes native active input and applies
  displacement at `0x44BAB6` before the priority-11 enemy-manager callback.
  The priority-15 FRScreen callback and priority-17 native input publication
  occur later. Therefore dialogue can freeze the manager counter after player
  movement has already occurred.
- `g_frscreen_update_serial` at `0x0160F428` increments in the priority-15
  callback. A positive delta is post-player update-chain evidence; absence of
  a delta is not proof that the player did not move.

The interpretation that this update ordering is the mechanism behind CE-0120
is **inferred** by joining those static facts with the retained runtime
displacement. It is not a native instruction trace. The meaning and producer
of signed state `-2` remain **hypothesized/unknown**.

Strong names, partial types, and boundary comments were applied in IDA and
are recorded in `notes/RESEARCH_LOG.md`.

## Shadow Semantic-Boundary Validation

The game-neutral tracker groups tri-state semantic observations without
issuing an action. A transition to `true` starts an episode, `false` closes
it, and `unknown` does not invent a close. If the manager frame changes while
the semantic gate is still active, the tracker censors the old episode and
opens a new one; the first physical run exposed and retained this required
segmentation rule.

The live probe and tracker explicitly declare
`shadow_no_input_or_epoch_authority`. Desired input and native active input
are separately retained. The `auto_confirm_wall_pulse` groups are a delayed
same-frame proxy used for comparison, not live authority and not ground
truth.

Two complete hard-no-Bomb Stage-4A runs produced:

| metric | `120839` | `122014` |
|---|---:|---:|
| decisions | 7,349 | 8,914 |
| semantic observations | 3,216 | 3,116 |
| gate false / true / unknown | 3,134 / 81 / 1 | 3,031 / 84 / 1 |
| wall-pulse groups | 5 | 5 |
| matched episodes / FP / FN vs delayed proxy | 4 / 0 / 1 | 5 / 0 / 0 |
| available viability queries | 7,216 | 8,759 |
| capture median / p95 / max | 0.341 / 0.444 / 12.640 ms | 0.191 / 0.490 / 17.181 ms |

`120839` merged the `4963` and `6763` groups because the semantic gate stayed
active while the physical frame changed. This is an **observed telemetry
segmentation defect**, not a native-detector false negative. The corrected
tracker in `122014` emitted five distinct episodes for pulse groups
`4963 x 4`, `6763 x 34`, `20845 x 6`, `29506 x 8`, and terminal
`44817 x 21`; the terminal group is right-censored. All 3,116 logged
observation reads were valid, one interval was unstable/unknown, and no `-2`
state was observed.

The `122014` trace used the first new-frame observation as the old censored
episode's endpoint, so its first serial delta `+76` is an upper boundary
sample, not a closed old-frame duration. Post-run code review changed future
tracker output to end a frame/context-censored episode at its last
semantically known old-frame sample before opening the new episode. This
unit-tested telemetry refinement does not change `122014`'s five-episode
segmentation or proxy classification, but it has not received another
physical run.

At manager frame `20845`, active input `0x81` moved the player from
`(66.494, 399.499)` to `(376.000, 399.499)`: `309.506 px` over `2.056 s`
while the manager frame remained frozen and the FRScreen serial advanced
124. Frame `29506` held `stay`, displaced `0 px` over `2.629 s`, and advanced
the serial 158. These are **observed runtime evidence** that the semantic
episode may contain player updates but only moves when the native active mask
contains direction.

On `122014`, the five gate-positive first-repeat observations arrived after
`32.864..68.187 ms` since manager progress. Gate-negative repeats overlapped
that wall-time range, while a hypothetical 50-ms cut classified 1,728
ordinary repeats and only five gate-positive repeats. This independently
confirms CE-0121's classification failure. The 98.19%/98.26% viability-query
availability in the two shadow runs lacks the 8.72% epoch-starvation
signature of `103856`; it does not prove zero CPU contention because total
capture calls, RNG, and host timing were not controlled.

These runs validate only Stage-4A shadow selectivity and tracker segmentation.
They do not validate neutralization latency, next-phase entry state, one-reset
semantics, `-2`, pauses, other workloads, or side-effect-free delivery.

## Formal Review

1. **State equivalence:** manager frame, cell, and input alone do not identify
   a control-equivalent state across hidden wall-time movement. Stable
   FRScreen identity and signed MSG state now separate observed active MSG
   episodes from ordinary slow repeated reads, but states inside one active
   episode still differ by hidden player updates and native active input.
2. **Uncertainty and causality:** the original recurrence still omits genuine
   hidden movement. The semantic predicate uses only current native reads and
   merges identical observations before tracker state changes; it does not
   branch hidden states and maximize separately. `unknown` cannot close an
   episode or create authority.
3. **Physical relevance:** the tracker answers the semantic classification
   question only. Even an exact manager-frame solve remains a proxy until an
   actuator restriction or an expanded physical recurrence handles movement
   inside the episode.
4. **Algorithm validity:** the tracker exactly implements its declared
   tri-state recurrence. Its falsifiers include an ordinary stable
   `msg_state >= 0` false positive, an unmatched genuine episode, an unstable
   interval classified as stable, or two pulse groups merged across a manager
   frame change. The first run found the last case; the corrected second run
   passed the retained Stage-4A proxy comparison.
5. **Delivery:** logged stable reads were normally sub-millisecond and the
   semantic gate was present on the first observed repeat without a fixed
   wall threshold. Total contention and any neutralizing write/epoch
   transaction remain unmeasured, so no live deadline or action-authority
   claim follows.

## Next Validation Gate

Before live input authority:

1. retain a shadow counterfactual that records, without writing, the exact
   episode-entry mask that would remove movement bits while preserving
   `SHOT`, and the single immutable epoch transition it would request;
2. broaden negatives beyond Stage 4A, including ordinary gameplay, pause,
   scene unload, and other stage/dialogue owners; retain every mismatch;
3. resolve `msg_state == -2` or keep it unknown and outside authority;
4. measure total probe/capture contention, first-detection latency,
   pre-detection displacement, and prospective policy retirement;
5. only then run an explicitly scoped physical trial of movement
   neutralization plus one epoch reset per confirmed `msg_state >= 0`
   episode, checking next-phase entry position and policy freshness.

CE-0120 is resolved at the native sensor/classification layer only. Its
actuation consequence remains open, and live behavior stays at the pre-guard
checkpoint.
