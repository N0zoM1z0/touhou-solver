# TH08 Lunatic NMNB Program Review And Roadmap

Date: 2026-07-29 (Asia/Singapore)

Workspace: `/home/pentester/coding/codex_ida/th08`

Review baseline: branch `main`, pre-documentation HEAD
`f28e13ca853280acec585f6296d947aafcabcaad`

Latest executable-code checkpoint at review time: `e4e266f`

Latest physical-code checkpoint at review time: `3f02ff1`

Latest retained complete physical workload at review time:
`lunatic_route2_stage5_unattended_20260729_125453`

Current execution progress:
`lunatic_route2_stage5_unattended_20260729_154229` passed the first
observer-off Stage-5 threshold at ten hits, but unchanged consecutive run
`lunatic_route2_stage5_unattended_20260729_161313` took 18. CE-0183 resets
the sequence and stops `PHYS-BASE-RING` before Stage 3. The later fixed
`SEM-TIMER` falsifier
`lunatic_route2_stage5_unattended_20260729_173957` took 12 hits and therefore
failed its `<=10` physical threshold. CE-0184 retains the failure and its
canonical first-hit audit; the timer-aware live consumer begins only after
the first six hits, so no timer rollback is causally justified. Checkpoint
`225ccc8` subsequently passes the `SEM-SCALE-A` exact primitive gate on
Linux and Windows. Checkpoint `6a71ac1` passes the `SEM-SCALE-B` offline
identity/consumer authority gate and makes root-only live coverage terminate
as explicit `UNKNOWN`. Checkpoint `1f639ef` passes the `SEM-SCALE-C1`
retained Final-B physical-root/conditional-player-replay gate over 230
quarter-scale rows. Checkpoint `555bbf8` passes the isolated-source
`SEM-SCALE-C2/C3` causal Final-B/static-Extra product-oracle gate plus one
exact historical restore transition. Checkpoint `f63b7ce` retains a passing
native-replay C4 complete-source capture for the narrow Final-B spell-190
scene; its source has no callback-28/29 side effect. The default-off C5 live
delivery implementation passes its Linux/Windows gates, but its fresh focused
physical falsifier and broader callback-28 hazard-side-effect authority
remain open. No scale-sensitive strategy or physical scene is promoted.

Companion native audit:
`notes/review/TH08_NATIVE_TO_SOLVER_READ_ONLY_AUDIT_20260729.md`

Document role: a reviewed implementation and evidence program. It does not
silently promote any shadow/proposed strategy, replace a formal contract, or
reinterpret a failed physical gate as passed.

The original review checkpoint changed documentation, indexes, authority, and
counterexample retention only. Subsequent dated execution entries implement
the accepted roadmap and may include solver corrections, retained evidence,
and evidence-backed IDA names/comments. They still do not silently authorize
strategy promotion, input injection, or a physical trial outside the current
gate.

## 1. Evidence Labels And Review Boundary

- **Observed** means directly visible in shipped instructions/dataflow,
  current source, a deterministic reproduction, or retained runtime evidence.
- **Inferred** means supported by multiple observed facts but not directly
  proved by a controlled physical comparison.
- **Hypothesized** means plausible and worth testing, but missing a decisive
  fact.

The review read the complete current handoff and strategy ledger, the formal
chain named by `START_HERE.md`, the recent G3–G5, delivery, combat, run, and
counterexample notes, current implementation paths and tests, and the moved
native audit. Selected high-impact native claims were rechecked against the
connected IDA database and current source.

The audit was originally made against code checkpoint `d85cca1`. The diff
from `d85cca1` through the review baseline changes launch/report retention,
repo skills, documentation, and supervisor artifact placement, but no
solver-semantic path implicated by F-001–F-020. Therefore the semantic
findings remain current at `f28e13c`; they are not stale findings from an
obsolete solver.

## 2. Executive Verdict

The project is a serious, evidence-rich control system, not an early
prototype. It already has:

- native process sensing and packed hazard decode;
- a hard no-Bomb actuation policy;
- explicit cadence, pickup-delay, held/pending/no-write semantics;
- versioned publication and fail-closed issue-time checks;
- native/Python differential oracles;
- coarse robust viability plus exact restricted lower-witness work;
- retained physical traces, compact reports, first-hit attribution, and
  cleanup supervision; and
- a disciplined distinction between live, shadow, proposed, and rejected
  work.

But the current system is not yet close enough to claim Lunatic NMNB
readiness. The review baseline Stage-5 run had 18 native hit edges and zero
Bombs. The first post-review observer-off control returned to the ten-hit
boundary, but its unchanged consecutive control returned to 18 and rejected
stable recovery. More importantly, the finite model still commonly loses all
global viability before contact, while several native semantics used by
movement, hazard, and future-event projection are either incomplete or
wrong.

The main conclusion is:

> The next leap is not a larger beam, a generic learned policy, or more G5
> delivery plumbing. It is a controlled recovery of physical-model
> authority, followed by earlier preservation of viable space and only then
> performance and route/resource optimization.

There are two immediate tracks, in this order:

1. preserve the current uncontaminated physical baseline by completing the
   already-fixed observer-off Stage-5 control gate;
2. before broad G5 or planner optimization, repair the model semantics that
   can make a certificate optimistic, version the corrected model, and
   revalidate its offline and physical authority one change at a time.

These tracks do not conflict. The observer-off gate diagnoses the current
18-hit regression without changing the system. The semantic repair program
is required even if that control gate recovers the historical eight-to-ten
hit range.

Physical evidence is a promotion requirement, not a final ceremonial check.
Every behavior-changing semantic, planner, combat, resource, or actuation
intervention needs a fresh focused physical falsification gate on the workload
that exercises it. Before integrated full-route promotion, the corrected
stack must also pass the four mandatory Lunatic scenes: Stage 3, Stage 4A,
Stage 5, and Final B. A tiny implementation checkpoint does not need four
game launches when one scene is the only causal workload; the integrated
model version does.

## 3. Program And Binary Identity

### 3.1 Connected IDA database

**Observed:**

- loaded program: `th08.exe`;
- IDA image base: `0x00400000`;
- input size reported by IDA: `840704` bytes;
- IDA metadata MD5:
  `454c96e08fe3c14df7064d104c26accf`;
- IDA metadata SHA-256:
  `ec101fcff80b77e717d43b54e326375487af19661bb7c8d11a19ee5e0fbf928b`;
- the database image has the known no-life-decrement patch at
  `0x0044D0FA`: byte `0x00`;
- the clean WSL executable has byte `0xFF` at raw offset `0x4CEFA`,
  size `840704`, and SHA-256
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`.

IDA's input-file hash is provenance metadata, not a hash of every current
database byte. The bounded patch comparison and the companion audit establish
the intended database baseline: shipped TH08 plus the single known
no-life-decrement instrumentation byte. No analysis conclusion here treats
that patch as permission to ignore hits; every native hit edge remains a
failed no-miss attempt.

### 3.2 IDA quality boundary

**Observed:** the local-type catalog contains only `_SCOPETABLE_ENTRY`.
Useful inherited function names and comments exist, but the database does not
contain a complete typed representation of the ECL VM, enemy, player, bullet,
or laser structures.

Therefore all inherited names, pseudocode variables, and comments remain
hypotheses until instruction/dataflow and runtime evidence revalidate them.
This review made no IDA rename, type, or comment change. That sentence records
the completed read-only audit checkpoint; it is not a prohibition on the
correction program below. During an authorized fix/implementation phase,
strong revalidated conclusions should be renamed, typed, and commented in the
IDB, with misleading annotations corrected and material changes logged.

## 4. Current Live System And Authority

The current live decision path is:

```text
native game state
  -> packed bullet/laser/enemy sensing
  -> hazard projection and coarse Boolean viability
  -> native local beam proposal
  -> fresh issue-time local collision certificate
  -> fresh/global action transaction
  -> complete-mask issue or exact no-write
```

The controller is hard no-Bomb. Bomb bit `0x02` is not authorized.

| Surface | Current authority | Important limit |
| --- | --- | --- |
| Native sensing and packed decode | Live | Native fields are not all semantically complete. |
| Input cadence/delay/no-write recurrence | Formal and tested | CE-0120 still blocks a complete physical clock boundary. |
| Four-worker coarse Boolean viability | Live | 16-pixel lattice, 8-frame layer, 80-frame horizon; `empty` is a finite proxy. |
| Native local beam | Live proposal path | Accelerates the current model; does not prove it physically complete. |
| Fresh issue-time local certificate | Live safety check | Only as sound as sensed/projected geometry and transitions. |
| Exact stationary/partial witnesses | Offline/trace-only | Restricted policy classes and future coverage `UNKNOWN`; no live authority. |
| G5 future-event observers | Trace-only | Source, callback, RNG, geometry, and delivery coverage incomplete. |
| Supplemental V1–V6 delivery | Rejected/failed physical gates | Some exact sub-evidence retained; no survival or publication authority. |
| Combat/Power/unfocused work | Telemetry/proposed | Must rank only inside a proved viable and issue-safe set. |

Python/C++ parity currently proves implementation parity for the declared
proxy. It does not prove that the proxy answers the physical TH08 survival
question.

## 5. Physical Status Versus NMNB

### 5.1 Consecutive observer-off controls and previous comparator

**Observed latest result:** unchanged Stage-5 run `20260729_161313`
completed with 12,639 decisions, frames `2..45288`, 18 hits, zero Bombs,
accepted completion, and cleanup. Phase hits nonspell/103/107/111/115 were
`10/2/5/1/0`.

The two observer-off sessions have exact equal controller config, executable
identity/patch, physical code, stage/difficulty, native backends, hard
no-Bomb policy, optional flags, and starting Power/lives/Bomb stock. They are
not same-seed or same-history paired samples. Pass 2 first contacts at frame
2,524, player `(371.121,82.873)`, active `down_left`, Power 128, with 267
bullets and zero lasers. It is a modeled committed-prefix collision:
global viability was empty for 240 frames, the robust action set was empty
for eight, and usable pipeline warning arrived only at contact. CE-0183
retains this earliest failing state and resets the consecutive sequence.

The immediately preceding run `20260729_154229` completed with 11,710 decisions,
frames `2..42335`, ten hits, zero Bombs, accepted completion, and cleanup.
All optional observers and pipeline shadows were disabled. Phase hits
nonspell/103/107/111/115 were `5/2/1/1/1`; it was a provisional pass 1, but
the unchanged follow-up rejects consecutive recovery.

The canonical first hit is frame 10,740 at player
`(349.070,383.773)`, active `up_fast`, Power 128, 883 bullets, and zero
lasers. It is an exact same-epoch enemy-body overlap with signed AABB
clearance `-12.270`; the body was present in the causal, hit-decision, and
action snapshots. Global viability was exhausted nine frames before contact,
and robust/pipeline warning lead was two frames. All ten hits followed global
viability exhaustion. CE-0182 retains the causal boundary without attributing
it to optional observers or CE-0176.

For comparison, previous V6 Stage-5 run `20260729_125453` completed with
12,039 decisions, frames `2..44053`, 18 hits, zero Bombs, accepted completion,
and cleanup. The hit split is:

| Phase | Hits |
| --- | ---: |
| nonspell | 6 |
| spell 103 | 2 |
| spell 107 | 4 |
| spell 111 | 2 |
| spell 115 | 4 |

The canonical first hit is frame 731 at player position `(376, 432)`, before
any selected spell-107 auxiliary envelope. It follows global viability
exhaustion and has positive current pipeline clearance. Four retained contacts
have bullet overlap, none have laser overlap, and none has exact same-epoch
enemy-body overlap. Those labels are model diagnostics, not proof that the
remaining contacts are impossible physical collisions.

The run has 7,827 queried decisions with an empty action set. All 18 hit
windows occur after global-kernel exhaustion. Local planning timing remains
roughly `11.813/24.257 ms` at median/p95, and observed cadence is
`2/4` frames at median/p95.

### 5.2 What this proves

**Observed:**

- hard no-Bomb enforcement works for this completed workload;
- capture, report, completion, and cleanup paths are usable;
- viability loss is an excellent diagnostic boundary;
- one observer-off run can realize the historical band, but the next
  unchanged run can return to 18 hits;
- optional V6 observers are not necessary for an 18-hit realization; and
- current full-horizon/coarse authority is unavailable for a large part of
  Stage 5.

**Not proved:**

- that viability exhaustion is the unique cause of every hit;
- that the 18-hit result was caused by V6 code;
- that optional observers have zero effect in a paired physical history;
- that rolling back post-`3adad09` observer/refactor changes improves
  survival;
- that current empty roots are physically losing;
- that any one stage/RNG sample predicts a full-route NMNB rate.

The retained eight-hit checkpoints first contact after frame 11,500; the
observer-off pair first contacts at frames 10,740 and 2,524, whereas the
previous V6 sample first contacted at frame 731. No planner, recurrence,
ranking, or issued-mask change between these observer-off runs isolates the
aggregate difference. A rollback is therefore not causally justified.

## 6. Bounded Recheck Of The Native Audit

### 6.1 Overall assessment

The moved audit is substantially accurate. Every high-impact finding selected
for recheck is still present in current source and agrees with shipped
instruction/dataflow. The audit should be treated as the detailed evidence
record; this section supplies the authority and implementation disposition.

Two wording refinements are important:

1. F-011's retained focus/unfocus transition proves an omitted
   action-conditioned body-eligibility gate, but does not prove it caused a
   retained hit.
2. F-020 is genuine undefined behavior. Which single beam state survives an
   extreme-value reproduction is not stable evidence; the durable fact is
   that native code merges/drops states for values whose quantized key cannot
   be represented as `int64`, while Python arbitrary-precision keys remain
   distinct.

### 6.2 Revalidated native paths

The following were rechecked in the connected IDA database:

- `sub_447421`: ECL timer advance uses a fractional component and float32
  scaled addition, rather than a scalar integer timer;
- `0x004186F1`: opcode `0x05` writes elapsed time and preserves the
  fractional timer component;
- `sub_42C420`: enemy contact/damage gating writes enemy flag `0x800` from
  player secondary-character state;
- player focus transition at `0x0044B1D9`/`0x0044B42C`;
- player movement at `0x0044BA6A` onward multiplies displacement by
  `g_gameplay_time_scale`;
- the SHT player hitbox header is divided by two before storing player
  half-extents;
- laser motion at `0x00431BC9` multiplies speed by global gameplay time
  scale;
- bullet collision checks honor per-bullet suppression at `+0x10B4`;
- callback code at `0x00424ADE`/`0x00424B59` toggles that suppression and
  scales velocity.

Current source independently confirms the corresponding omissions:

- player and local-beam transitions use `speed * frames` without time scale;
- laser projection steps without global time scale;
- ECL product and test oracle both reduce timer state to one scalar;
- enemy-body decode removes every `flags & 0x830` body before action-dependent
  projection;
- `PLAYER_RADIUS` is `2.0`;
- every nonzero bullet state is treated as active/lethal;
- offline movement bounds are `0..384 x 0..448`;
- decoded callback auxiliary state is not consumed as a collision schedule;
- native trace cursor increment and extreme beam quantization lack safe
  arithmetic boundaries.

### 6.3 Finding disposition

| ID | Recheck result | Direction/authority effect | Ordered disposition |
| --- | --- | --- | --- |
| F-001 | Confirmed | Database baseline is usable with the declared instrumentation caveat. | Keep identity and patch verification in every physical preflight. |
| F-002 | Confirmed | ECL locals `10036..10039` map to `+0x58..+0x64`. | Preserve offsets; add types only after full structure validation. |
| F-003 | Confirmed | Variable `10050` is a three-component Euclidean norm. | Keep dynamic and fail-closed until its observation-time inputs are modeled. |
| F-004 | Confirmed | IDA type coverage is inadequate. | Add reviewed structs/enums incrementally; never bulk-apply inferred types. |
| F-005 | Confirmed | Opcode `0x87` replaces an auxiliary VM; it is not an interrupt. Shipped inputs stay within observed limits. | Correct terminology and add bounds/single-evaluation tests before extending it. |
| F-006 | Confirmed | Native ECL call depth 15 drops the caller rather than providing unbounded stack semantics. | Model the exact bounded stack or stop before overflow; retain an adversarial case. |
| F-007 | Confirmed, high | Product and alleged independent oracle share the same timer-fraction defect. Existing 108 cases all have fraction zero. | Replace state with native elapsed/fraction semantics and a genuinely independent oracle. Narrow the old exactness claim. |
| F-008 | Confirmed | Callback catalog omits custom/global/lethal effects. Direction is unknown. | Inventory callers and effects; unknown callbacks remain unavailable to hard coverage. |
| F-009 | Offsets confirmed; semantics incomplete | HP/damage telemetry is valid, but damageable/transition state is not complete. | Keep S18 telemetry-only; model transition state before kill/end authority. |
| F-010 | Confirmed, high | Laser projection without time scale is non-authoritative when scale differs from one. | Thread observed/versioned scale through native-equivalent float32 laser transitions. |
| V-001 | Confirmed | Runtime ECL normalization is correct for its declared input. | Retain. |
| F-011 | Confirmed, high | Focus/secondary-character history changes which enemy bodies can collide or receive damage; current future sensing can be optimistic. | Add action-conditioned player-mode state and body eligibility before unfocused action promotion. |
| F-012 | Confirmed | Native lethal player half-extent is `1.0`; solver radius `2.0` is conservative but compresses viability. | Separate exact physical hitbox from lattice/sampling margin and recertify. |
| F-013 | Confirmed, severe | Player reachability can be optimistic by multiples when time scale is below one. Final/Extra reach such states. | Correct before any full-route physical-model certificate. |
| F-014 | Confirmed | Native laser collision is a rotated local AABB, not the solver capsule. Observed error is mostly overblocking, but global direction is not certified. | Implement an independent scalar rectangle oracle and native-equivalent projection. |
| V-002 | Confirmed | Four native death-caller families are visible. | Use them to close the callback inventory; do not infer omitted custom effects harmless. |
| F-015 | Confirmed | Bullet fade state 5 is nonlethal; treating all nonzero states as lethal is conservative. | Model lifecycle explicitly and recertify safe masks/viable states. |
| F-016 | Confirmed | Offline bounds admit physically unreachable edge positions. This can be optimistic. | Unify the physical clamp `x=8..376`, `y=16..432` across all oracles. |
| F-017 | Confirmed native mechanism; route impact inferred | Route-2 focus/shot callbacks consume shared gameplay RNG, so actions can alter future births. | Capture/version RNG and callback state or branch conservatively before future-birth authority. |
| F-018 | Confirmed by deterministic crash | `INT_MAX + 1` in native derived observation produces signed-overflow behavior and a child `SIGSEGV` in the current build. | Validate before increment; fail closed; add sanitizer/boundary tests. |
| F-019 | Confirmed | Bullet collision suppression is observed but absent from collision projection, currently causing conservative false hazards. | Carry per-frame suppression state/schedule into the bullet model. |
| F-020 | Confirmed undefined behavior | Extreme finite quantization can merge/drop distinct beam states; normal live coordinates are currently bounded. | Check representability before conversion and keep a Python-key differential case. |
| V-003 | Confirmed for the declared default | Narrow player-shot model and boss-width rescaling agree with shipped behavior. | Retain, but do not generalize it to complete targeting/combat authority. |
| P-001 | Confirmed as the largest visible local-beam optimization target | Python marshals about 190 buffers for a 10-step request. | Optimize only after semantic version stabilization. |
| P-002 | Confirmed risk | Native scratch-vector reuse can reduce allocation tails but is reentrancy-sensitive. | Use owned workspace state and explicit concurrency tests. |
| P-003 | Confirmed | The full enemy-sensor tail carries useful state. | Keep sparse full-tail capture; do not truncate it for a small average saving. |

## 7. Effect On Existing Evidence And Certificates

The review does not erase earlier work. It narrows what each artifact proves.

### 7.1 Evidence that remains valid

- Retained physical hit/Bomb/resource/timing observations remain observations
  of the actual run.
- Input-pipeline cadence, delay-support, no-write, version, and causal
  quantifier counterexamples remain valid unless their own declared state is
  changed.
- Python/native parity remains valid as implementation parity for the exact
  model version tested.
- Radius-`2.0`, fade-lethal, and missing-suppression models are conservative
  in the identified dimensions. A verified winning witness under only those
  overapproximations is not invalidated by the true smaller hazard alone.
- The Phase-A ECL raw capture and local projection remain valid observations.
- The 108 retained opcode-`0x05` cases remain useful zero-fraction fixtures.

### 7.2 Evidence whose authority is narrowed

- Phase-B1 opcode-`0x05` “exact” parity is exact only for the retained
  zero-fraction, observed-scale slice. Its product and scalar oracle are not
  independent with respect to native timer representation.
- Any player/laser certificate that assumes unit time scale is not a
  physical certificate for a non-unit-scale history.
- Any future enemy-body or damage claim that ignores the focus transition is
  incomplete for actions that can change secondary-character state.
- Offline witnesses using `0..384 x 0..448` include unreachable roots and
  must be regenerated under the physical clamp.
- Future-hazard completeness cannot include action-dependent RNG, omitted
  callback effects, or bullet suppression/lifecycle until they are explicit.

### 7.3 No blanket rollback

The high-severity time-scale findings do not explain Stage-5 frame 731 unless
the retained state shows non-unit scale there; current evidence does not.
The conservative hitbox/lifecycle findings may explain unnecessary viability
loss, but not an unsafe collision. F-011 proves a missing action-conditioned
gate, but no retained hit has been causally assigned to it.

Therefore the correct response is model-version repair and controlled
revalidation, not deletion of history or speculative source rollback.

## 8. Gap To Lunatic NMNB

### 8.1 Survival gap

The immediate numerical gap is 18 Stage-5 hits to zero full-route hits.
Aggregate hit count understates the challenge: one early miss changes Power,
position, invulnerability, phase timing, and later hazard history. The
canonical first hit of each fresh attempt is the clean causal witness.

### 8.2 Physical-model gap

The solver does not yet preserve native:

- elapsed/fractional ECL timer evolution;
- global time-scale player and laser transitions;
- action-conditioned enemy contact/damage eligibility;
- exact player and laser hit geometry;
- bullet state/collision-suppression lifecycle;
- physical clamp bounds; and
- complete callback/RNG-conditioned future sources.

Some errors are conservative and destroy usable space. Others are optimistic
and prevent hard physical authority. Both must be fixed.

### 8.3 Viability gap

The coarse 16-pixel/8-frame/80-frame kernel frequently becomes empty. G3/G4
show that some Boolean-empty roots still have exact restricted full or
partial witnesses, but future coverage becomes `UNKNOWN`. This proves that
`empty` overloads discretization, horizon, uncertainty, and source-coverage
failures. It does not prove unrestricted physical loss.

### 8.4 Future-hazard gap

The G5 chain has excellent observation and provenance infrastructure, but no
complete all-source future-birth model. Main VM, auxiliary VM, callbacks,
native/deferred sources, source lifetime, transforms, action-dependent RNG,
and emission geometry must meet at one versioned causal boundary.

### 8.5 Delivery gap

Exact supplemental work has repeatedly failed Windows/live delivery despite
passing isolated semantics. V6 proves coalesced one-write composition and
exact replay for one event class, but fails compact tails, a
control-equivalent comparator, and survival. The issue thread cannot start
cold expansion.

### 8.6 Route/resource gap

Stage practice commonly starts at max Power. A real Lunatic Route-2 NMNB
attempt begins at Power 0. Damage, enemy kill/end timing, Power collection,
and phase exposure change the future hazard history. These are constraints
and subordinate objectives inside the viable set, not generic aggression
weights.

“Stage-3 Power-0 baseline” must be interpreted carefully. A route-faithful
run starts Stage 1 at Power 0 and reaches Stage 3 with whatever Power was
actually collected in Stages 1–2. Artificially setting Stage 3 itself to zero
or using max-Power practice answers a different question. Both practice and
route-prefix evidence are useful, but they have separate authority.

The retained evidence supports the following scoped judgments:

- **Observed:** all ten retained complete Stage-5 practices have a nonspell
  canonical first hit at Power 128. Nonspell contributes 60/128 hits over
  82,588/125,088 decisions; its absolute burden is high, but its hit rate per
  decision is below the combined spell rate.
- **Inferred:** opening and middle nonspell are a clean-route barrier worth
  isolating; the data do not establish that every nonspell decision is more
  dangerous.
- **Hypothesized:** some ordinary enemies have a kill-before-saturation
  deadline. Earlier verified kills may prevent later tracking/homing
  emissions.
- **Hypothesized:** spellcards remain survival-first, but “damage only affects
  bonus” is too strong. Scoring bonus is irrelevant to NMNB, while verified
  boss damage can shorten dangerous exposure. Phase compression is therefore
  a survival-equivalent tie-break, not a chase-through-pattern objective.
- **Hypothesized:** releasing Focus outside fine-dodge windows may use
  Sakuya's wider shot coverage to kill distributed nonspell enemies sooner.
  This cannot be promoted until focus-transition contact/damage gates and
  action-dependent RNG are modeled.
- **Observed boundary:** post-death Power recovery is useful diagnosis but
  cannot support the clean pre-loss NMNB policy.

### 8.7 Acceptance-evidence gap

The project has not yet retained one uncontaminated complete Lunatic Route-2
run with zero hit edges and zero Bombs. A planned route or offline witness is
not NMNB acceptance.

## 9. Ordered Program Toward NMNB

Every implementation phase below is a separate focused checkpoint. A phase
must preserve exact model/version identity, retain a falsifier, run the
smallest focused tests while iterating, and pass required Linux/Windows gates
before physical promotion.

### Physical evidence policy

Use two non-interchangeable physical layers:

1. **mechanics-focused practice:** starts from the practice workload's
   configured resources, isolates geometry/timing/phase behavior, and is the
   right first falsifier for one narrow intervention;
2. **route-faithful prefix or full route:** starts Stage 1 at Power 0,
   preserves earned items/Power, damage, position, RNG, and transition
   history, and is the only resource/route authority.

No offline or shadow result gains live authority without the focused physical
layer. No integrated model version proceeds to full-route NMNB acceptance
until all four mandatory scene families below have fresh compatible evidence.

| Workload | Why it is mandatory | Mechanics-focused gate | Route-faithful gate |
| --- | --- | --- | --- |
| Lunatic Stage 3 | Historical practice still has eight hits, with nonspell boundary pressure and spell-50 laser/action-lag failures. It is the first hard cross-stage and early-resource workload. | Fresh complete practice for geometry, cadence, delay, nonspell, and laser regression. Practice Power is not route authority. | Start Stage 1 at Power 0; retain every item/Power transition through Stage-3 entry and completion. |
| Lunatic Stage 4A | Reimu workloads expose dense bullets, ECL callbacks, enemy bodies, dialogue/frozen-manager behavior, and CE-0120/0121 actuator boundaries. | Fresh complete practice after timer/ECL/body/clock changes, with transitions and first-hit attribution. | Preserve the actual Stage-1–4A route state, earned Power, RNG, and dialogue history. |
| Lunatic Stage 5 | Current 18-hit control boundary and the canonical nonspell combat/Power/unfocused research workload. | First restore two observer-off controls at `<=10`; later test one preregistered nonspell intervention at a time. | Enter from the normal Power-0 route and retain source lifetime, kills/despawns, drops, pickups, Power, and first-hit history. |
| Lunatic Final B | Historical focused practice has 37 hits, 8,292/16,813 empty queries, nine laser overlaps, and strong boundary/funnel pressure. It directly exercises time scale, laser geometry, long-horizon viability, and phase transitions. | Fresh dominant-spell and complete Final-B practice after scaled movement/laser and geometry correction. | A complete compatible Route-2 run reaching and clearing Final B with accumulated resources is required for NMNB. |

Stage 1 and Stage 6B remain useful supporting regressions. They do not replace
any of the four mandatory scenes.

### Diagnostic and dynamic-debugging ladder

Dynamic debugging is needed selectively, not as the default gameplay method.
Use the least contaminating level that can answer the exact semantic question:

1. shipped instructions/dataflow in IDA plus current source;
2. deterministic Python/native oracle, retained replay, and adversarial
   capsule;
3. default-off, read-only, manager-frame-bracketed runtime probe with no live
   action consumer;
4. isolated controlled debugger session for one unresolved update-order,
   transition, callback, RNG, kill/despawn, item pickup, or time-scale fact;
5. clean focused physical A/B after the probe/debugger is removed.

Debugger stepping, breakpoints, Windows CLI focus theft, or instrumentation
that changes cadence makes that run diagnostic-only. It cannot satisfy a
survival or timing gate. Prefer bounded native tracing over interactive
single-stepping when timing/order can be observed without stopping the game.
Record executable/model identity, exact address/field, trigger, pre/post
state, thread/frame context, and whether the observation is static, probed, or
debugger-contaminated.

### External reverse-engineering references

A bounded GitHub search identified and locally cloned two useful candidates
outside this repository:

- `thpatch/thtk` at commit
  `892114a0fcaa0bbdaaecf3cb4ad56f758683fb40`, under
  `/home/pentester/coding/codex_ida/external/thtk`;
- `Priw8/eclmap` at commit
  `f146162e330c27d1b0a8880c3a41884615147a11`, under
  `/home/pentester/coding/codex_ida/external/eclmap`.

**Observed:** thtk supports TH08 archive and ECL/MSG/STD disassembly and
reassembly. Its `thecl/thecl06.c` contains a TH08 opcode parameter-format
table. The companion `th08.eclm` supplies community mnemonic candidates for
TH08 ECL and timeline instructions. No complete TH08 executable
decompilation was found in this bounded search; the prominent decompilation
project found was for TH06.

Use these repositories as hypothesis generators and independent file-format
or script-disassembly aids, not native authority. In `SEM-SOURCE` and
`COMBAT-GEN`, decompile owned TH08 stage ECL, diff opcode/signature coverage
against the current parser, and turn disagreements into targeted IDA
instruction/dataflow/caller/callee checks and bounded probes. Do not import
mnemonic meanings, callback semantics, update order, kill/despawn behavior,
or executable structure without revalidation against this exact shipped
build. The cloned `eclmap` snapshot exposes no license file, so do not copy
its mapping content into this repository; record only independently
revalidated facts. Neither external project was built or executed in this
planning checkpoint.

### Phase 0 — Preserve the current causal baseline

Do this before source changes:

1. run current code on Lunatic Stage 5 with every optional observer off;
2. retain the complete outcome and canonical first-hit dossier;
3. require two consecutive runs at `<=10` hits;
4. after Stage 5 passes, take one fresh current-code observer-off
   mechanics-focused control each for Lunatic Stage 3, Stage 4A, and Final B;
   record their practice resource initialization and do not treat it as
   route-faithful Power evidence;
5. if any control materially fails, compare the first clean hit against the
   eight-hit checkpoints by exact physical state, geometry, viability age,
   cadence, delay root, action, and phase—not aggregate count;
6. if the four-scene current-code ring is stable enough for characterization,
   run one complete Lunatic Route-2 hard no-Bomb control from Power 0;
7. do not mix Focus/unfocused, targeting, Power, G5 delivery, worker,
   priority, affinity, or planner changes into this control.

Exit gate: two consecutive accepted observer-off Stage-5 controls at no more
than ten hits, fresh compatible Stage-3/4A/Final-B characterization, and one
route-faithful full-run control; or a retained causal counterexample that
names the first failing state/contract. A failure opens a correction; it does
not authorize threshold weakening or uncontrolled expansion.

Execution progress on 2026-07-29:

- **Observed:** `20260729_154229` completed the exact observer-off contract at
  ten hits, hard no-Bomb, accepted artifacts, and cleanup. This is
  the isolated threshold pass.
- **Observed:** the canonical first hit is CE-0182, an enemy-body overlap
  after global viability exhaustion; it does not establish observer or
  focus-mode causality.
- **Observed failure:** unchanged `20260729_161313` then completed at 18 hits.
  Its frame-2,524 modeled committed-prefix first hit follows global viability
  loss by 240 frames and robust-action exhaustion by eight. Equal config,
  code, flags, and starting resources rule out those variables for the pair;
  unmatched physical/RNG history prevents a paired causal claim.
- **Exit taken:** CE-0183 names the earliest failing state, resets the
  sequence, and stops physical expansion. Do not run Stage 3 or another
  unchanged Stage-5 repeat now.
- **Next gate:** begin Phase 1 at `SEM-TIMER`, retain an independent native
  transition oracle and versioned correction, then take the smallest physical
  falsifier required by the corrected primitive.

### Phase 1 — Freeze and repair native transition semantics

This phase is correction work, not investigation-only review. For each strong
native conclusion, update the IDB rename/type/comment after checking
instructions, dataflow, relevant callers/callees, and available runtime
evidence. Record exact material IDB changes in the daily research shard and
keep inherited, revalidated, corrected, and unresolved labels distinct. Do
not bulk-apply inferred structs or let a convenient annotation substitute for
native evidence.

#### 1A. Native timer contract

- represent ECL time as native elapsed integer plus float32 fraction;
- specify float32 rounding, scaled addition, carry, branch/reset behavior,
  and serialized identity;
- build an independent raw-transition oracle that does not share product
  timer representation;
- add nonzero-fraction, non-unit-scale, carry, negative/edge, and opcode
  `0x05` preservation fixtures;
- regenerate the 108 retained cases without changing their historical blob.

Exit gate: product, independent Python oracle, and a tiny native probe agree
bitwise over deterministic and adversarial cases. Old Phase-B1 authority is
explicitly tagged as the zero-fraction slice.

Execution progress on 2026-07-29:

- **Observed native contract:** IDA revalidation confirms the component
  helper at `0x00447421`, exact integer-time equality at `0x004185AF`, and
  fraction-preserving opcode-`0x04`/taken-`0x05` write at `0x004186F1`.
  Evidence-backed function/type/comments are persisted in the IDB and logged.
- **Observed offline gate:** versioned product, structurally independent
  raw-bit Python oracle, and Linux/Windows x87 probes agree on 17/17
  deterministic/adversarial cases per platform. Complete Linux and repeated
  complete Windows discovery pass 1,075 tests; the initial Windows
  CE-0166-compatible timing-tail failure is retained as a failed first
  attempt rather than hidden.
- **Observed retained replay:** the immutable V1 108-case fixture remains the
  zero-fraction/unit-scale historical slice. The V2 component replay decodes
  all 3,117 in-scope Stage-4A rows, preserves 108 unique cases with zero
  mismatch, and grants no new completion.
- **Propagation:** the offline VM-local shadow, existing live velocity
  lookahead, and trace-only birth lookahead now share exact component timer
  state under distinct immutable semantics versions. Decision traces include
  fraction bits, scale bits, and component identity.
- **Exit taken:** the Phase-1A offline semantic gate passes. Because an
  existing live hazard consumer changed, executable/physical code is fixed at
  `e309c81`. The program therefore required the exact observer-off Stage-5
  physical falsifier before `SEM-SCALE`. One accepted result would not
  establish NMNB or timer causality; a result above ten stops and opens a
  first-hit audit.
- **Observed physical failure:** fixed observer-off run
  `20260729_173957` completed hard no-Bomb Stage 5 with 12 hits
  (`7/2/2/0/1` by nonspell/103/107/111/115), accepted artifacts, and exact
  cleanup. It fails the preregistered `<=10` threshold, so no Stage-3/4A/
  Final-B expansion or same-version repeat is permitted.
- **Observed causal boundary:** the canonical committed-prefix hit at frame
  2,069 follows global viability exhaustion at 1,829 and robust-action
  exhaustion at 2,063. The timer-aware consumer first appears at frame
  21,751; the canonical and first six hits precede it. Aggregate failure
  therefore does not causally reject or justify rollback of SEM-TIMER.
- **Observed integration slice:** all 3,940 timer-aware rows carry the
  expected component/lookahead versions. Per-session affine inference selects
  Stage-5 runtime base `0x0B1D0048`, maps all 33 unique roots, and yields
  3,835 future plus 105 equal roots with zero past/unmapped roots. Every
  physical fraction is zero and scale is `1.0`, so nonzero-fraction/nonunit
  scale physical authority remains open.
- **Exit taken:** CE-0184 retains the failed physical threshold and stops
  repetition. With no timer-causal rollback target, continue the ordered
  correction program at `SEM-SCALE`; do not promote SEM-TIMER to survival
  authority.

#### 1B. Player and laser time scale

- add observed scale to immutable model identity;
- implement native-equivalent float32 player and laser stepping;
- distinguish “scale observed constant over the declared horizon” from
  unobserved future scale changes;
- fail closed or branch over supported future scale transitions; never
  silently hold the root value forever;
- compare current optimized paths to independent scalar recurrences.

Exit gate: zero mismatch over unit/non-unit scales, stop/resume, direction
change, laser phase change, and retained Final/Extra scale capsules. No
full-route certificate uses the old transition.

Execution progress on 2026-07-29:

- **Observed native contract:** revalidated player stores at
  `0x0044B641/0x0044BA67/0x0044BAA8`, laser motion/timer order at
  `0x00431BC9..0x004320ED`, callback writers `0x00424F90`,
  `0x004251B0`, and `0x00425290`, and priority order
  player 9 -> enemy/ECL 11 -> laser/bullet 14. A same-update ECL write can
  therefore change the laser scale after player motion.
- **Corrected model boundary:** immutable schedules carry separate exact
  player- and laser-phase float32 prefixes. A post-update root observation
  proves one next-player value and no next-laser value; it is never repeated
  silently across a certificate horizon.
- **Observed SEM-SCALE-A gate:** product, independent raw-bit Python oracle,
  and explicit-x87 Linux/Windows probes agree bitwise on 17/17 deterministic
  cases per platform (36 player and 44 laser steps). A separate seeded sweep
  covers 4,096 player and 2,048 laser cases with zero mismatch. Complete
  Linux/Windows discovery passes 1,084 tests; Windows has the three existing
  skips.
- **Observed SEM-SCALE-B gate:** checkpoint `6a71ac1` carries immutable
  schedule identity through live capture, local/issue requests,
  committed-prefix and beam stepping, robust certificates, laser lowering,
  corridor artifacts/versions, traces, and audit capsules. Complete
  constant non-unit Python/native local-beam outputs and optimized/scalar
  certificate safe-action/CVaR labels agree. Root-only/short local and
  corridor schedules are explicit incomplete `UNKNOWN`; the current coarse
  corridor also reports complete non-unit or varying schedules as unsupported
  `UNKNOWN`. Complete Linux/Windows discovery passes 1,087 tests; Windows
  keeps three existing skips.
- **Authority boundary:** SEM-SCALE-A/B and isolated-source C1/C2/C3 pass
  their declared offline/retained slices; C4 passes one read-only physical
  complete-source row. C5 now physically passes exact live schedule delivery
  for one contaminated spell-190 restore interval, but this authority is
  version- and source-local. It does not establish clean player state,
  pre-target transport, stage-wide source completeness, corridor support for
  varying scale, survival, or strategy promotion.
- **Observed SEM-SCALE-C1 root capsule:** checkpoint `1f639ef` binds the
  three existing Final-B raw sessions and retains 68/78/84 spell-190 rows at
  binary32 scale `0.25`. All 230 read-lag horizons are zero or one, so root
  scale covers that conditional replay; 113 old unit-scale projected
  positions change and maximum delta is `3.000020432` pixels. All selected
  rows have zero active lasers and no Bomb emission. The reconstructed
  historical movement input is an inference, not native active-input proof;
  repeated-root multi-frame control output is explicitly noncausal. This
  completes only the compact Final-B root and conditional player-position
  slice. Action certificates, complete live source coverage, trace-only, and
  physical survival remain open.
- **Observed SEM-SCALE-C2/C3 isolated-source gate:** checkpoint `555bbf8`
  implements the causal player-before-ECL/laser-after-ECL producer, explicit
  complete-source authority record, supported literal loop/integer branch/
  callback-18/28/29 semantics, spell-finish flag projection, and a separate
  raw-byte/raw-timer oracle. Missing writer inventory, scheduler order,
  installed-callback state, phase stability, post-update capture, coherent
  external state, or supported control flow truncates to root-only/partial
  coverage. Shipped Final-B sub44 and Extra sub86 have bitwise product/oracle
  parity over 300 future frames and both restore on frame 241; player sees
  quarter scale on that frame and laser sees unit scale. Final-B consumes
  10099 under the no-hit/no-Bomb continuation; Extra consumes none.
  Historical session `004142` predicts and observes the unit restore at ECL
  frame 75027 exactly; sessions `011639`/`163501` are right censored at
  finish/freeze. The retained report SHA-256 is
  `2c6cedcc5b30b4e9f805ff19cc7cbcd465f6123df2ccfda63e2fac21a8777d27`;
  Linux/Windows bytes agree and full suites pass 1,096 tests in
  14.353/29.889 seconds with three existing Windows skips. This proves only
  the declared isolated source plus one historical transition, not complete
  live main/auxiliary inventory, callback-28 bullet rescaling in hazards,
  clean survival, or action authority.
- **Observed SEM-SCALE-C4 implementation gate:** checkpoint `ead1f21` adds a
  read-only spell-190 observer and strict physical report. It binds exact
  runtime `ecldata7.ecl`, brackets all 480 ordinary slots plus an out-of-pool
  spell owner with stable frame/phase/root/Bomb identity, records active main
  VM state, selected-VM installed callback and four auxiliary pointers, and
  calls the causal producer only for a singleton valid quarter-scale sub44
  source. It rejects every auxiliary context, unknown/scale installed
  callback, invalid/multiple source, identity drift, incomplete schedule, and
  callback-28/29 bullet velocity side effect. Connected IDA revalidation
  corrected the installed fields to selected ECL VM `+0x10/+0x14` (main
  enemy `+0x808/+0x80C`) and confirmed main VM -> auxiliary 0..3 -> enemy
  motion order. Linux/Windows discovery passes 1,107 tests in
  13.728/29.427 seconds with three existing Windows skips.
- **Observed SEM-SCALE-C4 physical gate:** corrected checkpoints `88b8c14`
  and `0c33645` first defer capture to the quarter-scale root, reduce the
  full-pool transaction from 36.834 ms to 7.734 ms, and separate stable
  replay/no-life-patch predeath residue from a fresh semantic-root hit.
  Native replay attempt `20260729_215613` then passes every strict check at
  manager frame 74787: exact executable/runtime-ECL identity, all ordinary
  slots plus spell owner, one valid main VM, zero auxiliary contexts,
  installed callback zero, scale `0.25`, Bomb zero, complete 300-frame
  schedule, one callback-18 unit restore at relative frame 240, and no
  callback-28/29 bullet side effect. Capture/report SHA-256 values are
  `22e3d69d249b512f6c73e3816e3206373c89776b53f183fc0ebf7e1d71a2e48d`
  and
  `d4aa9b9c065bde6de3ba899ff95e4ff3eea10f166714e561c00743100d4e138a`.
  The replay has zero Bomb presses, but the physical root retains predeath 7.
  Thus the complete-source semantics are accepted; clean player state,
  schedule delivery, action authority, survival, and NMNB remain open.
  CE-0186/0187 retain the two rejected assumptions, and
  `notes/operations/NATIVE_REPLAY_PHYSICAL_FALSIFICATION.md` makes the
  shipped-replay hypothesis-check method reusable.
- **Observed SEM-SCALE-C5 implementation gate:** the default-off live
  consumer requires explicit Lunatic stage 7, hard no-Bomb, and exact runtime
  ECL identity. It binds the accepted source to immutable
  gameplay/route/difficulty/stage/spell identity, causally slices the exact
  player/laser tuples at each manager-frame offset, and rejects fresh hit,
  Bomb, predeath-baseline change, context, source-frame, observed-root, or
  horizon mismatch through the existing terminate/release fallback. Since
  only whole-stage original Practice Start is available, pre-target unit
  roots use an explicitly unknown-direction transport schedule with no hard
  scale authority; non-unit unknown rows wait. A source/root/context/horizon
  mismatch waits without a new write and preserves the rest of the stage
  evidence; process, foreground, and key-release failures still stop and
  clean up. Non-unit/varying exact schedules remain outside corridor
  authority and feed only the exact local path. The retained C4
  artifact crosses the relative-239 player/laser phase split and relative-240
  unit restore under this recurrence. Linux/Windows discovery passes 1,132
  tests in 13.596/29.764 seconds with three existing Windows skips. At that
  implementation checkpoint no game was launched; its next physical scope was fixed in
  `notes/operations/FINALB_SEM_SCALE_LIVE_DELIVERY_GATE.md`.
  Spell 190 remains only the smallest causal falsifier. The research and
  promotion unit is a complete stage: after this gate, source-authority
  generalization must be stage-wide and may not depend on enabling a feature
  only when one hand-picked spell is reached.
- `SEM-SCALE-C5-1` then physically ran the whole original-game Stage 6B:
  17,282 decisions, 19 hits, zero Bomb masks, and route completion. It failed
  exact delivery because the spell-190 hit at frame 73,477 left the player in
  phase 3/predeath 7 across the entire quarter-scale source window. The old
  phase-0 gate waited until unit scale returned and never captured a source.
  CE-0188 retains the raw hash and causal witness. The corrected proposal
  captures source player phase, treats phase 3 as contamination rather than
  normal-player authority, and continues evidence collection without new
  input writes instead of exiting on scale-authority loss.
- The next physical unit was expanded first to original Game Start Lunatic
  Sakuya/Remilia from Power 0 through the complete route, with stage/phase
  hits, Bombs, lives, Power/items, combat progress, transitions, and C5
  exact-delivery retained as separate conclusions. The full-route controller
  did not auto-stop at the restore.
- **Observed full-route result:** run
  `lunatic_route2_fullrun_unattended_20260730_002115` completed the original
  Power-0 Game Start route with 60,877 decisions, 74 hits, zero Bomb masks,
  and exact cleanup. Stage hits were `3/4/6/21/17/23`; Stage 4A is the largest
  single-stage failure. Non-aborting C5 evidence continuation passed its
  behavioral requirement, but exact delivery remained unexercised: Final B
  recorded 299 decisions in spell 174, 311 in 178, and zero in
  182/186/190, with unit scale throughout. CE-0189 rejects treating route
  completion or a zero spell-hit count as proof of live spell coverage.
- **Observed SEM-SCALE-C5-2 physical gate:** whole-stage run
  `lunatic_route2_stage6b_finalb_scale_delivery_20260730_020015` completed
  frames `1..76050` with 18,332 decisions, 22 hits, zero Bomb masks, normal
  route unload, and exact cleanup. One coherent spell-190/sub44 source was
  captured at manager frame 75,811, one frame after controller
  decision/expected frame 75,810; no authority is backfilled before the
  capture. The first sampled exact row is offset 1. All 111 exact decisions
  through offset 238 use the accepted quarter-scale schedule with zero
  fallback, fresh hit, or Bomb. Callback 18 schedules unit restore at offset
  239; cadence skips that frame and offset 240 observes the unit root
  together with `terminal_unload`. Strict report v4 passes all 20 checks.
  Source phase 3/predeath 7 remains explicit contamination. Raw/report
  SHA-256 values are
  `cbad986f0bb627d88135e2a4ae31c48389b6e030657ad77e557b882585aedcfc`
  and
  `53cddd1162769010dbc467bf9d295e90e5389db3ffb4fce3d1c73c42076b08ec`.
  CE-0190 rejects v3's noncausal requirement for sampled offset-zero and
  active restore rows.
- **Promotion boundary and next slice:** C5 exact delivery is observed, but
  the whole-stage survival result fails at 22 hits; the canonical hit is
  nonspell frame 7,412 and every contact follows global viability
  exhaustion. Do not repeat C5 or the unchanged full route. Continue at
  `SEM-MODE`, then `SEM-GEOM`, `SEM-SOURCE`, and `SEM-ROBUST` in order.

#### 1C. Action-conditioned player/enemy mode

- include focus/secondary-character transition state and its native delay;
- project enemy `0x800` contact/damage eligibility per action/history;
- distinguish contact eligibility from damage eligibility;
- preserve observation-compatible branch merging;
- keep unfocused combat promotion disabled.

Exit gate: the retained frame `10065 -> 10075` transition and adversarial
focus toggles match native state/body sets; every action-conditioned branch is
causal.

2026-07-30 `SEM-MODE-A` checkpoint: the decoder now retains active geometry
blocked by enemy bit `0x800`; a pure projection separates contact and
player-shot damage eligibility; native player `+3/+5/+8` are exposed
diagnostically; and exhaustive adversarial focus histories match an
independent scalar recurrence. This is offline/shadow evidence only. The exit
gate remains open until a frame-bracketed mode/enemy observation, causal
pickup/cadence recurrence, exact-version publication, body-set differential,
and whole-stage physical gate pass. See
`../architecture/TH08_ACTION_CONDITIONED_PLAYER_ENEMY_MODE_SEMANTICS_20260730.md`.

2026-07-30 `SEM-MODE-B` preflight: a bounded transaction now brackets active
input, player `+3/+5/+8`, Bomb state, and the existing first-64 enemy-prefix
read. Crossed updates retry twice; exhausted or flag-incoherent reads are
retained diagnostically and never fail-close gameplay. A default-off
whole-stage/whole-route flag, compact source-hashed report, raw body identity
evidence, and deterministic `10065 -> 10075` fixture pass complete 1,162-test
Linux/Windows suites. The mode record has no action authority and its runtime
cost may perturb cadence. The exit gate remains open pending the original-game
whole-Stage-5 observation, causal pickup/cadence recurrence, exact-version
publication, and body-set differential.

CE-0191 correction: the first physical attempt reached gameplay frame 1 but
the default root-only scale-authority fail-close terminated before any
decision. The default hard boundary remains unchanged. For the SEM-MODE-B
whole-stage observer only, an additional explicit flag may repeat the current
root over the finite consumer horizon so the stage completes. This proxy is
unknown-direction, cannot combine with exact Final-B scale authority, and
grants no survival/certificate authority even if the physical run is clean.
It exists to preserve a whole-stage native observation unit instead of losing
all evidence at the first root-only frame.

### Phase 2 — Repair collision geometry and lifecycle

Implement as small, separately reviewable changes:

1. exact player half-extent `1.0`, with lattice/sampling error represented as
   a separate explicit clearance term;
2. native rotated local-AABB laser collision and float32 phase evolution;
3. explicit bullet lethal/fade states;
4. per-frame bullet collision-suppression state/schedule;
5. physical player clamp `x=8..376`, `y=16..432` in every oracle and planner.

For each change, retain viable-state and safe-action-mask diffs, classify
every delta as expected or unresolved, and never combine a geometry fix with
ranking changes.

Exit gate: independent scalar, optimized Python, and native kernels agree for
stop/resume/redirect/reversal, laser head/tail/rotation, fade/suppression,
boundary, dense-pool, and retained capsule cases. Unknown-direction
mismatches block live authority.

### Phase 3 — Reset model versions and recertify

The Phase-1/2 changes alter physical state equivalence and transitions.
Therefore:

- issue a new immutable hazard/model version;
- publish an invalidation matrix for old fixtures, witnesses, caches, reports,
  and physical claims;
- preserve old artifacts under their original version and SHA;
- reject cross-version cache/publication lookup;
- regenerate exact scalar/Python/native parity;
- replay retained Stage-5 and Final/Extra capsules in shadow;
- take a fresh trace-only physical metadata gate before live action changes;
- map every changed primitive to its first focused physical falsifier:
  Stage 3 for early nonspell/laser and resource-prefix behavior, Stage 4A for
  ECL/body/clock behavior, Stage 5 for nonspell/future-source behavior, and
  Final B for non-unit-scale/laser/funnel behavior.

Exit gate: no artifact is silently interpreted under the new model; every
current live consumer either matches the exact version or falls back to the
existing Boolean policy plus fresh local hard certificate.

### Phase 4 — Complete native source and action semantics

Continue G5 one event class at a time only after the base transitions are
sound:

1. close ECL call-depth and opcode-`0x87` semantics;
2. inventory all callback/custom/global/lethal effects from callers and
   runtime evidence;
3. capture source generation/lifetime/transform identity;
4. model main and auxiliary VM composition;
5. add shared gameplay RNG and Route-2 shot/focus consumption;
6. make bullet suppression/lifecycle part of emitted hazard schedules;
7. keep unsupported branches `UNKNOWN`.

Exit gate for one event class: shipped instruction identity, independent
oracle parity, complete source identity, exact geometry, bounded deadline,
exact-version lookup, replayable witness, and fresh trace-only physical
metadata all pass. No single class implies all-source completeness.

### Phase 5 — Preserve viability earlier

Use the corrected model to attack the dominant survival boundary:

- retain exact first-loss dossiers for the first clean failure of each
  workload;
- decompose empty into coarsening, horizon, uncertainty, forecast/source,
  route/tube, and unresolved categories;
- extend exact causal stationary/partial witnesses only as attainable lower
  bounds for declared policy classes;
- build pre-loss continuation/interior reserve from an earlier immutable
  version;
- use proof-backed query-local sparse refinement, dominance, and admissible
  bounds;
- require future coverage before a lower witness reaches physical authority.

Do not replace this with beam-width growth, Monte Carlo, MCTS, learned
ranking, or unproved pruning. Those methods may be shadow proposals but
cannot certify hard survival.

Exit gate: on retained first-loss roots, the controller either publishes a
completed causal witness before issue time or returns an explicit unresolved
class. It never labels timeout/unvisited work losing and never consumes an
unknown-direction approximation.

### Phase 6 — Optimize only the corrected recurrence

Profile after semantic/version stabilization:

1. replace repeated Python marshalling of roughly 190 local-beam buffers with
   a persistent owned SoA workspace and fused native step;
2. reuse scratch storage only with explicit ownership, cancellation,
   reentrancy, and newest-version tests;
3. keep the sparse full enemy-sensor tail;
4. measure decode, lower, pack, induction, publication, and issue
   separately;
5. run Linux and Windows performance gates in isolation, never concurrently.

Exit gate: exact hard-mask, selected-action, viable-state, and witness parity
are unchanged; Windows deadline, cadence, RSS, cancellation, and stale-version
gates pass. A faster proxy with changed semantics fails.

### Phase 7 — Add route, combat, and resource progress inside survival

Run trace-only work in parallel when it cannot contend with the live control;
then test one intervention at a time:

1. establish enemy generation/end and distinguish verified kill, timeout,
   scripted despawn, transition, and unknown;
2. join source lifetime to realized bullet births and define a measurable
   kill-before-saturation deadline for one Stage-5 nonspell segment;
3. retain player Shot/focus/option state, damage, target coverage, clearance,
   viable alternatives, emission exposure, drops, item motion/pickup, and
   Power delta;
4. build a trace-only target shadow that ranks only actions already proved
   viable and issue-safe;
5. compare focused versus unfocused target coverage only after Phase 1C and
   action-dependent RNG/source coverage. The focus transition is a delayed
   physical mode change, not a free shot-width toggle;
6. test one opening Stage-5 nonspell segment over repeated RNG-distinct
   samples. Earlier verified kill must reduce later exposure/emissions without
   worsening first-hit survival, clearance, reserve, cadence, or deadline;
7. treat spell damage only as a survival-equivalent phase-compression
   tie-break and test it per spell, not as a universal aggression weight;
8. model Power and item collection as resource-constrained route state.
   Collection is eligible only inside the viable/issue-safe set and must show
   a verified pickup plus useful downstream damage or survival benefit;
9. obtain route-faithful prefixes by starting Stage 1 at Power 0. Do not call
   a max-Power Stage-3/4A/5 practice a Power strategy gate;
10. keep every post-death collection/recovery analysis in a separately
    labeled diagnostic history.

Exit gate: a combat/resource action is considered only inside the same
verified viable and issue-safe set and improves a preregistered physical
phase metric over repeated physical samples without degrading first-hit
survival, clearance/reserve, cadence, deadlines, or later mandatory scenes.
Absence of survival-equivalent choices is a valid null result.

### Phase 8 — Physical acceptance ladder

Use focused trials and repeat clean phase passes before expanding scope:

1. two consecutive observer-off Lunatic Stage-5 controls at `<=10` hits;
2. complete the corrected-model mechanics ring: fresh compatible Lunatic
   Stage 3, Stage 4A, Stage 5, and Final B practices, with the exact semantic
   fields and deadlines each change claims;
3. complete a route-faithful Power/resource prefix from Stage 1 at Power 0
   through Stage 3, then extend the same evidence boundary through Stage 4A
   and Stage 5;
4. require a compatible complete route reaching and clearing Final B; a
   Final-B practice clear cannot substitute for inherited route state;
5. run Stage 1 and Stage 6B supporting regressions where the changed
   primitive applies;
6. repeat clean passes for every unresolved canonical first-hit phase;
7. run one complete Lunatic Route-2 hard no-Bomb attempt;
8. progressively eliminate the first clean miss, restarting causal analysis
   from the new first miss after every success;
9. retain the first complete zero-hit, zero-Bomb run as **NMNB-1**;
10. separately establish repeatability with additional RNG-distinct complete
   zero-hit, zero-Bomb runs as **NMNB-R**.

The first physical NMNB is the requested milestone. Repeatability is a
stronger claim and must be reported separately. The repository's eventual
acceptance target also includes Extra, but Extra work must not be conflated
with completion of the Lunatic milestone.

## 10. Lunatic NMNB Acceptance Contract

The first accepted NMNB run must satisfy all of the following:

- Sakuya/Remilia, Lunatic, Route 2, normal full-route start from Power 0;
- complete route and every required dialogue/stage transition;
- route-faithful Stage-3/4A/5/Final-B evidence must derive from that same
  accumulated history rather than practice-mode resource injection;
- zero native hit edges from start through route completion;
- zero Bomb actions and no observed Bomb bit `0x02`;
- no manual `Z`, foreground loss, debugger/CLI contamination, or unrecorded
  intervention during gameplay;
- verified executable, route, difficulty, team, foreground, gameplay state,
  and no-life-decrement instrumentation;
- exact cleanup with every injected key released and no unattended controller;
- compact tracked report containing frames, hits/Bombs, resources, Power/items,
  phase attribution, cadence, deadline, viability, model version, and source
  provenance;
- one replay-capable raw bundle retained locally under the active two-newest
  policy.

The no-life-decrement patch is instrumentation only. It cannot convert a hit
into a pass: any native hit edge rejects NMNB.

`NMNB-1` means one uncontaminated complete accepted run. `NMNB-R` should
require at least two further complete RNG-distinct accepted runs, with at
least two consecutive successes among the validation set. Do not call
`NMNB-1` a robust success rate.

## 11. Stop Rules

Stop and retain a counterexample when:

- optimized/native output differs from an independent scalar oracle;
- a previously conservative error changes direction or becomes unknown;
- model identity omits time scale, timer fraction, player mode, RNG, source,
  geometry, cadence, delay, or clamp state used by the recurrence;
- a consumer accepts a stale, partial, wrong-version, or unknown-coverage
  publication;
- Linux/Windows performance is measured concurrently;
- optional work delays authoritative publication or changes issued input;
- a physical run has a hit, unexpected Bomb, missed transition, foreground
  loss, or cleanup failure;
- an aggregate comparison lacks a control-equivalent workload;
- timeout, exhaustion, or unvisited actions are relabeled as losing;
- a strategy objective ranks outside the viable and issue-safe set.

Do not weaken a test, clearance, deadline, coverage, or hit threshold to make
a candidate pass.

## 12. Explicitly Not Next

- Do not roll back `3f02ff1` or later documentation/retention checkpoints on
  the evidence currently available.
- Do not rerun V6 unchanged or relabel its failed report.
- Do not optimize Python/native local-beam marshalling before Phase 1/2 model
  stabilization.
- Do not promote Focus/unfocused, targeting, damage, Power, item, or graze
  objectives from one trace.
- Do not interpret global-kernel empty as physical loss.
- Do not expand G5 source classes while the shared timer/movement/hazard
  primitives are known wrong.
- Do not change recurrence and performance architecture in one checkpoint.
- Do not run a physical trial unless explicitly authorized.

## 13. Immediate Implementation Backlog

`PHYS-BASE-RING` has taken its causal-failure exit: the first observer-off
Stage-5 control had ten hits and the unchanged second had 18. CE-0183 stops
physical expansion before Stage 3. Begin source correction at `SEM-TIMER`;
do not weaken the threshold, launch a third uncontrolled repeat, or treat the
incomplete ring as route authority.

After that baseline, the next correction checkpoints should be:

1. `SEM-TIMER`: offline semantic gate complete and immutable code fixed; its
   prescribed observer-off Stage-5 falsifier is retained as CE-0184 after 12
   hits. It confirms live version integration only on the
   zero-fraction/unit-scale slice, fails survival authority, and supplies no
   timer-causal rollback target;
2. `SEM-SCALE`: complete for its declared C1–C5 delivery program. C5-1
   rejects the phase-0 trigger, the corrected Power-0 full route preserves
   evidence but never reaches spell 190, and whole-stage C5-2 physically
   passes one exact contaminated restore interval while separately failing
   Stage-6B survival at 22 hits. Do not repeat it or generalize it to clean
   survival, stage-wide source authority, Extra, or NMNB;
3. `SEM-MODE`: focus/secondary-character transition and action-conditioned
   enemy contact/damage eligibility;
4. `SEM-GEOM`: exact player/laser geometry, bullet lifecycle/suppression, and
   physical clamp;
5. `SEM-SOURCE`: callback inventory, bounded call semantics, and
   action-dependent RNG;
6. `SEM-ROBUST`: derived-observer cursor and beam-quantization boundaries,
   plus incremental IDA typing;
7. `MODEL-VNEXT`: cross-version invalidation, differential replay, and
   trace-only physical metadata;
8. `PHYS-MODEL-RING`: take the smallest causal scene after each slice, then
   require fresh compatible Stage-3/4A/5/Final-B evidence before integrated
   promotion;
9. `COMBAT-GEN`: establish generation/end, kill/despawn, target, shot mode,
   damage, drop, pickup, and Power telemetry without action authority;
10. `COMBAT-SHADOW`: preregister and test one Stage-5
    kill-before-saturation or survival-equivalent phase-compression
    hypothesis at a time;
11. `POWER-ROUTE`: retain route prefixes from Stage 1 Power 0 and test item
    collection/unfocused coverage only inside the unchanged viable and
    issue-safe set;
12. return to G5/viability/performance in Phases 4–6 when their semantic and
    physical dependencies are satisfied.

Each label is a program slice, not permission to batch every bullet into one
commit. The implementation agent should split a slice further whenever one
counterexample, formal contract, or physical gate can be isolated.

## 14. Review Deliverables And Remaining Uncertainty

The original review changed repository documentation only. The later physical
workload refinement also updated the audit/revalidation repo-skill
instructions and pinned two external reference clones outside this Git
repository. It moved the original temporary audit into `notes/review/`,
retained its original digest, recorded new durable counterexamples, narrowed
the affected G5 exactness claim, and aligned the volatile
handoff/strategy/roadmap indexes.

No source, executable, raw capture, retained report, test oracle, live
strategy, physical policy, or IDA annotation was changed in these review and
planning checkpoints. This historical non-action does not restrict
evidence-backed IDB correction during the authorized implementation phases.

Remaining high-value runtime uncertainties are:

- the actual time-scale histories in retained first-hit windows;
- whether conservative hitbox/lifecycle corrections materially recover
  viable space;
- exact player-mode/contact transitions across all Route-2 phase boundaries;
- complete callback and action-dependent RNG source coverage;
- which component first causes corrected-model viability loss;
- which versioned correction prevents CE-0183's early viability loss and
  restores a consecutive observer-off Stage-5 baseline;
- the first clean full-route bottleneck after Stage 5 is controlled.

The next agent must start from `START_HERE.md`, this roadmap, the companion
audit, CE-0175 onward, and the corrected G5 timer authority note. It must not
start implementation from the severity list alone: the Phase-0 causal
baseline and the ordered dependency chain above are part of the result.

## 15. Checkpoint Validation

- At the original audit checkpoint, complete Linux discovery:
  `PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'`
  passes 1,057 tests in 13.557 seconds.
- For the later planning refinement, `git diff --check` passes; both modified
  repo skills pass the skill-creator `quick_validate.py`; and LeanToken
  reconciles every changed Markdown file as parse-complete and structurally
  complete.
- Every newly referenced retained artifact/authority path checked by the
  review exists.
- `/tmp/ths_analysis.md` no longer exists; the durable audit is under
  `notes/review/`.
- For observer-off Stage-5 pass 1, focused supervisor discovery passed 28/28
  on Linux and 28/28 on Windows before launch, and the post-run Linux repeat
  passed 28/28. The accepted session, summary, dossier, comparison,
  regressions, deaths CSV, raw hash, hard no-Bomb fields, ignore rules,
  cleanup state, Markdown structure, and staged whitespace were revalidated
  before retention.
- For unchanged pass 2, the same preflight tests passed 28/28 on both
  platforms and the post-run Linux repeat passed 28/28. Exact controller
  config/entry-resource comparison, five compact JSON reports, 18-row deaths
  CSV, raw provenance/hash, hard no-Bomb fields, ignore rules, process
  cleanup, Markdown structure, and whitespace checks pass. CE-0183 preserves
  the failed threshold without relabeling it.
- For the SEM-TIMER falsifier, focused supervisor discovery passed 28/28 on
  Linux and Windows before launch. Run `20260729_173957` completed 11,597
  decisions over frames `1..42021`, hard no-Bomb, accepted artifacts, exact
  cleanup, and 12 hits. Its ignored 477,436,227-byte raw JSONL hashes to
  `e0b32ee0e042056079d7159f1055aa2ad289447d03efc078d2c2d73f98585367`.
  Compact reports parse and the 12-row deaths CSV is consistent. A
  stream-based component audit finds 3,940 expected-version rows, 33/33
  Stage-5 roots mapped at base `0x0B1D0048`, zero past/unmapped roots, and
  only zero-fraction/unit-scale physical states. CE-0184 preserves the failed
  threshold without misattributing the pre-consumer canonical hit.
- For SEM-SCALE-C4, three exact native-replay attempts are retained. The first
  fails the quarter-root/frame-coherence gate, the second falsifies a
  zero-predeath source-semantic requirement, and `20260729_215613` passes the
  strict physical complete-source report. The accepted capture is 26,627
  bytes, has exact executable/runtime-ECL/replay scope, manager frame 74787,
  7.734-ms capture, one main source, no auxiliary/installed callback, and a
  complete callback-18 restore schedule. Its predeath-7 contamination is
  explicit and grants no clean-survival or NMNB authority. CE-0186/0187,
  the replay-method note, compact artifacts, hashes, and IDA replay-menu
  annotations are retained.
- For SEM-SCALE-C5 live delivery, C5-1 physically completed Stage 6B with
  17,282 decisions, 19 hits, and zero Bomb masks but accepted no exact source;
  CE-0188 retains the phase-0 trigger failure and raw hash. The corrected
  player-phase evidence boundary, native-summary parser, non-aborting
  continuation, focused/full-route auto-stop split, and original Game Start
  transport pass focused Ruff/tests. Complete Linux/Windows discovery pass
  1,137 tests in 13.612/30.825 seconds, with the three existing Windows
  skips. This adds a physical counterexample, not a hit-free or survival
  sample.
- The corrected original Game Start full route
  `lunatic_route2_fullrun_unattended_20260730_002115` completes frames
  `1..229992` with 60,877 decisions, 74 hits, zero Bomb masks, no foreground
  interruption, no JSON decode errors, and exact game/controller cleanup. Its
  ignored 2,009,399,974-byte raw JSONL hashes to
  `ffe52f97e959a92ec0adb06e418c17e2a97c8e2209f0978a1249f1b66e8a69d0`.
  Stage hit counts are `3/4/6/21/17/23`; the first canonical hit is Stage-1
  nonspell frame 2,022. The strict C5 report correctly fails with zero
  authority rows because active spell-decision counts for
  174/178/182/186/190 are `299/311/0/0/0` and scale remains unit. No replay
  was created. CE-0189 and dossier schema v4 retain target reachability
  separately from hit attribution.
- The dossier-v4/whole-stage-C5-2 correction passes focused Ruff and
  supervisor/report tests. Complete Linux/Windows discovery passes 1,140
  tests in 13.404/29.833 seconds, with the three existing Windows skips.
- Whole-stage C5-2
  `lunatic_route2_stage6b_finalb_scale_delivery_20260730_020015` completes
  frames `1..76050` with 18,332 decisions, 22 hits, zero Bomb masks,
  `route_complete`, and exact cleanup. The ignored raw JSONL is 634,344,375
  bytes and
  hashes to
  `cbad986f0bb627d88135e2a4ae31c48389b6e030657ad77e557b882585aedcfc`.
  Strict schema v4 passes all 20 checks over a one-frame causal capture lag,
  111 exact sampled decisions, callback-18 restore at offset 239, and a
  unit-root/terminal-unload bracket at offset 240. The source phase
  3/predeath 7 and whole-stage hits remain contamination. CE-0190 preserves
  the rejected v3 report contract. The checkpoint containing this handoff
  adds one schedule-derived completion regression. Focused authority/report
  discovery passes 13/10 tests; complete Linux discovery passes 1,143 tests
  in 13.481 seconds and the exact Windows UNC suite passes 1,143 in 29.925
  seconds with the three existing skips. A regenerated v4 report is
  byte-identical to the retained compact artifact.
- No matching TH08 gameplay, controller, practice-supervisor, or
  full-route-supervisor process is left running.
- The original documentation-only checkpoint did not rerun Windows tests;
  the two later physical preflights above did. Keep those scopes distinct.
- No IDA mutation occurred in the review or Phase-0 physical checkpoints.
  Phase 1 evidence-backed IDB changes are now retained: scale/ECL field and
  scheduler comments, spell-state renames/comments, replay-menu function
  rename `title_replay_menu_update`, and compact-selection/launch-state
  comments. C5-2 additionally renames/types `0x017CE758` as
  `g_game_timing_state: Th08GameTimingState` and comments the physical
  asynchronous-capture/terminal-restore evidence at `0x00424FB4`.
