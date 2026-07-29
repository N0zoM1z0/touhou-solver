# Final-B SEM-SCALE Stage-Launched Live Delivery Gate

This is the preregistered original-game `SEM-SCALE-C5` falsifier after the
read-only C4 native-replay gate. THPRAC is not available. The existing
unattended Practice Start supervisor selects the whole Lunatic Final B
(`6b`) stage. The controller observes spell ID 190 automatically if the
stage reaches it, but exact delivery no longer stops the trial: the physical
research unit is the complete stage through native route unload.

This gate separates two scopes:

- **pre-target transport:** an explicit unknown-direction unit-scale
  approximation lets the existing solver traverse Final B from its stage
  start. It is proposal-only and has no hard scale authority; and
- **exact C5 scope:** begins at the coherent spell-190 quarter-scale source
  capture. Only this interval through the first sampled unit-scale row can
  pass the delivery gate.

The run is not a clean Final-B stage pass or Lunatic NMNB result merely
because the exact C5 scope passes. Pre-target hits, Power, position, and
death-patch residue remain visible and are reported separately.

## Fixed launch

- shipped `th08.exe` SHA-256
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`;
- verified no-life-decrement patch;
- original-game Practice Start, Lunatic, Sakuya/Remilia, Final B (`6b`,
  native stage-route index 7);
- decoded `ecldata7.ecl` SHA-256
  `20b35dca3820438f0b90ae44e3362a7af27d2fc1ac7ae5888c477dc1c89a3734`;
- hard no-Bomb for the entire trial; and
- no birth, combat, Power, unfocused-shot, ranking, shadow, or other
  experiment flags.

Run non-interactively from WSL:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_finalb_scale_live_trial.bat' \
  --status-seconds 15 --stall-timeout 120
```

The BAT delegates to the existing original-game practice supervisor. It
performs native menu selection, executable/patch/foreground verification,
prewarms the controller before final stage confirm, monitors the exact
interop process and trace, and always releases keys and terminates the
identity-verified game in cleanup.

Do not run Windows CLI probes during gameplay. WSL launch return is not
supervisor completion.

## Pre-target transport boundary

Before exact spell-190 authority exists, a sampled unit root receives a
256-frame constant unit schedule with provenance
`experimental_pretarget_unit_transport_unknown_direction`. This schedule may
drive the local and corridor policies, but its sensing row has
`hard_authority=false`; its repeated 256-frame tuples are omitted from raw
trace rows with `phase_schedule_omitted=true`. It is an explicit physical
transport experiment, not proof that no hidden writer exists.

If a pre-target root is non-unit and complete source is not due, the
controller waits without issuing input. Pre-target hit and resource history
do not become independent clean samples. The first hit of the fresh stage
attempt remains the canonical stage counterexample.

## Exact-scope acceptance

All of the following must pass:

- exact executable, patch, route, difficulty, stage, foreground, and runtime
  ECL identities;
- exactly one Bomb-zero, coherent 480-slot plus spell-owner source capture
  at spell 190 whose capture frame equals the controller root;
- one observed predeath baseline stable inside the source transaction and
  unchanged through the exact scope. Baseline zero is clean; nonzero residue
  is retained contamination and grants no clean-player authority;
- offset-zero exact live authority with the 300-frame schedule;
- every exact consumed row has one immutable
  gameplay/route/difficulty/stage/spell/source identity, the expected native
  root, complete remaining horizon, the same predeath baseline, and
  `live_exact_rebase` provenance;
- non-unit/varying exact coverage never enters the unsupported corridor;
- a sampled quarter row before relative frame 240 and a sampled unit row at
  or after 240, with callback 18 restoring `0.25 -> 1.0` at relative frame
  240 and no callback-28/29 bullet-velocity side effect;
- zero fresh hit edges and zero Bomb masks from exact offset zero through the
  first unit row;
- every pre-target decision is explicitly labeled experimental and every
  decision in the whole trial is no-Bomb;
- no exact-scope authority fallback, context/root/source mismatch, runtime
  error, or foreground loss; and
- normal `route_complete` termination after the complete stage plus exact
  supervisor/game cleanup. Exact restore completion remains a nested report
  gate and does not shrink the physical workload.

The first fresh hit after offset zero is the canonical C5 failure witness.
Any mismatch stops promotion and is routed through
`notes/COUNTEREXAMPLES.md`.

## Artifacts and authority

The supervisor retains the normal raw trace/session/dossier/death attribution
without comparing this partial scope to a completed Stage-6B baseline. It
also emits:

```text
artifacts/runtime_reports/lunatic_route2_stage6b_finalb_scale_delivery_TIMESTAMP.scale_delivery_report.json
```

The strict report schema is
`th08-finalb-scale-live-delivery-physical-report-v3`. Raw JSONL remains local
and ignored; retain its SHA-256, the compact strict report, normal summary,
first-hit attribution, resources/Power, timing, and cleanup state.

A strict pass observes exact schedule delivery and no fresh hit/Bomb across
one physical restore interval. It does not prove the pre-target transport,
clean Final-B survival, another RNG/resource history, Stage 3/4A/5, a normal
Power-0 route, Extra, or Lunatic NMNB.

## Observed C5-1 result and correction

The 2026-07-29 run
`lunatic_route2_stage6b_finalb_scale_delivery_20260729_233720`
completed Stage 6B but failed the exact gate:

- 17,282 decisions, 19 hits, zero Bomb masks;
- canonical fresh-attempt hit at nonspell frame 8,085;
- final hit at spell-190 frame 73,477;
- first quarter-scale wait at frame 73,600; and
- route unload at frame 74,080 without an accepted complete source.

The player was phase 3 with predeath residue 7 immediately before the
quarter window and returned to phase 0 only after the native root restored to
unit. CE-0188 therefore rejects the old phase-0-only trigger. Raw JSONL
SHA-256 is
`11ba10fb1ac771e138627cff0e6faf7855e0858c5cf70b88c0fa2c9966e52b8a`.
The post-close strict v3 report SHA-256 is
`18f26f3f2d27234ae2b419aa01966fd3c646b0268419e4af76c7ac60398ca0a6`.
No replay was created.

The corrected gate captures `player_phase` in the coherent source
transaction and permits phase-3 delivery as explicit contamination. It does
not promote that row to normal-player survival. An incomplete or mismatched
C5 schedule now waits without a new input write and continues the physical
run; it still fails the strict report.

Focused Ruff/tests and complete Linux/Windows discovery pass 1,137 tests in
13.612/30.825 seconds, with three existing Windows skips.

## Observed full-route reachability result and C5-2 scope

The 2026-07-30 original Game Start run
`lunatic_route2_fullrun_unattended_20260730_002115` exercised the corrected
non-aborting continuation from Power 0 through `route_complete`: 60,877
decisions, 74 hits, zero Bomb masks, and exact cleanup. It did not exercise an
exact C5 source. Final B entered spells 174/178 for 299/311 decisions but
never entered 182/186/190; every root remained unit scale. The strict report
therefore correctly has zero authority rows and fails. No replay was created.
CE-0189 retains the gate-coverage failure separately from stage survival.

The next authorized C5-2 trial uses the same command above and the same
original-game whole Stage-6B launch. It:

- requires no THPRAC, precise-spell selection, or operator-time feature
  activation;
- carries the corrected phase-contamination source contract from stage start;
- keeps restore auto-stop disabled and retains the whole stage even after an
  exact pass or mismatch;
- treats the first post-source hit or exact identity mismatch as the C5
  witness without discarding later stage evidence; and
- reports exact delivery, whole-stage hits/Bombs/resources, and spell
  reachability as separate conclusions.

The whole-stage auto-stop correction and dossier-v4 coverage report pass
complete Linux/Windows discovery: 1,140 tests in 13.404/29.833 seconds, with
the three existing Windows skips.
