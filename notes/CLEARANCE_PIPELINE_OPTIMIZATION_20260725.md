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
