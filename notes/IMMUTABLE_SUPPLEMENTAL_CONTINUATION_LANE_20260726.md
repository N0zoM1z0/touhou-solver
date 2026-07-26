# Immutable Supplemental Continuation Lane

Date: 2026-07-26

Status: implemented and offline-validated; default-off proposal/shadow only

## Decision

CE-0129 rejects sharing continuation-biased pruning with the historical local
beam.  The replacement experiment keeps that beam immutable and computes a
second, bounded candidate lane.  The second lane may add a completed endpoint
to final comparison, but it cannot remove, reorder, or consume capacity from
the historical beam.

The experiment is useful only if it increases the coverage of exact
same-query continuation and interior-reserve preferences without worsening:

- the local and terminal hard vector;
- the fresh issue-prefix certificate;
- membership in the effective global/fresh action set; or
- the historical route-gate deficit.

The lane is proposal generation, not a new safety proof.  Its final admission
filter is the authoritative part of this experiment.

## Physical Problem Contract

### Objective

The physical objective remains hard no-Bomb survival.  At a root for which the
current global query has a complete, nonrelaxed viable action set, retain the
historical local decision as an incumbent and search for an endpoint with more
worst-delay continuation volume or more reversible boundary reserve.

### State and observations

The experiment uses only data already available for the same local decision:

- immutable policy version and exact-root viable-action query;
- the effective global/fresh action set and complete per-action repair volume;
- the observed player and input state;
- the same bullet, laser, and enemy-body projections;
- the same delay support, route target, target deadline, and local horizon;
- the same local and issue-prefix certificates.

It may not use a later replay row, later hit, hidden RNG result, future policy
publication, or an observation that arrives after issue.

### Actions and write semantics

The physical action alphabet, focus masks, hard no-Bomb rule, and actuator
write/no-write semantics are unchanged.  At step one both lanes are restricted
to the same effective global/fresh action set.  A supplemental endpoint cannot
introduce an action that the historical root was not permitted to issue.

The experiment activates only when:

1. it is explicitly enabled with a positive supplemental width;
2. the original global action set is nonempty;
3. the effective set is nonempty and neither globally nor fresh-prefix
   relaxed; and
4. every effective action has a repair-volume value from the same query.

Otherwise the historical algorithm is authoritative.

### Uncertainty and transition

Both lanes use identical clamped player dynamics, hazard frames, local
uncertainty, delay-prefix data, and terminal rollout.  The second lane changes
only finite-beam proposal order.  It does not add recursive cadence,
active/held/pending input histories, future births, transform events missing
from the supplied projection, or frozen-manager-clock histories.

### Horizon and resources

The historical beam width and local/terminal horizons are immutable.  The
supplemental width is a separate bounded resource.  It cannot borrow slots
from the historical beam.  Lives, Bombs, Power, damage, phase time, and route
resources retain their existing meanings and are not converted into a scalar
safety weight.

### Safety invariants

- The disabled path is behaviorally identical to the historical planner.
- Every historical beam survivor remains available to historical final
  selection.
- A supplemental endpoint must use an effective globally allowed first
  action.
- Local collision count, local negative signed clearance, terminal collision
  count, terminal negative signed clearance, issue-prefix collision count, and
  issue-prefix negative signed clearance are all componentwise no worse than
  the historical incumbent.
- The endpoint's route-gate deficit is no greater than the historical
  incumbent's deficit.
- A supplemental action is selected only for a strict lexicographic
  improvement in exact repair volume and then boundary reserve.
- Fresh issue-time recertification remains mandatory.
- No path may emit Bomb.

Componentwise hard nonregression is deliberately stricter than merely
comparing one aggregate or a lexicographic hard tuple.  It forbids trading an
extra collision in one horizon for clearance in another.

### Computation, publication, deadline, and fallback

The historical lane runs first logically and uses the unchanged native
reducer.  Supplemental drafts may share one batch hazard query because the
per-position geometry contract is batch-invariant, but they have an
independent reducer and width.  Batch sharing must have exact disabled-path
and isolated-query parity.

The supplemental lane is default-off and must expose its own timing,
candidate count, selected source, and historical incumbent.  An exception,
missing repair value, relaxation, deadline miss, unsupported reducer, or
failed admission filter returns the historical decision.  Live publication
must not wait for optional shadow work; before any action authority, the lane
must either fit an explicit synchronous budget or move to a cancellable
side-effect-free service whose miss is lookup-only fallback.

## Supplemental Proposal Order

The lane preserves the historical local and issue-prefix hard columns.  It
then prioritizes:

1. route-gate deficit;
2. exact same-query repair volume, descending;
3. delay-scaled boundary reserve deficit;
4. the remaining historical soft order.

This order is intentionally heuristic.  Repair volume is not an admissible
bound on terminal threat, as CE-0129 proves.  The immutable incumbent and
post-terminal admission filter contain that unknown-direction approximation.

## Proof-Backed Pruning Boundary

Three filters are safe relative to the declared finite comparison:

1. **Exact action-set pruning:** a first action outside the effective
   global/fresh set cannot be emitted.
2. **Final hard dominance:** a candidate worse in any declared hard component
   cannot satisfy the nonregression contract.
3. **Final route dominance:** after hard nonregression, a candidate with
   greater route-gate deficit cannot satisfy the route contract.

These filters never claim that an omitted proposal was globally optimal.
Width truncation, quantized state merging, repair ordering, and reserve
ordering remain unknown-direction proposal heuristics.

Hazard pruning has a separate proof obligation.  A hazard may be removed only
when conservative space-time bounds show that it cannot change collision,
signed clearance, or risk for any queried position.  The existing native
local kernel already uses hazard-batch and hazard-position AABB rejection with
the complete collision/uncertainty/risk radius.  A new spatial index is
accepted only if unindexed parity holds on live-like, off-tube, boundary,
laser, and transform-adversarial workloads and its measured end-to-end cost is
lower.

## Five Formal Review Questions

### 1. Which physical histories map to one model state?

The lanes merge exactly the histories already merged by the local planner and
global query: policy version, projected global root, observed continuous
player state, estimator state used by the current caller, and supplied hazard
snapshot.  Subcell global state, unresolved input-pipeline histories, future
births, and semantic clock freezes are not proved control-equivalent.  The
experiment therefore remains finite-model proposal logic.

### 2. Are all declared uncertainty branches causal?

Both lanes see the same already-expanded local hazard and delay data.  The root
action is selected before any modeled branch.  No future replay information is
used.  The experiment does not repair omitted recursive cadence or hidden
pipeline branches, so it inherits that model boundary.

### 3. What does an exact solve answer?

Even an exhaustive supplemental lane would answer only which endpoint is best
under the current finite local rollout, terminal constant-action warning,
global repair-volume proxy, and route target.  It would not establish
unrestricted physical survival or globally optimal control.

### 4. What is solved or bounded, and what falsifies it?

The historical beam is reproduced exactly.  The supplemental lane is bounded
proposal search.  Final action-set, hard-component, and route nonregression
checks are exact for their supplied values.  The claim is falsified by:

- any disabled-path or historical-incumbent mismatch;
- any selected action outside the effective global/fresh set;
- any selected hard component or route deficit worse than the incumbent;
- Python/native supplemental reducer mismatch;
- any batch-composition hazard mismatch;
- a material local-plan or authoritative-policy delivery regression; or
- a retained physical hit whose causal witness shows the new action violated
  one of these contracts.

### 5. Can it be consumed before issue without changing the problem?

That is not yet established.  The lane must report geometry, reduction,
terminal, and total timing separately on Linux and Windows.  Replay timing is
not a Windows issue deadline.  Before live authority it must pass direct-root
observe/decode/project/certify/issue measurement and show that optional work
does not age the authoritative global publication.

## Intensive Differential Workloads

The offline gate must combine retained TH08 roots with generated workloads
that are denser than the native pools:

- 256 through 4,096 AABBs with straight, stop, resume, redirect, and reversal
  events;
- boundary-clamped and near-tangent player positions;
- dense bullet fields with transformed uncertainty;
- packed laser storms, degenerate segments, long crossing segments, growing
  radii, and fully off-tube segments;
- mixed bullet/laser/body fields;
- repeated exact positions embedded in different companion batches;
- narrow gates whose clearances lie near zero; and
- lane widths and action orders chosen to force quantized collisions.

For geometry, the NumPy/scalar implementation is the independent oracle.
Required results are exact collision parity, exact clearance-sign parity,
bounded numeric difference, and selected-action/hard-label parity.  For the
lane, a width-unbounded tiny-state enumeration and the historical disabled
path are independent references.  Failing generated cases are shrunk and
retained as counterexamples.

## Promotion Sequence

1. implement the default-off lane and telemetry;
2. add deterministic unit and generated adversarial differentials;
3. run fixed-reservoir Hard broad and pre-hit same-root replays;
4. measure lane-width coverage and latency, including concurrent planner
   contention;
5. keep or reject the proposal from hard/route parity and effect size;
6. run Linux and Windows quick suites;
7. only after a favorable direct-root Windows gate, consider a focused,
   repeated Hard physical A/B.

Same-root replay measures proposal quality, not prevented hits.  RNG-distinct
physical totals alone are not causal evidence.

## First Offline Result

### Retained Hard replay

**Observed:** the historical beam and reducer remain unchanged.  The
supplemental lane has a separate native export and a Python oracle.  Across
128 randomized direct reducer differentials and end-to-end randomized local
decisions, retained indices and decisions matched exactly.

**Observed:** fixed-reservoir replay over complete Hard Route-2 `184942` and
Stage-4A `202439/211210/212756` produced:

| Cohort/variant | Action changes | Repair improvements | Equal-repair reserve improvements | Historical mismatch | Hard/route/global violations | Supplemental median/p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| broad final-only | 8/800 | 1 | 7 | 0 | `0/0/0` | `0/0 ms` |
| broad width 4 | 286/800 | 273 | 13 | 0 | `0/0/0` | `2.449/3.114 ms` |
| broad width 8 | 288/800 | 276 | 12 | 0 | `0/0/0` | `3.147/4.119 ms` |
| broad width 12 | 296/800 | 280 | 16 | 0 | `0/0/0` | `3.828/4.842 ms` |
| pre-hit-300 final-only | 13/800 | 3 | 10 | 0 | `0/0/0` | `0/0 ms` |
| pre-hit-300 width 4 | 341/800 | 323 | 18 | 0 | `0/0/0` | `2.425/3.026 ms` |
| pre-hit-300 width 8 | 350/800 | 335 | 15 | 0 | `0/0/0` | `3.125/3.816 ms` |
| pre-hit-300 width 12 | 364/800 | 348 | 16 | 0 | `0/0/0` | `3.816/4.593 ms` |

The hard check includes issue-prefix collision/negative clearance, local beam
collision/negative clearance, and terminal collision/negative clearance as
separate componentwise constraints.  Every active proposal stayed inside the
effective global set.  There were zero supplemental exceptions and zero
continuation-contract violations.

Historical versus width-4 total replay time was `6.461/9.546` versus
`9.115/12.156 ms` median/p95 on the broad cohort and `6.749/10.038` versus
`9.429/12.663 ms` near hits.  Width 8 and 12 buy only 2 and 10 additional
broad action changes, or 9 and 23 pre-hit changes, while paying a larger tail.
**Inference:** width 4 is the current Pareto candidate.  This is still
same-root evidence, not prevented-hit evidence.

The route nonregression filter also removes the one route-deficit regression
in the older final-only experiment.  The final-only changed-action count is
now 8 broad and 13 pre-hit rather than the earlier 7 and 13 because admission
is expressed relative to the exact historical incumbent after its current
issue-prefix override.

Retained artifacts:

- `artifacts/benchmarks/hard_supplemental_continuation_lane_broad_20260726.json`;
- `artifacts/benchmarks/hard_supplemental_continuation_lane_prehit300_20260726.json`.

### Generated intensive geometry

**Observed:** a deterministic TH08-semantic corpus now covers:

- 1,536-bullet/256-laser native-pool loads;
- a clustered reachable-tube batch at the same pool load;
- 4,096 piecewise stop/resume/reverse/redirect transformed bullets plus 512
  lasers;
- 4,096 bullets and 1,024 lasers fully outside the queried tube;
- 2,048 near-tangent boundary bullets; and
- 2,048 degenerate/crossing lasers.

Executable laser lifecycles, transformed uncertainty, enemy bodies, batch
composition, and end-to-end Python/native selection are inside the gate.
All six workloads had exact collision parity, exact clearance-sign parity,
zero batch-invariance mismatches, and equal end-to-end action/hard labels.
Maximum absolute clearance difference was below `3.32e-5`.  Risk accumulation
differs by floating-point order, with maximum absolute difference `0.213`;
its error direction remains unknown and it receives no hard authority.

Ten already-lowered native queries measured:

| Workload | Median/p95 |
| --- | ---: |
| native-pool, full-field positions | `27.178/27.942 ms` |
| native-pool, clustered reachable tube | `9.512/9.975 ms` |
| 4,096/512 beyond-pool transformed | `108.711/112.989 ms` |
| 4,096/1,024 fully off-tube | `2.211/2.408 ms` |
| boundary near-tangent | `13.739/15.033 ms` |
| 2,048 degenerate/crossing lasers | `66.333/85.595 ms` |

The off-tube result is direct evidence that the existing conservative
hazard-batch and hazard-position AABB pruning works.  The dense crossing
cases show the expected quadratic tail when most hazards are genuinely
relevant.  **Decision:** do not add a viewport crop, present-velocity cone, or
new per-decision spatial index at this checkpoint.  Actual retained local
queries are clustered and geometry was already about 1--2 ms outside
contention; a new index must first beat construction cost on that workload.

Retained artifact:
`artifacts/benchmarks/th08_local_intensive_cases_20260726.json`.

### Authority decision

The implementation remains default-off and has no live CLI switch.  Width 4
is the only candidate worth a direct-root Windows shadow/contention gate.
Its approximately 2.4-ms synchronous median cost is not yet permission to
delay authoritative publication.  A physical A/B is deferred until the
complete observe/decode/project/certify/issue boundary and background
four-worker contention show that this optional lane fits without increasing
policy age or issue misses.

### Reproducibility and validation

Artifact SHA-256:

- broad replay:
  `28072dd8589bb3abcb8aa382443f93d6bd693f59194b62b5d8d7e495210b8a84`;
- pre-hit-300 replay:
  `8f336702b0d4f4ed5f798bb845be3c537d9352068204d2bb7a8ae84432500c38`;
- intensive geometry:
  `2e654aa456bfb9bbb1abee41d565950ab7a86c63f7ab45de05f0818672409d54`.

The complete quick suite passes `583/583` on Linux in `5.158 s` and Windows
in `7.979 s`.  The Windows run used the verified UNC loader from
`START_HERE.md`.  Native build output remains ignored and is not retained as
evidence.

Reproduce the retained reservoirs from the four trace paths recorded inside
each artifact:

```bash
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_supplemental_continuation_lane.py \
  artifacts/runtime_reports/hard_route2_fullrun_unattended_20260726_184942.jsonl \
  artifacts/runtime_reports/hard_route2_stage4a_unattended_20260726_202439.jsonl \
  artifacts/runtime_reports/hard_route2_stage4a_unattended_20260726_211210.jsonl \
  artifacts/runtime_reports/hard_route2_stage4a_unattended_20260726_212756.jsonl \
  --output artifacts/benchmarks/hard_supplemental_continuation_lane_broad_20260726.json \
  --samples 800 --widths 4,8,12 --backend native

PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_supplemental_continuation_lane.py \
  artifacts/runtime_reports/hard_route2_fullrun_unattended_20260726_184942.jsonl \
  artifacts/runtime_reports/hard_route2_stage4a_unattended_20260726_202439.jsonl \
  artifacts/runtime_reports/hard_route2_stage4a_unattended_20260726_211210.jsonl \
  artifacts/runtime_reports/hard_route2_stage4a_unattended_20260726_212756.jsonl \
  --output artifacts/benchmarks/hard_supplemental_continuation_lane_prehit300_20260726.json \
  --samples 800 --prehit-window 300 --widths 4,8,12 --backend native

PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_th08_local_intensive_cases.py \
  artifacts/benchmarks/th08_local_intensive_cases_20260726.json
```
