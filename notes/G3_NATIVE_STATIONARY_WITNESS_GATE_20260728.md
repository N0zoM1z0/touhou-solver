# G3 Native Stationary Witness Gate

Date: 2026-07-28

Status: offline Gate 4 complete; delivery, complete-mask capsule, hazard
coverage, and physical-consumption gates remain open

## Result

Checkpoint `25d5f68` adds internal native extraction of the complete
deterministic worst path for one exact stationary causal policy. It does not
add a public ABI symbol, a Python production consumer, shadow publication, or
live action authority.

The extractor accepts only the already-declared stationary specialization:

- one singleton continuation action;
- zero continuation budget and no budgeted actions;
- physical remaining-delay observation (`remaining_delay_bucket_size = 0`);
- no proposal-only continuation restriction; and
- one exact augmented root and unrestricted root action.

Any incompatible workspace, invalid pending support, timeout, cancellation,
insufficient complete output capacity, or internal label mismatch returns no
completed witness.

## Implementation Boundary

`native/src/pipeline/belief_stationary_witness.{hpp,cpp}` now owns reusable
belief state/observation records, deterministic nature ordering,
observation-compatible hidden-branch merging, worst-branch tie-breaking, and
path extraction. `belief_workspace.cpp` retains the authoritative recurrence,
supplies exact successor labels, and converts a completed internal path into
the internal fixed-layout record.

Every native transition now retains:

```text
(hidden remaining delay, recursive cadence, pickup delay or no-write)
```

For a successful observation group, extraction unions successor remaining
support, retains the lowest prefix margin and deterministic attaining nature
tuple, evaluates the merged successor once, and minimizes

```text
(survival label, nature tuple, failed flag, successor key)
```

exactly as the independent Python stationary witness does. The native path is
also checked against the authoritative native action label at every decision;
a mismatch fails closed.

The test probe is a separate executable built by
`scripts/tools/build_native_stationary_witness_probe.py`. It links the
internal implementation directly and is not part of the shipped shared
library.

## Independent Checks

**Observed:** Linux and Windows full-path differentials match the independent
Python witness at exact float32 label fields and every discrete field. The
deterministic corpus covers:

- all three root actions for four randomized clearance volumes;
- recursive cadence support `(2, 3)`;
- pickup support `(0, 1)`;
- observation-compatible merged remaining support;
- a pending same-desired no-write path with remaining support `(1, 2)`; and
- an unsafe root with an empty path.

The comparisons include root and successor labels, active/pending actions,
remaining masks, selected action, hidden remaining delay, pickup/no-write,
cadence, prefix bottleneck, failure state, successor identity, and merged
hidden-branch count.

**Observed:** the production Linux and Windows libraries build after the
split. The Linux sanitizer profile also builds. The authoritative ABI tests
confirm that the header and both built libraries still match the checked-in
46-symbol manifest exactly; the internal extractor is not dynamically
exported.

**Observed:** complete quick suites pass `726/726` on Linux in `9.635 s` and
Windows in `14.362 s`, with the three existing Windows platform skips.

## Interpretation And Remaining Gates

**Inferred:** Gate 4 proves native/Python implementation parity for the
complete stationary worst path, not only its root label. It also establishes
an internal complete-only extraction boundary suitable for later cancellable
background measurement.

This does not prove the physical model. The retained Stage-4A/Stage-6B
capsules still use the historical 17-movement-action alphabet, omit unknown
future births/transforms/bodies, and include no issue-time delivery result.
The extractor therefore remains offline. Gate 5 is next:

1. build exact 36-token complete-mask augmented roots;
2. truncate or reject every claim at the first unknown future-event slab;
3. measure cooperative cancellation and Windows contention; and
4. only then consider exact-version, complete-only shadow lookup with a fresh
   local hard intersection.

No physical run was used to promote this checkpoint because the new object
has no consumer and every current physical hazard root remains
`model_unknown`. A live trial before those gates would measure the unchanged
Boolean controller, not native witness delivery.
