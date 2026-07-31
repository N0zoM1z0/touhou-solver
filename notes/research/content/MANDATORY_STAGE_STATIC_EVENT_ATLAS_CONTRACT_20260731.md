# Mandatory-Stage Static Event Atlas Contract

Date: 2026-07-31

Taskbook card: `CONTENT-02`

Status: mandatory static opcode semantics complete; runtime event join remains
open

## Question

For the pinned Sakuya/Remilia Route-2 Lunatic content, which event classes
occur in the Stage-3, Stage-4A, Stage-5, and Final-B ECL files, which
subroutine occurrences are conservatively reachable after known
route/difficulty folding, and how can each occurrence be joined to a future
exact runtime image? For timeline opcode `0x06`, what ordered native
route/combat/item effects must that future join preserve?

This checkpoint does not ask whether an occurrence executed in a retained
physical run. It grants static shipped-instruction/dataflow authority for
opcode `0x06`, not event-level execution, timing, or causal action authority.

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

The retained v2 output has SHA-256
`fc7156165a43de4e0a7dcaad79a00d6ff183423122d798098c522c2e005dad9c`
and internal pre-digest
`53645ae1f210a6ffaeb72b8a3dd0023dac35c21f68aac677c564bb21b5cbb82b`.
A second generation was byte-identical.

## Result

**Observed from pinned decoded bytes:** the atlas retains 2,885 classified
event occurrences:

| workload | occurrences | CFG-reachable instructions | reachable subroutines | unknown semantics |
| --- | ---: | ---: | ---: | ---: |
| Stage 3 | 714 | 1,386 | 63 | 0 |
| Stage 4A | 775 | 1,458 | 59 | 0 |
| Stage 5 | 696 | 1,592 | 87 | 0 |
| Final B | 700 | 2,329 | 85 | 0 |

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
| forced enemy HP zero | 52 | 30 | 3 |
| callback installation/use | 52 | 52 | 0 |
| item/resource event | 100 | 78 | 3 |
| message-script start | 19 | 0 | 0 |
| scripted enemy cleanup | 19 | 0 | 0 |
| item motion control | 19 | 0 | 0 |
| movement redirect | 355 | 333 | 22 |
| phase control | 750 | 705 | 45 |
| spell lifecycle | 91 | 80 | 11 |

The route timelines add 519 enemy-birth schedule candidates, 71
wait/marker candidates, 9 control candidates, and 19 observed
message-script/cleanup candidates. Timeline schedule candidates occupy the
separate matrix column, so the three new rows above have 19 timeline
candidates even though their CFG-reachable columns are zero.

CE-0219 corrected the inherited opcode-`0x5F` label after revalidation of
`0x0042EFB0`: the opcode forces eligible HP to zero but does not itself clear
the active bit. The atlas class and retained digest above include that
correction.

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

## Timeline Opcode `0x06` Native Semantic Closure

**Observed and revalidated in the connected shipped TH08 IDB:**

1. `stage_timeline_step` case `0x06` at `0x0042ABD2` passes the record's sole
   dword argument through `frscreen_start_timeline_message_script`
   (`0x00439810`) as a message-script selector.
2. `frscreen_start_message_script` (`0x0043396D`) resets the message state and
   applies its native stage/route selector branches.
3. It calls `enemy_manager_zero_eligible_hp_with_score_items`
   (`0x0042EFB0`). In ascending ordinary-slot order, active non-boss enemies
   not excluded by flags2 bit 6 receive current HP `+0x2DFC = 0`; active
   retirement is not performed here. Flag-`0x80` enemies request type-6 score
   items, parent links are removed, and configured signed end subroutines are
   started and cleared.
4. `item_manager_force_all_homing` (`0x004413E0`) then visits the active item
   list, including newly allocated score items, writes motion state
   `+0x2D7 = 1`, and stores velocity `(0,-0.5,0)` at `+0x2B0`. The next item
   update takes the homing path. This helper does not itself commit pickup,
   Power, lives, or Bombs.

The 19 mandatory-route occurrences are therefore no longer unknown:
4/4/2/9 occur statically in Stage 3/4A/5/Final B. Shared timeline opcode
`0x09` remains unknown but has zero Lunatic-eligible occurrence in these four
route timelines. The mandatory static-semantic subgate is closed.

**Observed physically only at workload granularity:** retained physical runs
have reached all four workloads. They do not identify whether any individual
`0x06` occurrence executed. `CONTENT-02` therefore remains open only for the
exact runtime-image/program-counter event join and event-level physical
reach. That capture debt must not block unrelated high-ROI route, combat, or
resource work.

## Authority

- **Observed:** exact input identities, decoded records, difficulty
  eligibility, class membership, static analyzer output, and the shipped
  native opcode-`0x06` dispatcher/callee dataflow above.
- **Inferred:** conservative route reachability after known route/difficulty
  folding.
- **Hypothesized:** whether a listed instruction executes in a physical
  history and the future runtime-PC join until separately observed.
- No physical trial was run.
- Static opcode-`0x06` side-effect authority is granted only for the ordered
  native dataflow above. No individual event-execution, event-timing,
  future-hazard, planner, action, or promotion authority is granted.

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
   mismatch, omitted eligible opcode, unresolved dynamic subroutine edge,
   shipped native instruction/dataflow contradiction, or exact runtime image
   showing an incorrect symbolic offset mapping.
5. **Can a live consumer use it before issue time?** No. The report is
   offline research evidence and is absent from the live publication path.
