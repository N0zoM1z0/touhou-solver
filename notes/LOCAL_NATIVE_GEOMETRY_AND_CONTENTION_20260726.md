# Local Native Geometry And Planner Contention

Date: 2026-07-26

Status: the hazard-major native query, cached packed-laser native fields, and
four-worker authoritative viability default are accepted implementation
choices. They do not enlarge either the local certificate's or the global
Boolean policy's model authority.

## Problem Contract

### Physical objective

Reduce synchronous observe-to-issue work while preserving the exact local
collision/certification proxy, and preserve authoritative corridor-policy
freshness when local issue work and background viability overlap. Survival
and hard no-Bomb remain the physical constraints. Geometry throughput is not
allowed to take priority over delivery of a fresh global plan.

### State, observations, actions, and transition

The local geometry kernel receives only observations already available at the
decision: candidate positions, projected bullet arrays, one packed laser
frame, enemy-body AABBs, player radius, and rollout step. It chooses and
issues no action. Bullet, laser, body, pickup-delay, cadence, active/held/
pending, and movement transitions remain unchanged.

The asynchronous corridor solver receives the same immutable snapshot and
finite robust-control problem as before. A thread-local native worker limit
changes only how many CPU workers execute the existing backward recurrence.
The live default is four workers at normal priority, which is the former
automatic maximum. Limits one through three remain explicit performance
ablations.

### Uncertainty, horizon, resources, and fallback

All existing transformed-bullet, laser-growth, body, delay, cadence, lattice
sampling, horizon, and clearance terms are preserved. The Python/NumPy local
query remains an explicit rollback and independent implementation oracle.
The worker-limit symbol is optional at the wrapper boundary; the live build
records whether the requested limit was actually applied.

No Bomb, item, Power, damage, or score authority is added. A missing native
hazard or beam symbol fails configuration before armed gameplay; it does not
silently replace a hard result.

## Five Formal Questions

1. **Which physical histories merge?** None are newly merged. Hazard-major
   iteration reorders arithmetic over the same candidate/hazard pairs.
   Candidate positions and hazard identities remain distinct. The native
   worker cap partitions independent lattice states inside one already
   declared recurrence.
2. **Are uncertainty branches and causality preserved?** Yes at these
   implementation boundaries. The local kernel evaluates the same supplied
   uncertainty-expanded hazards. The viability recurrence and its
   controller-exists/nature-for-all quantifiers are unchanged. This does not
   repair the open active/held/pending or frozen-manager semantics.
3. **Does exact computation answer the physical decision?** No. It exactly
   implements the current finite local proxy and finite Boolean recurrence.
   Future births, observation validity, recurrence completeness, and physical
   survival remain separate claims.
4. **What is solved and what falsifies it?** Exact collision counts,
   clearance signs, selected actions, and hard labels must match independent
   Python/NumPy and retained-root replays. A mismatch, native error, new
   deadline miss, or planner-age regression falsifies promotion. Risk and
   score accumulation use a different floating-point order; their error
   direction is unknown, so retained decisions and hard labels are checked
   explicitly.
5. **Can the result arrive before issue?** Windows retained-root timing
   establishes lower local cost for the sampled workloads. Interleaved
   contention timing establishes the worker-throughput tradeoff, but only a
   physical run measures the complete scheduler, process-read, decode,
   publication, and issue boundary.

## Observed Bottleneck

Complete Stage-6B trace `165841` contained laser-heavy decisions with more
than 200 active laser records. At frame 22030, 111 bullets, 210 lasers, five
bodies, 81 delay branches, and ten certificate steps produced:

- `67.119 ms` certificate geometry;
- `95.883 ms` local planning; and
- `110.549 ms` observe-to-input.

Other decisions in the same region reached roughly 40--66 ms certificate
geometry. The serialized laser frames contained about the same number of
packed segments as native records; there was no hidden segment explosion.

A same-size native certificate workload outside gameplay required only about
1--2 ms per ten-query sequence. Therefore the large physical tail is
**inferred** to be mostly scheduler/background-solver contention rather than
irreducible segment-distance cost. This inference does not assign every
outlier to one thread and requires a post-change physical trace.

## Geometry Implementation

The native query now iterates hazard-major:

- compute each laser's uncertainty, endpoint, occupied AABB, and squared
  length once;
- reject a hazard once against the complete candidate-position AABB;
- then evaluate only locally relevant candidate positions;
- apply the same structure to bullets and bodies; and
- reuse float32 packed-laser fields prepared at frame construction instead of
  recasting them on every local query.

Candidate output order, collision counting, per-hazard risk accumulation
order for each candidate, robust-clearance minimum, and local relevance
margins remain unchanged.

Windows synthetic median results for ten steps:

| Workload | Position-major | Hazard-major |
| --- | ---: | ---: |
| 81 positions, 111 bullets, 210 lasers, 5 bodies | 1.736 ms | 1.212 ms |
| 240 positions, 600 bullets, 210 lasers, 5 bodies | 21.858 ms | 14.172 ms |
| 81 positions, 111 bullets, 240 distant lasers, 5 bodies | 1.511 ms | 0.904 ms |

Collision and clearance-sign parity were exact. Absolute risk differences
were at most `0.0267` in these workloads and arise from float accumulation.

On 64 direct roots from each of Stage 4A `160712` and Stage 6B `165841`,
native versus NumPy produced zero action mismatches and zero hard-label
mismatches. Stage-6B certificate geometry changed from `2.210/4.903 ms` to
`1.337/2.304 ms` median/p95; complete local planning changed from
`14.441/23.110 ms` to `12.540/17.223 ms`. The largest hard-clearance
difference was below `1.8e-5`.

## Planner-First Contention Decision

The Windows contention benchmark alternated order across four rounds. Each
variant timed 120 certificate and 120 beam geometry sequences while a
representative `81 x 27 x 24`, 17-action native viability solve ran
continuously on a separate normal-priority Python thread.

| Native viability workers | Plan solve median/p95 | Beam geometry p95 |
| ---: | ---: | ---: |
| 1 | 40.716 / 57.090 ms | 15.920 ms |
| 2 | 36.070 / 43.880 ms | 18.882 ms |
| 4 | 26.953 / 29.821 ms | 17.282 ms |

Four workers approximately halve plan p95 relative to one worker. Its beam
geometry p95 is about 8.5% above one worker, a cost explicitly accepted to
prioritize authoritative plan freshness. The live default is therefore four
workers at normal priority. The local issue thread remains uncapped for its
own native calls.

## Advanced Geometry Decision

Uniform grids, BVHs, sweep structures, and segment trees are useful when a
large mostly-static hazard set serves many spatial queries. The current TH08
local workload is different:

- the laser endpoints and uncertainty volume are rebuilt per projected frame;
- the candidate set is small for the exact certificate and moderate for the
  beam;
- the adopted candidate-AABB broad phase already rejects globally irrelevant
  hazards;
- building and invalidating a per-frame spatial index adds work on the issue
  path; and
- the exact certificate kernel is already near 1--2 ms without contention.

Consequently, a dynamic grid/BVH is **deferred**, not declared impossible.
It becomes useful only if a retained physical trace shows geometry itself,
outside planner contention and decode/read work, still dominating. Any such
index must preserve complete viable-state and safe-action-mask parity; an
occupancy-only lattice is not an acceptable replacement for signed
clearance.

Compiler vectorization and a wider SoA/SIMD kernel remain hypotheses for the
larger beam workload. They are lower priority than plan freshness and require
the same hard-label and retained-root gates.

## Retained Evidence

- `artifacts/benchmarks/local_hazard_geometry_windows_before_loop_20260726.json`
- `artifacts/benchmarks/local_hazard_geometry_windows_hazard_major_20260726.json`
- `artifacts/benchmarks/local_native_hazard_hazard_major_windows_20260726.json`
- `artifacts/benchmarks/local_issue_contention_windows_20260726.json`
- `scripts/benchmarks/local_hazard_geometry_benchmark.py`
- `scripts/benchmarks/local_issue_contention_benchmark.py`
