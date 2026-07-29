# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V3 Stage-5 Failure

Date: 2026-07-29

Run: `lunatic_route2_stage5_unattended_20260729_104222`

Code checkpoint: `fcc37ec`

Status: semantic cross-epoch delivery observed; physical timing and survival
gates failed

## Result

**Observed:** the first schema-v6/event-v3 physical run corrected CE-0169.
The accepted program remained at controller epoch 0 while all 127 selected
spell-107 batches occurred at observation epoch 2. Every program-identity and
epoch-provenance check passed. The strict auditor independently replayed all
3,384 requests complete with zero unknown:

```text
target 69 / 72 / 73 = 840 / 852 / 1692
cache misses / persistent / request-local / eviction
                      = 46 / 1592 / 1746 / 0
```

Online preparation was `0.090 ms` bind and `0.121 ms` total, safely below the
fixed `1.000 ms` maximum. The report regenerated twice byte-identically.

The run nevertheless failed four fixed gates:

- event derivation p95 was `0.620 ms` against `0.500 ms`;
- replay-bundle compact p95 was `0.564 ms` against `0.500 ms`;
- preceding synchronous emit p95 was `2.862 ms` against `1.000 ms`; and
- the run took 11 hits against the user-set maximum of ten.

Transaction-total p95 was `2.893 ms` against `3.000 ms`, and decision-cadence
p50/p95 was `2/4` frames, equal to the retained schema-v3 baseline. These
passing aggregate values do not erase the three failed component gates.

## Physical Scope

- decisions/frames: 11,058 / `1..40304`;
- termination: `route_complete`;
- hard no-Bomb: pass over every decision;
- accepted supervisor completion and exact game cleanup;
- hit frames:
  `[11807, 13702, 28903, 32866, 33731, 34907, 35637, 36078, 36798, 38114, 39160]`;
- phase hits nonspell/103/107/111/115:
  `4/0/1/4/2`;
- all 11 contacts followed global viability-kernel exhaustion;
- primary classes: seven observed bullet overlaps and four modeled committed
  prefix collisions;
- contributing factors: boundary 7, fast mode 5, density over 1,000 on 2;
  and
- Power fell from 128 to 0 after the accumulated deaths.

This is one fresh attempt. Its first contact at frame 11,807 is the canonical
causal witness; later contacts remain geometry/planner evidence after respawn.
The reduction from the preceding 20-hit run is descriptive, not a causal
claim for a trace-only observer.

## Delivery Attribution

**Observed:** selected batch JSON line bytes p50/p95/max were
`66080/92142/97166`. The recorded preceding emit time correlates with the
previous batch-line size at `0.785`.

Event-derive component p50/p95/max was:

| Component | p50 | p95 | max |
| --- | ---: | ---: | ---: |
| state decode | 0.269 | 0.354 | 0.557 |
| cached lower | 0.057 | 0.179 | 0.407 |
| result compact | 0.072 | 0.126 | 0.242 |

The observation carried up to 164 native records but at most 34 usable raw
VM blobs. Null-record dictionaries and full repeated derived-result JSON are
therefore redundant transport, not independent replay evidence.

**Hypothesized correction, measured offline only:** retaining all usable raw
bytes and exact source indices while replacing null-record dictionaries and
full derived results with independently checked commitments projects the
same rows to p50/p95/max `20378/22449/22516` bytes. This projection is not a
production or physical result and receives no authority from this note.

## Retained Evidence

- raw trace bytes/SHA-256:
  `444980473` /
  `365aaee1c9a328b45b538510536bb5736a0ed66f699058e50b93a6a80882eee4`;
- session SHA-256:
  `c8cb44148e97584d751e1a33a298c0ed9b28d95f742096adef3f54ac4342f263`;
- strict failed report SHA-256:
  `3738d329d1921932b0688223f044d4666f29825e72023b9ee43cb03ee76cb24b`;
- run review:
  `notes/runs/lunatic_route2_stage5_unattended_20260729_104222.md`; and
- counterexample: CE-0170.

## Decision

Schema v6/event v3 proves the corrected epoch/program boundary physically,
but it has no physical delivery acceptance because timing and survival both
failed. Do not select another RNG sample before addressing the measured
delivery redundancy.

The next version must preserve the exact raw replay bundle, native coherence
accounting, source mapping, production-result parity, cache parity, and all
unchanged timing/survival gates while removing only independently
reconstructible JSON duplication.
