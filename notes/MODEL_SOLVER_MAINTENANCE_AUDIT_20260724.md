# Model, Solver, Performance, And Maintenance Audit

Status: verified offline maintenance checkpoint. No strategy was promoted and
no physical survival claim is made. Conclusions below are labeled observed,
inferred, or unresolved. New binary inspection used only the connected IDA
Pro database; no REA analysis was used.

## Outcome

Two concrete modeling errors were found and repaired:

1. Exact native laser lifecycle records were correctly free of generic
   horizon drift in the global adapter, but the local MPC still added
   `min(6, 0.08 * step)` to every laser.
2. Both live bullet decoders forced native half extents into `[1, 24]`, even
   though native collision consumes the copied template width/height without
   that clamp. This enlarged very small bullets and shrank bullets wider than
   48 pixels.

The native/NumPy solver recurrence still passes the independent differential
workloads exercised here. The dominant measured global cost remains hazard
clearance construction, not backward viability. The quick unit suite is too
cheap to justify weakening it; expensive replays, multi-resolution solves,
Windows duplication, and physical trials remain explicit research tiers.

## Modeling Audit

| Family | Evidence and current status | Remaining boundary |
| --- | --- | --- |
| Hostile bullet collision size | **Observed in IDA.** `bullet_spawn_from_emission_descriptor` at `0x0042F5F0` copies template dimensions to bullet `+0xD34`. `player_test_bullet_collision_or_cancel` at `0x0044A230` divides those dimensions by two and performs the inclusive AABB test. There is no native minimum or maximum clamp. Both compact and diagnostic decoders now preserve every positive size exactly; a regression covers widths `0.5` and `96`. Reproduction comments were persisted at `0x0042FA12` and `0x0044A284` in the connected IDA database. | A malformed negative snapshot is conservatively normalized by absolute value. Native templates are expected to be positive, but a whole-corpus native dimension distribution has not been retained. |
| Straight bullets | **Observed/inferred.** Current position, velocity, collision dimensions, active state, and transform flags come directly from native pool records. Straight projection and native/scalar AABB clearance agree on retained and generated tests. | Same-frame creation/order and future births still require an event oracle. |
| Stop/resume/redirect/reversal | **Partially observed.** Queue records and native handlers are decoded; callback-12 tagged velocity changes are lowered into time-indexed trajectories. Generated piecewise hazards cover stop, resume, redirect, and reversal above native pool density. | The live planning decoder does not execute every queued transform kind. Unknown transform-bearing bullets use bounded uncertainty rather than exact future activation/expiration. Full same-slot runtime differential coverage is still required before claiming all-card parity. |
| Lasers | **Observed in IDA and runtime traces.** `bullet_manager_update` at `0x00431240` advances head/tail, length clamp, warmup/active/fade transitions, fallthrough, and collision gates. `player_test_collision_and_graze` at `0x0044A6A0` performs the rotated inclusive AABB. The retained differential has 33,230 same-allocation/same-phase pairs: head/tail p99 error zero, origin/angle error zero, and only a few 2.5-pixel phase-boundary outliers. | Future, not-yet-allocated laser births and an unknown-state fallback remain conservative rather than exact. |
| Enemy contact bodies | **Observed.** Exact live geometry, latent contact modes, synchronous prefix capture, and issue-time version recertification are modeled. | CE-0097 remains open: an enemy first allocated after the final observation cannot be recovered from current geometry. ECL/timeline `BirthWindow` lowering is the next semantic requirement. |
| Player movement/input | **Observed locally.** Route-2 movement increments, focus modes, read-lag projection, delay support, and issue-time action certification are executable. | Complete player/input/collision same-frame runtime parity is not yet established for every boundary transition. |
| Player shots and Boss damage | **Observed statically, shadow only operationally.** SHT cadence, option sources, default shot motion/collision, piercing, damage cap, Boss HP/timer/gate fields, and the native damage commit exist as executable pieces. | Predicted per-frame HP delta has not yet demonstrated native shadow parity. Boss-x alignment remains rejected. |

### Exact-laser local correction

`Laser.uncertainty_per_frame` now distinguishes:

- exact `LaserState`: measured base read uncertainty, zero generic horizon
  growth;
- missing lifecycle state: the prior conservative `0.08` local fallback.

The trace schema appends this field and legacy replay reconstructs old
state-backed records with zero growth. On 100 evenly spaced Spell-50 decisions
from retained run `20260724_132007`, exact projection versus the removed local
behavior changed 7 selected actions and 90 full `Decision` values. Median
times were `15.20` and `14.99 ms`, so the old behavior bought no material
performance. Compact evidence is
`artifacts/benchmarks/local_laser_model_audit_20260724.json`; the synthetic
CE-0078 regression remains executable after raw-trace deletion.

## Solver Correctness Audit

### Global plan

**Observed:** 24 deterministic seeds with 2,048 piecewise hazards each, a
48-frame horizon, up to six events per hazard, and a 16-pixel grid all passed
the independent scalar clearance oracle. Maximum absolute error was
`9.835e-7`; native sparse clearance median was `59.76 ms`.

**Observed:** existing Boolean, terminal-mask, max-min safety-value, and fused
survival-label tests retain native/NumPy or native/scalar parity. Splitting the
C++ transition table did not change these results.

**Inferred limitation, not a recurrence bug:** the 16-pixel finite lattice can
still report a false empty set in narrow components (CE-0100), and a complete
8-pixel live recomputation can improve the frozen model while making delivered
policies expire (CE-0102). Query-local/reachable-tube refinement must satisfy
the delivery budget before promotion.

### Local plan and micro-control

**Observed:** the exact-laser uncertainty mismatch was a local-only semantic
bug and is fixed. Local fused/object laser timelines remain action- and
decision-identical on the 80-row retained fusion replay.

**Observed:** first-action delay certificates, fresh hazard intersection,
issue-time enemy recertification, hard collision priority, survival-horizon
priority, boundary clamp aliases, and actuator epoch resets have concrete
counterexample regressions.

**Inferred limitation:** `choose_action` remains a 947-line, 37-argument
boundary with beam, certificate, recovery, terminal, item, and strategy terms
in one function. No additional hard-vector ordering bug was demonstrated in
this audit, but this coupling is a high-risk change surface. The next split
should introduce an immutable local planning request/config and move the pure
search/ranking code out of process I/O orchestration.

## Performance Audit

Deterministic heavy corridor benchmark:

| Component | Warm median |
| --- | ---: |
| Complete solve | `152.97 ms` |
| Hazard clearance | `146.39 ms` |
| Backward viability | `5.24 ms` |

With 1,500 AABBs, 250 segments, 200 trajectory segments, an 80-frame
forecast, and delay support `1..6`, clearance consumes about 96 percent of the
warm solve. Optimizing the Boolean recurrence first would not address the
measured bottleneck.

Retained local replay profiling previously measured about `16.8 ms` per
`choose_action` call. `_robust_action_certificates` and repeated
`_hazards_for_positions` batches are the meaningful Python hot path. Streaming
JSON parsing took `4.85 s` in the offline profile but is not part of live
decision latency.

Static size/complexity before this checkpoint:

- `th08_live_dodge_agent.py`: 6,406 lines; `run` 2,211 lines; `choose_action`
  947 lines and 37 arguments;
- `corridor_planner.py`: 1,512 lines;
- `touhou_control/viability.py`: 1,400 lines;
- `robust_viability_kernel.cpp`: 2,442 lines.

After the first structural split:

- laser trace/projection/packing is a 249-line `th08_laser_runtime.py`;
- the live agent is 6,216 lines;
- the C++ kernel is 2,118 lines and the shared separable transition cache is a
  327-line `robust_transition_table.hpp`.

This is partial decomposition, not a claim that the remaining large functions
are now easy to maintain.

## Repository Structure Decision

The scripts tree now separates roles:

```text
scripts/
  importable models, adapters, and live entry points
  analysis/    differential, dossier, report, regression programs
  benchmarks/  timing and ablation programs
  tools/       explicit build, probe, patch, and capture entry points
  touhou_control/ game-neutral online control and planning
```

Fourteen benchmark programs and eleven analysis/report programs no longer sit
beside runtime models. Imports use packages rather than relying on a benchmark
becoming an accidental production dependency. `AGENTS.md` records this rule.

## Tests And Checks

The final complete Linux suite passed 423 tests in `1.368 s`; the Windows
suite passed the same 423 tests in `2.714 s`. That runtime is not an iteration
bottleneck, so no safety/model/counterexample test was disabled.

The default policy is:

1. one focused discovery pattern while editing;
2. the complete seconds-scale suite before a code checkpoint;
3. expensive raw trace/capsule replay only when its model changes;
4. Windows/native duplication only for platform/native changes or physical
   promotion;
5. physical trials only after offline and delivery gates.

Redundant formatting, CLI-help, schema-plumbing, and private-implementation
tests should not be added without a concrete research or safety failure.

## Artifact Cleanup

**Observed cleanup:** all ignored raw runtime JSONL/PNG/log files, ignored
viability capsules, menu-audit PNGs, stop sentinels, Python caches, and
rebuildable native binaries were deleted after their compact tracked reports
and regression artifacts were verified. The workspace fell from about
`11 GiB` to `74 MiB`; tracked/compact artifacts occupy about `48 MiB`.
`image.png` was explicitly left untouched.

Raw data is not recoverable from Git. Future raw captures are temporary by
default and may remain only for a named active differential.

## Ordered Remaining Work

1. Lower future ECL/timeline bullet, laser, and enemy-body births into a
   game-neutral event window.
2. Establish same-slot transform activation/expiration parity for all
   target-used stop/resume/redirect families before reducing their
   uncertainty.
3. Build exact shot-to-Boss HP-delta shadow parity by Power, focus/options,
   cadence, Boss motion, and damage gate.
4. Extract the pure local request/search/ranking boundary from the live agent,
   then profile packed decode-plus-projection before considering more C++.
5. Prototype only query-local/reachable-tube refinement that meets a measured
   policy delivery SLO.
