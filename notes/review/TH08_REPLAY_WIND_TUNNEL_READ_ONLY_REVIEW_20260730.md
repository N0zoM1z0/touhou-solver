# TH08 Replay / Native-Root “Wind Tunnel” Read-Only Review

Date: 2026-07-30
Workspace: `/home/pentester/coding/codex_ida/th08`
Branch/HEAD: shared working tree at `293cca8f9d04b5ef586e571f0da826ec99b0db7a`
when first inspected; concurrent uncommitted replay/root work is changing
during this review.
Dirty-state caveat: shared worktree contains concurrent agent changes; this
review will not modify, stage, test as authoritative, or otherwise take
ownership of them.
Connected IDB identity: TH08 `th08.exe`, base `0x00400000`, database input
SHA-256 `ec101fcff80b77e717d43b54e326375487af19661bb7c8d11a19ee5e0fbf928b`,
file size `0xCD400`.
Physical executable identity in the new replay evidence:
SHA-256 `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`,
with the retained no-life-decrement byte at `0x0044D0FA` equal to `0x00`.
Latest retained evidence cutoff: committed checkpoint `293cca8` plus the
explicitly listed concurrent uncommitted artifacts inspected below.
Scope: explain the proposed replay-root-counterfactual “wind tunnel,” inspect
what the concurrent workspace implementation actually builds, trace one
concrete workflow, and state why it is or is not a faster iteration loop than
fresh RNG-varying physical runs.
Non-actions: no repository, note, IDA, strategy, runtime, input, or gameplay
mutation; no physical trial.

## Retention And Supersession

This document remains the read-only review at its stated evidence cutoff.
Subsequent work launched the generated branches, corrected a same-frame
manager/collision stop race, and closed the native-prefix experiment. The
accepted current result and next architecture are in
`../architecture/NATIVE_REPLAY_CAUSAL_WIND_TUNNEL_AND_REPLAY_SAVE_CONTRACT_20260730.md`.

## Evidence Labels

- **Observed:** direct current source/diff, retained deterministic/native
  evidence, or shipped-program evidence.
- **Inferred:** supported by multiple observed facts but not directly proved
  at runtime.
- **Hypothesized:** proposed explanation or benefit awaiting a decisive gate.

## Live Summary

The concurrent work is building two related mechanisms, not one:

1. a **native-replay branch oracle**: save/archive a Stage-5 replay, rewrite a
   declared replay input interval into all 36 no-Bomb complete masks, and let
   the original TH08 executable recompute each future from the same replay
   seed and immutable input prefix; and
2. a **native-root/executor path**: capture content-addressed process byte
   regions at a fixed native frame so that the repository's own short-prefix
   executor can eventually branch without replaying the whole prefix.

The first mechanism is a valuable intermediate wind tunnel because it does
not reuse recorded enemy/bullet/world state after the altered action; the
original executable advances ECL, RNG, pools, damage, and geometry. It is not
yet a closed-loop offline solver: after the declared held-mask interval the
current corpus restores the original replay's open-loop input suffix.

The second mechanism is not complete. The formal root inventory still marks
seven of ten minimum semantic requirements missing and grants no predictive
authority even to a coherent byte capture. A fourth concurrent attempt
captured all 15 declared fixed regions, but crossed the manager-frame bracket
(`12318 -> 12320`). A fifth attempt suspended the whole process for
`519.8315 ms` and captured a stable `12316 -> 12316` byte slice. It correctly
remains a `partial_native_root_inventory`, not a predictive root.

Current observed progress:

- a content-addressed Lunatic Route-2 Stage-5 replay was archived, SHA-256
  `d83b98a23a2fd8f01c79c62f1aa824d56c05224449a5da1db2904f6022b68782`,
  with 30,498 decoded input records, seed 7,337, and no Bomb press;
- original TH08 replay playback observed the first native hit at
  `enemy_manager_frame = 12322`;
- the retained alignment candidates are not authoritative: best mask
  agreement is only `0.60892`, and best transition agreement only `0.47878`;
- three attempted root captures named for frame 8,715 failed, respectively,
  on component sorting, ordinary-pool component identity, and a
  template-plus-pool versus pool-only size mismatch;
- the fourth attempt retained 15 component blobs but remained incoherent
  after three retries and still reported seven missing semantic requirements;
- the fifth attempt retained the same 15 blobs under whole-process
  suspension, produced an equal manager-frame bracket at 12,316, still
  reported seven missing requirements, and reproduced the first hit at
  manager frame 12,322 after resume;
- the all-36 replay corpus generator itself was independently run in `/tmp`
  during this audit. It generated and decode/encode-verified all 36 no-Bomb
  one-frame branches in 8.5 seconds. This validates file generation only;
  none of those mutated branches was launched in TH08 by this audit.

The exact conclusion is therefore: **the design is genuinely replay-based,
but the current workspace has built the replay acquisition/encoding,
single-replay observation, and coherent-but-partial fixed-byte capture layers,
not yet the complete wind-tunnel loop.**

Focused Linux verification at the reconciled working-tree snapshot passes:

- native future-body root: 12 tests;
- replay decode/encode/mutation: 4 tests;
- content-addressed replay archive: 1 test;
- native replay first-hit helpers: 2 tests;
- generic replay menu/contract observer: 7 tests;
- accepted-practice replay save: 2 tests; and
- practice supervisor: 34 tests;
- runtime/whole-process suspension helpers: 17 tests.

These are implementation gates. They do not prove that a re-encoded or
mutated replay is accepted by the original executable, that the replay/native
frame coordinate is exact, or that a branch avoids the hit.

## Audit Checklist

- [x] Read the complete current handoff and strategy ledger.
- [x] Read the current notes selected by the handoff for replay/root/lifecycle.
- [x] Reconcile IDB/executable identity and shared worktree snapshot.
- [x] Inspect concurrent source, tests, artifacts, and documentation changes.
- [x] Trace replay capture -> root -> alternative actions -> simulator ->
      native differential -> candidate -> focused physical.
- [x] Separate implemented machinery from proposed future capability.
- [x] Explain causal and iteration-speed benefits with a concrete example.

## Positive Validations

### V-001 — The native replay is an implicit deterministic root

**Observed.** The archive binds one exact Stage-5 replay SHA, route,
difficulty, stage, RNG seed, complete input digest, and zero Bomb presses.
The replay observer binds the selected native replay entry/stage, executable
identity, replay mode, route, difficulty, and stage before accepting gameplay.
Gameplay itself receives no injected solver input.

The root is implicit because TH08 reconstructs it by executing the same seed
and input prefix from the stage start. It is accurate but costs the whole
prefix on every branch.

### V-002 — The 36-file generator preserves causal future recomputation

**Observed.** The generator rejects Bomb masks, verifies exactly 36 complete
mask identities, preserves the input prefix and post-interval input suffix,
and decode/encode-verifies every output. The audit's `/tmp` run completed all
36 files.

Because only replay command words are changed, not recorded bullets, bodies,
or RNG values, the original executable can recompute an action-conditioned
world for the resulting active-input stream. Native acceptance and first
divergence of a re-encoded branch remain unverified.

### V-003 — Current authority labels fail closed

**Observed.** The branch manifest says `physical_authority=false`; the root
slice says `physical_predictive_authority=false`; missing requirements are
enumerated; crossed captures remain incoherent; and even a coherent
byte-complete slice would not claim executor authority. These boundaries are
consistent with the formal control and future-body contracts.

## Findings

### F-001 — The replay branch design is a real counterfactual world branch,
but only for a declared open-loop input stream

**Observed.** `th08_replay_causal_branch_corpus.py` preserves the source input
prefix, replaces a declared interval with each of the 36 no-Bomb complete
masks, restores the source input suffix, round-trips each `.rpy`, and names
the original TH08 executable as the future-world executor.

The altered branch does not replay recorded world state. TH08 starts from the
same stage replay seed/prefix and consumes future RNG according to the events
caused by that branch. This avoids CE-0197's impossible action/world Cartesian
product.

The continuation is nevertheless the old replay input stream. It is a valid
declared open-loop continuation, not an observation-conditioned policy and
not yet an exact multi-decision no-hit witness.

### F-002 — Replay removes fresh-run RNG confounding, but does not remove all
native execution cost

**Observed/inferred.** Repeating one content-addressed replay supplies the same
initial stage seed and input prefix, so action A/B results are paired rather
than incomparable fresh RNG samples. It also retains original ECL, pool,
damage, geometry, lifecycle, and RNG semantics.

Current tooling still replays from the stage start in the original Windows
process. It has no batch runner for all 36 branches, no proven render-skipped
acceleration, and no fixed-process root restore. Generating 36 `.rpy` files
is fast; executing them is not yet the final high-speed tunnel.

### F-003 — The canonical first-hit replay coordinate is not yet established

**Observed.** Baseline native replay saw the first hit at manager frame 12,322.
The retained input-alignment audit has only 60.892% best mask agreement and
47.878% best transition agreement. A branch/root coordinate of 8,715 is
therefore not yet justified by the retained alignment artifact.

Before attributing any alternative-mask result, the implementation needs an
exact replay-callback/native-update coordinate or a native callback serial
that identifies the changed replay word and first divergent physical update.

### F-004 — The native root capture is currently a mounting fixture, not a
branchable save state

**Observed.** The root module explicitly reports
`native_root_bytes_only_no_predictive_authority`; fixed pointer roots do not
stand in for their dynamic pointees, and even a byte-complete coherent slice
would report `complete_root_bytes_without_executor_authority`.

The fifth concurrent attempt retained all 15 declared component blobs under a
`519.8315-ms` whole-process suspension. Its byte bracket is coherent at
`12316 -> 12316`, but its authority status remains
`partial_native_root_inventory`. The retained architecture note says only
ordinary template/pool,
motion/lifecycle bytes, and the exact shared RNG root presently satisfy whole
requirements. Main/aux VM pointees, timeline/runtime image, player shot and
resource state, scheduler/transition state, damage/phase coupling, bullets,
lasers, items, callbacks, and exact world-position execution remain open.

### F-005 — Three failed replay-length capture attempts expose exactly the
iteration anti-pattern the wind tunnel should remove

**Observed.** The first three frame-8,715 capture trials each spent an
original-game replay run to discover deterministic capture-schema errors.
The current static spec captures one `0x53D0` template followed by 480 pool
slots, while the decoder version observed at the third failure accepted only
480 strides starting at offset zero. A focused product-spec fixture was then
added concurrently. The fourth attempt passed that shape gate but exposed the
next real boundary: externally reading the current approximately 20.55-MiB
fixed slice did not fit in one manager-frame bracket. The fifth attempt
obtained stable bytes only by pausing the game for about half a second.

About 10.30 MiB of that transaction is a duplicate read: the
`ordinary_enemy_template_and_pool` region already contains the entire
480-slot pool that `ordinary_enemy_ecl_and_callback_roots` captures again.
Canonical disjoint physical regions with multiple semantic requirement
annotations, followed by separate dynamic-pointee capture, should remove this
duplicate before another physical bracket experiment. If the remaining
transaction still crosses, an in-process preallocated frame-boundary copy is
the appropriate next mechanism.

### F-006 — Whole-process suspension makes the bytes atomic, not automatically
a canonical physical-update root

**Observed/inferred.** The concurrent implementation now wraps root reads in
`NtSuspendProcess`/`NtResumeProcess`. v5 confirms that this prevents the
manager-frame word from changing while the approximately 20.55-MiB
transaction is copied: the bracket is `12316 -> 12316`, suspension duration
is `519.8315 ms`, resume is recorded successful, and the native replay later
reproduces the first hit at frame 12,322. This is appropriately
diagnostic-only.

Suspension can occur at an arbitrary instruction inside priority 9, timeline,
enemy-slot, collision, or priority-17 work. An equal manager-frame word before
and after the frozen read proves byte stability, not that every subsystem
belongs to the same declared post-update phase. A snapshot suspended halfway
through the 480-slot enemy loop is atomic but not a valid controller decision
root.

Before executor use, the capture needs a revalidated phase boundary: for
example a one-shot in-process copy at a verified scheduler callback epilogue,
or an equivalent hook/event handshake whose pre/post phase serial and
component invariants are retained. Any native execution after an arbitrary
whole-process pause is timing-contaminated and cannot support real-time
delivery or physical survival claims.

## Implemented Versus Intended Wind Tunnel

| Layer | Intended role | Current observed state |
| --- | --- | --- |
| Replay acquisition | Save one no-Bomb canonical stage history and archive it by content | Implemented; one Stage-5 replay archived and parsed |
| Baseline native replay | Reproduce the same native scene and locate the canonical first hit/root | One first hit observed; replay/native coordinate remains unresolved |
| Replay input encoder | Build alternative active-input streams without copying future world state | Implemented and offline round-trip tested |
| All-36 root corpus | Cover every no-Bomb complete mask | File generation works; no mutated branch has native execution evidence |
| Actuator-history composition | Expand one desired mask into every reachable asynchronous active-mask history | Existing scalar/native recurrence exists elsewhere; not composed into replay corpus |
| Native branch runner | Launch, bind, stop at root plus horizon, and retain comparable fingerprints for every branch | Single-replay observer exists; no 36-branch batch runner/report |
| Explicit native root | Capture one complete, canonical decision-phase process root | 15 fixed blobs captured coherently under suspension; phase remains arbitrary and seven semantic requirements are missing |
| Exact-prefix executor | Start from explicit root and run supported native-order event classes | Partial simulator/lifecycle slices only; complete future producer absent |
| First-mismatch differential | Compare original TH08 and product state at every supported phase | Existing event-class differentials; no replay-root full-prefix differential |
| Robust witness solve | Find a no-hit policy over action, pickup/cadence, RNG/world, and observation branches | Not available for this physical root |
| Native candidate replay | Reproduce the winning fixed-root active-input history in original TH08 | Not yet attempted |
| Focused live falsifier | Exercise sensing, publication, `SendInput`, pickup/no-write, and deadline | Remains the final sparse physical gate |

## P-001 — Concrete Two-Level Wind-Tunnel Workflow

The recommended workflow uses native replay first and the repository executor
second:

```text
one focused physical stage
        |
        v
content-addressed .rpy (seed + input stream)
        |
        +--> baseline original-TH08 replay
        |       |
        |       +--> exact first-hit/root coordinate and native fingerprints
        |
        +--> desired mask u in all 36
                |
                +--> every reachable active-mask history h from actuator model
                        |
                        +--> mutated replay prefix + h + declared continuation
                                |
                                +--> original TH08 native trace
                                +--> own exact-prefix trace
                                           |
                                           v
                                  first differing phase/field
                                           |
                                  fix one event class, rerun offline
                                           |
                                  exact/robust no-hit witness
                                           |
                                  native replay confirmation
                                           |
                                  one focused live physical falsifier
```

For one controller action the correct finite unit is not merely:

```text
one desired mask -> one replay word
```

It is:

```text
one desired mask
  -> nature's reachable ordered pickup/publication histories
  -> action-conditioned TH08 worlds for those histories
  -> observation-compatible successor merging
```

The controller chooses the desired mask before nature chooses pickup,
cadence, scheduler, RNG/world, and hidden schedule branches. The next
controller action is chosen only after branches produce different complete
observations.

### Concrete first-hit example

Assume root `R` is fixed 40 physical updates before a fresh hit and the
controller considers complete mask `u`.

1. The actuator oracle enumerates histories such as “old mask for one update,
   an ordered intermediate mask for one update, then `u`” and “old mask for
   two updates, then `u`.” These are nature branches of one controller choice,
   not separate clairvoyant choices.
2. One replay stream is produced for each active-mask history. Every stream
   has the same replay SHA-derived root seed and identical prefix.
3. Original TH08 runs each stream. Direction changes aimed geometry; Focus
   changes body gates; Shot/damage may change RNG consumption, enemy death,
   item state, and later births. None of those future values is copied from
   the baseline replay.
4. The product executor advances the same root/history. At each native phase
   it compares input/mode, RNG state and call count, timeline PC, ordered
   allocation generation, VM/callback state, body/flag/world geometry,
   bullet/laser/item pools, resources, and collision state.
5. If the first mismatch is, for example, an RNG call before a timeline
   allocation at root+2, later collision labels are ignored. The RNG/event
   class is corrected and the deterministic corpus reruns.
6. Only after every reached mutation is exact or conservatively enclosed may
   the solver call the horizon a no-hit witness.

The current one-frame corpus restores the source replay suffix. That is useful
for a root-action probe, but a longer witness must encode its entire declared
continuation or recursively choose later actions from observable state.

## Why This Is Better Than Fresh Physical Hit Counts

| Question | Fresh full physical run | Fixed-root wind tunnel |
| --- | --- | --- |
| Initial world | New RNG and accumulated route/resource history | Same content-addressed seed/root/prefix |
| Actions sampled | One controller trajectory | All 36 desired masks and declared timing histories |
| Primary signal | Aggregate hits after deaths contaminate later state | First hit, exact horizon, and first differing native field |
| Causal comparison | Unpaired and often ambiguous | Paired at the same root |
| Reproducibility | Low across runs | Deterministic corpus and immutable versions |
| Mechanics accuracy | Original engine | Original engine for native oracle; executor only within passed coverage |
| Live delivery | Included but confounded with mechanics | Deliberately deferred to focused physical gate |
| Iteration cost today | One long run per guess | File generation is fast; native replay still pays the prefix |
| Intended iteration cost | Still one long run per guess | Root-local exact executor pays only the short horizon |

The immediate gain is **information quality and variance removal**, not yet a
large native wall-clock speedup. The baseline replay took roughly 160 seconds
including launch/menu/observation. Replaying 36 branches serially from the
stage start would be on the order of 96 minutes before overhead. The actual
speed breakthrough arrives when either:

1. an accelerated original-engine stepper passes normal-speed per-frame
   fingerprint parity; or
2. the explicit root and fail-closed exact-prefix executor allow all branches
   to begin at `R`.

Until then, native replay is still valuable because an unattended,
deterministic 96-minute corpus can answer 36 paired questions once, whereas
several fresh physical runs can consume similar time and still answer none of
them causally.

## Immediate Gate Order

1. Close replay-record/native-phase identity with a verified callback serial
   or hook boundary. Do not infer root index from the current low-agreement
   correlation.
2. Native-load an input-identical re-encoded replay and require per-frame
   baseline fingerprints to match the original replay.
3. Native-load a three-branch smoke corpus: unchanged mask, one direction
   change, and one Focus/Shot identity change. Require the first divergence at
   the declared replay callback and no earlier state drift.
4. Add the asynchronous actuator-history expansion; rename the existing
   one-replay-per-final-mask corpus as an ideal active-input slice until then.
5. Make the root transaction physically disjoint, remove the duplicated pool
   read, and capture dynamic pointees with exact owner/version checks.
6. Replace arbitrary-time whole-process suspension with a verified
   decision-phase in-process snapshot boundary before executor authority.
7. Retain a compact native fingerprint schema and a first-mismatch report.
8. Extend the product executor in native update order, returning `UNKNOWN`
   before every unsupported mutation.
9. Only after a candidate wins the complete declared fixed-root recurrence,
   run native replay confirmation and one focused live physical gate.

## IDA / Native Revalidation Backlog

No IDA database mutation was made by this audit. Before the next authority
step, revalidate and retain:

1. the exact replay input-record consumption callback, its record index/frame
   coordinate, and its priority relative to player/enemy updates;
2. one canonical controller-decision or post-update scheduler boundary at
   which a root may be copied without mid-loop mixture;
3. every dynamic pointee owner/version required by the fixed root inventory;
4. the update-phase fingerprints needed to localize first mismatch without
   relying only on `enemy_manager_frame`; and
5. whether replay end/phase timing can truncate a divergent short branch.

The connected database identity for this audit is recorded in the metadata
header. Inherited names/comments remain hypotheses except where the current
authority notes explicitly record revalidation.

## Verification Matrix

| Claim | Evidence | Result |
| --- | --- | --- |
| Exact archived Stage-5 replay identity/no-Bomb input | Archive manifest and native replay contract | Passed |
| Baseline replay launches and reaches native first hit | `native_replay_stage5_slot15_first_hit_20260730.json` | Passed for one replay; first hit frame 12,322 |
| Replay/native input coordinate is exact | Retained alignment candidates | Failed/open |
| 36 replay files preserve prefix, selected interval, suffix, and no-Bomb | Audit `/tmp` generation plus decoder round trip | Passed offline |
| Re-encoded replay is accepted by TH08 | No native branch execution artifact | Not tested |
| Mutated replay diverges first at requested input callback | No native branch execution artifact | Not tested |
| Root fixed-region bytes can be captured | v5 root artifact and local component files | Passed as stable bytes |
| Root bytes are stable during capture | v5 suspension and bracket `12316 -> 12316` | Passed |
| Root is at a canonical decision/update phase | Suspension occurs at an unverified arbitrary instruction boundary | Failed/open |
| Root inventory is semantically complete | Seven explicit missing requirements | Failed/open |
| Product can execute all reached event classes | Current producer contract and simulator boundary | Failed/open |
| One exact no-hit witness exists at this root | No completed branch/native result | Unresolved |
| Live controller can deliver the witness | No candidate or focused gate | Unresolved |

## Verification Commands And Results

```text
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_th08_native_future_body_root.py'
12/12 passed.

Focused replay/archive/observer/save/supervisor files:
4 + 1 + 2 + 7 + 2 + 34 = 50 tests passed.

PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_th08_runtime_agent.py'
17/17 passed.

PYTHONPATH=scripts python3 \
  scripts/analysis/th08_replay_causal_branch_corpus.py \
  artifacts/replays/archive/th8_15_d83b98a2...b68782.rpy \
  /tmp/th08-replay-audit.dgSuwr/branches \
  /tmp/th08-replay-audit.dgSuwr/report.json \
  --stage-index 5 --root-frame 8715 --hold-frames 1
Generated and round-trip verified 36/36 no-Bomb replay files in 8.5 seconds.
No generated branch was launched in TH08.
```

## Non-Actions

- No repository or authority-document file was edited by this audit.
- No source, test, artifact, or concurrent change was staged or committed.
- No IDA name, type, comment, or database object was mutated.
- No native replay, physical gameplay, controller input, or Windows process
  was launched by this audit.
- The only generated branch corpus is under
  `/tmp/th08-replay-audit.dgSuwr/`; it was used for offline encode/decode
  verification and not installed into the game replay directory.
- Existing concurrent replay/root artifacts were inspected but not adopted as
  this audit's outputs.

## Conclusion

The workspace is pursuing a sound and potentially transformative iteration
architecture. Replay is not the finished simulator; it is the deterministic
native oracle and implicit-root mechanism that can bootstrap one. The current
code can acquire/archive a fixed Stage-5 replay, observe its first hit,
generate 36 immutable alternative input files, and capture stable fixed bytes
under suspension. It cannot yet map the canonical replay input coordinate
exactly, execute any mutated branch in native TH08, represent actuator timing
histories in that corpus, produce a complete canonical native root, or solve
and validate a no-hit witness.

The decisive next result is therefore not another hit-count run and not
another broad root dump. It is one three-branch native replay differential
whose changed callback is exact, whose first divergent native field is
retained, and whose unchanged branch matches the original replay. That closes
the first real wind-tunnel cell. The complete high-speed tunnel then grows
from that cell one event class and one bounded horizon at a time.
