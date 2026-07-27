# Touhou Solver Current Handoff

This is the volatile entrypoint for the TH08 Sakuya/Remilia no-Bomb solver.
`AGENTS.md` is the durable contract, `STRATEGY.md` is the promotion ledger,
and design/run notes retain derivations and history.

## Read In This Order

1. `AGENTS.md`
2. this file
3. `STRATEGY.md`
4. `notes/review/CONSOLIDATED_RESEARCH_AND_REFACTOR_ROADMAP_20260727.md`
   for the agreed implementation order; the formal notes below remain
   authoritative
5. `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
6. `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`
7. `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`
8. `notes/HARD_FULL_ROUTE_FEASIBILITY_DIAGNOSIS_20260726.md`
9. `notes/PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md`
10. `notes/NATIVE_SUPPLEMENTAL_ROLLOUT_DEADLINE_CONTRACT_20260726.md`
11. `notes/EXACT_VERSION_ASYNC_SUPPLEMENTAL_PUBLICATION_20260726.md`
12. `notes/TH08_SEMANTIC_DIFFERENTIAL_FUZZER_CONTRACT_20260726.md`
13. `notes/SUPPLEMENTAL_DIRECT_ROOT_WINDOWS_CONTENTION_GATE_20260726.md`
14. the relevant recent run note and counterexample rows before live work

Before trusting a result, verify that the physical problem, formal
recurrence, implementation, immutable version, and publication deadline still
describe the same decision. Python/C++ parity is not physical correctness.

## Exact Checkpoint

- Repository branch: `main`.
- Latest algorithmic checkpoint:
  `d4467bd Add deadline-aware native supplemental gate`.
- Latest structural checkpoint: native-binding R2 shared-library boundary.
  `touhou_control.native.library` owns platform path/load state, reusable
  symbol caches, atomic optional function groups, and pipeline status
  conversion. `native_backend` still owns every ctypes declaration and
  wrapper pending the domain split, while compatibility names and exact
  loader/status behavior are retained. Corridor R1 remains complete with its
  169-line façade and split runtime ownership. The R0 behavior and 43-symbol
  ABI baselines remain unchanged. No model, recurrence, action, strategy, or
  C ABI changed.
- The current release-preparation commit must be a descendant of that
  checkpoint.
- Release verification rebuilt both native targets and passed the reduced
  quick suite `584/584` on Linux in `5.213 s` and Windows in `14.365 s`.
- The native-library checkpoint passes the expanded quick suite `600/600`
  on Linux in `5.420 s` and Windows in `8.223 s` with one existing skip.
- No TH08 process, controller daemon, supervisor, or unfinished experiment is
  expected to be alive.
- Native build output, raw traces, screenshots, caches, and the local
  `image.png` are ignored. A normal pre-work tree is clean.

Sanity check:

```bash
git status --short
git log -5 --oneline
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

## Current Result

### Local micro-control

**Observed:** persistent pool-read destinations, packed native bullet decode,
hazard-major shared native C++ queries, and native quantized no-item beam
reduction match their independent Python/NumPy paths on retained direct roots
and generated semantic cases. The live issue path still uses a fresh exact
local collision certificate and hard no-Bomb fallback.

**Observed:** the 256-case semantic gate and 96-case research profile had zero
collision, clearance sign/value, risk, batch-invariance, or supplemental
endpoint mismatches. Research maxima were 3,900 bullets, 1,387 lasers,
62 bodies, and horizon 24. NumPy/native geometry p95 was
`121.538/40.500 ms`; Python/native supplemental p95 was
`9.931/3.337 ms`.

**Conclusion:** local decode/geometry performance is serviceable and is not
the dominant physical failure in current Hard evidence. This is implementation
and sampled finite-semantics evidence, not complete shipped-game or physical
safety proof. Keep the Python oracles and explicit rollback paths.

### Physical Hard evidence

**Observed:** Hard Stage-1 run `175049` completed 7,099 decisions with zero
hits, Bombs, or deadline misses.

**Observed:** complete original-game Hard Route-2 run `184942` reached Final B
and `route_complete` with 70,699 decisions, 39 hits, zero Bombs, and stage hit
counts `1/1/8/11/9/9`. Global viability was already empty before 38/39 hits.
Boundary and fast-mode factors appeared on 30 and 29 hits. Per-stage
local-plan median/p95 remained within `11.81..14.55/20.86..26.90 ms`, at up
to 1,231 bullets and 256 lasers.

**Observed:** Hard Stage-4A audit `202439` retained 1,741 validated capsules.
Of 61 empty same-root queries, six were coarse spatial false empties, eight
were primary horizon collapses, and 47 remained unresolved. Uniform full-field
4-pixel solving cost `1062.85/3506.43 ms` median/p95 on 12 roots and is not a
live design.

**Conclusion:** the primary algorithmic problem is preserving global
feasibility earlier and defining certified behavior after finite-kernel
exhaustion, not a wholesale local geometry rewrite.

### Issue transaction and supplemental search

**Observed:** CE-0127/0128's fresh/global issue transaction passed no-audit
Hard Stage-4A runs `211210` and `212756`: 4,627 transactions had zero silent
outside-global selections, zero Bombs, and no latency regression.

**Observed:** adding repair volume to shared beam pruning regressed two of 800
pre-hit terminal hard vectors (CE-0129). The historical beam and native reducer
ABI therefore remain unchanged. The width-4 supplemental lane preserves the
historical endpoint and passed same-root finite nonregression checks, but is
proposal-only.

**Observed:** the complete native supplemental boundary uses a persistent C++
workspace, 5-ms absolute deadline, cooperative cancellation, and
complete-only results. Native rollout cost `0.876/1.365/1.942 ms`
median/p95/max under the retained Windows workload, but end-to-end synchronous
delivery still had `7.054/53.721 ms` paired p95/max and one new deadline proxy
miss.

**Observed:** exact-version asynchronous publication used a below-normal,
newest-wins worker, exact identity, stale cancellation/discard, and
nonblocking lookup. It completed 728/729 eligible roots and retained 294/294
reference changes with zero finite/parity/fallback violations, but paired
latency remained `2.240/8.139/12.214 ms` and created CE-0131's new hybrid
deadline miss.

**Decision:** both current-issue supplemental delivery forms are rejected.
Keep the live four-worker global planner, keep supplemental modes default-off,
and do not enter a focused physical A/B without a new causal publication
design and the unchanged Windows contention gate.

### Frozen manager-frame boundary

**Observed:** during post-spell/dialogue transitions,
`enemy_manager_frame` can freeze while held input continues moving the player
(CE-0120). The 50-ms repeated-counter detector fired on ordinary slow
decisions, churned versions, and starved viability (CE-0121).

**Decision:** the native FRScreen/MSG episode sensor remains shadow-only. No
wall-time threshold or manager counter currently has live actuator authority.
This remains a parallel sensing/control obligation, but it is not the primary
global-planning objective.

## Authority Boundary

| Status | Component | Authority |
| --- | --- | --- |
| live | native-state sensing and TH08 hazard projection | Gameplay state comes from native memory; screenshots are not a runtime sensor. |
| live | native local implementation acceleration | Pool buffers, packed decode, shared hazard query, and local reducer implement existing semantics with Python rollback. They add no model authority. |
| live | issue-time local collision certificate | Fresh hard fallback, per-position batch semantics, hard no-Bomb, and the CE-0127/0128 fresh/global transaction. Live callers still use the active-equals-held estimator fallback. |
| live | coarse Boolean robust viability | Current global finite-model safety authority, subject to declared resolution/horizon/uncertainty and the unresolved transition-clock boundary. |
| shadow | native FRScreen/MSG input-clock boundary | Detects episodes; cannot retire/reset policy or neutralize movement. |
| shadow | explicit active/held/pending certificate | Has scalar/packed oracles and direct-root telemetry; cannot rank live input. |
| shadow | restricted losing-root candidate verifier/publication | May prove a declared finite candidate and retain its witness; cannot claim unrestricted losing/optimality or change input. |
| offline/shadow | belief lower bounds, revealed-delay upper, resumable refinement | Feasibility/optimality research; too slow or optimistic for current live authority. |
| proposal-only | losing-state control reserve | Ranks fresh-hard-equivalent actions after Boolean exhaustion; physical effect unmeasured. |
| proposal-only | final-only continuation and width-4 supplemental lane | Preserves hard membership and the historical incumbent in finite replay; no live CLI or delivery authority. |
| rejected | repair-aware shared beam pruning | CE-0129 terminal-hard regressions. |
| rejected | synchronous native supplemental delivery | End-to-end Windows latency gate failed. |
| rejected | same-issue exact-version async supplemental delivery | CE-0131 deadline-proxy miss. |
| rejected | repeated-manager-frame wall-time guard | CE-0121 false firing and publication starvation. |
| rejected | every-root candidate submission / inline survival refinement | Measurable contention on the live publication path. |
| proposal-only | greedy, learned, Monte Carlo, MCTS, unproved beam/pruning | May order proposals; cannot replace worst-case verification. |

Promotion requires an updated formal review, exact authority boundary,
deterministic regressions, clean side-effect-free shadow evidence, delivery
measurement, and a `STRATEGY.md` status change.

## Open Problems In Priority Order

### P0 — Preserve global feasibility and define post-loss authority

Current Hard failures overwhelmingly follow finite-kernel exhaustion.
The next gate should:

1. replay identical retained direct roots and split loss into spatial
   coarsening, horizon, uncertainty, forecast/birth, route/tube, and unresolved
   causes;
2. introduce proof-backed query-local refinement only where a coarse state is
   ambiguous, never uniform full-field 4-pixel solving;
3. retain root actions unrestricted while using exact augmented-root
   partial-survival witnesses as a post-loss lower bound;
4. keep survival hard and route/resource objectives inside the viable set;
5. publish the authoritative Boolean result before optional work;
6. use extra CPU through deterministic process-level independent-root shards,
   without increasing the live same-root worker default beyond four;
7. validate recurrence/geometry changes with the semantic fuzzer and validate
   delivery claims on Windows direct roots.

Candidate exhaustion, timeout, or a budgeted lower bound must remain
unresolved rather than “losing.”

### P1 — Complete sensing and future-hazard semantics

One Hard-route contact was a sensor gap, one enemy-body contact was absent
from the action snapshot, and earlier cached-global selections were contradicted
by fresh local prefixes. Continue birth, transform, body, and issue-snapshot
audits with retained minimal witnesses. Do not broaden action authority from
incomplete sensing.

### P2 — Resolve CE-0120 at the actuator boundary

Retain exact episode-entry active/held/pending roots and a no-write
counterfactual that removes movement while preserving `SHOT`. Extend the
negative set across pauses, unloads, dialogues, and `msg_state == -2`;
measure probe and delivery contention. Only then consider an explicitly
scoped physical neutralization/reset trial.

### P3 — Reopen supplemental delivery only with a new causal boundary

The finite selector remains useful offline. Reopen it only if the exact
hazard/policy version can exist before the issue transaction or execution
resources are genuinely isolated. Rerun the unchanged Windows gate; do not
weaken four global workers or reuse a merely similar root.

## Formal References

- Base physical/information contract:
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
- Reachable tube:
  `notes/AUGMENTED_PIPELINE_REACHABLE_TUBE_20260725.md`
- Lower/upper/anytime synthesis:
  `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`,
  `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`,
  `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`,
  `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`
- Candidate witness/publication:
  `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`,
  `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`
- Local pipeline and native acceleration:
  `notes/LOCAL_PIPELINE_CERTIFICATE_AND_BEAM_AUDIT_20260726.md`,
  `notes/LOCAL_NATIVE_GEOMETRY_AND_CONTENTION_20260726.md`
- Hard feasibility:
  `notes/HARD_FULL_ROUTE_FEASIBILITY_DIAGNOSIS_20260726.md`,
  `notes/HARD_STAGE4A_VIABILITY_DIFFERENTIAL_20260726.md`
- Pre-loss/supplemental:
  `notes/PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md`,
  `notes/IMMUTABLE_SUPPLEMENTAL_CONTINUATION_LANE_20260726.md`,
  `notes/NATIVE_SUPPLEMENTAL_ROLLOUT_DEADLINE_CONTRACT_20260726.md`,
  `notes/EXACT_VERSION_ASYNC_SUPPLEMENTAL_PUBLICATION_20260726.md`,
  `notes/SUPPLEMENTAL_DIRECT_ROOT_WINDOWS_CONTENTION_GATE_20260726.md`
- Frozen input clock:
  `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`
- Generated differential:
  `notes/TH08_SEMANTIC_DIFFERENTIAL_FUZZER_CONTRACT_20260726.md`

Relevant durable failures include CE-0108, CE-0109, CE-0111, CE-0118,
CE-0120 through CE-0125, and CE-0127 through CE-0131. Historical notes do not
override the authority table above.

## Retained Workloads

| Workload | Bundle | Purpose |
| --- | --- | --- |
| Lunatic Route-2 Stage 4A | `100451`, `103856` | CE-0120/0121 canonical transition evidence and replay floor. |
| Hard Route-2 Stage 1 | `175049` | Zero-hit native local gate; one-bundle evidence only. |
| Hard Route-2 full route | `184942` | Complete route, 39-hit feasibility diagnosis; one-bundle evidence only. |
| Hard Route-2 Stage 4A | `202439`, `211210`, `212756` | Capsule audit and fresh/global issue transaction; `211210/212756` form the newest compatible no-audit floor. |

Compact benchmark evidence:

- `artifacts/benchmarks/local_pipeline_certificate_20260726.json`
- `artifacts/benchmarks/local_native_hazard_hazard_major_windows_20260726.json`
- `artifacts/benchmarks/native_packed_bullet_decode_windows_20260726.json`
- `artifacts/benchmarks/local_issue_contention_windows_20260726.json`
- `artifacts/benchmarks/hard_supplemental_direct_root_contention_windows_20260726.json`
- `artifacts/benchmarks/hard_supplemental_full_native_direct_root_contention_windows_20260726.json`
- `artifacts/benchmarks/hard_supplemental_exact_async_final_direct_root_contention_windows_20260726.json`
- `artifacts/benchmarks/th08_semantic_differential_gate_20260726.json`
- `artifacts/benchmarks/th08_semantic_differential_research_20260726.json`

Raw replay bundles remain local and ignored. Do not delete an older workload
bundle until the two-newer-compatible-bundle rule in `AGENTS.md` is satisfied.

## Environment And Build

- WSL distribution: `ubuntu`
- Windows game directory:
  `D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)`
- Target: `th08.exe`
- Required SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
- Launcher: `run_th08_no_life_decrement_attach.bat`
- No-life-decrement patch byte: `0x0044D0FA`, expected `0x00`
- Windows Python:
  `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`

The external launcher calls
`scripts\tools\th08_attach_no_life_decrement.py`. Windows tools under
`scripts/tools/` prepend their parent `scripts/` path before imports.

Rebuild ignored native libraries after C++ changes:

```bash
python3 scripts/tools/build_native_planner.py --target linux
python3 scripts/tools/build_native_planner.py --target windows
```

Use `TOUHOU_DISABLE_NATIVE_PLANNER=1` only for explicit NumPy/Python ablation.

## Test Commands

Focused local pipeline:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_touhou_control_local_pipeline_oracle.py'
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_th08_local_pipeline_certificate.py'
```

Quick suite:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

Bounded formal/performance profiles:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/audit_pipeline_formal_correctness.py \
  /tmp/pipeline-formal-quick.json
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_belief_pipeline_workspace.py \
  /tmp/belief-pipeline-quick.json
```

Semantic gate:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_semantic_differential.py \
  --profile gate --seed 0xce0132 --count 256 \
  --output /tmp/th08-semantic-gate.json
```

Run broad/unrestricted/capsule profiles only when their model/kernel changes
or evidence is being retained.

Windows UNC discovery must use the loader below; ordinary
`unittest -s <UNC>`, UNC `cmd.exe` `cd/pushd`, and a PowerShell-only `PSDrive`
do not produce an importable root:

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe -c \
  'import sys,unittest; root=r"\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08"; sys.path.insert(0,root+r"\scripts"); tests=root+r"\tests"; suite=unittest.TestLoader().discover(tests,pattern="test_*.py",top_level_dir=tests); result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(0 if result.wasSuccessful() else 1)'
```

Change only `pattern` for a focused Windows run.

## Physical Trial Commands

Do not start a physical run merely to validate a documentation checkpoint.
Use non-TTY WSL launch.

Practice:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat' \
  --stage 4a --status-seconds 15 --stall-timeout 120
```

Continuous Hard Route-2, leaving the accepted game alive for manual replay
save:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_full_route_agent.bat' \
  --difficulty hard --leave-game-running \
  --status-seconds 30 --stall-timeout 120
```

Omit `--leave-game-running` for identity-scoped automatic cleanup. The switch
never chooses save/no-save and cannot preserve a failed run. Route-2 practice
stages are `1 2 3 4a 5 6b`; 4B and 6A are route-locked.

Operational rules:

- never launch the supervisor with a PTY;
- WSL command return is not supervisor completion;
- avoid Windows console/process probes during active gameplay;
- stop the supervisor first and allow `finally` cleanup;
- release all keys before any identity-scoped process termination;
- require Final-B `terminal_unload` and later
  `termination_reason=route_complete`;
- record manual input, manual `Z`, foreground loss, reset tails, unexpected
  Bombs, and auto-confirm failure;
- never end a turn with a required game, supervisor, or daemon alive.

Monitor:

```bash
trace=$(ls -1t artifacts/runtime_reports/*unattended*.jsonl | head -n1)
PYTHONPATH=scripts python3 scripts/analysis/th08_longrun_status.py "$trace"
tail -n 1 "$trace"
```

## Common Traps

- Do not use REA.
- Do not equate implementation parity with physical correctness.
- Do not turn timeout, candidate exhaustion, or a restricted lower bound into
  unrestricted losing/optimality.
- Do not let hidden delay/cadence branches choose separate future actions.
- Do not reset pending delay on held/no-write input.
- Do not use manager frame or a short wall-time threshold as the sole physical
  input clock.
- Do not grant candidate, label, continuation, or supplemental shadow output
  live action authority.
- Do not share optional work with the authoritative publication critical path
  without measuring contention.
- Do not reuse labels across immutable versions.
- Do not tune one stage/spell into universal mechanics.
- Do not add tests that protect only formatting, help text, or schema plumbing.
- Do not confuse compact reports with replay-capable raw evidence.
- Do not stage raw traces, screenshots, native builds, caches, game
  executables, or credentials.
