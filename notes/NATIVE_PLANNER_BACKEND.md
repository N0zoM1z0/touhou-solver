# Game-Neutral Native Planner Backend

## Problem

The Final B practice trace `20260723_213126` proved that forecasted future
policy epochs fixed delivery but did not make a serial policy worker
serviceable:

- policy horizon: 80 physical frames
- solve time: 1,957 / 2,915 / 3,268 ms median/p95/max
- equivalent solve time at 60 FPS: about 117 / 175 / 197 frames
- policy decisions: 17,914
- queryable decisions: 8,309
- expired decisions: 8,834

This is not a TH08 spell-specific failure. A serial asynchronous solver cannot
provide continuous policies when its submit interval is longer than the
finite policy horizon.

## Boundary

Python remains the orchestration and reference layer. The native backend owns
only two game-neutral numerical contracts:

1. Moving AABBs and finite segments become a physical-frame clearance volume.
2. A clearance volume, lattice dynamics, action set, and delay support become
   backward viability and safe-action masks.

The native ABI contains no TH08 addresses, input bits, stage numbers, spell
IDs, ECL opcodes, item types, or route-specific objectives. A new Touhou game
supplies its own hazard oracle and movement adapter to the same contracts.

## Survival Semantics

The reference equation remains:

```text
V[layer, active_action, y, x] =
    current_state_is_safe
    and exists next_action
        such that for every actuation_delay:
            every intermediate physical sample is safe
            and the successor is in V[layer + 1]
```

The native kernel preserves:

- active input as part of state during the uncontrollable prefix
- `exists action, forall delay` quantifier order
- every intermediate physical-frame collision check
- nearest-lattice continuous sampling error
- optional clamping versus strict out-of-bounds rejection
- exact safe-action bit masks used by the Python query and repair-volume layer

NumPy remains the executable reference oracle. Randomized native/NumPy parity
tests compare the entire viability tensor and every safe-action mask. Mixed
moving-AABB/segment tests compare the complete clearance volume.

## Async Contract

`AsyncPolicyLead` now reports the rolling p90 solve duration in frames and a
serial coverage margin:

```text
serial_margin = policy_horizon
                - max(policy_epoch_interval, p90_solve_frames)
```

The worker is serviceable only when this margin is positive. This signal is
written into every future trace instead of inferring health from a completed
future alone.

Delay support can change while a policy is solving. The generic
`delay_support_envelope` pads the current contiguous support by one bounded
frame on each side before submission. The live local controller still uses
the current learned support; the asynchronous policy remains valid when the
estimator moves one boundary during the solve interval.

## Performance

The retained stress workload uses 1,500 moving AABBs, 250 finite segments,
17 actions, an 80-frame horizon, 648 lattice points, and a 148-frame forecast.

Windows x86-64:

| Backend | Delay support | Warm median | Maximum | Clearance | Viability |
| --- | --- | ---: | ---: | ---: | ---: |
| NumPy | 1..3 | 1,501.9 ms | 1,653.3 ms | 890.2 ms | 600.3 ms |
| Native | 1..3 | 540.2 ms | 619.8 ms | 520.8 ms | 19.2 ms |
| Native | 1..6 | 511.4 ms | 561.4 ms | 486.4 ms | 24.8 ms |

The full-delay native maximum is about 34 physical frames at 60 FPS. This is
below the 80-frame horizon and leaves synthetic serial timing headroom. The
physical Final B trace still must prove that game contention and real hazard
mixtures preserve this margin.

The compact source measurements are retained in
`artifacts/runtime_reports/native_planner_performance_20260723.json`.

## Build And Deployment

```bash
PYTHONPATH=scripts python scripts/build_native_planner.py --target linux
PYTHONPATH=scripts python scripts/build_native_planner.py --target windows
```

The rebuildable `.so` and `.dll` are ignored. The Windows x86-64 DLL is
cross-compiled with the MinGW runtime linked statically so Windows Python does
not require a compiler or extra runtime DLL. The current local build hashes
are:

```text
linux  af69b2870a480f71342a9323608f8f3adf266fe1d4bc3c5829d24187ae4a534d
win64  38821d17f6d6f6e3b1316802c03a86e681d31a7be93de7fca23ccb57c82eb66c
```

If the native library is absent, the planner uses the NumPy reference
implementation. `TOUHOU_DISABLE_NATIVE_PLANNER=1` forces that path for
benchmarks and parity diagnosis.

## Remaining Limits

- Native acceleration does not repair an inaccurate future hazard oracle.
  Current transformed-bullet and laser uncertainty still grows through the
  forecast interval.
- The live policy still sees current projectiles projected forward. Exact ECL
  spawn, transform, and laser execution is required to model hazards that do
  not yet exist in the snapshot.
- The benchmark establishes throughput and semantic parity, not physical
  acceptance.
- The next focused Final B trace must show `native_planner_backend=true`,
  positive serial coverage margin, sharply fewer expired decisions, reduced
  delay-support mismatch, and no regression of hard no-Bomb evidence.
