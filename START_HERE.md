# TH08 Current Handoff

This is the single current-state entrypoint for the TH08 Sakuya/Remilia
Lunatic/Extra no-Bomb solver. It is intentionally short and volatile.
`AGENTS.md` contains durable workspace rules; `STRATEGY.md` is the strategy
status ledger; design notes and run notes contain derivations and history.

## Read In This Order

1. `AGENTS.md`
2. this file
3. `STRATEGY.md`
4. `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
5. `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`
6. `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`
7. `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`
8. the lower/upper/anytime notes listed under “Formal references” below
9. the relevant recent run note and counterexample rows before touching live
   behavior

First verify that the physical problem, formal recurrence, implementation, and
publication deadline are still equivalent enough for the claim being made.
Python/C++ parity for the same recurrence is not physical correctness.

## Exact Checkpoint

- Repository: `/home/pentester/coding/codex_ida/th08`
- Branch: `main`
- Algorithmic parent:
  `7860a16 Fix local input-pipeline certification`
- The current HEAD should include the native local implementation, selectable
  full-route handoff, and complete Hard-route evidence checkpoints above that
  parent. If not, inspect the intervening diff before trusting this file.
- The live local implementation defaults to persistent pool-read
  destinations, native shared hazard queries, native quantized no-item beam
  reduction, and packed native bullet decode above 16 active slots. Python
  implementations remain explicit rollback/oracles. Hazard-major geometry
  and direct-root retained replays had zero action/hard-label mismatches.
- The authoritative corridor planner remains normal-priority with four native
  workers. One/two-worker limits are ablations; they are not the default.
  Dynamic grid/BVH geometry is deferred because exact certificate geometry is
  already about 1--2 ms outside contention and plan freshness has priority.
- Complete Hard Stage-1 `175049` had 7,099 decisions, zero hits, zero Bomb,
  and zero deadline misses. It also established CE-0124: the first
  post-discontinuity native active input need not equal reset held desired.
  Explicit active/held/pending roots remain shadow-only.
- Complete original-game Hard Route-2 `184942` reached Final B
  `route_complete` with 70,699 decisions, 39 hits, zero Bomb, and stage counts
  `1/1/8/11/9/9`. Global viability was already empty before 38/39 hits;
  boundary and fast-mode factors occurred on 30 and 29. Per-stage local-plan
  median/p95 stayed within `11.81..14.55/20.86..26.90 ms` at up to 1,231
  bullets and 256 lasers. The next primary problem is early feasibility and
  losing-state/route strategy, not another wholesale local geometry rewrite.
- A fixed-reservoir offline replay of 400 empty-kernel Hard pre-hit roots
  changed 28 actions when the default-off losing-state control reserve was
  enabled. All 400 fresh hard vectors were unchanged; 27 changed actions
  reduced reserve deficit, one tied, and none regressed. This is a
  proposal-only losing-state ranking result, not restored viability or
  physical survival evidence.
- Complete audit-only Hard Stage-4A `202439` retained 13,535 decisions and
  1,741 validated capsules. Among 61 empty same-root queries, 6 were spatial
  false empties, 8 primary horizon collapses, and 47 remained unresolved.
  Uniform 4-pixel full-field solve cost `1062.85/3506.43 ms` median/p95 on a
  12-root sample and is not the next live design.
- CE-0127's issue transaction is offline-fixed: the fresh-enemy recertifier
  now preserves a planned member of the fresh/global intersection, restricts
  replacement to that intersection, and explicitly marks empty-intersection
  relaxation. Planned/selected certificates and exact transaction telemetry
  are retained. No-audit Hard Stage-4A gates `211210` and `212756` together
  retained 4,627 transactions with zero silent outside-global selections,
  zero Bomb, and no latency regression. The second reason-aware audit had
  zero violations, closing CE-0127/0128 for this boundary.
- Option-A pre-loss replay rejected putting repair volume into shared beam
  pruning: 2/800 hit-window roots regressed the later terminal hard vector
  (CE-0129). The historical beam and native reducer ABI remain unchanged. A
  new default-off supplemental lane preserves that beam as an immutable
  incumbent and has a separate native reducer. Width 4 changed 286/800 broad
  and 341/800 pre-hit actions; repair improved on 273 and 323, with another
  13 and 18 equal-repair reserve improvements. Historical action identity,
  effective-global membership, componentwise issue/local/terminal hard
  nonregression, route nonregression, and continuation admission all had zero
  violations. Its synchronous supplemental cost was `2.449/3.114 ms`
  broad and `2.425/3.026 ms` pre-hit median/p95. This is proposal-only
  same-root evidence, not physical survival or issue-deadline evidence.
- The direct-root Windows/four-worker gate keeps the width-4 finite selector
  contract-clean: 1,518 comparisons had zero historical/effective-global,
  componentwise hard, route, continuation, Bomb, exception, or forced-issue
  transaction violations. The four-worker planner also passed at
  `0.998x` solve-p95 and `1.015x` throughput ratios. Synchronous current-issue
  delivery is rejected by CE-0130: paired compute increment was
  `2.354/14.273/25.184 ms` median/p95/max, failed fixed
  `5.0/<16.667 ms` limits, and created one new hybrid deadline-proxy miss.
  Do not start the focused Hard physical A/B. The next gate is a complete
  deadline-aware native supplemental boundary or exact-version asynchronous
  publication, followed by the same Windows contention test.
- Six generated TH08-semantic intensive geometry workloads cover native-pool
  and beyond-pool bullets, stop/resume/reverse/redirect transforms,
  executable and degenerate lasers, bodies, tangent boundaries, and
  companion-batch invariance. Collision and clearance-sign parity, batch
  invariance, and end-to-end action/hard labels were exact. Fully off-tube
  `4096`-bullet/`1024`-laser queries cost only `2.211/2.408 ms` for ten
  already-lowered native queries, confirming that the current conservative
  AABB pruning works. Dense genuinely crossing fields remain expensive; no
  viewport crop or per-decision grid/BVH is promoted.
- The original-game full-route supervisor accepts
  `--difficulty easy|normal|hard|lunatic`. `--leave-game-running` applies
  only after accepted `route_complete`: it releases injected keys, closes the
  agent, sends no result/save choice, and leaves the identity-verified game
  process running for a manual replay save. Failures still clean up.
- Linux and Windows quick suites pass `587/587` in `5.283/8.008 s`. The
  bounded formal audit retained only the expected legacy/no-write
  counterexamples at seeds `20002/20003`; the quick belief workspace had zero
  scalar/native, upper, candidate, certification, or bound failures.
- No TH08 runtime, daemon, or unfinished experiment should be alive.
- The only expected untracked file is user-owned `image.png`. Do not stage,
  modify, delete, or clean it.
- The connected IDA database contains the FRScreen names, partial types, and
  input-clock boundary comments recorded in `notes/RESEARCH_LOG.md`. New
  binary work must use IDA Pro MCP, never REA.

Sanity check:

```bash
cd /home/pentester/coding/codex_ida/th08
git status --short
git log -5 --oneline
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected pre-work status:

```text
?? image.png
```

## Current Authority Boundary

| Status | Component | Meaning |
| --- | --- | --- |
| live | native-state sensing and TH08 trajectory/laser/enemy projection | Gameplay sensing is native; screenshots are not a sensor. |
| live | native local implementation acceleration | Persistent pool buffers, packed bullet decode, hazard-major shared query, and quantized no-item beam reducer implement existing boundaries with Python rollback. They add no model authority. |
| live | local exact collision certificate | Fresh issue-time hard fallback with per-position batch semantics and packed equivalent-root induction; hard no-Bomb. Live callers still use the active-equals-held fallback. CE-0127/0128's fresh/global transaction passed two physical authority/latency gates. |
| live | coarse Boolean robust viability | Current global safety authority, subject to its explicit finite model and the unresolved transition-clock boundary. |
| shadow | native FRScreen/MSG input-clock boundary | Tri-state native probe and episode tracker identify manager-clock blocking without control-state authority. Synchronous issue-thread reads/logging are physically perturbative and total contention is unmeasured. |
| shadow | explicit active/held/pending local certificate | Independent scalar oracle, packed finite lease, and root telemetry; old replay roots are inferred and the result cannot rank live input. |
| shadow | losing-root stationary candidate verifier | Exact universal verification of a restricted causal candidate can prove finite-model feasibility, but cannot claim unrestricted losing/optimality. |
| shadow | exact candidate witness publication | Retains root, witness, issued-action label, all-action local certificate, version, and timing; it never changes the live mask. |
| offline/shadow | belief lower bounds, revealed-delay upper, resumable threshold refinement | Research tools for feasibility/optimality gaps; too slow and/or too optimistic for live authority as currently integrated. |
| proposal-only | losing-state control reserve | After Boolean exhaustion, ranks only fresh-hard-equivalent actions by delay-scaled reversal reserve. Hard replay improved reserve deficit without relabeling viability; physical effect is unmeasured. |
| proposal-only | final-only pre-loss continuation/reserve | Inside a complete nonrelaxed viable set, ranks completed historical beam endpoints after hard terminal scoring. Hard replay changed few actions with zero hard regression; physical effect is unmeasured. |
| proposal-only | immutable supplemental continuation lane | Keeps the complete historical beam as an incumbent and admits a separately budgeted endpoint only after exact effective-global, componentwise hard, route, and strict repair/reserve nonregression checks. Width 4 is the retained offline Pareto candidate; it has no live CLI or deadline authority. |
| rejected | repair-aware shared beam pruning | CE-0129: root repair volume displaced endpoints before terminal threat was known and regressed 2/800 pre-hit terminal hard vectors. |
| rejected | every-root candidate submission | Caused measurable live CPU/delivery contention. |
| rejected | 50-ms repeated-manager-frame guard | CE-0121: fired on ordinary slow decisions, churned policy versions, and starved viability. |
| rejected | first-action beam deduplication for live use | Changed only soft choices and improved no sampled hard vector; wider/partitioned variants were materially slower. |
| rejected | inline/fused survival labels, legacy prewarm, synchronous full upper | Delivery cost or invalid cross-version assumptions outweighed their value. |
| proposal-only | beam, greedy, learned, Monte Carlo, MCTS | May order candidates, never replace worst-case verification. |

Do not quietly promote a shadow component. Promotion requires an updated
formal review, exact authority boundary, focused regressions, clean physical
shadow evidence, and a `STRATEGY.md` status change.

## What Is Actually Open

### P0 — CE-0120: physical input clock at frozen manager frames

Observed in complete Stage-4A replay `100451`: after a spell ended,
`enemy_manager_frame` froze during dialogue/transition while the held
direction continued moving the player. `up_left_fast` moved `434.63 px` to
the top-left boundary across six wall pulses; `left_fast` moved `343.65 px`
to the left boundary across eight. Re-audit found five pulse groups, including
one terminal right-censored group; the older report listed only four closed
episodes.

The attempted 50-ms detector was invalid. Complete Stage-4A run `103856`
produced `2,780` guard firings in `7,925` decisions for only `72` real wall
pulses. Available viability queries fell from `9,073` in `100451` to `691`,
and the run recorded `64` hits. RNG means `21 -> 64` is not a controlled
effect size, but the policy-starvation mechanism is direct. The guard was
reverted.

The native semantic boundary is now identified. IDA shows
`frscreen_blocks_enemy_clock` at `0x4358BB` blocks the manager counter exactly
when a non-null FRScreen implementation has signed MSG state `>= 0` or `-2`.
Player movement runs earlier and can still consume active directional input.
Two new complete shadow-only Stage-4A runs retained this state directly.
Corrected run `122014` produced five semantic episodes for five delayed
same-frame pulse groups with zero false positives/negatives against that
proxy; 3,031 ordinary observations were gate-negative, one unstable interval
was unknown, and `-2` was not observed.

This resolves CE-0120 only at the sensor/classification layer. The detector
cannot release movement, reset an epoch, retire a policy, or alter estimator
state. Its opt-in captures and logging still consume issue-thread time, so it
is not physically side-effect-free. Next validate a no-write action/epoch
counterfactual, broaden negative workloads, resolve or exclude `-2`, and
measure total contention before any explicitly scoped neutralization trial.
Do not recreate a raw wall-time threshold or promote FRScreen serial into a
universal player clock.

### P1 — direct local pipeline roots exposed a discontinuity defect

The local audit found two correctness defects. First, a batched hazard result
could depend on unrelated companion positions; per-position bullet/laser
relevance masking now restores batch invariance. Second, the old local
certificate equated held desired input with native active input and sampled a
new full pickup delay even when holding the complete desired mask should be
no-write.

An independent scalar oracle and a packed finite-lease implementation now
model native active input, held desired input, an optional older pending
command, conditioned remaining support, and conditional new writes. The
packed equivalent-root path had zero hard parity failures on the retained
`155 + 156` sampled roots. Pending-aware semantics changed 86 and 85 sampled
safe-action sets. These mismatch/pre-hit-heavy samples establish materiality,
not population rates or prevented hits.

The correct packed certificate measured `3.134/6.372 ms` Stage 4A and
`3.936/7.911 ms` Stage 6B median/p95 in Linux replay, excluding JSON/object
decode but including projection, packing, induction, and all-action
certification. That does not prove a Windows issue deadline. Old trace roots
are inferred; new rows retain explicit root telemetry, but live selection
still uses active-equals-held fallback semantics.

First-action beam labels changed five and four soft choices with no sampled
hard-vector improvement. Independent first-action partitions also improved
zero hard roots at `191.795/275.649 ms` median, so those modes remain
default-off. A wholesale C++ rewrite is deferred until a correct explicit-root
Windows end-to-end boundary demonstrates a deadline miss.

Direct roots are now retained. Hard Stage-1 CE-0124 observed
`input_current=down_right` while held desired had been reset to stay at the
first decision after an action-epoch discontinuity. There was no reconstructed
pending support and the estimator correctly marked the root inconsistent.
Therefore an epoch reset cannot initialize active input from held desired.

The current checkpoint accelerates the existing fallback but does not pass the
explicit root into live selection. Reconcile discontinuity initialization,
unknown pending support, CE-0120, and direct-root replay before any authority
change. See CE-0122 through CE-0124,
`notes/LOCAL_PIPELINE_CERTIFICATE_AND_BEAM_AUDIT_20260726.md`, and
`notes/LOCAL_NATIVE_GEOMETRY_AND_CONTENTION_20260726.md`.

### P2 — candidate publication is measured, not promoted

Clean Stage-4A shadow `100451` completed `9,222` decisions with `21` hits,
zero Bomb, and no runtime/foreground/manual/JSON failure. Exact losing-root
candidate delivery was `3,913/4,187 = 93.46%`; `438` delivered roots were
candidate-winning, `223` raised the issued action from modeled loss to modeled
feasibility, and publication integrity errors were zero.

Run `103856` added explicit publication-helper timing:

- publication median/p95: approximately `0.0041/0.0059 ms`;
- lookup median/p95: approximately `0.0149/0.0208 ms`;
- exact delivery: `267/297 = 89.9%`;
- `32` winning hits and `17` feasibility-gain rows;
- zero publication-integrity errors.

However, `103856` was physically contaminated by the rejected frame guard.
It validates helper cost and integrity only, not survival or clean contention.
Before considering action authority, run a fresh post-rollback shadow on a
non-Stage-6B workload and retain candidate witness plus alternate-action
certificate. A candidate win proves only feasibility in its declared finite
model.

### P3 — Boolean-losing is not unrestricted losing

Stage-6B losing-only v2 `011639` completed `14,652` hard-no-Bomb decisions
with `26` hits and delivered `6,192/6,618 = 93.56%` exact losing roots without
the contention of the rejected every-root service. All `26` contacts still
followed Boolean-kernel exhaustion.

Two RNG-distinct Stage-6B capsule cohorts each classified 32 roots as:

- 20 exact losing under the tested finite recurrence;
- 11 feasible under a verified stationary candidate;
- 1 feasible only after targeted action-column refinement.

One threshold needed `265.77 ms` before refinement found a positive 32-frame
witness. Candidate exhaustion and a 100-ms deadline therefore remain
unresolved, not losing. The broad research problem is still planning
completeness under partial input-pipeline information, unrestricted
continuation-action growth, future births/transform uncertainty, and issue-time
delivery. Do not spend more performance effort on a recurrence until its
physical/information semantics pass the formal audit.

Priority order:

1. resolve CE-0120’s semantic clock boundary without live authority;
2. obtain a direct-root, full-boundary local-certificate shadow gate;
3. obtain a clean post-rollback candidate-publication shadow gate;
4. use retained losing roots to improve attainable lower refinement and
   issue-time feasible-action coverage;
5. refine upper/optimality work only for actions still capable of changing the
   decision;
6. then return to broader route strategy.

## Current Physical Evidence

Retain the two newest complete replay-capable bundles per workload:

| Workload | Bundles | Interpretation |
| --- | --- | --- |
| Lunatic Route-2 Stage 6B, candidate shadow | `004142`, `011639` | `004142` every-root service rejected; `011639` losing-only service accepted shadow-only. |
| Lunatic Route-2 Stage 4A, publication/clock replay floor | `100451`, `103856` | `100451` is the original CE-0120 witness; `103856` rejects the live guard. Both retain the prior replay-capable floor. |
| Lunatic Route-2 Stage 4A, semantic input-clock telemetry | `120839`, `122014` | `120839` exposed tracker segmentation; corrected `122014` matched all five delayed pulse groups. Viability capsules were intentionally disabled, so these do not replace the replay floor or support planner-replay claims. |
| Lunatic Route-2 Stage 4A, native local implementation | `151821`, `160712` | Complete direct-root/replay workloads for pool-buffer, hazard, and native-beam measurement. |
| Lunatic Route-2 Stage 6B, native local implementation | `163501`, `165841` | Complete direct-root/replay workloads; `165841` contains the 210-laser geometry/contention witness. |
| Hard Route-2 Stage 1, native local implementation | `175049` | One complete zero-hit/no-Bomb/deadline-miss focused gate. It is not yet a two-bundle workload floor. |
| Hard Route-2 full route, feasibility diagnosis | `184942` | Complete Final-B run with 39 hits, no Bomb, replayable raw trace, compact dossier, and manual replay-save handoff. One bundle does not satisfy the two-bundle floor. |
| Hard Route-2 Stage 4A, viability audit | `202439` | Complete audit-only run with 1,741 readable capsules, exact same-root differential, and CE-0127 issue-intersection witness. One bundle does not satisfy the two-bundle floor. |

The `103856` `.session.json` says `failed` only because the original
postprocessor rejected an explicit null enemy snapshot after the accepted
route-complete trial. The parser was repaired and artifacts recovered without
rewriting provenance. Its raw audit passed `10,784` records and `2,060`
capsules; bundle SHA-256:
`d8d6ecdf7b0ae955c58317fd27fa3735fea9c14ee1471faebe1d7fca1f5e4c29`.

The complete `011639` audit passed `14,791` records, `14,652` decisions, and
`2,689` capsules; bundle SHA-256:
`9e8af717c548dc6456d471c15ac2be9777f755d7b94bc3fc6067e4b289b38a77`.

The two current Stage-4A raw JSONL traces contain `10,653` and `12,122`
records. Their SHA-256 values are
`520d7e772464967a01d49b60a95f26b26f8a6c405e878c07d34a6ede3ceb903f`
and
`25a01efe87fba457051ca78b0f485a6068f7606f1f98b772b0f3372689d8122f`.
Both reached `terminal_unload` and `route_complete`, passed hard no-Bomb
verification, and left the semantic detector shadow-only. Older `100451` and
`103856` remain the canonical CE-0120/0121 evidence and replay-capable floor;
they were not deleted. The new semantic traces and compact artifacts are also
retained locally, but `viability_audit_capsules` is null by design.
The compact input-clock audit SHA-256 values are
`76d052d36f9b5183fa01508f11504835400ad8fce39c92a42b28d69134b9f0cf`
and
`f145a5f2631d833ce90ae2d5059948e38251ce191b9cfc16b1f6ef5ad7e98f6c`.

Compact evidence and interpretation live in `notes/runs/`,
`notes/COUNTEREXAMPLES.md`, and `notes/RESEARCH_LOG.md`. Do not delete either
raw bundle until the two-bundle rule in `AGENTS.md` is satisfied by newer
same-workload captures.

Start physical review with:

- `notes/runs/lunatic_route2_stage6b_unattended_20260726_011639.md`
- `notes/runs/lunatic_route2_stage4a_unattended_20260726_120839.md`
- `notes/runs/lunatic_route2_stage4a_unattended_20260726_122014.md`

## Formal References

Read only the subset relevant to the change, but always begin with the base
formalization.

- Base physical/information contract:
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
- Unrestricted action growth and attainable lower bounds:
  `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`
- Correctness/performance audit:
  `notes/BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md`
- Incumbent/selective upper:
  `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`
- Resumable deadline-safe certification:
  `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`
- Feasibility-first anytime synthesis:
  `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`
- Exact augmented state/reachable tube:
  `notes/AUGMENTED_PIPELINE_REACHABLE_TUBE_20260725.md`
- Rolling/cross-version prewarm:
  `notes/ROLLING_PIPELINE_PREWARM_20260725.md` and
  `notes/EXACT_ROOT_FRONTIER_PREWARM_20260725.md`
- Candidate service and witness publication:
  `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md` and
  `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`
- Frozen manager/input boundary:
  `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`
- Local active/held/pending certificate and beam audit:
  `notes/LOCAL_PIPELINE_CERTIFICATE_AND_BEAM_AUDIT_20260726.md`
- Native local geometry, decode, beam, and contention:
  `notes/LOCAL_NATIVE_GEOMETRY_AND_CONTENTION_20260726.md`,
  `notes/LOCAL_NATIVE_HAZARD_QUERY_PROPOSAL_20260726.md`,
  `notes/LOCAL_NATIVE_BEAM_REDUCTION_PROPOSAL_20260726.md`, and
  `notes/PACKED_NATIVE_BULLET_DECODE_PROPOSAL_20260726.md`
- Earlier Boolean/losing root analysis:
  `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md` and
  `notes/LOSING_STATE_ROOT_CAUSE_20260725.md`
- Current Hard same-root feasibility split and decision:
  `notes/HARD_STAGE4A_VIABILITY_DIFFERENTIAL_20260726.md`
- Current pre-loss ranking and immutable supplemental-lane contracts:
  `notes/PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md` and
  `notes/IMMUTABLE_SUPPLEMENTAL_CONTINUATION_LANE_20260726.md`

Relevant durable counterexamples include CE-0108, CE-0109, CE-0111, CE-0118,
CE-0120 through CE-0125, and CE-0127 through CE-0129. Do not infer present
authority from a historical
note; the table above and `STRATEGY.md` control current status.

## Environment And Build

- WSL distribution: `ubuntu`
- Workspace:
  `/home/pentester/coding/codex_ida/th08`
- Windows game directory:
  `D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)`
- WSL game directory:
  `/mnt/d/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)`
- Target: `th08.exe`
- Required SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
- Launcher: `run_th08_no_life_decrement_attach.bat`
- Patch byte: `0x0044D0FA`, expected runtime value `0x00`
- Windows Python:
  `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`

The external launcher must call
`scripts\tools\th08_attach_no_life_decrement.py`. A Windows entrypoint under
`scripts/tools/` must prepend its parent `scripts/` directory before imports.

Rebuild ignored native libraries after C++ changes:

```bash
PYTHONPATH=scripts python3 scripts/tools/build_native_planner.py --target linux
PYTHONPATH=scripts python3 scripts/tools/build_native_planner.py --target windows
```

The NumPy fallback is useful for parity but too slow for physical acceptance.
Use `TOUHOU_DISABLE_NATIVE_PLANNER=1` only for explicit ablation.

## Tests And Offline Profiles

Focused test:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_touhou_control_local_pipeline_oracle.py'
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_th08_local_pipeline_certificate.py'
```

Quick complete suite:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

Quick formal/performance profiles:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/audit_pipeline_formal_correctness.py \
  /tmp/pipeline-formal-quick.json
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_belief_pipeline_workspace.py \
  /tmp/belief-pipeline-quick.json
```

Run full 128-case/unrestricted/capsule profiles only when their model or native
recurrence changes or when retaining evidence. Benchmarks belong in
`scripts/benchmarks/`; reports/differentials in `scripts/analysis/`; explicit
build/probe/patch/capture commands in `scripts/tools/`.

Retained local replay evidence:

- `artifacts/benchmarks/local_pipeline_certificate_20260726.json`
- `artifacts/benchmarks/local_beam_stability_20260726.json`
- `artifacts/benchmarks/local_native_beam_windows_20260726.json`
- `artifacts/benchmarks/local_native_hazard_hazard_major_windows_20260726.json`
- `artifacts/benchmarks/native_packed_bullet_decode_windows_20260726.json`
- `artifacts/benchmarks/local_issue_contention_windows_20260726.json`
- `artifacts/benchmarks/hard_supplemental_direct_root_contention_windows_20260726.json`

The exact reproduction commands and timing boundaries are in
`notes/LOCAL_PIPELINE_CERTIFICATE_AND_BEAM_AUDIT_20260726.md`.

Windows UNC discovery must use this loader. Ordinary `unittest -s <UNC>`,
`cmd.exe` UNC `cd/pushd`, and a PowerShell-only `PSDrive` do not provide an
importable test root:

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe -c \
  'import sys,unittest; root=r"\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08"; sys.path.insert(0,root+r"\scripts"); tests=root+r"\tests"; suite=unittest.TestLoader().discover(tests,pattern="test_*.py",top_level_dir=tests); result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(0 if result.wasSuccessful() else 1)'
```

Change only the `pattern` for a focused Windows run.

## Physical Trial Commands

The user has authorized unattended launch, input injection, monitoring,
stopping, and identity-scoped cleanup. Do not start a physical run merely to
validate this documentation checkpoint.

Practice stage from WSL, always non-TTY:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat' \
  --stage 4a --status-seconds 15 --stall-timeout 120
```

Continuous Hard Route-2, retaining the game after accepted completion so the
replay can be saved manually:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_full_route_agent.bat' \
  --difficulty hard --leave-game-running \
  --status-seconds 30 --stall-timeout 120
```

Omit `--leave-game-running` for the old automatic identity-scoped process
cleanup. The switch never sends a save/no-save selection. It cannot preserve
a failed or incomplete attempt.

Selectable Sakuya/Remilia Route-2 practice stages are
`1 2 3 4a 5 6b`; 4B and 6A are route-locked. Do not patch the route mask to
claim coverage.

Important WSL/Windows behavior:

- never launch the supervisor with a PTY; a PTY can block on a Windows console
  cursor query before the game appears;
- a WSL `cmd.exe`/Windows-Python call can return while the supervisor remains
  alive under `/init`; completion requires the trace, terminal record, final
  summary, session status, and process cleanup;
- monitor active gameplay using low-load Linux reads; Windows consoles and
  process probes can steal foreground and invalidate the run;
- stop the supervisor first and allow its `finally` cleanup; release keys
  before killing only the verified TH08 image;
- never end a turn with a required game, supervisor, or daemon still running.

Monitor a trace:

```bash
trace=$(ls -1t artifacts/runtime_reports/*unattended*.jsonl | head -n1)
PYTHONPATH=scripts python3 scripts/analysis/th08_longrun_status.py "$trace"
tail -n 1 "$trace"
```

Full-route success requires both Final-B `terminal_unload` and the later
`termination_reason=route_complete`. Record foreground loss, manual input,
manual `Z`, reset tails, unexpected Bomb, and auto-confirm failure as
contamination.

For a focused thprac loop, start a fresh prewarmed Windows hotkey daemon for
each attempt, enter gameplay manually, then use F8 to start, F9 to stop/pause,
and F10 to exit. The unattended supervisor remains the preferred acceptance
path because it also validates menus, terminal unload, no-save handling,
artifacts, and cleanup.

## Next Good Checkpoint

The complete Hard route is finished. The immutable supplemental-lane offline
gate is also complete. The current user-directed algorithmic gate is:

1. measure width 4 on direct Windows roots across
   observe/decode/project/certify/supplemental/issue and under the live
   four-worker planner contention. A miss or budget overrun must return the
   historical decision; optional work must not age authoritative
   publication;
2. if delivery remains clean, run the lane as side-effect-free focused Hard
   shadow before considering a physical A/B. Do not add a live CLI or infer
   prevented hits from same-root replay;
3. add exact augmented-root partial-survival candidate witnesses as the
   post-loss fallback;
4. keep 8/4-pixel work query-local and proof-backed. Full-field fine
   refinement remains rejected by low rescue rate and deadline cost;
5. use additional CPU through deterministic process-level independent-root
   shards. Do not raise the four-worker live same-root default without a
   delivery-contention gate;
6. retain the current AABB geometry pruning. Revisit a per-frame index only
   if direct-root telemetry isolates genuinely relevant dense geometry after
   construction/lowering, rather than planner contention, as the deadline
   bottleneck.

The current evidence and five formal-review answers are in
`notes/HARD_FULL_ROUTE_FEASIBILITY_DIAGNOSIS_20260726.md` and
`notes/HARD_STAGE4A_VIABILITY_DIFFERENTIAL_20260726.md`. The current
pre-loss contract, rejected beam counterexample, and final-only evidence are
in `notes/PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md`. The immutable
supplemental design, replay results, intensive geometry corpus, and promotion
boundary are in
`notes/IMMUTABLE_SUPPLEMENTAL_CONTINUATION_LANE_20260726.md`.

A useful next algorithmic checkpoint is the action consequence of the now
validated semantic sensor, not another detector or threshold tweak. It should:

1. retain a no-write counterfactual for the exact episode-entry mask that
   would remove movement bits, preserve `SHOT`, and request one immutable
   epoch transition;
2. compare prospective policy retirement, pre-detection displacement, and
   next-phase entry state without changing live input;
3. extend the negative set beyond Stage 4A to pauses, scene unloads, and other
   stage/dialogue owners; resolve `msg_state == -2` or explicitly exclude it;
4. measure total probe/capture CPU and delivery contention, not only logged
   lookup time;
5. retain every mismatch and keep the counterfactual shadow-only until its
   action consequence is bounded;
6. only then run an explicitly scoped physical neutralization/one-reset trial
   for confirmed `msg_state >= 0` episodes;
7. update the formal/design note, strategy ledger, counterexamples, research
   log, focused tests, and quick Linux/Windows suites;
8. commit one focused checkpoint.

If continuing local micro-control, first collect a shadow-only trace with the
new direct `local_pipeline_root` rows, verify every estimator-consistency
failure, replay direct rather than reconstructed roots, and measure the full
Windows observe/decode/project/certify/issue boundary. Do not pass the root to
`choose_action` or `recertify_action_for_fresh_hazards` until that gate and a
strategy-status change pass. Reconsider a compact native
decode/project/certify boundary only if the correct end-to-end path misses its
deadline.

If instead working on candidate authority, first obtain a fresh uncontaminated
post-rollback Stage-4A (or another non-Stage-6B) shadow run with exact witness,
alternate-action certificate, publication timing, and measured
CPU/delivery/policy-age contention. A physical run remains evidence, not a
promotion by itself.

## Common Traps

- Do not use REA.
- Do not treat Python/C++ parity as problem correctness.
- Do not treat a budgeted lower bound, exhausted candidate set, timeout, or
  incomplete upper as unrestricted losing/optimality.
- Do not let hidden delay/cadence branches choose separate future actions.
- Do not reset pending delay when the desired mask is held/no-write.
- Do not use `enemy_manager_frame` or a short wall-time threshold as the only
  physical input clock.
- Do not grant action authority to candidate/label shadow output.
- Do not submit expensive shadow work on every root or share the live
  publication critical path.
- Do not reuse proof labels across immutable policy versions.
- Do not tune one stage/spell into universal mechanics.
- Do not add engineering-plumbing tests that do not protect evidence or a
  safety contract.
- Do not confuse compact reports with replay-capable raw evidence.
- Do not stage `image.png`, connector-created `node_modules/`/`package*.json`,
  raw JSONL, capsules, binaries, logs, caches, or credentials.
