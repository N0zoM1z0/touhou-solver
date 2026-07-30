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

The next decisive milestone is an **explicit native root executor**, not
another broad replay-prefix portfolio.

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
copy-on-write baseline is the preferred proposal. Whole-process restore is
not accepted without explicit thread, heap, handle, DirectX/audio, timer,
input, and external-state ownership.

## Local Retention

- Compact accepted/rejected reports remain under
  `artifacts/runtime_reports/`.
- Large branch replays and child logs are retained locally under
  `artifacts/native_replay_wind_tunnel/raw/` and intentionally ignored.
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
  is not the `ResultSysInf` object base.

These annotations are native/menu semantics only. They grant no solver action
or survival authority.
