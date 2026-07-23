# TH08 Reverse Engineering Workspace

This directory is the persistent workspace for the ongoing TH08 investigation.
All new notes, address maps, scripts, and generated analysis artifacts belong
under this directory.

## Version Control

This directory is an independent Git repository. Commit scripts, tests, notes,
IDA-derived address maps, and compact generated summaries at each verified
checkpoint. Large live JSONL captures, screenshots, daemon logs, and Python
caches remain local through `.gitignore`; keep a compact tracked summary for
any raw capture cited by a conclusion or regression test.

## Layout

- `notes/`: curated findings and chronological research logs
- `scripts/`: runtime entry points plus TH08 inspection and extraction tools
- `scripts/touhou_control/`: game-neutral online control components
- `tests/`: unit and retained-counterexample regression tests
- `artifacts/`: generated reports and small derived metadata (no game binaries)

## Current Investigation

The active topic is the stage danmaku pipeline:

1. stage selection and resource lookup
2. ECL loading and instruction scheduling
3. enemy VM execution
4. bullet creation APIs and bullet-pool updates
5. mapping individual stage scripts to observable patterns

The main pipeline through item 4 is structurally parsed. Complete ECL listings,
all 185 opcode slots, all 222 spell-card payloads, and pinned route manifests
are available under `artifacts/`. Static control flow now resolves the full
Sakuya/Remilia Lunatic Final A (33 cards), Final B (37 cards), and Extra
(14 cards) targets. Each reachable card now includes its phase-local
call/child/interrupt/auxiliary subgraph, transition exits, and per-subroutine
bullet/transform/laser/callback counts. These are analysis targets, not yet
solved input traces.
Route-2 Bomb resources now include executable Sakuya region geometry and
Remilia level-6/7 player-shot cadence, motion, collision, and damage models.
Laser kinematics, phase fallthrough, rotated collision, and graze geometry are
also executable in `scripts/th08_laser_model.py`.
All decoded bullet-transform record kinds, including Extra's two-record derived
emission, are mapped in `scripts/th08_bullet_transform_model.py`.
The native 32-entry ECL callback table is indexed in
`scripts/th08_ecl_callback_model.py`; all 19 indices reachable on the three
acceptance routes are named, and their solver-relevant projectile/time/item
rules are executable.
Item motion states 0/1/2/3/5, exact spawn RNG use, collection gating, type 0..8
resource effects, point-value conversion, and Lunatic/Extra point-item extend
thresholds are executable in `scripts/th08_item_model.py`.
The stable priority scheduler is game-independent in
`scripts/frame_schedule.py`; `scripts/th08_update_order.py` supplies the TH08
live/record/playback phases and exact solver-critical substep order.
Route-2 focus transitions and all four option shot-source positions are
executable in `scripts/th08_option_model.py`.
Game-neutral movement geometry is in `scripts/movement_model.py`; TH08 input
decoding, Bomb focus override, and the route-2 SHT profile are in
`scripts/th08_movement_model.py`.
Game-neutral pattern motion, easing, fixed spell-reward, timeline-gate, and
historical-hitbox-trail primitives are in `scripts/pattern_ir.py`.
`scripts/th08_enemy_movement_model.py` lowers ECL opcode `0xB2` into those
primitives while retaining TH08 RNG consumption, periodic horizontal
targeting, boundary reflection, and binary32 stores.
`scripts/th08_pattern_adapter.py` lowers TH08 pattern controls such as opcode
`0xAF`, and separates opcode `0x9D` visual trails from optional historical
collision. Every opcode used by the shipped 24-file ECL corpus now has an
observed or inferred meaning; the ten remaining unknown slots are unused.
The priority-9 route-2 player subset is executable in
`scripts/th08_route2_player_runtime.py`, including native spawn/focus
initialization, binary32 movement stores, and all route-2 Bomb movement-scale
timelines. `scripts/deterministic_sim.py` executes reconstructed handlers in
the observed stable frame order, and `scripts/state_trace.py` records exact
event-boundary projections plus the first mismatching field.
`scripts/th08_simulator.py` currently integrates replay publication, route-2
player state, stage timelines, item updates, base straight hostile bullets,
and laser/player contact through that executor. The full 66,386-frame Extra
input-only projection retains its binary32 position hash; its five native
Bomb/Last-Spell outcomes remain explicit differential targets.
`scripts/th08_runtime_agent.py` is the Windows-host bridge. It validates the
exact executable hash, reads solver-critical state with `ReadProcessMemory`,
and exposes an explicitly armed, foreground-gated `SendInput` path. Screenshots
are retained only for menu/bootstrap audits and are not a gameplay sensor.
`scripts/th08_attach_no_life_decrement.py` is the exact-image runtime patcher
used by `run_th08_no_life_decrement_attach.bat`; the bridge reports the live
patch byte on every probe. `scripts/touhou_control/viability.py` implements
game-neutral finite-horizon backward reachability with the exact control
quantifiers `exists action, forall learned delay`. The asynchronous TH08
corridor worker returns the complete policy kernel, and the live local
controller queries it by current age, position, and active input before
optimizing repair volume, clearance, items, or position.
`scripts/th08_live_dodge_agent.py` physically shoots and moves under this
policy, defaults to hard no-Bomb, and retains policy exhaustion in its trace.
This is the first integrated global-survival architecture, not yet a
physically accepted Lunatic/Extra solver.

Workspace evidence, artifact, counterexample, physical-trial, and checkpoint
requirements are binding in `AGENTS.md`. The robust planner derivation and its
current approximation boundary are in `notes/ROBUST_VIABILITY.md`.

## Reproduce

```bash
# List/extract the PBGZ archive.
python th08/scripts/th08_pbgz.py --help

# Remove the optional edz? resource wrapper.
python th08/scripts/th08_resource.py --help

# Validate or list decoded ECL files.
python th08/scripts/th08_ecl.py info th08/artifacts/decoded
python th08/scripts/th08_ecl.py corpus \
  th08/artifacts/decoded th08/artifacts/ecl_reports

# Regenerate the pinned Sakuya/Remilia route manifests.
python th08/scripts/th08_route_manifest.py \
  th08/artifacts/decoded th08/artifacts/route_manifests

# Decode local replays and emit compact frame-indexed input traces.
python th08/scripts/th08_replay.py \
  '/mnt/d/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)/replay' \
  th08/artifacts/replay_reports/local_replays.json \
  --trace-dir th08/artifacts/replay_reports/traces

# Project route-2 Extra controls without inventing unresolved Bomb outcomes.
python th08/scripts/th08_replay_player_projection.py \
  '/mnt/d/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)/replay/th8_06.rpy' \
  8 th08/artifacts/replay_reports/th8_06_stage8_player_projection.json

# Run all route, runtime-model, generic-schedule, and TH08 adapter tests.
PYTHONPATH=th08/scripts python -m unittest discover -s th08/tests -p 'test_*.py' -v

# On the Windows host, inspect the live process without writing game memory.
python th08/scripts/th08_runtime_agent.py probe

# Explicitly armed event-only capture of native replay Bomb boundaries.
python th08/scripts/th08_runtime_agent.py capture-replay-bombs \
  th08/artifacts/runtime_reports/th8_06_bomb_capture.jsonl --armed

# Physically control active route-2 gameplay from native projectile memory.
python th08/scripts/th08_live_dodge_agent.py \
  th08/artifacts/runtime_reports/live_dodge.jsonl --duration 60 --armed

# Stitch a completed multi-segment run into review and regression artifacts.
python th08/scripts/th08_run_dossier.py --help

# Execute structural/geometric invariants for every retained native hit.
python th08/scripts/th08_fullrun_regression.py \
  th08/artifacts/runtime_reports/lunatic_route2_fullrun_20260723.regressions.json
```

The curated model, address map, evidence distinctions, and remaining unknowns
are in `notes/DANMAKU_SYSTEM.md`. The solver acceptance contract and current
Extra baseline are in `notes/SOLVER_MODEL.md`.
