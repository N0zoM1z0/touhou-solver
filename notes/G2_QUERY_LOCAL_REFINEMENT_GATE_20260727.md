# G2 Query-Local Refinement Gate

Date: 2026-07-27

Status: **offline finite-model semantic gate passed; delivery gate failed**.
This result changes no live planner, publication path, worker allocation, or
input authority.

## Result

The retained six-root gate completed with:

- six of six exact roots recovered by a completed lower witness;
- zero lower action bits absent from the exhaustive fine reference;
- zero fine-reference action bits absent from the upper bound;
- zero full-field patches;
- exact root query action, frame, position, delay support, capsule identity,
  and problem identity retained in the report.

The deterministic report is
`artifacts/viability_audit/g2_spatial_refinement_gate_20260727.json`, SHA-256
`bfc42d9f1c71f1b8228187360cca76d4023807201713a222d9c05664824f2bde`.

## Implemented Finite Contract

The implementation now provides:

1. round-to-even coarse-cell membership with lower/intersection and
   upper/union action masks;
2. explicit active-action, selected-action, hidden-delay, decision-layer, and
   physical-step transition identities;
3. branch-fixed exact forward tubes intersected with optimistic terminal
   co-reachability;
4. root-relevant ambiguity selection with conservative transition-sample
   dependency closure and a one-layer clearance halo;
5. a proposal-only candidate guide whose omissions can only weaken the lower
   result;
6. an independent scalar bounded recurrence for generated small cases;
7. a vectorized rectangle implementation for retained workloads;
8. fail-closed timeout behavior: uncomputed lower remains zero and upper
   remains all actions.

The retained gate tries 8 pixels first, then 4 pixels, and permits one extra
empty-state guide expansion only when the first 4-pixel lower remains empty.
Root actions remain unrestricted.

## Retained Workload Evidence

Three roots were recovered at 8 pixels. Three required 4 pixels. One of those
required two empty-state guide expansion layers and requested 225,004 refined
states over 77.47% of the spatial field. Across all ten attempted
root/resolution evaluations:

- patch construction: `3160.63..14153.12 ms`, median `5008.91 ms`;
- vector solve: `859.02..4008.67 ms`, median `1018.57 ms`;
- patch spatial fraction: `4.71%..77.47%`, median `21.74%`.

These are Linux offline measurements. They are already orders of magnitude
outside the live issue budget, so the unchanged Windows publication-age and
contention gate cannot pass with this implementation. A Windows semantic quick
suite was still run; a Windows retained timing run would not turn the observed
multi-second Linux implementation into a deliverable result.

## Independent Checks And Limitations

The independent scalar oracle exercises exact hidden-branch lower/reference/
upper inclusion on generated stop, resume, redirect, and reversal cases. The
retained vectorized rectangle implementation and exhaustive fine reference
reuse the same dense native recurrence, so their retained comparison is not
implementation-independent. Retained hidden-branch output is currently the
sound but trivial interval from zero to all actions; generated scalar cases
exercise tightened branch bounds.

The finite reference includes the declared movement, delay, horizon,
clearance, and terminal model only. It does not close future-event coverage,
continuous physical state, the frozen manager-frame boundary, complete-mask
live integration, publication identity, or actuator delivery.

## Decision

The G2 spatial soundness direction is retained. The current Python patch
builder and dense-rectangle data plane are rejected for live delivery.
`S09` remains offline/shadow-only.

The next acceptable performance implementation must preserve the same
lower/reference/upper quantifiers and exact root identity while replacing
Python state enumeration and dense rectangle solving with sparse/native,
cooperatively cancellable work. It must then pass:

1. scalar/native generated differentials;
2. the unchanged six-root retained inclusion gate;
3. Windows solve, publication-age, contention, cancellation, and exact-version
   lookup measurements;
4. side-effect-free shadow evidence before any authority proposal.

## Validation

```text
focused dual-bound tests:          8/8 passed
focused adaptive-refinement tests: 12/12 passed
Linux quick suite:                 683/683 passed in 8.381 s
Windows quick suite:               683/683 passed in 12.852 s, 3 skipped
ruff:                              passed
git diff --check:                  passed before documentation update
retained six-root gate:            passed
```
