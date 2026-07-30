# Mandatory-Stage Static Event Atlas Contract

Date: 2026-07-31

Taskbook card: `CONTENT-02`

Status: static foundation retained; physical event-priority gate remains open

## Question

For the pinned Sakuya/Remilia Route-2 Lunatic content, which event classes
occur in the Stage-3, Stage-4A, Stage-5, and Final-B ECL files, which
subroutine occurrences are conservatively reachable after known
route/difficulty folding, and how can each occurrence be joined to a future
exact runtime image?

This checkpoint does not ask whether an occurrence executed in a retained
physical run or what its side effect was.

## Inputs And Reproduction

- Immutable content manifest:
  `artifacts/runtime_reports/th08_immutable_content_manifest_20260731.json`,
  SHA-256
  `3a52b6f485ada63c833f77ae8cd1653f469ae4fadeef3c38336a737c7e753ae1`.
- Decoded ECL inputs under `artifacts/decoded/`, validated against the exact
  per-file SHA-256 values in that manifest before analysis.
- Static branch configuration: route ID 2, difficulty index 3, difficulty
  mask `0x08`.
- Analyzer:
  `scripts/analysis/th08_mandatory_event_atlas.py`.

Reproduce with:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_mandatory_event_atlas.py \
  --decoded-dir artifacts/decoded \
  --content-manifest \
    artifacts/runtime_reports/th08_immutable_content_manifest_20260731.json \
  --output \
    artifacts/runtime_reports/th08_mandatory_event_atlas_20260731.json
```

The retained output has SHA-256
`b8184692cd8a03e37ea5f233e6390b94f3319187e0742a1b48afbcffaad7680a`
and internal pre-digest
`2e2b33645bca24474a7cdc2a950e474135ad9dc46ddb146cb229c8fad7242a37`.
A second generation was byte-identical.

## Result

**Observed from pinned decoded bytes:** the atlas retains 2,885 classified
event occurrences:

| workload | occurrences | CFG-reachable instructions | reachable subroutines | unknown semantics |
| --- | ---: | ---: | ---: | ---: |
| Stage 3 | 714 | 1,386 | 63 | 4 |
| Stage 4A | 775 | 1,458 | 59 | 4 |
| Stage 5 | 696 | 1,592 | 87 | 2 |
| Final B | 700 | 2,329 | 85 | 9 |

The conservative flow analysis reports no unresolved dynamic subroutine edge
in these four route ECL files. It folds 8 statically observable branches and
preserves 91 other branches conservatively. That is a static
overapproximation, not proof that an instruction executes.

Event-class totals overlap when one opcode has more than one material
effect. The retained matrix includes:

| event class | total | conservative route-reachable | eligible but CFG-unreachable |
| --- | ---: | ---: | ---: |
| hostile fire | 375 | 331 | 44 |
| bullet transform | 179 | 151 | 28 |
| laser lifecycle | 13 | 13 | 0 |
| enemy birth | 277 | 259 | 18 |
| global enemy cleanup | 33 | 30 | 3 |
| callback installation/use | 52 | 52 | 0 |
| item/resource event | 81 | 78 | 3 |
| movement redirect | 355 | 333 | 22 |
| phase control | 750 | 705 | 45 |
| spell lifecycle | 91 | 80 | 11 |

The route timelines add 519 enemy-birth schedule candidates, 71
wait/marker candidates, 9 control candidates, and 19 unknown candidates.

## Symbolic Runtime Join

Each occurrence is keyed by:

```text
content-set digest
+ decoded ECL SHA-256
+ scope (timeline or subroutine)
+ scope index
+ decoded file offset
```

The report retains a symbolic ID such as
`ecldata5.ecl:timeline:0:0x0000b788`. A later native capture must first prove
the exact loaded runtime image and its base, then join the runtime program
counter to the decoded offset. No occurrence in this checkpoint has that
runtime join, so the atlas grants no event-execution authority.

Spell-practice ECL hashes are retained only as references. They are not
treated as evidence about the natural mandatory route.

## Unknown-Event Priority

**Observed statically:** all 19 unknown mandatory-route occurrences use
timeline opcode `0x06`: 4 in Stage 3, 4 in Stage 4A, 2 in Stage 5, and 9 in
Final B. Timeline opcode `0x09` remains semantically unknown in the shared
catalog but does not occur in these four Lunatic-eligible route timelines.

**Observed physically only at workload granularity:** retained physical runs
have reached all four workloads. They do not identify whether any individual
`0x06` occurrence executed.

Therefore the unknowns can currently be prioritized only by mandatory-stage
workload reach, not by event-level physical reach. Final B has the largest
static debt, followed by Stage 3 and Stage 4A, then Stage 5. This ordering is
a capture priority, not a semantic or survival-risk ranking.

The `CONTENT-02` gate remains open until exact runtime-image/program-counter
joins establish event-level physical reach and opcode `0x06` is revalidated
against the native timeline dispatcher. This capture debt must not block
unrelated high-ROI route, combat, or resource work.

## Authority

- **Observed:** exact input identities, decoded records, difficulty
  eligibility, class membership, and static analyzer output.
- **Inferred:** conservative route reachability after known route/difficulty
  folding.
- **Hypothesized:** whether a listed instruction executes in a physical
  history, the meaning of timeline opcode `0x06`, and the future runtime-PC
  join until separately observed.
- No physical trial was run.
- No opcode side-effect, event-timing, future-hazard, planner, action, or
  promotion authority is granted.

## Formal Authority Questions

1. **Which physical histories map to one model state?** None. The artifact is
   a static content atlas, not a control-state abstraction.
2. **Are all uncertainty branches present and nonclairvoyant?** Known
   route/difficulty predicates are folded. Other static CFG alternatives are
   retained conservatively; the analyzer makes no controller choice.
3. **Does exact solution answer the physical question?** No. Static
   reachability answers only whether a pinned instruction remains a candidate
   under this overapproximation.
4. **What falsifies the claim?** A parser differential, content-hash
   mismatch, omitted eligible opcode, unresolved dynamic subroutine edge, or
   exact runtime image showing an incorrect symbolic offset mapping.
5. **Can a live consumer use it before issue time?** No. The report is
   offline research evidence and is absent from the live publication path.
