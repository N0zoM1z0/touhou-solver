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
- Last physical checkpoint: `d2b810d` (`Retain Stage 3 4A and 5 physical
  ring`).
- Native H=32 wind-tunnel checkpoint: `3d15953`.
- Workspace-prune checkpoint: `be3e583` (`Prune TH08 active research
  workspace`). It removed dormant supplemental, candidate, prewarm, G5,
  priority-17, and old focused Final-B lanes while preserving the promoted
  baseline/pre-loss live path, native snapshot executor, exact pipeline
  workspace, and Final-B scale authority.
- Final cleanup gates: Linux discovery passed 1,136 tests in 9.611 seconds;
  the complete Windows UNC discovery over the same test set exited zero.
  Linux and Windows native builds pass the checked-in 41-symbol ABI gate.
- No WS-H combat, Focus, or Power ranking currently changes physical input.
- `audits/` and `archive/` are untracked/local. Never stage them.

## Current Outcome

### Physical baselines

Latest user-authorized Lunatic Route-2 practice ring:

| Workload | Run | Hits | First hit | Bombs | Replay |
| --- | --- | ---: | ---: | ---: | --- |
| Stage 3 | `20260731_091104` | 5 | 2150 | 0 | accepted |
| Stage 4A | `20260731_091925` | 13 | 2555 | 0 | accepted |
| Stage 5 | `20260731_093027` | 12 | 2124 | 0 | accepted |

The automatic older-root comparisons were 15→5, 10→13, and 19→12. They are
observational only: RNG roots differ and the proposed WS-H strategies were
disabled.

Latest full game-start Lunatic Route-2 run:

- `lunatic_route2_fullrun_unattended_20260730_222529`
- 68 hits, zero Bombs
- stage counts `2/3/5/20/15/23`
- reached `route_complete`
- result-state replay save was unavailable after Final-B unload; do not rerun
  solely for that replay.

The five retained dossiers are under `notes/runs/`. Compact reports and valid
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

The active offline WS-H reconstruction now covers Route-2 normal shots,
supported native damage, enemy generations, defeat/cleanup distinction,
Boss transition identity, item allocation/pickup, Power/resources, and
mandatory timeline events. It is fail-closed and has no live ranking
authority.

The immediate high-value hypothesis is not another schema:

- spells: survival first;
- ordinary enemies: inside the survival-feasible set, test whether earlier
  kills prevent later saturation;
- dynamically compare focused micro-control with unfocused fast movement and
  shot coverage;
- collect early Power only when a safe path produces a causal later benefit.

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

Removed lanes must not be re-enabled from archive without a new causal need
and explicit `STRATEGY.md` decision.

## Next Useful Gate

The next agent should build one general combat/control experiment, not another
broad audit:

1. Select a first-hit-bounded, generation-safe ordinary-enemy root from the
   Stage 3/4A/5 corpus.
2. Capture complete player shots, enemy generation/HP, lifecycle, hostile
   births, item/resource state, RNG, and active/held input.
3. Reproduce the parent root exactly in native TH08.
4. Branch focused, unfocused, and causal refocus schedules inside the same
   survival-feasible action set.
5. Measure kill timing, prevented hostile births, Power transaction, minimum
   clearance, and native survival horizon.
6. Stop at the first unsupported event or model/native mismatch.
7. Repeat the winner on a second root before changing the live planner.
8. Only then pay one rotated focused physical trial.

If this hypothesis fails, return to the first mismatch or planner/action
factorization. Do not compensate with a stage-specific waypoint.

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
