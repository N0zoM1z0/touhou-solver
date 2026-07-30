# TH08 Explicit-Root And Title-Demo Read-Only Audit

Date: 2026-07-30
Workspace: `/home/pentester/coding/codex_ida/th08`
Branch/HEAD at audit start: `main` / `293cca8f9d04b5ef586e571f0da826ec99b0db7a`
Connected IDB input MD5: `454c96e08fe3c14df7064d104c26accf`
Connected IDB input SHA-256: `ec101fcff80b77e717d43b54e326375487af19661bb7c8d11a19ee5e0fbf928b`
Clean shipped executable MD5: `77b6785e04a3406e50be68714a193650`
Clean shipped executable SHA-256: `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
Identity reconciliation: the IDB input differs from the clean executable at raw
offset `0x4CEFA` / VA `0x44D0FA` only, changing `FF` to `00` in the retained
no-life-decrement patch (`6A FF` to `6A 00`). This difference is unrelated to
the title-demo or snapshot semantics examined here.
Latest retained evidence cutoff: current dirty workspace and retained
2026-07-30 native-replay/root artifacts.
Scope: determine whether a canonical native snapshot can become an explicit
root for short-horizon counterfactual execution, and whether TH08 title-idle
demo playback contains reusable decision logic or infrastructure.
Non-actions: no game launch, input injection, physical trial, workspace-file
mutation, IDA mutation, strategy promotion, or claim of physical authority.

## Evidence Labels

- **Observed:** directly established by current source/artifacts, shipped
  native instructions/dataflow, deterministic tooling, or primary-source code.
- **Inferred:** supported by multiple observations but not directly
  demonstrated as retained native runtime behavior.
- **Hypothesized:** plausible architecture or experiment awaiting a decisive
  native differential.

## Workspace Caveat

The worktree contains concurrent modified and untracked replay/root work. This
audit is read-only and treats those files as a moving evidence surface.
Implementation must bind every result to an immutable code/root/executable
version and re-run the relevant checks.

## Live Summary

**Verdict:** an explicit native root is technically achievable and should
substantially shorten iteration, but the current `capture_v5` artifact is not
one. It is an atomic, partial byte inventory with no executor and no
demonstrated restore/step determinism. The highest-leverage first implementation
is a TH08-specific in-process rollback stepper at one revalidated scheduler
boundary. It should replay the prefix once, restore the same root before every
branch, replace the replay-published action, run exactly one native gameplay
tick, fingerprint the result, and fail closed on unsupported side effects.

The title-idle demonstration is not an online dodge AI. It loads one of four
embedded `demorpy*.rpy` files, decodes the ordinary TH08 replay format, restores
the recorded RNG seed/stage state, and publishes recorded input masks through
the normal replay input path. Its useful contribution is therefore a
deterministic stage bootstrap and a proven input-substitution seam, not a
planner. Normal replay mode is a cleaner harness than demo mode because demo
adds title-return and persistence/UI behavior that is irrelevant to mechanics.

General Windows rerecording tools show that process savestates are possible in
restricted conditions, but also document why a general-purpose snapshot is the
wrong first target. TH08-specific control over the single gameplay update chain
can avoid much of the kernel object, renderer, audio, timer, and external-state
surface.

## Prioritized Findings

### F1 — Current native root is partial capture evidence, not a restorable root

**Severity:** blocking for predictive use.
**Evidence:** observed.

`artifacts/runtime_reports/native_replay_stage5_slot15_root8715_capture_v5_20260730.json`
records a whole-process suspension lasting about `519.8315 ms` with
`enemy_manager_frame` bracket `[12316, 12316]`. This establishes a byte-atomic
capture interval relative to that counter; it does not establish an
instruction-boundary or scheduler-phase root.

The artifact explicitly reports:

- `authority = native_root_bytes_only_no_predictive_authority`
- `physical_predictive_authority = false`
- seven missing semantic components:
  `damage_power_and_resources`,
  `external_callback_and_transition_state`,
  `gameplay_and_route_identity`,
  `main_and_auxiliary_ecl_contexts`,
  `physical_clock_and_scheduler_gates`,
  `player_input_mode_and_shot_state`, and
  `timeline_runtime_state`
- pointer roots without recursively captured pointees
- unresolved replay alignment: the best reported input-mask agreement is
  `60.89%` at offset `-1`; transition agreement is `47.86%`

Two declared regions also duplicate almost the same large memory interval:
`ordinary_enemy_template_and_pool` spans `10,320,336` bytes and
`ordinary_enemy_ecl_and_callback_roots` spans `10,298,880` bytes wholly inside
it. That is `9.8218 MiB` of duplicate transaction data and illustrates that
the capture is still a region inventory rather than a normalized state
contract.

**Consequence:** serializing these bytes, or restoring them at an arbitrary
suspended instruction, cannot yet answer “what would native TH08 do after
action A?”

### F2 — A narrow original-engine rollback stepper is the best first explicit root

**Severity:** highest-leverage implementation proposal.
**Evidence:** inferred architecture grounded in observed native boundaries;
runtime feasibility remains to be demonstrated.

The recommended root is not “all process memory at any instant.” It is one
canonical state of the gameplay calculation chain, on its owning thread,
before a precisely named input publication/pickup transition. A small injected
native harness should:

1. Boot a deterministic normal replay once to the chosen scene.
2. Stop on a revalidated canonical scheduler callback boundary, preferably
   immediately before the priority-6 replay input publisher or at the exact
   controller observation/action-pickup boundary defined by the formal model.
3. Capture mutable gameplay pages, mapping/allocation epoch, gameplay root
   metadata, x87/FPU control state, TLS assumptions, callback ordinal, and the
   immutable root version.
4. For each allowed no-Bomb mask, restore the root, replace the replay cursor
   output, execute exactly one native calculation tick, and collect a strict
   state fingerprint.
5. Restore again and verify the root fingerprint before trying the next mask.
6. Return `UNKNOWN`, never “safe,” on an untracked allocation, mapping change,
   external callback, transition, thread interaction, or other unsupported
   side effect.

A page-protection/VEH dirty-page journal is a plausible efficient restore
mechanism. A Process Snapshotting VA clone may also supply a copy-on-write
baseline, but Microsoft documents PSS as a process-state capture facility and
exposes clone/context/handle *information*; it is not a supported arbitrary
resume/restore engine. Its usefulness here would be as a byte source for a
TH08-owned executor, not as the executor itself.

The harness’s trampoline/worker stack must not be rolled back beneath itself.
Either run the verified gameplay chain on a dedicated harness stack with
validated TLS/FPU assumptions, or use a main-thread trampoline whose control
state lives outside the restored region. Renderer/audio suppression is allowed
only after normal-versus-fast per-frame gameplay fingerprint parity.

### F3 — Whole-process savestate precedents exist, but expose the wrong problem surface

**Severity:** architectural caution.
**Evidence:** observed in cloned primary-source projects; applicability to
TH08/this executable is inferred.

Hourglass saves writable committed regions and thread contexts, reconstructs
mappings on load, and hooks D3D8 and DirectSound. This is direct precedent for
Windows rerecording and TH08 has historical Hourglass TAS activity. The project
is deprecated, its own ecosystem documents compatibility limitations, and the
postmortem explains the external/kernel state problem in general Windows
rerecording.

libTAS tracks thread contexts, mappings, descriptors, deterministic time,
audio and display state, and implements incremental savestates using Linux
memory facilities. It describes Wine support as experimental and not actively
developed. It is useful as a bounded research spike or independent shadow
oracle, not a substitute for Windows-native physical validation.

Hyper-V standard checkpoints can capture VM memory, device and disk state and
therefore provide a coarse correctness fallback. Their expected reset and
branch overhead makes them unsuitable for the inner all-action loop.

**Consequence:** do not spend the first milestone recreating a general Windows
TAS system. Exploit the TH08-specific, mostly single gameplay update chain and
execute only the native mechanics needed by a short horizon.

### F4 — Title-idle autoplay is prerecorded replay, not a decision policy

**Severity:** decisive answer to the demo question.
**Evidence:** observed in shipped native code and retained runtime evidence.

`title_main_menu_update` at `0x4674E0` increments an idle counter, resets it on
raw input, and after more than 1500 frames cycles through four archive members:

- `demo/demorpy0.rpy` at string VA `0x4B8E1C`
- `demo/demorpy1.rpy` at string VA `0x4B8E08`
- `demo/demorpy2.rpy` at string VA `0x4B8DF4`
- `demo/demorpy3.rpy` at string VA `0x4B8DE0`

The files are archive-decoded by `load_resource_file` (`0x43E660`) and
`decode_edz_resource` (`0x43E390`), then parsed by the normal `T8RP` replay
decoder `replay_decode_and_decompress` (`0x451D90`). Replay stage loading at
`0x452D60` restores route, difficulty, resources and the recorded stage RNG
seed through `rng_set_seed`. `replay_play_input_frame` (`0x452550`) and its
extended form (`0x4526C0`) write the next recorded mask to
`g_input_current`; the publication runs before player movement in the
revalidated callback order.

Retained 2026-07-23 runtime evidence independently observed 121 demo frames
with raw keyboard input remaining zero while replay-published input changed and
the manager counter advanced without gaps.

The four decoded embedded records are ordinary single-stage, two-byte-input
replays:

| file | route | difficulty | stage index | RNG seed | input frames | recorded Bomb frames |
|---|---:|---:|---:|---:|---:|---|
| `demorpy0.rpy` | 0 | 3 (Lunatic) | 5 | `0x8D07` | 11084 | 5201, 6180 |
| `demorpy1.rpy` | 1 | 3 (Lunatic) | 3 | `0x684D` | 7741 | 3854 |
| `demorpy2.rpy` | 3 | 3 (Lunatic) | 2 | `0xD39A` | 9273 | 4652, 5040, 5451 |
| `demorpy3.rpy` | 2 | 3 (Lunatic) | 1 | `0x0322` | 9264 | 5997, 6677 |

All four demonstrations contain recorded Bomb presses. They are neither a
no-Bomb witness nor evidence of a hidden NMNB planner.

### F5 — Demo/replay infrastructure is valuable as a bootstrap and action seam

**Severity:** useful near-term engineering reuse.
**Evidence:** observed seam; proposed use is hypothesized until differential
validation.

The replay path gives the harness:

- deterministic route/difficulty/stage/resource initialization
- a recorded per-stage RNG seed
- a known priority-6 input publication point before player movement
- automatic progression through the native gameplay update chain
- a simple place to substitute one mask or a branch-specific policy callback

Use **normal replay mode** or an externally generated compatible replay as the
carrier. Demo mode adds title-idle selection, demo HUD/return behavior, and
suppression of some persistent unlock/BGM writes. Static xref review found no
direct demo-bit branch in the enemy, bullet, player, collision, or gameplay RNG
updates, but absence of a direct xref is not complete semantic proof; indirect
mode behavior remains possible. Before treating demo and normal replay as
mechanically equivalent, compare their per-frame gameplay fingerprints for the
same decoded replay/seed.

The original replay suffix must not be appended after a counterfactual action.
Once an action changes position or observations, later actions must be produced
from that branch’s observations. Reusing the recorded future would create an
open-loop trajectory, not a causal policy witness.

### F6 — The explicit root changes the iteration scale, not merely convenience

**Severity:** major expected throughput gain.
**Evidence:** deterministic update-count comparison; wall-clock gain remains
to be measured.

For a representative root at native update `12316`, 36 no-Bomb masks and a
60-update horizon:

- replaying the prefix separately for every action executes approximately
  `36 × (12316 + 60) = 445,536` native updates
- replaying once and restoring one explicit root executes approximately
  `12316 + 36 × 60 = 14,476` native updates
- this is about `30.8×` fewer total native updates
- inside the already-captured root, branch work drops from prefix-dominated
  execution to `2160` short-horizon updates, roughly a `206×` update-count
  reduction relative to replaying the prefix for every branch

These are not promised wall-clock speedups. Snapshot/restore, fingerprinting,
allocation tracking, and native callback overhead must be measured. The
important qualitative change is that one canonical failure can be tested
hundreds or thousands of times without rerunning the menu, stage prefix,
unrelated RNG history, renderer, and physical input path.

### F7 — Native branching is an oracle layer, not automatic physical authority

**Severity:** formal/acceptance boundary.
**Evidence:** observed workspace contract plus inferred architecture.

Two roots must remain distinct:

- a **mechanics root** immediately before replay/native input publication,
  useful for “given active mask A, what does native mechanics do next?”
- a **controller root** at the actual live observation/issue boundary, which
  must retain cadence, pending command, current active input, no-write
  semantics, and remaining pickup-delay belief

If the offline branch injects an action directly at the native publisher but
the live controller could not causally realize that active action at that
frame, the branch is an optimistic mechanics counterfactual, not a physical
winning witness. Delay/cadence/nondelivery branches still belong in the formal
recurrence.

The snapshot oracle can validate action-conditioned native futures and remove
model errors rapidly. Physical promotion still requires an immutable winning
candidate, fixed-root/native differential evidence, deadline-safe live
consumption, and focused repeated physical execution.

## Concrete Wind-Tunnel Pipeline

The minimal useful pipeline is:

```text
ordinary replay prefix (once)
        |
        v
canonical pre-input native root R(f)
        |
        +---- restore R -> publish action a0 -> native tick -> fingerprint S0
        +---- restore R -> publish action a1 -> native tick -> fingerprint S1
        ...
        +---- restore R -> publish action a35 -> native tick -> fingerprint S35
                              |
                              v
                 branch-specific policy for f+1...
                              |
                              v
          exact no-hit witness / first-mismatch counterexample
                              |
                              v
             normal native replay diagnostic, then focused physical gate
```

The strict per-frame fingerprint should initially include at least:

- gameplay RNG state and call-count/trace digest
- `input_current`, previous/held desired input, replay cursor and mode flags
- player position/velocity/state/hit/graze and shots
- bullet and laser pool identities, generations, transforms and lifecycle
- all enemy slots, generations, templates, HP/damage state and callbacks
- main and auxiliary ECL VM PCs, timers, stacks and dynamic pointees
- timeline/spawn runtime state and callback registry
- power, lives, Bombs, resources, phase and route identity
- scheduler/callback ordinal and every physical clock/gate used by mechanics
- allocation/mapping epoch and the dirty-page set

The first implementation should support only one stable, allocation-free,
non-transition scene. Narrowness is a feature: unsupported behavior must fail
closed and become a named coverage item.

## Decisive Verification Ladder

| gate | experiment | required observation | authority if passed |
|---|---|---|---|
| G0 phase | stop 100 times at declared boundary | same thread/callback ordinal and valid pre-input state | boundary candidate only |
| G1 no-op | capture, step one frame with recorded action | fingerprint equals unmodified normal replay | one-step executor parity |
| G2 restore | `A → restore → A`, repeated | byte/semantic fingerprints exactly equal | deterministic same-action restore |
| G3 causality | `A → restore → B` | roots equal before pickup; first difference occurs only at/after declared action pickup | action seam validity |
| G4 horizon | repeat G2/G3 at 2, 4, 8, 16, 32, 60 frames | deterministic same-action futures; explained first mismatch | bounded scene oracle |
| G5 all 36 | enumerate every no-Bomb mask from one immutable root | all results versioned; unsupported branches are `UNKNOWN` | complete root-action mechanics corpus |
| G6 model diff | native result versus independent scalar/external executor | first mismatch localized and classified | model correction evidence |
| G7 witness | branch-specific causal policy yields exact no-hit trace | replayed native trace reproduces fingerprint/hit result | fixed-root native witness |
| G8 physical | live controller executes candidate repeatedly in focused scene | no hit/Bomb, correct resources/timing/input semantics | scoped physical evidence |

Do not jump from G1 to a long-horizon claim. A state omission often remains
latent for several frames; geometric horizon growth localizes its activation.

## External Repository Review

All repositories were shallow-cloned read-only beneath
`/tmp/th08-external-research-17wrD4`:

| repository | audited HEAD | relevant lesson |
|---|---|---|
| `GensokyoClub/th08` | `84738749bdcf6cffabe8d0d76e17f19253a20d50` | useful matching decomp and title/replay control flow; core gameplay managers are incomplete, so it is not a runnable TH08 oracle |
| `thpatch/thtk` | `892114a0fcaa0bbdaaecf3cb4ad56f758683fb40` | authoritative practical archive/replay format tooling; not a gameplay engine |
| `PyTouhou` | `fbfba5269cfc98def3ff0e899694d2686c8f9eac` | demonstrates separating per-frame gameplay stepping from window/rendering, but targets TH06 and cannot establish TH08 semantics |
| `thprac` | `8b3338f4d2cc7853d5a32d30dc7d252dc50bf2b3` | useful practice/scene bootstrap ideas; documents custom replay incompatibility and lacks mid-game replay save for TH06–10 |
| `libTAS` | `a1bffe9f990734993f795278408f639923e1deb0` | mature incremental savestate/determinism mechanisms; Wine support is experimental |
| `hourglass-win32` | `78fa7c6d2be1b5eb46b8d4c0a37e56af616e1a46` | direct Windows savestate/D3D8/DirectSound precedent and historical TH08 use; general compatibility/external state is the limiting surface |

Primary upstream references:

- <https://github.com/GensokyoClub/th08>
- <https://github.com/thpatch/thtk>
- <https://github.com/GovanifY/PyTouhou>
- <https://github.com/touhouworldcup/thprac>
- <https://github.com/clementgallet/libTAS>
- <https://github.com/TASEmulators/hourglass-win32>
- <https://learn.microsoft.com/en-us/previous-versions/windows/desktop/proc_snap/overview-of-process-snapshotting>
- <https://learn.microsoft.com/en-us/windows/win32/api/processsnapshot/ne-processsnapshot-pss_capture_flags>
- <https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/checkpoints>
- <https://tasvideos.org/EmulatorResources/Hourglass>
- <https://tasvideos.org/Forum/Topics/20210>

The review corrects one overly broad novelty statement: offline manual
rerecording/savestate exploration of Touhou/Windows games is not new. What was
not found in these projects is an automatic TH08 NMNB policy solver with
observation-compatible robust branching, live pickup-delay/cadence semantics,
and physical promotion of exact native counterfactual witnesses.

## Proposed Implementation Order

1. **One-frame replay-publisher seam.** Inject only enough code to replace the
   next replay mask at the canonical boundary and prove normal replay parity.
2. **Same-session rollback for one stable scene.** Track writes to a
   conservatively broad mutable region/page set; reject allocation, transition,
   async or external events.
3. **A/restore/A and A/restore/B gates.** Retain exact fingerprints and first
   mismatch reports.
4. **Geometric short horizon and all 36 masks.** Add branch-specific action
   callbacks; do not replay the incompatible recorded suffix.
5. **Close semantic coverage one event class at a time.** Add ECL pointees,
   timeline, lasers, callbacks, allocation and transitions only with a retained
   counterexample/gate.
6. **Cross-check against the external exact-prefix executor.** The original
   engine is the semantic oracle; the structured executor supplies scalable,
   versionable branches.
7. **Promote only a fixed-root witness.** Run a normal native replay diagnostic,
   then a focused physical controller trial; repeat before expanding scope.

This hybrid avoids waiting for a complete reconstructed TH08 engine before
gaining native counterfactual evidence, while still moving toward a portable,
formally versioned executor.

## IDA / Native Backlog Before Implementation Authority

The following items require revalidation in the connected IDB and, where
possible, bounded runtime probes:

1. Exact owning thread and callback order for the priority-6 replay publisher,
   input pickup, player movement, enemy ECL, bullet/laser update, collision,
   damage and cleanup.
2. A canonical pre-input/post-input phase marker stronger than
   `enemy_manager_frame`, including behavior when that counter freezes.
3. Every writer/reader of `g_input_current`, previous/held desired input and
   replay cursor around the selected boundary.
4. x87 control/status, TLS, SEH and stack assumptions of calling one gameplay
   tick from a trampoline.
5. Allocation/free/mapping behavior in the first supported scene and identity
   rules for pool slot reuse.
6. Main/auxiliary ECL VM dynamic state, timeline runtime state and external
   callbacks reachable within the declared horizon.
7. Renderer/audio/timer functions that may be safely bypassed without changing
   gameplay fingerprints.
8. Indirect demo-mode readers or callbacks not exposed by direct xrefs to the
   game-manager flag word.

Strong conclusions should be renamed/typed/commented in IDA only in a separate,
authorized retained checkpoint; this audit made no database changes.

## Validation Commands And Reproducibility

Read-only checks used or suitable for reproducing this audit:

```bash
git rev-parse HEAD
git status --short --branch

sha256sum artifacts/runtime_reports/native_replay_stage5_slot15_root8715_capture_v5_20260730.json
jq '{authority, physical_predictive_authority, status, capture_transaction, components}' \
  artifacts/runtime_reports/native_replay_stage5_slot15_root8715_capture_v5_20260730.json

PYTHONPATH=scripts python3 scripts/th08_pbgz.py /path/to/th08.dat list 'demorpy*.rpy'

for repo in th08-decomp thtk PyTouhou thprac libTAS hourglass-win32; do
  git -C /tmp/th08-external-research-17wrD4/$repo rev-parse HEAD
done
```

Focused source locations:

- `scripts/th08_native_future_body_root.py`: capture specifications and
  transaction implementation
- `scripts/th08_runtime/win32.py`: process suspension implementation
- `notes/CAUSAL_ACTION_CONDITIONED_FUTURE_BODY_PRODUCER_CONTRACT_20260730.md`
- `notes/IMMUTABLE_FUTURE_BODY_FLAG_GEOMETRY_SCHEDULE_CONTRACT_20260730.md`
- `notes/architecture/NATIVE_PRODUCER_ROOT_LAYOUT_AND_TIMELINE_SPAWN_LIFECYCLE_20260730.md`
- `/tmp/th08-external-research-17wrD4/th08-decomp/src/TitleScreen.cpp`
- `/tmp/th08-external-research-17wrD4/th08-decomp/src/ReplayManager.cpp`
- `/tmp/th08-external-research-17wrD4/hourglass-win32/src/wintaser/wintaser.cpp`
- `/tmp/th08-external-research-17wrD4/libTAS/docs/guides/how.md`

No repository test suite was run because this was a read-only architecture and
native-semantics audit over a concurrently changing worktree. No code was
changed by this audit.

## Remaining Unknowns

- Whether all gameplay mutations for a useful stable scene can be isolated
  from renderer/audio/OS state with low enough restore overhead.
- Whether native callbacks depend on hidden TLS, FPU, wall-time or thread state
  not represented in the first root.
- Exact dirty-page and fingerprint costs, hence realized rather than
  update-count speedup.
- Normal replay versus title-demo per-frame gameplay parity under an identical
  record.
- How soon allocations, ECL external callbacks or stage transitions force a
  structured rather than byte-level restore.
- The smallest controller-root representation that preserves pickup delay,
  cadence and no-write semantics while using the mechanics oracle.

## Completion State

This audit is complete for architecture selection and title-demo
classification. It authorizes no physical action or predictive claim. The
next decisive retained milestone is G2/G3: exact one-frame
`A → restore → A` reproducibility and causally localized
`A → restore → B` divergence at one immutable normal-replay root.
