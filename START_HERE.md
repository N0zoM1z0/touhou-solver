# Touhou Solver Current Handoff

Last updated: 2026-07-31.

This is the only volatile entrypoint. Read `AGENTS.md`, `GOAL.MD`, then this
file, `STRATEGY.md`, and the focused task card in
`notes/review/TH08_LUNATIC_NMNB_RESEARCH_TASKBOOK.md`.

Historical material removed from the active tree is recoverable through
`ARCHIVE_INDEX.md` and tag `pre-workspace-prune-20260731`. It has no current
authority.

## Checkpoint

- Branch: `main`.
- Last physical checkpoint:
  `lunatic_route2_stage4a_unattended_20260731_152921`, based on immutable
  live-code checkpoint `1c64751`.
- Native H=32 wind-tunnel checkpoint: `3d15953`.
- Workspace-prune checkpoint: `be3e583` (`Prune TH08 active research
  workspace`). It removed dormant supplemental, candidate, prewarm, G5,
  priority-17, and old focused Final-B lanes while preserving the promoted
  baseline/pre-loss live path, native snapshot executor, exact pipeline
  workspace, and Final-B scale authority.
- Current Linux discovery passed 1,196 tests in 9.377 seconds. The affected
  Windows UNC delivery/parser/planner gate passed 188 tests; complete Windows
  discovery remains the pre-physical-promotion gate. Linux and Windows native
  builds at the preceding checkpoint pass the checked-in 41-symbol ABI gate.
- **Implemented, deterministic gate closed:** default-off
  `--ordinary-preexhaustion-authority` no longer uses scalar boundary
  reserve. It now forms the exact observed active/held/pending root, checks
  every pickup branch through a fresh signed-clearance prefix, and takes the
  causal predecessor of a completed future signed safety-value policy at its
  publication epoch. Full per-action values are retained; live-to-lattice
  error is subtracted before certification. A pending held mask remains
  no-write, and zero residual pickup is conservatively included in the future
  policy delay support.
- The hard result is versioned and fail closed. Coverage must span the current
  observation, publication lead, and complete future policy horizon. The
  existing unseen-birth/event slab remains `UNKNOWN`, so it produces
  diagnostic candidate/recovery sets but no `allowed_actions`. Observed-body
  early kill is applied only inside a nonempty hard set; an empty predecessor
  is never relaxed for the objective.
- In the physical gate, all 7,202 nonspell decisions were incorrectly
  rejected by the `player_transition_or_predeath` eligibility check, so the
  filter and early-kill preference each affected zero decisions. Native
  evidence shows player `+0xE2A68` retains a deathbomb-window limit and is not
  zero while alive. More importantly, an offline counterfactual with only
  that check removed still permits the canonical `down_left` action and
  degenerates to all 17 actions under an uncontrollable prefix and at a
  clamped boundary. Scalar boundary reserve is not equivalent to global
  viability; do not rerun this design.
- The retained f817/833/835/850/910 regression is now explicit. Native
  transition eligibility uses player phase (1/2 are transition/death;
  movement phases 0/3 remain eligible) and ignores the retained value 10.
  Hazard-space recovery remains directional: `left_fast` is best at f835 and
  f910 while scalar reserve ties all 17 actions at f850/f910. The source run
  predates retained signed per-action values and every future slab is
  `model_unknown`, so the required nontrivial exact allowed set is unresolved
  and the authorized Stage-4A physical trial was not run.
- `--kill-before-saturation` now uses observed ordinary bodies only. The
  falsified timeline spawn forecast is withheld from live input.
  Observed-body alignment/unfocus remains a proposed objective, but the
  rejected reserve set is no longer an eligibility source; exact ordinary
  viable membership and fresh issue safety are required before another live
  gate.
- `audits/` and `archive/` are untracked/local. Never stage them.

## Current Outcome

### Physical baselines

Latest user-authorized Lunatic Route-2 practice ring:

| Workload | Run | Hits | First hit | Bombs | Replay |
| --- | --- | ---: | ---: | ---: | --- |
| Stage 3 | `20260731_091104` | 5 | 2150 | 0 | accepted |
| Stage 4A | `20260731_091925` | 13 | 2555 | 0 | accepted |
| Stage 5 | `20260731_093027` | 12 | 2124 | 0 | accepted |
| Stage 5 early-kill gate | `20260731_122855` | 13 | 6981 | 0 | accepted |
| Stage 4A global/early-kill gate | `20260731_130103` | 16 | 1827 | 0 | accepted |
| Stage 4A pre-exhaustion early-kill gate | `20260731_133852` | 11 | 4148 | 0 | accepted |
| Stage 4A forecast/global investigation | `20260731_142342` | 18 | 1915 | 0 | accepted |
| Stage 4A reserve-authority falsifier | `20260731_152921` | 17 | 914 | 0 | accepted |

The automatic older-root comparisons were 15→5, 10→13, and 19→12. They are
observational only: RNG roots differ and the proposed WS-H strategies were
disabled in the original ring. The later early-kill gate is also
different-RNG: it physically applied 27 certified unfocus preferences,
delayed first hit by 4857 frames relative to the listed Stage-5 baseline, but
worsened total hits by one.

The newest Stage-4A run is different-RNG and its 17/914 aggregate is
observational. Its experiment activation is decisive: the flag was present
on all 12,029 decisions but yielded zero eligible, applicable, or effective
constraints and zero early-kill applications. All 7,202 nonspell decisions
failed on a stale native-field interpretation. The canonical hit also
falsifies a gate-only repair. Contact bullet slot 455 first entered the
retained nearby set at decision 817; the snapshot-801 global policy still
certified `down_left` through frame 833, while the snapshot-818 policy
delivered an empty set at 835. The compact trace cannot attribute that version
flip to slot 455 alone. Counterfactual reserve evaluation still allowed
`down_left` there and allowed all 17 actions at frames 850 and 910. Robust
local prefixes exhausted only at 910, four frames before the hit.

The physical forecast gate also falsified the current timeline observer as a
general later-wave source. All 376 observations recycled the same timeline-0
startup birth at time 1, x=30, and only three affected input. Full-health
observed-body targeting remains useful, but zero-pointer timeline lifecycle
must be disambiguated before the birth forecast is trusted again. The live
forecaster is now disabled rather than used as an eligibility source.

Latest full game-start Lunatic Route-2 run:

- `lunatic_route2_fullrun_unattended_20260730_222529`
- 68 hits, zero Bombs
- stage counts `2/3/5/20/15/23`
- reached `route_complete`
- result-state replay save was unavailable after Final-B unload; do not rerun
  solely for that replay.

Retained dossiers are under `notes/runs/`. Compact reports and valid
practice replays remain under `artifacts/`.

### Native wind tunnel

Canonical Stage-5 replay first hit:

- manager frame 2136;
- root frame 2129;
- recorded mask `0x05`;
- hostile bullet slot 45;
- signed separation `-0.966766`.

The rolling executor replaces only the fixed native calculation-chain call,
holds the owner at the root, freezes unrelated threads, executes original
TH08 update code, and restores a verified same-session root. Parent replay is
bit/exact-state checked before branch authority.

Observed result:

- all 36 no-Bomb root masks were executed in original TH08;
- 324 causal branches were searched;
- a warm session executed 180 branches in 309.089 seconds with exact parent
  repeats;
- policy `0x94 -> 0x44 -> 0x10 -> 0xA4` at frames
  `2129/2137/2145/2153` stays unhit through frame 2161;
- an H=32 natural frame pump matches 32/32 native snapshot ticks.

This proves one exact fixed-root, fixed-horizon original-engine witness. It
does not prove a full spell, live delivery, or physical NMNB.

Primary evidence:

- `artifacts/runtime_reports/th08_native_snapshot_causal_policy_root2129_h32_20260730.json`
- `artifacts/runtime_reports/th08_native_model_trajectory_root2129_h32_20260730.json`
- `artifacts/runtime_reports/th08_native_model_consumable_h1_root2129_20260730.json`
- `artifacts/runtime_reports/th08_native_state2_lifecycle_root2129_h8_20260730.json`
- `artifacts/runtime_reports/th08_native_h1_ecl_source_differential_root2129_20260730.json`
- `notes/architecture/NATIVE_REPLAY_CAUSAL_WIND_TUNNEL_AND_REPLAY_SAVE_CONTRACT_20260730.md`

The old closed-form slot-45 forecast first differed by one x ULP. A corrected
per-update binary32 recurrence matches the retained native fixture. The
current source differential still returns `UNKNOWN` at the unresolved
pre-enemy/pre-aux producer; do not infer it from retrospective RNG alignment.

One mapping-epoch poison event is retained. A future persistent warm service
must use single-writer ownership, immutable session/root IDs, branch
validation, cooperative cancellation, idle TTL, poison cleanup, and automatic
rebootstrap. Do not weaken the epoch gate for speed.

### Combat/resource model

The active WS-H reconstruction now covers Route-2 normal shots,
supported native damage, enemy generations, defeat/cleanup distinction,
Boss transition identity, item allocation/pickup, Power/resources, and
mandatory timeline events. Its general combat model remains offline. The only
live combat experiment is the narrow default-off ordinary-enemy alignment
preference described above. It has no independent safety authority.

The immediate high-value hypothesis is not another schema:

- spells: survival first;
- ordinary enemies: inside the survival-feasible set, test whether earlier
  kills prevent later saturation;
- dynamically compare focused micro-control with unfocused fast movement and
  shot coverage;
- collect early Power only when a safe path produces a causal later benefit.

The first Stage-5 root-4300 test is complete. **Observed:** clearing Focus for
eight ticks defeated one 20-HP enemy, suppressed three later hostile bullets
per nine-frame emission cadence, and reduced the endpoint bullet count
548→539. **Observed:** the current offline global layer-0 viable masks and
safe-action masks remained exact-equal at frames 4314/4323/4332. That offline
result did not end the hypothesis; the physical gate below exercised the rule
27 times, but global live guidance still never published.

See `notes/CURRENT_COMBAT_RESOURCE_MODEL.md`.

## Live Authority

The physical policy is hard no-Bomb:

1. native state sensing and hazard projection;
2. native packed bullet decode;
3. robust Boolean viability;
4. baseline local beam plus promoted pre-loss continuation preference;
5. fresh issue-time collision certificate;
6. exact-version action transaction and fail-safe fallback.

Final-B uses the exact pinned global-time-scale schedule. The root-only
constant-scale continuation is diagnostic and unknown-direction, never a
general hard-safety authority.

The rejected scalar pre-exhaustion experiment is no longer connected to live
input. The replacement remains default-off and has no action authority while
ordinary birth/event coverage is unknown.

Removed lanes must not be re-enabled from archive without a new causal need
and explicit `STRATEGY.md` decision.

## Next Useful Gate

Do not pay another physical run for the current scalar-reserve design, and do
not run the conditional Stage-5 follow-up. Next:

1. Keep the corrected phase-only capture/issue predicate and the
   signed/off-grid active/held/pending prepublication predecessor.
2. Establish bounded ordinary future-birth/event coverage over the combined
   prefix plus future-policy interval. Do not promote the existing `UNKNOWN`
   slab or substitute the falsified timeline observer.
3. Recompute the retained chain with signed per-action values and require a
   nontrivial exact set before f835. The current source trace cannot answer
   that because those values were not retained.
4. Only after steps 2–3 pass, run the already authorized single fresh
   Stage-4A physical trial. The current hard gate says not to run.
5. Preserve observed-body early kill only inside that exact set. Hostile-birth
   modeling is the blocker; local ranking remains later.

Do not compensate with a stage-specific waypoint.

## Research Loop

Use this sequence:

`first hit/root -> exact parent repeat -> offline/native branches -> first mismatch -> one general change -> same-root win -> native replay confirmation -> rotated focused physical trial -> full route after a major integrated gain`

All-36 portfolios, long horizons, complete test suites, and full physical
routes are milestone gates, not mandatory per-edit checks.

## Commands

### Import smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 - <<'PY'
import th08_live.controller
import th08_runtime.native_snapshot
import th08_runtime.native_snapshot_projection
import tools.th08_native_snapshot_causal_search
import analysis.th08_native_combat_branch_report
import th08_automation.practice_supervisor
import th08_automation.full_route_supervisor
print("import smoke: ok")
PY
```

### Focused and complete Linux tests

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_relevant_file.py'

PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

### Windows UNC discovery

Do not use `cmd.exe cd/pushd` or ordinary UNC discovery. Use:

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe -c \
  'import sys,unittest; root=r"\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08"; sys.path.insert(0,root+r"\scripts"); tests=root+r"\tests"; suite=unittest.TestLoader().discover(tests,pattern="test_*.py",top_level_dir=tests); result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(0 if result.wasSuccessful() else 1)'
```

Change only `pattern` for a focused Windows run. Do not run Linux and Windows
performance gates concurrently.

### Native build

```bash
python3 scripts/tools/build_native_planner.py --target linux
python3 scripts/tools/build_native_planner.py --target windows
```

Use `TOUHOU_DISABLE_NATIVE_PLANNER=1` only for an explicit rollback/ablation.

### Physical trials

Run only with explicit user authorization from Windows:

```bat
run_th08_practice_agent.bat --stage 3
run_th08_practice_agent.bat --stage 4a
run_th08_practice_agent.bat --stage 5
run_th08_practice_agent.bat --stage 6b
run_th08_full_route_agent.bat
```

The BAT wrappers add `--armed`. F8 starts, F9 stops, and F10 exits. Before
launch verify TH08 identity, foreground, route/difficulty, gameplay state,
no-life-decrement patch, and no-Bomb configuration. Monitor trace growth and
the exact interop process; always release keys and clean up.

## Common Traps

- Different-RNG hit totals are not controlled A/B evidence.
- A later hit is not independent after the first hit changed resources.
- A replay future cannot be reused after a different action.
- Native/Python parity is not model completeness.
- Static shot width, damage, item availability, or Power gain is not survival
  improvement.
- More tests, reports, schemas, or audited addresses are not solver progress
  unless they unblock a causal hit-reduction experiment.
- Do not restore retired code because an archived note mentions it.
