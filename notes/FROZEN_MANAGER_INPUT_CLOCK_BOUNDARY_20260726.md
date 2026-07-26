# Frozen Manager Counter And Input-Clock Boundary

Date: 2026-07-26

Status: observed physical counterexample; fail-closed live correction
implemented, focused regression passed, fresh physical validation pending.

## Problem Contract

### Physical objective

Do not allow a finite-horizon movement decision to continue for unmodeled
wall time across dialogue or a phase transition. Preserve a reviewable,
freshly sensed entry state for the next attack.

### State and clocks

The robust planner advances a physical step `t` for every player-motion and
hazard transition. Live orchestration had identified this step with native
`enemy_manager_frame = m`.

The Stage-4A trace disproves that identification globally. During some
post-spell dialogue:

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

The planner may still use `m` as its step clock inside a contiguous gameplay
epoch, but it may not carry a movement action or policy across an observed
wall-clock freeze of `m`.

### Observations

The controller observes:

- `m` from native memory;
- its own monotonic wall clock `tau`;
- the desired mask it holds;
- native input evidence on ordinary decision iterations;
- gameplay/foreground state and the previous native player/spell snapshot.

While `m` is frozen, the normal decision path does not refresh the complete
hazard/player snapshot. The number of hidden player-motion steps is not
observed.

### Actions and transition

Before this correction, the repeated-counter branch only generated a fresh
`Z` edge:

```text
release Z -> wait 40 ms -> press Z
```

It did not release `UP/DOWN/LEFT/RIGHT`. A desired action such as
`up_left_fast` could therefore remain physically active for every hidden
render/update step even though its modeled manager-frame hold did not
advance.

Let `n(tau)` be the unknown number of player-motion updates during a manager
freeze. The omitted transition was:

```text
q' = clamp(q + n(tau) * velocity(g))
```

With unrestricted freeze duration, the reachable position set is not the
single lattice successor used by the planner and can reach a playfield
boundary.

### Uncertainty and horizon

The live system has no proved finite upper bound on `n(tau)` under arbitrary
Windows scheduling and dialogue duration. Expanding the normal viability
recurrence over an unbounded hidden wall-time support is neither useful nor
deliverable.

The engineering correction restricts the actuator instead:

1. when `m` has made no progress for 50 ms, release all movement/focus keys
   and retain only `SHOT`;
2. do this once per frozen counter value;
3. increment the gameplay epoch and reset delay/cadence evidence;
4. retire the current and pending Boolean policies, corridor commitment,
   enemy-body memories, phase tracker, and ECL cache;
5. reject background enemy snapshots whose submission epoch no longer
   matches;
6. continue wall-clock `Z` pulses using the now-neutral movement mask;
7. after `m` resumes, plan only from a fresh native snapshot and new policy
   version.

This changes the post-detection hidden transition to zero commanded
displacement. It does not claim that displacement before detection is zero.

### Invariants

- No directional bit remains held after the frozen-input guard fires.
- A frozen episode creates a new gameplay epoch even if the prior action was
  already neutral.
- No policy or asynchronous enemy snapshot from the pre-freeze epoch has
  action authority after the guard.
- Wall-clock auto-confirm may toggle `Z` but may not reintroduce a direction.
- The first post-freeze decision still requires the normal fresh local hard
  certificate.

### Delivery deadline and approximation direction

The nominal deadline is 50 ms, or three 60-Hz render frames. At the observed
unfocused diagonal speed, three frames are about 12 pixels of displacement.
This is a user-space wall-clock guard, not a hard real-time proof: scheduler
starvation can delay detection. The correction is conservative after it
runs, but the pre-detection displacement bound is unknown under arbitrary
scheduling. The guard therefore fixes the unbounded persistent hold without
turning the complete transition into a mathematically exact clock model.

Fresh physical evidence must report the measured `frozen_seconds`, prior and
safe masks, entry displacement, and whether any old policy/snapshot was
consumed. Until then the implementation checkpoint is tested but not
physically accepted.

## Physical Evidence

Run:

```text
lunatic_route2_stage4a_unattended_20260726_100451
```

The trace contains four wall-pulse episodes. Two started from `stay` and had
zero displacement. Two started from a direction and produced boundary-scale
motion:

| frozen `m` | held action | wall pulses | before | after | displacement |
|---:|---|---:|---|---|---:|
| 21467 | `up_left_fast` | 6 | `(252.69, 391.37)` | `(8.00, 32.16)` | 434.63 px |
| 30128 | `left_fast` | 8 | `(351.65, 381.73)` | `(8.00, 381.73)` | 343.65 px |

At `m=21467`, item utility was zero, predicted collections were empty, and
the planner's center-lane target made `up_left_fast` a reasonable
manager-frame action. The failure was not that local target by itself; it was
allowing the action to remain active across six wall-clock dialogue pulses.
The next attack began from the top-left edge and contact occurred at frame
21611 near the top boundary. This temporal proximity does not by itself prove
that neutralization would have prevented the hit.

Compact evidence:

- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260726_100451.frozen_input.json`
- ignored raw JSONL SHA-256
  `b8e9428f648b6c87ee379291d896804410019469b8b7f86ef6233456e050c5a1`

## Formal Review

1. **State equivalence:** histories with equal manager frame, cell, and input
   are not control-equivalent when one has spent hidden wall time moving.
   They must be separated by an epoch boundary or modeled with another
   physical clock.
2. **Uncertainty and causality:** the old recurrence omitted hidden movement
   steps entirely. The correction does not grant future information; it
   restricts the held action once a freeze is observed.
3. **Physical relevance:** solving the old recurrence exactly would still not
   answer the physical transition because its time base stopped while the
   plant continued.
4. **Algorithm validity:** neutralization bounds future commanded
   displacement after detection. A retained trace showing a direction still
   held after `frozen_input_neutralized`, or an old epoch policy/snapshot
   consumed after it, falsifies the implementation claim.
5. **Delivery:** the guard is on the lightweight repeated-counter path and
   precedes the slower auto-confirm pulse. Physical promotion requires the
   measured event to arrive early enough under the live Windows scheduler.

## Validation Gate

- Focused unit regression: a held `SHOT|UP|LEFT` mask becomes `SHOT` at the
  50-ms threshold and cannot fire twice for the same frozen counter.
- Complete Linux and Windows quick suites.
- A fresh Stage-4A candidate-shadow trial with at least one dialogue freeze.
- Audit every `frozen_input_neutralized` record against the next decision:
  no direction after the event, new gameplay epoch, fresh corridor context,
  and no boundary-scale hidden displacement.
- Retain the run even if it disproves the 50-ms engineering deadline.
