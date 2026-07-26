# Frozen Manager Counter And Input-Clock Boundary

Date: 2026-07-26

Status: physical clock counterexample confirmed; the 50-ms
repeated-manager-frame guard was physically rejected and removed. The
original post-spell directional-hold defect remains unresolved.

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
     held desired mask g, gameplay epoch e)
```

Histories with equal `(m, q, a, g)` before and after an unknown number of
hidden player-motion updates are not control-equivalent. A policy proved only
on the manager-frame recurrence has no authority across this boundary.

### Observations

The controller observes:

- `m` from native memory;
- its monotonic wall clock `tau`;
- the mask it holds;
- native input evidence on ordinary decision iterations;
- gameplay/foreground state and the previous native player/spell snapshot;
- wall-clock auto-confirm pulse eligibility.

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
- Candidate-verifier results remain shadow-only and do not affect the mask.

### Delivery deadline and approximation direction

There is no proved finite upper bound on `n(tau)` under arbitrary Windows
scheduling and dialogue duration. A practical replacement may restrict the
actuator instead of expanding unbounded hidden time, but it must bind the
restriction to evidence of an actual transition.

Plausible evidence sources include a native dialogue/phase state, an exact ECL
or scene-transition signal, or the existing wall-pulse state machine. Any
proposal must first run in shadow and report:

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

The complete hard-no-Bomb trace contains four wall-pulse episodes. Two
started from `stay` and had zero displacement. Two started from a direction
and produced boundary-scale motion:

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

## Formal Review

1. **State equivalence:** manager frame, cell, and input do not identify a
   control-equivalent state across hidden wall-time movement.
2. **Uncertainty and causality:** the original recurrence omits genuine hidden
   movement. The rejected guard did not add clairvoyance, but its observation
   predicate merged ordinary slow iterations with semantic freezes.
3. **Physical relevance:** an exact solve of the manager-frame recurrence
   still answers only a proxy at this boundary.
4. **Algorithm validity:** the 50-ms predicate did enforce neutral input after
   firing, but it did not solve the detection problem. CE-0121 falsifies its
   required classification premise.
5. **Delivery:** guard execution was fast enough; correctness, not compute
   time, failed. A replacement must demonstrate semantic selectivity before
   input authority.

## Next Validation Gate

Before another physical input-authority trial:

1. implement only a shadow episode detector;
2. compare its detections with retained wall-pulse/phase evidence;
3. require near-zero detections during ordinary gameplay iterations;
4. retain a counterexample for every false positive;
5. only then test neutralization and one epoch reset per genuine episode.

Until that gate passes, CE-0120 remains open and live behavior stays at the
pre-guard checkpoint.
