# Delivery-Aware Planning Reassessment

Date: 2026-07-24

Status: the full-horizon fine-refinement and fused-survival live experiment is
rejected. Both mechanisms remain reproducible shadow/offline tools. This note
does not claim that coarse Boolean viability is correct or sufficient.

## What The Experiment Actually Tested

The candidate controller combined two changes:

1. a coarse 16-pixel fused survival-label policy; and
2. after a coarse source state was empty, a full-field, full-80-frame
   8-pixel Boolean policy.

The 8-pixel implementation recovered the three CE-0100 Stage-5 capsule
witnesses offline. The fused recurrence matched the independent scalar oracle
and corrected CE-0101's endpoint-ranking counterexample. These are valid
model-level results.

They did not establish that either result could be delivered with a fresh
enough hazard model to improve physical control.

## Physical Rejection

**Observed:** Complete hard-no-Bomb Stage-4A run
`lunatic_route2_stage4a_unattended_20260724_220032` reached
`route_complete` with 40 native hits. The comparison run
`lunatic_route2_stage4a_unattended_20260724_185059` had 26 hits under a
different RNG/respawn history, so the `+14` aggregate is descriptive rather
than a controlled causal effect.

The delivery metrics are direct:

| Metric | Boolean baseline | Candidate | Change |
| --- | ---: | ---: | ---: |
| Solve median | 170.77 ms | 532.04 ms | +361.27 ms |
| Solve p95 | 380.59 ms | 1174.21 ms | +793.62 ms |
| Unique policies | 1,728 | 630 | -1,098 |
| Decisions without query | 68 | 274 | +206 |
| Expired-policy decisions | 34 | 178 | +144 |
| Queryable decisions | 7,867 | 6,837 | -1,030 |
| Empty queried sets | 3,391 | 2,434 | -957 |
| Local-plan median/p95 | 27.05/49.96 ms | 31.06/63.11 ms | worse |

**Observed:** The candidate reduced reported empty sets by 28.2 percent while
making policy delivery much worse. Therefore “fewer empty sets” is not an
end-to-end acceptance objective.

**Observed:** The candidate backends split into 268 coarse fused-survival
solves and 362 refined Boolean solves. Fine refinement viability alone cost
285.55/845.68 ms median/p95. It was not local or adaptive in the computational
sense: one coarse-empty source triggered a complete fine field over the
complete horizon.

**Observed:** A second run disabled fine refinement while leaving coarse fused
survival active. It stopped at frame 13,077 with
`termination_reason=process_unreadable`, 2,070 decisions, and 12 hits. The
session is explicitly `discarded`, `trial_accepted=false`; it cannot be used
as an acceptance or rejection baseline. Its solve median/p95 returned to
196.09/354.90 ms, which isolates most of the first run's background cost to
fine refinement. It does not establish that survival-label live ranking is
beneficial.

## Root Cause Reassessment

**Inferred from the observed delivery metrics:** The experiment optimized the
wrong object. It computed a more precise policy for one frozen future-hazard
snapshot, while the controller needs the best policy whose assumptions still
hold when input is issued.

There are four separate contracts:

1. **Model completeness:** future bullet/laser/enemy births and hybrid
   transforms are present or bounded.
2. **Discrete solver correctness:** the recurrence and optimized kernel match
   an independent oracle.
3. **Policy delivery:** a result arrives before its source/forecast version
   ceases to be useful.
4. **Issue-time authority:** the selected action is recertified against the
   freshest state and current actuator delay.

CE-0100/0101 improved contract 2. The physical experiment materially worsened
contract 3 and did not close contracts 1 or 4. Scalar parity cannot compensate
for that ordering error.

## Rollback Boundary

**Implemented decision:**

- live refinement grid steps are empty;
- live fused survival labels are disabled;
- prewarm returns to the coarse Boolean policy only;
- experimental native worker-count changes and frame-parallel clearance are
  reverted to the last committed values;
- 8-pixel refinement and survival labels remain callable by audit/replay;
- the `th08_corridor_runtime` and game-neutral `policy_guidance` module
  extraction remains, because it changes ownership and testability rather
  than control policy.

The rollback is pinned by
`test_rejected_fine_and_survival_strategies_remain_shadow_only`.

## Damage-Aware Phase Completion Hypothesis

The user raised a different route-level objective: a controller that only
avoids the current pattern may unnecessarily prolong boss phases. Earlier
phase completion can reduce total exposure to later dense emissions.

**Observed:** Shot is already held almost continuously. In the baseline trace,
97.78 percent of output decisions and 97.66 percent of observed native input
contain Shot. The rejected candidate has 97.38/97.39 percent. The missing
behavior is not “press Shot”; it is verified damage delivery.

**Observed:** The current controller has no boss HP, damage-rate, shot-cadence,
option-geometry, damageability, or remaining-phase-time objective. Its
terminal position cost prefers bottom-center or a corridor target.

**Observed shadow proxy:** The retained
`artifacts/strategy/stage4a_attack_alignment_20260724.json` audit measures
absolute player-x versus spell-owner-x during native player phase 3. Alignment
varies widely. For example:

- baseline spell 69 spent 0 percent of measured normal-owner rows within 48
  pixels and had a median horizontal error of 139.66 pixels;
- candidate spell 73 spent 18.61 percent within 48 pixels and had a median
  error of 112.58 pixels;
- other phases reached 51--86 percent within 48 pixels.

All measured spell spans were roughly 2,808--3,229 manager frames, while Power
was usually near zero after earlier discovery hits.

**Inferred, not observed:** The long spans and depleted Power are consistent
with many phases ending near timeout rather than early HP depletion. The
current trace does not record HP or the phase-exit cause, so this cannot yet be
promoted to a runtime conclusion.

**Hypothesis:** A damage-aware tie-breaker can improve route survival if and
only if it operates inside actions that are equivalent under the fresh
collision, delay, and viability certificates. Its useful state is phase
progress, not a generic “move toward boss” weight.

The first implementation gate is read-only telemetry:

- boss current HP and next health threshold;
- damageable/immunity flags;
- phase timer, timeout, and exit cause;
- player shot cadence/profile and option state;
- observed per-frame HP delta.

Only after native HP-delta parity should a TH08 attack adapter expose a
game-neutral phase-progress utility. The initial physical experiment must
isolate one boss phase and then cross-check another stage.

## Next Architecture

The next useful hierarchy is:

```text
fresh packed issue-time shield
    -> versioned bounded-service background invariant tube
    -> event-complete future hazard model
    -> phase progress / damage among survival-equivalent controls
```

The background planner should be anytime and cancellable. A policy publication
must state its source version, event coverage, delay support, terminal
invariant, and expiry. Fine computation that misses this deadline is not a
better policy.

Uniform full-field refinement should be replaced by query-local or
reachable-tube refinement around a topological ambiguity. The packed native
issue-time shield remains the highest-value C++ boundary because it reduces
both object cost and the observe-to-act invalidation window.
