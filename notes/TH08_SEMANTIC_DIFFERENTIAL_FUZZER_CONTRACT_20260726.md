# TH08 Semantic Differential Fuzzer Contract

Date: 2026-07-26

Status: implemented; gate and research profiles pass, offline evidence only

## Purpose

Build a deterministic, replayable, shrinkable TH08-like workload generator and
differential runner.  It must cover far more density and mechanic combinations
than a small collection of hand-written benchmarks while preserving two
independent evidence chains:

1. scalar/NumPy semantics versus optimized packed/native geometry; and
2. Python supplemental recurrence versus the complete native recurrence.

Generated agreement proves implementation parity over the sampled finite
semantics.  It does not prove that the semantics match every shipped-game
behavior or that any planner is physically safe.

## Generated Case Contract

Every case has a stable schema version, seed, case index, family, difficulty
tier and content digest.  It serializes enough data to replay without the
generator:

- player position, previous direction/focus, action/delay/hold/horizon/width
  parameters, target and reserve parameters;
- allowed root actions and complete per-action certificate, survival, safety,
  recovery and repair attributes;
- bullets with geometry, kinematics and piecewise stop, resume, redirect and
  reversal events;
- lasers including active intervals, moving/rotating/growing segments,
  degenerate zero-length cases and uncertainty;
- moving enemy bodies; and
- explicit tangent/boundary perturbations used to exercise signed clearance.

TH08-native-pool-like density is one tier, not a ceiling.  Research tiers span
empty/sparse fields through 4,096 bullets and 2,048 lasers, mixed hazards,
off-tube distractors, duplicate positions, narrow gates, quantized beam
aliases, and float32 near-zero clearances.  Difficulty changes distributions
and density only; it never changes the oracle.

The required families are aimed fans, radial rings, spirals, wave/lanes,
walls, crossfire, random clouds, boundary/tangent traps, laser storms,
transform-adversarial fields, off-tube broadphase fields, and mixed phases.
Case selection is deterministic from `(schema, seed, index, profile)`.

## Oracles And Comparisons

- The independent Python scalar/NumPy hazard implementation is retained.
  Native code may not generate its own expected values.
- Frame projection/lowering is compared at semantic boundaries before packed
  hazard evaluation.
- Collision counts are exact.  Signed-clearance sign must agree; finite
  clearance and risk use explicit absolute/relative tolerances.  Infinite
  empty-field clearance must agree.
- Batch invariance embeds the same queried point in different companion
  batches.
- Pure-Python supplemental, Python with native reducer, and complete-native
  supplemental endpoints are compared in order and final-decision fields.
- Small cases additionally exercise existing independent scalar pipeline
  certificate oracles where their state size is bounded.

A differential mismatch, exception, NaN, out-of-range result, nondeterministic
replay, or deadline/cancellation partial publication is a failure.  Performance
budgets are reported separately and never suppress correctness failures.

## Shrinking And Retention

On failure, deterministic delta debugging first removes hazard chunks by type,
then removes transform events, reduces horizon/hold/width/action sets, and
simplifies numeric values toward boundaries, zero, axes and tangent contact.
Each simplification is accepted only when the same named predicate still
fails.  The runner writes:

- the original replay capsule;
- the smallest capsule reached within the shrink budget;
- predicate, expected/actual values and first divergent step;
- seed/profile/tool versions; and
- phase timing.

The shrunk capsule becomes an executable regression and is recorded in
`notes/COUNTEREXAMPLES.md`.  Passing bulk corpora are summarized in compact
tracked JSON; large generated/raw corpora and native builds remain ignored.

## Profiles And Performance Boundaries

- `quick`: deterministic small cases suitable for the seconds-scale test
  suite.
- `gate`: hundreds to thousands of cases spanning all families and native
  pool density.
- `research`: explicitly requested high-density and beyond-pool stress.

Report generation, projection/lowering, packing, scalar geometry, native
geometry, Python recurrence and full-native recurrence separately.  Also
report hazard count, queried position count, horizon, throughput, p50/p95/max
and peak resident memory where available.  Results from different workload
identities are not pooled into one performance claim.

The initial correctness gate is zero mismatches for every completed case.
Timeout stress is its own predicate: it must publish no partial answer and
must not be counted as a correctness pass.  A performance regression cannot
be hidden by reducing generated density after results are observed.

## Five Formal Review Questions

1. **Which histories merge?**  A generated case is one explicit finite
   snapshot and event schedule.  Histories absent from that capsule are not
   asserted control-equivalent.  Cases vary hidden-looking histories rather
   than merging them inside an oracle.
2. **Is the recurrence causal?**  The supplemental oracle uses only the
   projected frames serialized in the case and selects before later modeled
   hazards.  Generator knowledge is never exposed to only one implementation.
3. **What does an exact solve answer?**  It answers geometry and bounded
   supplemental parity for the generated finite TH08-like semantics, not
   shipped-game completeness or physical survival.
4. **What is solved or bounded?**  Scalar geometry is an independent oracle;
   bounded supplemental search is compared exactly between implementations.
   Width/quantization remain proposal approximations.  A serialized smallest
   counterexample falsifies a parity claim.
5. **Can it be consumed before issue?**  This harness is offline and grants no
   publication authority.  Its phase timings inform delivery engineering, but
   only the fixed Windows direct-root gate measures current-issue suitability.

## Implemented Harness And Observed Evidence

`scripts/th08_semantic_cases.py` implements the versioned generator, complete
JSON replay capsule, digest check and deterministic reducer.  It generates all
twelve required families at Normal, Hard, Lunatic and beyond-pool tiers.
`scripts/analysis/th08_semantic_differential.py` separately measures
projection/lowering, NumPy geometry, native geometry, Python supplemental
recurrence and complete-native supplemental recurrence.  A real mismatch
writes original and minimized capsules under
`artifacts/counterexamples/th08_semantic/`.

The first gate exposed only an overstrict report tolerance: discrete results,
collision counts, clearance signs, endpoint order and decisions agreed, while
float32-packed body clearance differed by at most roughly `3e-5`.  The
comparison now keeps exact discrete/sign checks and explicit
`rtol/atol` bounds for finite soft values.  No failing capsule was retained
because this was not a model or implementation counterexample.

**Observed gate profile:** 256 cases covered 87,534 bullets, 4,385 lasers and
730 bodies.
Collision, clearance sign/value, risk, batch invariance and supplemental
endpoint mismatch counts were all zero.  NumPy/native geometry p95 was
`9.264/3.079 ms`; Python/native supplemental p95 was
`3.787/1.131 ms`.

**Observed research profile:** 96 higher-intensity cases covered 99,858
bullets, 19,816 lasers and 1,383 bodies.  Individual maxima were 3,900
bullets, 1,387 lasers, 62 bodies and horizon 24.  Every mismatch count
remained zero.  NumPy/native geometry p95 was `121.538/40.500 ms`;
Python/native supplemental p95 was `9.931/3.337 ms`.  Native supplemental
maximum was `19.341 ms` on
`research:0000000000ce0133:91:boundary_tangent:beyond_pool`, with 3,090
bullets, 89 lasers, 62 bodies and horizon 15; this tail is retained rather
than hidden by the aggregate p95.

These are generated finite-semantics parity and performance observations, not
proof of shipped ECL completeness or physical survival.  Compact artifacts:

- `artifacts/benchmarks/th08_semantic_differential_gate_20260726.json`
  (SHA-256
  `9604b098171a295a71f10f44dfea019771cb2e75d1cb385952abf2cb6125e207`);
- `artifacts/benchmarks/th08_semantic_differential_research_20260726.json`
  (SHA-256
  `b53090113945ddb0b7853da5052b840872546a679cc40a92ffcc60c7007e5744`).

Reproduction:

```bash
PYTHONPATH=scripts python3 scripts/analysis/th08_semantic_differential.py \
  --profile gate --seed 0xce0132 --count 256 \
  --output artifacts/benchmarks/th08_semantic_differential_gate_20260726.json
PYTHONPATH=scripts python3 scripts/analysis/th08_semantic_differential.py \
  --profile research --seed 0xce0133 --count 96 \
  --output artifacts/benchmarks/th08_semantic_differential_research_20260726.json
```
