# Native Replay Causal Wind Tunnel And Accepted Replay-Save Contract

Date: 2026-07-30

This note is the durable handoff for the replay-save, native-replay
counterfactual, and explicit-root work completed after the initial offline
iteration review. It records implementation and observed evidence; it does
not promote the current solver or grant finite-model or physical survival
authority.

## Evidence Labels

- **Observed:** established by retained original-game execution, shipped
  instructions/dataflow, compact artifacts, or deterministic tests.
- **Inferred:** supported by observations but not yet directly demonstrated
  as a native executable transition.
- **Hypothesized:** a proposed next architecture or experiment.

## Retained Identity

- Shipped executable SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`.
- The runtime no-life-decrement byte remains
  `0x0044D0FA = 0x00`; this patch preserves evidence collection after a hit
  but does not turn later contacts into fresh-route survival samples.
- Current canonical Stage-5 replay SHA-256:
  `de1e4e941adc8c2899eb3ae1bedd2b4faaf14362d4ce2af984d1c9e5a32da613`.
- Replay identity: Route 2, Lunatic, single Stage 5, 34,267 input frames,
  stage RNG seed 59,590, input SHA-256
  `a14f5ef29705098fd9d919f05c92dee8d4cff30a458e241b468b34252acd4508`,
  and no Bomb press.
- The replay and its manifest are retained under
  `artifacts/replays/archive/`.

## Accepted Replay Save

### Native object identity

**Observed and revalidated:** the result/save-menu object is a dynamic
`ResultSysInf` allocation, not the fixed address `0x018B8A68`.

- `result_menu_create_and_register` at `0x004582A0` allocates `0x477B0`
  bytes.
- It stores the update node at object `+0x46468`.
- The update node callback is `result_menu_update_dispatch` at
  `0x004584B0`.
- Node `+0x1C` points back to the heap object.
- The node is inserted into the update-chain sentinel at `0x0164F548`.

The automation resolves the current object by traversing the update chain,
matching callback `0x004584B0`, reading context `+0x1C`, and checking that the
object's `+0x46468` back-reference is the same node. A fixed object address is
rejected.

### Revalidated save states and fields

The accepted state machine is:

| State | Meaning | Accepted action |
| ---: | --- | --- |
| 10 | save prompt | select `はい` and confirm |
| 12 | 15-slot list | move to the declared slot and confirm |
| 14 | occupied-slot overwrite prompt | select `はい` and confirm |
| 13 | name editor | retain the previous name, select End at cursor 95, confirm |
| 2 | completed result state | verify terminal save state |

Relevant heap-object fields are:

| Offset | Meaning |
| ---: | --- |
| `+0x04` | state age |
| `+0x08` | state |
| `+0x1C` | active cursor |
| `+0x28` | selected slot or name length, depending on state |
| `+0x2C` | name-grid cursor |
| `+0x58` | eight-byte replay name |
| `+0x46468` | registered update-node back-reference |

`replay_save_menu_update` at `0x0045696F` handles states 10–14.
Name-grid cursor 95 reaches the End command, formats
`./replay/th8_%02d.rpy`, and calls `replay_write_file`.

### Physical acceptance

**Observed:** Stage-1 run
`lunatic_route2_stage1_unattended_20260730_144256` completed with one hit,
hard no-Bomb, resolved the dynamic menu object, traversed
`10 -> 12 -> 14 -> 13 -> 2`, and saved slot 15. The resulting replay SHA-256
is
`3eae54a2c50af3ed20df25759ed6b0a6821f087054ea16c320a826aeb9989dff`.

**Observed:** Stage-5 run
`lunatic_route2_stage5_unattended_20260730_144830` completed with 19 hits,
hard no-Bomb, traversed the same state chain, archived the prior Stage-1
replay, and saved the current canonical Stage-5 replay
`de1e4e941adc8c2899eb3ae1bedd2b4faaf14362d4ce2af984d1c9e5a32da613`.
The original game slot and the isolated wind-tunnel slot were restored to
that canonical SHA after every branch trial.

The 19-hit aggregate is not rollback evidence. Its RNG seed and canonical
first hit differ from earlier Stage-5 runs, and the only new behavior occurred
after stage completion in the save menu.

## Native Replay As An Implicit Root

**Observed:** the canonical replay reproduces a first native hit at enemy
manager frame 2,136. Replay input frame `manager - 1` matches:

- 2,136 of 2,136 complete masks;
- 450 of 450 input transitions; and
- an exact 64-frame suffix.

The canonical branch input coordinate is therefore replay frame 2,129 for a
six-callback-frame anticipation window before the frame-2,136 hit. This
coordinate is replay-specific and must stay bound to the replay and input
digests above.

The replay is an **implicit root**: original TH08 reconstructs the state by
executing the same seed and input prefix from Stage-5 start. This has strong
semantic value because TH08 itself recomputes ECL, enemy/bullet/item pools,
damage, shared RNG, geometry, and collision after changed input. It is slow
because every branch repeats the prefix.

## Atomic Native Root Capture

**Observed:** the exact retry captured all 15 declared byte components under
`NtSuspendProcess`/`NtResumeProcess` with:

- enemy-manager bracket `[2130, 2130]`;
- suspension duration about `480.751 ms`;
- resume verified;
- content SHA-256
  `289da8a4daf80353ea98f0394ffc0b011b7a30e950007a41f47452bbf3ebeabb`;
  and
- the same later first hit at frame 2,136.

This remains
`native_root_bytes_only_no_predictive_authority` /
`partial_native_root_inventory`. Only three minimum requirements are complete:

- ordinary enemy template/pool;
- motion/flag/lifecycle bytes; and
- shared gameplay RNG.

Seven requirements remain partial: route identity, physical scheduler/clock,
timeline, main/aux ECL contexts, player input/mode/shot, resources/damage, and
external callbacks/transitions. The capture also has no restore-and-step
executor. Atomic bytes are not a canonical scheduler phase and cannot be
`memcpy`-restored as physical evidence.

## Replay Branch Corpus

**Observed:** the corpus generator created 36 unique no-Bomb complete-mask
replays at root input frame 2,129, holding each mask for three replay frames.
Every branch round-trips through the repository decoder/encoder and retains
the same prefix. The original executable is the future-world executor; no
recorded future world is reused.

The current corpus restores the original replay input suffix after the
three-frame intervention. It is therefore a declared open-loop
counterfactual, not an observation-conditioned policy witness.

## Stop-Fence Counterexample

The enemy-manager counter advances at an earlier update priority than player
collision. An external observer may see manager frame 2,136 before collision
for that same frame has completed.

**Observed:** a pilot that stopped as soon as the counter reached 2,136
reported unchanged-mask `0x00` and source-equivalent `0x05` as no-hit. The
source-equivalent canary made that conclusion impossible. Requiring manager
frame 2,137 closes frame 2,136 and reproduces the expected hit for all four
unchanged/stationary pilot masks.

Therefore:

- a branch is no-hit through physical frame `F` only after the observer sees a
  verified later fence;
- a manager-counter equality is not an end-of-collision-frame barrier; and
- the rejected 2,136-fence reports remain counterexample evidence only.

## All-Action Native Results

At the corrected 2,137 fence, all 36 branches completed:

- 30 had a native hit by the fence;
- six reached the fence without a hit:
  `0x14`, `0x15`, `0x90`, `0x91`, `0x94`, and `0x95`;
- the Shot-off/on pair for each motion had the same local classification; and
- no branch report has physical or explicit-root-executor authority.

The six local candidates were then extended to manager frame 2,257. All six
hit:

| Mask | Motion | First hit |
| ---: | --- | ---: |
| `0x14` | up | 2141 |
| `0x15` | up + Shot | 2142 |
| `0x90` | up-right-fast | 2140 |
| `0x91` | up-right-fast + Shot | 2140 |
| `0x94` | up-right | 2141 |
| `0x95` | up-right + Shot | 2141 |

**Conclusion:** the three-frame action at replay frame 2,129 can delay the
canonical hit by four to six frames, but it supplies no no-hit witness. This
points to earlier anticipation, multi-decision closed-loop continuation, or a
different planner architecture; it does not prove the physical root
unavoidable.

## Throughput Verdict

The native replay executor is valuable as:

- an exact replay/parser encoder acceptance check;
- a same-seed semantic oracle;
- a canary for action-coordinate and stop-fence claims; and
- a sparse validator for candidates already selected offline.

It is rejected as the primary all-action inner loop. Thirty-six original-game
prefix branches took roughly half an hour to answer one short-horizon
question. Holding `Ctrl` preserved the gameplay fingerprint but did not
materially reduce wall time.

## Next Architecture

The **explicit native root executor** milestone is now implemented and passes
at one canonical Stage-5 root. This closes the first one-tick construction
gate only; it does not close event-class coverage, longer horizons, external
effects, or physical authority.

Minimum acceptance order:

1. Hook one revalidated calculation boundary before replay input publication
   or controller pickup.
2. Capture all mutable gameplay state required by one native tick, plus
   scheduler phase, allocation epoch, FPU/TLS assumptions, and immutable
   identity.
3. Prove `A -> restore -> A` produces identical per-frame fingerprints.
4. Prove `A -> restore -> B` stays identical until the declared input
   effect point and diverges only afterward.
5. Return `UNKNOWN` on untracked allocation, mapping, callback, transition,
   thread, renderer/audio, timer, or external-state effects.
6. Grow exact horizons `1 -> 2 -> 4 -> 8 -> 16`, then run all 36 masks.
7. Add a branch-specific causal controller only after every reached event
   class is covered.
8. Use native replay as an independent oracle, then a focused physical stage
   as the delivery gate.

A TH08-specific in-process rollback stepper with a dirty-page journal or
copy-on-write baseline was the preferred proposal. The retained implementation
uses a stable same-session byte baseline plus a dirty-page journal. Whole-
process predictive authority remains rejected without explicit thread, heap,
handle, DirectX/audio, timer, input, and external-state ownership.

## One-Tick Explicit-Root Result

**Observed:** `scripts/th08_runtime/native_snapshot.py` replaces only the
fixed call at `0x00441F4D` from the 60 Hz frame pump to
`update_chain_execute` at `0x0043CA50`. Before calculation at manager frame
2,129, its injected barrier records the owner thread, stack/frame pointers,
and FPU/SSE state. Every branch calls the original update chain exactly once
and stops before render with manager frame 2,130.

The replay action seam is the priority-6 playback callback at `0x00452550`.
The callback loads the next action word at `0x004525BE` and publishes it at
`0x004525C1`. The canonical action was `0x05`; action B was `0x15`. A used
true no-write semantics. B changed exactly one byte in the replay action word
before calculation. Neither action contains the Bomb bit.

**Observed:** the first broad capture changed the virtual-region
partitioning while the owner remained in the barrier and every other target
thread was suspended. A second capture had identical pre/post mapping
identity and became the root. This is consistent with one-time observation
of writable copy-on-write image pages; it is not interpreted as a game tick.

The stable root covered 110,141,440 bytes in 248 writable private/image
regions. Its same-session SHA-256 was
`b35e595afbd4936630b7536185d95507308ba4935df1d489f6594805e005c3ea`.
The epoch contained 34 threads: the barrier owner plus 33 suspended threads.
Frozen non-owner stacks, the barrier allocation, and writable mapped/external
regions remained outside the byte baseline.

**Observed:** A1 and A2 produced the same captured endpoint SHA-256
`2c7b220df5e06c6ebf3aac62480a0dcde7cfd12861e7c8073261bda7be25d387`
and the same revalidated native-root projection SHA-256
`437e234f907c7f54be1cbd824a826353090690ba37f9ae2726deb83a8e47ef39`.
Both returned to the exact root stack/frame pointers and advanced manager
time by one.

**Observed:** B produced a different captured endpoint and changed four
declared native projection components:

- gameplay RNG and input masks;
- ordinary-enemy ECL and callback roots;
- ordinary-enemy template and pool; and
- player state through resource transitions.

All three branches retained one mapping/thread epoch. Each endpoint dirtied
896 or 897 pages. Coalesced restore took 10.824--11.816 ms; rereading every
dirty span took 9.846--11.814 ms; all three restorations matched the same
baseline. The original calculation took 0.785--0.999 ms, endpoint discovery
151.671--172.387 ms, and the native projection 16.386--17.535 ms. The current
inner loop therefore evaluates roughly four to five candidates per second
after reaching the root once.

The compact retained report is
`artifacts/runtime_reports/th08_native_snapshot_one_tick_20260730.json`,
SHA-256
`6144624093386619d0ac66b69da5bf90c84b88f158d4b4f5529f953d376585a9`.
Its ignored full source report hashes to
`bb6d054c69ab79a31741901bfc6314110babcc164ac1e7c5a9130f8b9cabe56f`.

**Inferred:** this executor is suitable for fast same-session, one-tick
candidate comparison over the retained native projection at this exact root.
It replaces repeated full-stage/replay-prefix iteration for this scope.

It has no live or physical predictive authority. Forty-two writable regions
were excluded, external handle/device/audio/timer effects remain unresolved,
and only one event class was tested. The rolling extension below supersedes
the one-tick horizon limit, but no long-horizon survival witness was produced.
The next gate is repeated identity at additional event classes. Write-watch
or guarded-page tracking may remove the remaining endpoint scan, but is only
a performance hypothesis.

## Rolling H2/H4/H8 And All-36 Result

**Observed:** the executor now preserves root and endpoint FPU/SSE state,
advances the replay action cursor by exactly two bytes per tick, and checks
owner stack/frame, manager clock, thread epoch, and committed-map epoch at
every H-step endpoint. Every branch restores all dirty spans before the next
action.

The progressive gate passed:

- H=2 recorded `0x05`, movement `0x15`, focus toggle `0x01`, and fence
  candidate `0x14`;
- H=4 `0x14`; and
- H=8 `0x14`, followed by the complete 36-mask no-Bomb portfolio.

The recorded H=2 compact states exactly match the retained natural replay
corpus at manager frames 2,130 and 2,131. Identical-seam natural-frame
capture matches the rolling collision/control projection and compact state
at every tick through H=8 for `0x14`, `0x61`, and `0x44`.

The collision/control projection keeps native input/RNG, enemy ECL/callback
tails, hostile bullet/laser pools, explicit player collision/control fields,
resources, and route-2 option causal tails. It excludes ordinary-enemy
render/ANM prefixes and the four FRScreen resource-notification bytes proved
render-consumed/decremented at `0x004372A7`. CE-0208 retains the initial
false mismatch before that correction. This is collision/control
equivalence, not full process identity.

**Observed causal witness:** the recorded `0x05` branch reaches player phase
2 at manager frame 2,136. Hostile bullet slot 45 is at
`(373.049164, 428.138336)` with signed box separation `-0.966766`. Holding
`0x14` for frames 2,130--2,132 and then resuming the recorded suffix leaves
the bullet at the same world position but moves the player from
`y=429.171570` to `y=422.271606`. Slot-45 separation becomes `+3.866730`;
the closest bullet is slot 322 at `+1.352203`. The candidate remains phase
0 with unchanged predeath counter through manager frame 2,137.

**Observed all-36 result:** one immutable root and one original-game replay
launch executed all 36 no-Bomb masks through H=8 in `63.583` seconds,
including per-tick native/collision capture and endpoint restore
verification. Median branch-plus-restore time was `1,731.995 ms`. Native
calculation step wait itself was `0.993 ms` median; broad and collision
projection medians were `17.559` and `46.670 ms`. Recorded canary and repeat
histories were exact. Thirty masks hit and the same six short-fence masks
`0x14/15/90/91/94/95` survived through 2,137.

The legacy polling corpus agrees on hit-versus-survive class for 36/36 masks
but is full-endpoint exact for 31/36. CE-0209 records why exact long-tail
comparison is diagnostic only: its `observe_state()` reads were not bracketed
and could cross a manager-frame update. Same-seam natural H=8 captures
resolve the `0x14` tail-RNG, `0x61` early-hit, and `0x44` late-hit
representatives in favor of the rolling result. The five differences remain
visible in the retained report.

Compact evidence is
`artifacts/runtime_reports/th08_native_snapshot_fast_iteration_root2129_h8_20260730.json`,
SHA-256
`ddd71ebf110207ef0baf098bfb3d9d710e5a403d08bcf5b1b09bda0eb8a000d7`.

**Inferred at the H=8 checkpoint:** this fixed-root loop is suitable for
rapid local hit-cause isolation and candidate ranking at the canonical replay
seam. H=8 alone did not show that `0x14` survives its later CE-0207 contact.
The promoted-subroot result below supersedes that horizon limit, but it still
does not generalize to spawn, redirect, callback, transform, or laser event
roots or grant live/physical authority.

## Promoted Subroots And H32 Causal Witness

**Observed implementation:** the rolling barrier schema is now v3. An idle
endpoint records its exact owner stack/frame, manager clock, and 512-byte
FXSAVE state as a content-addressed `NativeBarrierRootCheckpoint`.
`promote_endpoint_to_root()` makes that endpoint the next calculation root;
`restore_root_checkpoint()` returns from a promoted child to the immutable
parent. Dirty pages, replay cursor, thread set, committed-map identity, owner
stack/frame, and FX state remain fail-closed at every branch and restore.

Exact per-tick schedules use either a declared complete no-Bomb mask or
`null` for the native replay action at that tick. `null` is an action-input
choice, not reuse of an action-incompatible future: every successor still
executes the original update chain from the changed native predecessor.

**Observed two-decision matrix:** the six H=8 survivors each received all 36
secondary masks from their promoted frame-2,137 subroot. This produced 216
causal continuations. The largest one-session batch evaluated 180 branches
in `309.089 s`; its full transaction was `348.621 s`, and its recorded
parent repeat was exact. Prefix survivor counts at frame 2,145 were:

| Prefix | Secondary survivors |
| ---: | ---: |
| `0x14` | 16 |
| `0x15` | 16 |
| `0x90` | 16 |
| `0x91` | 16 |
| `0x94` | 12 |
| `0x95` | 12 |

Maximizing whole-segment minimum signed clearance, then endpoint clearance,
then the lower equivalent Shot mask selects `0x94` for frames
2,130--2,132 and `0x44` for frames 2,138--2,140. Replay actions are consumed
for the five remaining ticks of each eight-tick segment.

**Observed continued portfolios:**

- from the frame-2,145 subroot, 26/36 third actions survive to 2,153;
  `0x10` maximizes the segment minimum clearance at `+5.781158`;
- from the frame-2,153 subroot, 30/36 fourth actions survive to 2,161;
  `0xA4` maximizes the segment minimum clearance at `+8.864166`; and
- every portfolio repeats its immutable parent projection, collision/control
  history, and compact state exactly after restore.

The resulting decision sequence is
`0x94 -> 0x44 -> 0x10 -> 0xA4` at calculation roots
`2129/2137/2145/2153`. Its exact 32-tick action schedule remains no-Bomb and
unhit through manager frame 2,161. Whole-witness minimum signed clearance is
`+1.471344` at frame 2,135 against hostile bullet slot 45. The recorded
`0x05` branch instead hits slot 45 at frame 2,136 with separation
`-0.966766`; at the same frame the witness keeps the bullet's world position
exact and changes the player path enough to make its separation `+1.845795`.

**Observed natural validation:** the exact H=32 schedule was then executed
through the real frame pump at the same calculation-call seam. All 32
collision/control projection digests and all 32 compact states match the
headless native trajectory. No headless/native first mismatch exists through
the declared endpoint.

This corrects CE-0207 only through the declared H=32 fixed replay horizon. It
does not prove a complete spell or stage, model parity, observation/delay
delivery, or physical survival.

The deterministic compact report is
`artifacts/runtime_reports/th08_native_snapshot_causal_policy_root2129_h32_20260730.json`,
SHA-256
`69e6ec2db0f5415a6ee8231808be0669b0f80006faf299f2c90aeb27e221bbaa`.
It emits content-addressed `NativeRootCapsule`, `NativeTrajectory`,
`FirstMismatchReport`, `ActionPortfolio`, `CounterexampleCorpus`, and
`ExactWitness` records. `ModelTrajectory` is deliberately
`not_generated` in that immutable report. The companion differential below
binds the rebuilt model without rewriting the original evidence.

Complete Linux discovery passes 1,351 tests in 13.760 seconds. Complete
Windows UNC discovery passes 1,351 tests in 28.592 seconds with the three
existing skips.

## ModelTrajectory And First-Mismatch Result

`scripts/analysis/th08_native_model_trajectory.py` SHA-pins both the compact
causal report and its ignored raw H=32 witness, validates the
content-addressed root/trajectory, and emits explicit player-mechanics and
constant-velocity-hazard layers. A `null` schedule entry resolves only from
the corresponding `NativeTrajectory.selected_action`; it must equal the
recorded action. Missing fields, digest disagreement, Bomb, or changed
time-scale identity fail closed.

**Observed CE-0211:** the prior default movement bounds represented playfield
extents `(0,0)..(384,448)`, not player-center clamps. From root
`(376,432)`, action `0x94` therefore projected `x=377.626343` at frame 2,130
instead of native `x=376`. The legacy trajectory had zero exact ticks.
Versioned center bounds `(8,16)..(376,432)` make position, input history,
focus transition state, secondary-character mode, and the declared carried
normal phase bit-exact for all 32 ticks.

**Observed CE-0212:** production bullet projection used
`base + velocity * elapsed`. Retained constant-velocity slot 45 first
distinguishes that expression from native repeated float32 stores at frame
2,132: x bits `0x43B97BCA` versus native `0x43B97BCB`. Production now
advances and stores once per native update, applying a velocity event before
that update. It matches an independent repeated-binary32 oracle and all three
retained native samples. Nonpositive snapshot alignment preserves the
existing linear-rewind convention.

The deterministic report is
`artifacts/runtime_reports/th08_native_model_trajectory_root2129_h32_20260730.json`,
SHA-256
`7f86ffb72ef3b7c72c329cd240bed6cdf5ee7d99d8e9defee88b4d219887a2af`.
It explicitly returns `UNKNOWN` for integrated collision/planner parity:
the compact input retains summaries and hashes rather than a full
model-consumable hostile inventory and event ledger. No physical run was
used. The next semantic gate is persisting that causal state/event input and
using it for integrated planner replay before any named physical falsifier.

### Warm-session lifecycle

The current CLI already amortizes one replay bootstrap across a batch; it
does not require one process per branch. Persisting across independent solver
queries is a sound performance proposal only as a supervised
`NativeWindTunnelServer` with:

- a single-writer transaction queue and immutable session/root IDs;
- exact root hash, FX, stack, replay cursor, thread, and map verification
  after every branch;
- cooperative timeout/cancellation and newest-query selection;
- explicit `healthy`/`poisoned` lifecycle states;
- automatic key release, target cleanup, and replay rebootstrap; and
- an idle TTL so no game or suspended thread set is left unattended.

One attempted 216-branch batch detected a committed-map epoch change after 14
continuations, returned `UNKNOWN`, cleaned the process, and discarded the
partial result. A fresh batch then completed 180 branches without recurrence.
CE-0210 retains this limit. A warm service must treat this as poison and
rebootstrap; it must not weaken mapping identity merely to preserve uptime.

## Local Retention

- Compact accepted/rejected reports remain under
  `artifacts/runtime_reports/`.
- Large branch replays and child logs are retained locally under
  `artifacts/native_replay_wind_tunnel/raw/` and intentionally ignored.
- Large rolling snapshot trials are retained locally under
  `artifacts/native_snapshot_rolling/raw/` and intentionally ignored.
- External primary-source clones are retained locally under
  `references/external/20260730/` and indexed by
  `notes/review/EXTERNAL_REFERENCE_SNAPSHOT_INDEX_20260730.md`.
- The isolated original-game directory is
  `D:/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)__codex_wind_tunnel`.
  Its game data/executable are local and never committed.

## IDA Database Changes

Evidence-backed changes made on 2026-07-30:

- retained existing rename `replay_save_menu_update` at `0x0045696F`;
- renamed `0x004582A0` to `result_menu_create_and_register`;
- renamed `0x004584B0` to `result_menu_update_dispatch`;
- commented the `0x477B0` heap allocation, node `+0x1C` context,
  object `+0x46468` back-reference, update-chain insertion, save-state
  offsets, and accepted write point; and
- corrected both helper calls involving `0x018B8A68` to say that this global
  is not the `ResultSysInf` object base;
- commented the revalidated calculation callsite `0x00441F4D` with the
  one-tick manager `2129 -> 2130` barrier result; and
- commented replay action load/store `0x004525BE/0x004525C1` with the
  priority-6 explicit-root A=`0x05`, B=`0x15` evidence and authority limit;
- renamed `dword_160F42C` to
  `g_frscreen_resource_notification_counters`; and
- commented `0x004372A7` to record that FRScreen rendering consumes and
  decrements the two-bit resource-notification counters at root
  `+0x04..+0x07`.

These annotations are native/menu semantics only. They grant no solver action
or survival authority.
