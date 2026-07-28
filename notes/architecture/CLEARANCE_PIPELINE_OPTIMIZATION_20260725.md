# Clearance Pipeline Optimization

Status: active implementation checkpoint. This note separates observed
measurements, inferred causes, proposed changes, and acceptance gates. It does
not claim physical promotion.

## Why The Earlier 96 Percent Result Needs Qualification

**Observed:** the retained heavy benchmark with 1,500 moving AABBs, 250
static segments, 200 segment trajectories, 81 physical frames, and a
24-by-27 lattice reproduced at:

| Phase | Warm median |
| --- | ---: |
| Complete solve | 148.35 ms |
| Clearance | 140.57 ms |
| Viability | 5.97 ms |

The clearance phase decomposed to approximately 24--28 ms for the moving
AABBs, 86--93 ms for the 250 static segments, and 28--36 ms for the 200
segment trajectories.

**Observed benchmark boundary:** the TH08 live adapter lowers every decoded
laser, including the missing-state fallback, to
`SegmentTrajectoryHazard`. It does not supply the static-segment input used by
the 250-segment stress component. The stress generator also makes its static
and trajectory segments geometrically overlap, so applying the trajectory
pass after the static pass changed almost no cells. The benchmark is a useful
game-neutral kernel stress test, but its 96-percent phase share and internal
mix are not a live TH08 cost attribution.

A closer synthetic live workload with 800 moving AABBs, 200 segment
trajectories, no static segments, the same horizon/lattice, and delay support
1--6 measured about 53--63 ms for clearance and 68--78 ms for the complete
pre-lowered solve. Retained native runs contain 200--230 simultaneous lasers,
so the trajectory path remains a real live bottleneck.

## Observed Causes

### Static segments

The static kernel evaluates every physical frame, lattice state, and segment:
`O(frame_count * state_count * segment_count)`. It calls `std::hypot` even
when a segment is too far away to improve the configured clearance cap.
Runtime is linear in segment count, horizon, and lattice state count, and was
effectively unchanged when the cap moved from 12 to 96 pixels.

### Segment trajectories

The trajectory kernel already has a segment bounding-box broad phase, but
every retained candidate cell still calls `std::hypot`. On a generated
200-trajectory workload, only about 7.2 percent of bounding-box cells could
improve a cap-initialized volume. With a dense AABB volume already applied,
the improvable fraction was smaller.

The Python boundary also materializes the same geometry twice:

1. `lower_lasers` creates one `SegmentHazard` object for every active
   laser/frame collision sample and groups them by trajectory;
2. `apply_segment_trajectory_clearance` scans those objects frame-by-frame and
   reads eight attributes into eight new NumPy arrays.

For 200 generated trajectories this represented 15,248 samples and about
122,000 Python attribute reads. Collection plus structure-of-arrays packing
cost about 9.6 ms before the native call. A retained 215-laser lifecycle
projection previously measured 41.35 ms warm before this backend repacking.

## Ordered Changes

1. Add a conservative squared-distance rejection before `std::hypot` in the
   trajectory kernel. The original `std::hypot` remains authoritative for
   every candidate that can improve a cell.
2. Add a game-neutral, frame-major packed segment batch. TH08 laser lowering
   writes this contract directly; the native boundary consumes it without
   rebuilding Python hazard objects.
3. Keep separate benchmark identities:
   - TH08 live-like moving AABBs plus segment trajectories;
   - game-neutral static-segment stress;
   - piecewise stop/resume/redirect/reversal adversarial workloads.
4. Traverse static segments segment-major inside an exact cap-expanded
   bounding box.
5. Evaluate, initially outside live authority, a Boolean occupancy volume for
   viability plus exact clearance only at representative rollout queries.

## Acceptance Gates

- Optimized native output must be bit-identical to the old native output where
  promised, and must retain scalar-oracle tolerance on deterministic
  adversarial workloads.
- Packed and object segment paths must produce identical clearance volumes,
  robust policies, representative paths, and capsule replay results.
- Stop, resume, redirect, reversal, lifecycle warning/active/fade, disabled
  collision frames, and zero-length segments remain covered.
- Linux and Windows native builds and the complete quick suite must pass.
- Performance claims must state hazard mix, frame count, lattice size, cap,
  warm/cold treatment, and whether lowering/packing is included.
- Boolean/query-local work remains shadow-only until full-policy parity is
  demonstrated across reachable, empty, repair, gate, and retained capsule
  cases.

## Checkpoint 1: Trajectory Distance Prefilter

**Implemented:** the segment-trajectory kernel now computes projected squared
distance first. If the squared distance is conservatively beyond the distance
that could improve the cell's current clearance, it skips `std::hypot`.
Candidates inside a floating-point rounding guard still execute the original
`std::hypot` calculation, so the optimized path does not substitute a
different reported distance.

**Observed old/new native differential:**

- 500 deterministic randomized workloads: maximum error zero, zero changed
  float cells, and zero clearance-sign changes;
- generated live-like 800-AABB/200-trajectory input: bit-identical output;
- raw trajectory native median: `21.92 -> 6.25 ms`, about 3.5 times faster;
- complete Linux quick suite: 423 tests in 1.328 seconds.

This is offline and synthetic acceptance. It is not physical promotion.

## Checkpoint 2: Packed Frame-Major Laser Contract

**Implemented:** `PackedSegmentFrames` is a game-neutral structure-of-arrays
contract with one monotone `int32` offset table and eight contiguous
`float32` geometry arrays. `lower_lasers_packed` writes samples directly in
frame-major order. The live TH08 lowering boundary now returns this batch
instead of creating `SegmentHazard` and `SegmentTrajectoryHazard` objects;
the object route remains only as a reference/compatibility input. Both routes
enter the same native C ABI.

Audit capsules use schema v2 when a packed batch is present and preserve the
arrays without converting them back to objects. The reader still accepts
schema v1 capsules. Offline differential and adaptive replay tools pass the
packed batch through to the planner.

**Observed parity and timing:**

- exact frame-offset and float32-array equality between direct packed
  lowering and the object reference across missing-state and lifecycle
  warning/active/fade inputs;
- bit-identical native clearance volumes for object and packed entry paths;
- a generated 215-laser, 81-frame active-lifecycle workload contained 17,415
  samples. Warm medians were 26.43 ms for object lowering plus 14.13 ms for
  repacking (40.47 ms combined), versus 16.67 ms for direct packed lowering;
- the complete Linux quick suite passes 432 tests in 1.227 seconds.

The timing is a generated lifecycle workload, not a retained physical trace.

## Checkpoint 3: Workload Split And Static-Segment Broad Phase

The former mixed benchmark was removed. It is replaced by three explicit
workload identities under `scripts/benchmarks/`:

- `benchmark_clearance_live_like.py`: pre-lowered moving AABBs plus packed
  frame-major laser trajectories;
- `benchmark_clearance_static_segments.py`: game-neutral static finite
  segments, optionally combined with moving AABBs;
- `benchmark_piecewise_native.py`: stop/resume/redirect/reversal
  piecewise-transform adversarial motion.

Reports state that solve timing excludes workload generation and TH08 sensor
decoding. Laser projection/lowering remains independently measurable with
`benchmark_laser_projection.py`.

**Implemented:** static finite segments are now traversed segment-major within
their exact finite geometry AABB expanded by occupied radius and the configured
clearance cap. A one-cell numeric guard preserves boundary candidates. The
authoritative clearance remains `std::hypot`; this change only rejects cells
that cannot improve the cap.

**Observed:**

- 500 randomized old/new native workloads, including far, reversed, growing,
  and zero-length segments at caps 1/12/48/96, changed zero float cells;
- pre-lowered native clearance for 1,500 moving AABBs, 250 static segments,
  81 frames, a 24-by-27 lattice, and cap 48 improved from 122.28 to 81.86 ms
  warm median (1.49 times);
- the separated static complete-solve workload measured 85.51 ms warm median,
  of which 80.12 ms was clearance and 4.88 ms viability;
- the separated live-like 800-AABB/200-laser workload measured 49.42 ms warm
  median, of which 37.40 ms was clearance and 10.63 ms viability;
- the 1,024-hazard piecewise dense/sparse benchmark retained a maximum
  difference of `2.003e-5`; sparse total median was 40.61 ms versus 158.58 ms;
- 24 seeds of 2,048 piecewise hazards, 48 frames, and up to six transform
  events all passed the independent scalar oracle with maximum error
  `9.537e-7`.

Compact reports are under `artifacts/benchmarks/` with the `20260725` suffix.

## Checkpoint 4: Boolean Occupancy Shadow

The simple premise that viability consumes only clearance sign is false for
the current certified recurrence. Every transition samples the nearest
lattice cell and subtracts its transition-specific Euclidean sampling error
before applying the zero-clearance test. On the 16-pixel lattice this error
can reach 11.314 pixels. Therefore two positive clearances with the same sign
can produce different action admissibility.

The reproducible semantic shadow in
`scripts/analysis/boolean_occupancy_shadow.py` compared the exact policy with:

1. an optimistic sign-only volume, where every positive cell is treated as
   clearing every sampling error;
2. a conservative volume, where every cell below the maximum possible
   sampling error is occupied.

For a 50-AABB/10-laser, 81-frame workload, the optimistic policy added 338,218
unsafe action bits and 18,601 false-positive viable states. The conservative
policy had no false positives but removed 115,584 valid action bits and 13,483
valid states. Exact clearance was needed at only 72 representative endpoint
rankings (46 unique cells), but endpoint reranking cannot reconstruct safety
over all intermediate frames and delay branches.

**Decision:** do not add a live Boolean kernel behind the current API. The
shadow is rejected for live parity, while the broader direction remains open.
A viable successor must either encode transition-specific dilation levels,
perform continuous exact occupancy queries inside the recurrence, or retain a
signed-distance narrow band. It must reproduce complete viable and safe-action
arrays before query-local endpoint clearance can replace the dense volume.
The semantic artifact deliberately derives Boolean arrays from the exact
volume and makes no construction-speed claim.

## Final Offline Validation

- Linux complete quick suite: 434/434 in 1.074 seconds.
- Windows complete UNC-safe suite: 434/434 in 2.367 seconds.
- Linux and Windows native libraries rebuilt from the same source; the C++
  source also passes `-Wall -Wextra -Wpedantic -fsyntax-only`.
- Packed object/reference plans have identical clearance, viable arrays,
  safe-action masks, representative paths, gates, and bottlenecks.

## Physical Full-Route Validation

The offline checkpoint was followed by one continuous original-game
Sakuya/Remilia Lunatic Route-2 run,
`lunatic_route2_fullrun_unattended_20260725_083917`.

**Observed:**

- native Final B scene unload at frame `226864`, followed by
  `termination_reason=route_complete`;
- one continuous trace, 52,479 decisions, no foreground interruption, no
  runtime error, no manual re-arm, and zero JSON decode errors;
- hard no-Bomb verification passed over every decision; 77 native hit edges
  and zero deathbomb requests;
- maximum observed workloads included 1,536 bullets, 240 lasers, and the
  Stage-3 200-laser pattern;
- compared with the retained 2026-07-23 complete hard no-Bomb baseline, hits
  changed `90 -> 77`. Per-stage changes were `+2, 0, -4, -9, +7, -9`, so
  Stage 1 and especially Stage 5 remain adverse samples rather than being
  hidden by the total.

**Observed delivery performance:**

- global solve median/p95/max changed
  `2455.95/4038.64/6141.66 -> 99.99/386.09/540.90 ms`;
- first-observed solution age median/p95 changed `152/259 -> 3/9` frames;
- unique delivered solutions changed `1,064 -> 9,308`, queries
  `759 -> 51,747`, and reported stale solutions `484 -> 15`;
- the new phase telemetry attributes clearance
  `12.11/33.53/104.71 ms` median/p95/max and viability
  `74.63/372.11/519.15 ms`. Clearance is no longer the dominant live global
  phase; Boolean viability induction is now the tail bottleneck.

**Model evidence and limits:**

- exact failure witnesses classified 21 bullet overlaps, three laser
  overlaps, and three enemy-body overlaps. The unattributed
  sensor-gap/unmodeled class changed `18 -> 1`, and
  active-laser-without-overlap changed `1 -> 0`;
- this is stronger coverage evidence, but not pure causal accuracy parity:
  enemy-body telemetry and attribution also improved between runs, and the
  RNG, entry resources, Power history, and phase durations differ;
- local read medians rose from roughly 7 ms to 11-12 ms and action-lag
  medians from one to two frames. The global optimization did not remove the
  local sensing/issue-time budget;
- no route strategy was promoted. This is one physical acceptance sample for
  the packed clearance implementation, not cross-RNG proof of a universally
  better controller.
